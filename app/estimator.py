import cv2
import numpy as np
from .utils import decode_image, remove_background, trim_image

class StitchEstimator:
    def __init__(self, image_bytes: bytes, target_width_inches: float, parameters=None):
        self.original_image = decode_image(image_bytes)
        self.target_width_inches = target_width_inches
        self.processed_image = None
        self.pixels_per_inch = 300
        
        # Use parameters from request or defaults
        if parameters:
            self.FILL_DENSITY = parameters.fill_density
            self.SATIN_SPACING_INCH = parameters.satin_spacing_inch
            self.RUNNING_DENSITY_PER_INCH = parameters.running_density_per_inch
            self.STITCHES_PER_COLOR = parameters.stitches_per_color
            self.UNDERLAY_FILL_RATIO = parameters.underlay_fill_ratio
            self.SATIN_MIN_WIDTH_INCH = parameters.satin_min_width_inch
            self.SATIN_MAX_WIDTH_INCH = parameters.satin_max_width_inch
        else:
            # Default values
            self.FILL_DENSITY = 1002.9
            self.SATIN_SPACING_INCH = 0.0108
            self.RUNNING_DENSITY_PER_INCH = 18.1
            self.STITCHES_PER_COLOR = 39
            self.UNDERLAY_FILL_RATIO = 0.165
            self.SATIN_MIN_WIDTH_INCH = 0.0236
            self.SATIN_MAX_WIDTH_INCH = 0.471
        
    def process_image(self):
        # 1. Remove background
        img = remove_background(self.original_image)
        
        # 1.5 Trim empty spaces
        img = trim_image(img)

        # Calculate scale based on TRIMMED width to preserve physical size of the actual design
        original_height, original_width = img.shape[:2]
        
        # Avoid division by zero
        if original_width == 0:
            original_width = 1
            
        scale_factor = (self.target_width_inches * self.pixels_per_inch) / original_width
        
        # 2. Resize using the calculated scale factor
        current_height, current_width = img.shape[:2]
        
        new_width = int(current_width * scale_factor)
        new_height = int(current_height * scale_factor)
        
        if new_width <= 0: new_width = 1
        if new_height <= 0: new_height = 1
            
        self.processed_image = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Update physical dimensions to reflect the trimmed size
        self.physical_width = new_width / self.pixels_per_inch
        self.physical_height = new_height / self.pixels_per_inch

    def quantize_colors(self, k=8) -> dict:
        """
        Reduces image to k dominant colors and returns masks for each.
        """
        img = self.processed_image
        
        # Reshape to list of pixels
        pixels = img.reshape((-1, 4))
        
        # Filter out transparent pixels
        valid_pixels_mask = pixels[:, 3] > 0
        valid_pixels = pixels[valid_pixels_mask]
        
        if len(valid_pixels) == 0:
            return {}
            
        # We only care about RGB for clustering
        valid_rgb = valid_pixels[:, :3].astype(np.float32)
        
        # K-Means
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        k = min(k, len(valid_rgb))
        
        if k == 0:
            return {}
            
        _, labels, centers = cv2.kmeans(valid_rgb, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Create masks for each label
        masks = {}
        
        # Map labels back to original image shape
        full_labels = np.full(pixels.shape[0], -1, dtype=np.int32)
        full_labels[valid_pixels_mask] = labels.flatten()
        full_labels = full_labels.reshape((img.shape[0], img.shape[1]))
        
        for i in range(k):
            mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
            mask[full_labels == i] = 255
            masks[i] = mask
            
        return masks

    def analyze_contours(self, mask) -> list:
        """
        Finds contours in a mask and classifies them using Distance Transform for width.
        Returns list of dicts: {'type': 'fill'|'satin'|'running', 'area': float, 'length': float, 'avg_width': float}
        """
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return []
            
        hierarchy = hierarchy[0]
        results = []
        
        # Distance Transform on the entire mask for width estimation
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        
        for i, cnt in enumerate(contours):
            if hierarchy[i][3] != -1:
                continue
                
            # Calculate metrics for Outer Contour
            outer_area_px = cv2.contourArea(cnt)
            perimeter_px = cv2.arcLength(cnt, True)
            
            # Calculate Hole Area
            hole_area_px = 0
            child_idx = hierarchy[i][2]
            while child_idx != -1:
                hole_area_px += cv2.contourArea(contours[child_idx])
                child_idx = hierarchy[child_idx][0]
            
            net_area_px = outer_area_px - hole_area_px
            if net_area_px < 0: net_area_px = 0
            
            if net_area_px == 0 and perimeter_px == 0:
                continue
                
            # Convert to physical units
            net_area_sq_in = net_area_px / (self.pixels_per_inch ** 2)
            perimeter_in = perimeter_px / self.pixels_per_inch
            
            # Estimate Width using Distance Transform
            c_mask = np.zeros_like(mask)
            cv2.drawContours(c_mask, [cnt], -1, 255, -1)
            child_idx = hierarchy[i][2]
            while child_idx != -1:
                cv2.drawContours(c_mask, [contours[child_idx]], -1, 0, -1)
                child_idx = hierarchy[child_idx][0]
            
            valid_dists = dist_transform[c_mask > 0]
            
            avg_width_px = 0
            max_width_px = 0
            
            if len(valid_dists) > 0:
                avg_width_px = 4 * np.mean(valid_dists)
                max_width_px = 2 * np.max(valid_dists)
                
            avg_width_in = avg_width_px / self.pixels_per_inch
            max_width_in = max_width_px / self.pixels_per_inch
            
            # Classification Logic using dynamic thresholds
            stitch_type = 'fill'
            
            if net_area_sq_in < 0.0005: 
                stitch_type = 'running'
            elif max_width_in < self.SATIN_MIN_WIDTH_INCH:
                stitch_type = 'running'
            elif max_width_in <= self.SATIN_MAX_WIDTH_INCH:
                stitch_type = 'satin'
            else:
                stitch_type = 'fill'
                
            results.append({
                'type': stitch_type,
                'area': net_area_sq_in,
                'length': perimeter_in,
                'avg_width': avg_width_in,
                'max_width': max_width_in
            })
            
        return results

    def estimate(self) -> dict:
        if self.processed_image is None:
            self.process_image()
            
        # 1. Segment Colors
        color_masks = self.quantize_colors(k=12)
        
        total_stitches = 0
        details = {
            'fill_stitches': 0,
            'satin_stitches': 0,
            'running_stitches': 0,
            'color_change_stitches': 0,
            'underlay_stitches': 0,
            'color_count': len(color_masks),
        }
        
        # 2. Analyze each color
        for color_idx, mask in color_masks.items():
            contours_data = self.analyze_contours(mask)
            
            color_stitches = 0
            
            for item in contours_data:
                stitches = 0
                underlay = 0
                
                if item['type'] == 'fill':
                    stitches = item['area'] * self.FILL_DENSITY
                    underlay = stitches * self.UNDERLAY_FILL_RATIO
                    details['fill_stitches'] += stitches
                    
                elif item['type'] == 'satin':
                    estimated_length = 0
                    if item['avg_width'] > 0:
                        estimated_length = item['area'] / item['avg_width']
                    
                    if estimated_length > 0:
                        steps = estimated_length / self.SATIN_SPACING_INCH
                        stitches = steps * 2
                        
                        underlay_factor = 1.0
                        if item['avg_width'] > 0.08:
                            underlay_factor = 2.0
                            
                        underlay = estimated_length * self.RUNNING_DENSITY_PER_INCH * underlay_factor
                        
                    details['satin_stitches'] += stitches
                    
                elif item['type'] == 'running':
                    length = item['length'] / 2
                    stitches = length * self.RUNNING_DENSITY_PER_INCH
                    details['running_stitches'] += stitches
                
                details['underlay_stitches'] += underlay
                color_stitches += (stitches + underlay)
            
            # Add color change penalty
            if color_stitches > 10:
                total_stitches += self.STITCHES_PER_COLOR
                details['color_change_stitches'] += self.STITCHES_PER_COLOR
            
            total_stitches += color_stitches
            
        # Final Rounding
        final_count = int(total_stitches)
        
        # Add dimensions to details
        details['physical_dimensions'] = f"{self.physical_width:.2f}x{self.physical_height:.2f} inches"
        
        # Clean up details for JSON
        details['fill_stitches'] = int(details['fill_stitches'])
        details['satin_stitches'] = int(details['satin_stitches'])
        details['running_stitches'] = int(details['running_stitches'])
        details['underlay_stitches'] = float(details['underlay_stitches'])
        
        return {
            "stitch_count": final_count,
            "details": details
        }