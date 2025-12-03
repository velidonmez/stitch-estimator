import cv2
import numpy as np
from .utils import decode_image, remove_background

class StitchEstimator:
    # --- DENSITY CONSTANTS ---
    # Tatami Fill: ~2400 stitches/sq inch (increased from 2000 for better coverage/pull comp)
    FILL_DENSITY = 2400.0
    
    # Satin Spacing: 0.35mm (~0.0138 inches)
    # Decreased from 0.4mm to increase density
    SATIN_SPACING_INCH = 0.0138
    
    # Running Stitch: ~40 stitches per inch (approx 0.6mm stitch length)
    # Increased to account for travel runs and details
    RUNNING_DENSITY_PER_INCH = 40.0
    
    # --- GLOBAL FACTORS ---
    # Stitches added per color change (trim, tie-off, tie-in)
    STITCHES_PER_COLOR = 20
    
    # Underlay factors
    # Satin: Center run (1x length) or Double (2x length) if wide
    # Fill: Lattice (approx 35% of top density, increased from 20%)
    UNDERLAY_FILL_RATIO = 0.35
    
    # Thresholds
    SATIN_MIN_WIDTH_INCH = 0.015  # ~0.38mm (lowered to catch thin satin columns)
    SATIN_MAX_WIDTH_INCH = 0.35  # ~9mm
    
    def __init__(self, image_bytes: bytes, target_width_inches: float):
        self.original_image = decode_image(image_bytes)
        self.target_width_inches = target_width_inches
        self.processed_image = None
        # Increased resolution for better detail and width estimation
        self.pixels_per_inch = 300 
        
    def process_image(self):
        # 1. Remove background
        img = remove_background(self.original_image)
        
        # 2. Resize
        height, width = img.shape[:2]
        aspect_ratio = height / width
        target_height_inches = self.target_width_inches * aspect_ratio
        
        new_width = int(self.target_width_inches * self.pixels_per_inch)
        new_height = int(target_height_inches * self.pixels_per_inch)
        
        self.processed_image = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        self.physical_width = self.target_width_inches
        self.physical_height = target_height_inches

    def quantize_colors(self, k=8) -> dict:
        """
        Reduces image to k dominant colors and returns masks for each.
        """
        img = self.processed_image
        
        # Reshape to list of pixels
        pixels = img.reshape((-1, 4))
        
        # Filter out transparent pixels
        # Alpha is at index 3
        valid_pixels_mask = pixels[:, 3] > 0
        valid_pixels = pixels[valid_pixels_mask]
        
        if len(valid_pixels) == 0:
            return {}
            
        # We only care about RGB for clustering
        valid_rgb = valid_pixels[:, :3].astype(np.float32)
        
        # K-Means
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        # If less pixels than k, adjust k
        k = min(k, len(valid_rgb))
        
        _, labels, centers = cv2.kmeans(valid_rgb, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Create masks for each label
        masks = {}
        
        # Map labels back to original image shape
        # Initialize full labels array with -1
        full_labels = np.full(pixels.shape[0], -1, dtype=np.int32)
        full_labels[valid_pixels_mask] = labels.flatten()
        full_labels = full_labels.reshape((img.shape[0], img.shape[1]))
        
        for i in range(k):
            # Create binary mask for this color
            mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
            mask[full_labels == i] = 255
            masks[i] = mask
            
        return masks

    def analyze_contours(self, mask) -> list:
        """
        Finds contours in a mask and classifies them using Distance Transform for width.
        Returns list of dicts: {'type': 'fill'|'satin'|'running', 'area': float, 'length': float, 'avg_width': float}
        """
        # Use RETR_CCOMP to handle holes
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return []
            
        hierarchy = hierarchy[0]
        results = []
        
        # Distance Transform on the entire mask for width estimation
        # We need a binary image where the object is white (255)
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        
        for i, cnt in enumerate(contours):
            # If parent is not -1, it's a hole (child), skip it. We process it via parent.
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
                child_idx = hierarchy[child_idx][0] # Next sibling
            
            net_area_px = outer_area_px - hole_area_px
            if net_area_px < 0: net_area_px = 0
            
            if net_area_px == 0 and perimeter_px == 0:
                continue
                
            # Convert to physical units
            net_area_sq_in = net_area_px / (self.pixels_per_inch ** 2)
            perimeter_in = perimeter_px / self.pixels_per_inch
            
            # Estimate Width using Distance Transform
            # Create a mask for just this contour to sample the distance transform
            c_mask = np.zeros_like(mask)
            cv2.drawContours(c_mask, [cnt], -1, 255, -1)
            # Subtract holes
            child_idx = hierarchy[i][2]
            while child_idx != -1:
                cv2.drawContours(c_mask, [contours[child_idx]], -1, 0, -1)
                child_idx = hierarchy[child_idx][0]
            
            # Mean distance inside the shape
            # Distance transform gives distance to nearest zero pixel (boundary)
            valid_dists = dist_transform[c_mask > 0]
            
            avg_width_px = 0
            max_width_px = 0
            
            if len(valid_dists) > 0:
                # For a ribbon shape (Satin), Mean Dist is approx Width / 4
                # So Avg Width = 4 * Mean Dist
                avg_width_px = 4 * np.mean(valid_dists)
                # Max width is 2 * Max Dist
                max_width_px = 2 * np.max(valid_dists)
                
            avg_width_in = avg_width_px / self.pixels_per_inch
            max_width_in = max_width_px / self.pixels_per_inch
            
            # Classification Logic
            stitch_type = 'fill'
            
            if net_area_sq_in < 0.0005: 
                # Tiny specks -> noise or running
                stitch_type = 'running'
            elif max_width_in < self.SATIN_MIN_WIDTH_INCH:
                # Too thin for satin -> running stitch
                stitch_type = 'running'
            elif max_width_in <= self.SATIN_MAX_WIDTH_INCH:
                # Within satin range
                stitch_type = 'satin'
            else:
                # Too wide -> Fill
                stitch_type = 'fill'
                
            results.append({
                'type': stitch_type,
                'area': net_area_sq_in,
                'length': perimeter_in, # Outer perimeter, not skeleton length
                'avg_width': avg_width_in
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
            # 'breakdown': []
        }
        
        # 2. Analyze each color
        for color_idx, mask in color_masks.items():
            contours_data = self.analyze_contours(mask)
            
            color_stitches = 0
            
            for item in contours_data:
                stitches = 0
                underlay = 0
                
                if item['type'] == 'fill':
                    # Area based
                    stitches = item['area'] * self.FILL_DENSITY
                    # Underlay: Lattice
                    underlay = stitches * self.UNDERLAY_FILL_RATIO
                    
                    details['fill_stitches'] += stitches
                    
                elif item['type'] == 'satin':
                    # Satin Formula: (Length / Spacing) * 2
                    # But we don't have the centerline length directly.
                    # We have Area and AvgWidth.
                    # Length ~ Area / AvgWidth
                    estimated_length = 0
                    if item['avg_width'] > 0:
                        estimated_length = item['area'] / item['avg_width']
                    
                    if estimated_length > 0:
                        # Zigzag: 2 stitches per step
                        steps = estimated_length / self.SATIN_SPACING_INCH
                        stitches = steps * 2
                        
                        # Underlay: Center run (1x length)
                        # If wide (> 2mm / 0.08"), add double underlay (edge run or double zigzag)
                        underlay_factor = 1.0
                        if item['avg_width'] > 0.08:
                            underlay_factor = 2.0
                            
                        underlay = estimated_length * self.RUNNING_DENSITY_PER_INCH * underlay_factor
                        
                    details['satin_stitches'] += stitches
                    
                elif item['type'] == 'running':
                    # Use perimeter for running stitch length?
                    # If it's a thin line, perimeter is ~2x length.
                    # If it's a speck, perimeter is adequate.
                    # Let's assume perimeter / 2 for lines, or just perimeter for outline?
                    # If it was classified as running because it's thin, it's likely a line.
                    # Perimeter of a line is 2 * length + 2 * width.
                    # So length ~ perimeter / 2.
                    length = item['length'] / 2
                    stitches = length * self.RUNNING_DENSITY_PER_INCH
                    details['running_stitches'] += stitches
                
                details['underlay_stitches'] += underlay
                color_stitches += (stitches + underlay)
                
                
                # details['breakdown'].append({
                #     'color_idx': color_idx,
                #     'type': item['type'],
                #     'area_sq_in': float(f"{item['area']:.4f}"),
                #     'avg_width_in': float(f"{item['avg_width']:.4f}"),
                #     'stitches': float(stitches),
                #     'underlay': float(underlay)
                # })
            
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

