import cv2
import numpy as np
import pytest
from app.utils import trim_image
from app.estimator import StitchEstimator

def create_image_with_transparent_border(inner_size, border_size, color=(0, 0, 0, 255)):
    total_size = inner_size + 2 * border_size
    img = np.zeros((total_size, total_size, 4), dtype=np.uint8)
    
    # Draw inner square
    start = border_size
    end = start + inner_size
    img[start:end, start:end] = color
    
    return img

def test_trim_image_logic():
    # Create 100x100 image with 50x50 content in center
    # Border is 25px on each side
    img = create_image_with_transparent_border(50, 25)
    
    assert img.shape == (100, 100, 4)
    
    trimmed = trim_image(img)
    
    # Should be trimmed to exactly 50x50
    assert trimmed.shape == (50, 50, 4)
    
    # Check content is preserved (center pixel should be colored)
    assert np.array_equal(trimmed[25, 25], [0, 0, 0, 255])

def test_trim_image_no_transparency():
    # 50x50 solid image
    img = np.zeros((50, 50, 4), dtype=np.uint8)
    img[:] = (255, 0, 0, 255)
    
    trimmed = trim_image(img)
    assert trimmed.shape == (50, 50, 4)

def test_trim_image_fully_transparent():
    # 50x50 transparent image
    img = np.zeros((50, 50, 4), dtype=np.uint8)
    
    trimmed = trim_image(img)
    # Should return original if fully transparent (or empty, depending on implementation choice)
    # Current implementation returns original
    assert trimmed.shape == (50, 50, 4)

def test_estimator_integration():
    # Create image with large transparent border
    # 100x100 total, 20x20 content
    img_bytes = cv2.imencode('.png', create_image_with_transparent_border(20, 40))[1].tobytes()
    
    # If we target 1 inch width:
    # WITHOUT trimming: The 100px width maps to 1 inch. The 20px content is 0.2 inches.
    # WITH trimming: The 20px content maps to 1 inch.
    
    # We can check physical dimensions in the estimator to verify trimming happened BEFORE resizing logic?
    # Actually, estimator logic:
    # 1. Remove BG -> 2. Trim -> 3. Resize to target width
    
    # So if we pass target_width=1.0, the FINAL processed image should represent the trimmed content scaled to 1 inch.
    
    estimator = StitchEstimator(img_bytes, target_width_inches=1.0)
    estimator.process_image()
    
    # The processed image should be resized such that width is ~1 inch * 300 PPI = 300 px
    # Since the content was square (20x20), the aspect ratio is 1:1.
    # So processed image should be 300x300.
    
    h, w = estimator.processed_image.shape[:2]
    assert w == 300
    assert h == 300
    
    # If trimming didn't happen, the aspect ratio would still be 1:1 (100x100 image), 
    # BUT the content inside would be small.
    # Wait, how to distinguish?
    # If trimming works, the entire 300x300 image should be filled with the content.
    # If trimming failed, the 300x300 image would have a large transparent border.
    
    # Check center pixel alpha
    center_pixel = estimator.processed_image[150, 150]
    assert center_pixel[3] == 255 # Should be opaque
    
    # Check corner pixel alpha
    # If trimmed and resized, corners of a square might still be opaque (it's a square filling the view).
    corner_pixel = estimator.processed_image[5, 5]
    assert corner_pixel[3] == 255 # Should be opaque if it's a full square
