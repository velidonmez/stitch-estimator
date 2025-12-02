import cv2
import numpy as np
from .utils import decode_image, remove_background

class StitchEstimator:
    # --- DENSITY CONSTANTS ---
    # Tatami Fill: ~1800 stitches/sq inch (standard coverage)
    # Adjusted to 1800 based on net area calculation.
    FILL_DENSITY = 1800.0
    
    # Satin Column: Calculated based on area but with higher density factor
    # or based on length. For simplicity and robustness, we treat it as
    # a denser fill. Satin is often 4-5x denser than fill in terms of lines,
    # but covers less area.
    # Let's use a multiplier on the fill density.
    SATIN_DENSITY_MULTIPLIER = 1.5  # 2700 stitches/sq inch equivalent
    
    # Running Stitch: For very thin lines.
    # ~12 stitches per inch (approx 2mm stitch length)
    RUNNING_DENSITY_PER_INCH = 12.0
    
    # --- GLOBAL FACTORS ---
    # Stitches added per color change (trim, tie-off, tie-in)
    STITCHES_PER_COLOR = 20
    
    # Underlay factor: Add % to total for underlay stitches
    # Reduced to 10%
    UNDERLAY_FACTOR = 0.10

    def __init__(self, image_bytes: bytes, target_width_inches: float):
        self.original_image = decode_image(image_bytes)
        self.target_width_inches = target_width_inches
        self.processed_image = None
        self.pixels_per_inch = 100 # Standard processing resolution
        
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
        Finds contours in a mask and classifies them.
        Returns list of dicts: {'type': 'fill'|'satin'|'running', 'area': float, 'length': float}
        """
        # Use RETR_CCOMP to handle holes (hierarchy: [Next, Prev, First_Child, Parent])
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return []
            
        hierarchy = hierarchy[0]
        results = []
        
        for i, cnt in enumerate(contours):
            # If parent is not -1, it's a hole (child), skip it. We process it via parent.
            if hierarchy[i][3] != -1:
                continue
                
            # Calculate metrics for Outer Contour
            outer_area_px = cv2.contourArea(cnt)
            perimeter_px = cv2.arcLength(cnt, True)
            
            # Calculate Hole Area and Count
            hole_area_px = 0
            hole_count = 0
            child_idx = hierarchy[i][2]
            while child_idx != -1:
                hole_area_px += cv2.contourArea(contours[child_idx])
                hole_count += 1
                child_idx = hierarchy[child_idx][0] # Next sibling
            
            net_area_px = outer_area_px - hole_area_px
            if net_area_px < 0: net_area_px = 0 # Safety
            
            if net_area_px == 0 and perimeter_px == 0:
                continue
                
            # Convert to physical units
            net_area_sq_in = net_area_px / (self.pixels_per_inch ** 2)
            perimeter_in = perimeter_px / self.pixels_per_inch
            
            # Thinness Ratio (Perimeter^2 / OuterArea)
            # Use OuterArea for shape classification because holes don't change the "thinness" of the container
            thinness = 0
            if outer_area_px > 0:
                thinness = (perimeter_px ** 2) / outer_area_px
            
            # Average Width (approximate)
            avg_width_in = 0
            if perimeter_in > 0:
                avg_width_in = 2 * (outer_area_px / (self.pixels_per_inch**2)) / perimeter_in
            
            stitch_type = 'fill'
            
            # Classification Logic
            if net_area_sq_in < 0.001: 
                # Very small area, likely noise or running stitch detail
                stitch_type = 'running'
            elif hole_count > 5:
                # Many holes implies a grid, mesh, or complex texture.
                # Treat as high density (Satin-like) to account for detail.
                stitch_type = 'satin'
            elif thinness > 40 and avg_width_in < 0.3:
                # High thinness ratio AND narrow width -> Satin column or line
                stitch_type = 'satin'
            else:
                # Low thinness ratio or wide shape -> Solid fill
                stitch_type = 'fill'
                
            # DEBUG
            if net_area_sq_in > 0.001:
               print(f"Type: {stitch_type}, Area: {net_area_sq_in:.4f}, Thinness: {thinness:.1f}, Width: {avg_width_in:.4f}, Holes: {hole_count}")
            
            results.append({
                'type': stitch_type,
                'area': net_area_sq_in,
                'length': perimeter_in
            })
            
        return results

    def estimate(self) -> dict:
        if self.processed_image is None:
            self.process_image()
            
        # 1. Segment Colors
        color_masks = self.quantize_colors(k=12) # Use up to 12 colors
        
        total_stitches = 0
        details = {
            'fill_stitches': 0,
            'satin_stitches': 0,
            'running_stitches': 0,
            'color_change_stitches': 0,
            'underlay_stitches': 0,
            'color_count': len(color_masks),
            'breakdown': []
        }
        
        # 2. Analyze each color
        for color_idx, mask in color_masks.items():
            contours_data = self.analyze_contours(mask)
            
            color_stitches = 0
            
            for item in contours_data:
                stitches = 0
                if item['type'] == 'fill':
                    stitches = item['area'] * self.FILL_DENSITY
                    details['fill_stitches'] += stitches
                elif item['type'] == 'satin':
                    stitches = item['area'] * self.FILL_DENSITY * self.SATIN_DENSITY_MULTIPLIER
                    details['satin_stitches'] += stitches
                elif item['type'] == 'running':
                    stitches = item['length'] * self.RUNNING_DENSITY_PER_INCH
                    details['running_stitches'] += stitches
                
                color_stitches += stitches
            
            # Add color change penalty (if significant stitches in this color)
            if color_stitches > 10:
                total_stitches += self.STITCHES_PER_COLOR
                details['color_change_stitches'] += self.STITCHES_PER_COLOR
            
            total_stitches += color_stitches
            
        # 3. Add Underlay
        underlay = total_stitches * self.UNDERLAY_FACTOR
        total_stitches += underlay
        details['underlay_stitches'] = int(underlay)
        
        # Final Rounding
        final_count = int(total_stitches)
        
        # Add dimensions to details
        details['physical_dimensions'] = f"{self.physical_width:.2f}x{self.physical_height:.2f} inches"
        
        # Clean up details for JSON
        details['fill_stitches'] = int(details['fill_stitches'])
        details['satin_stitches'] = int(details['satin_stitches'])
        details['running_stitches'] = int(details['running_stitches'])
        
        return {
            "stitch_count": final_count,
            "details": details
        }
