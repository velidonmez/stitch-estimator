import sys
import os
import cv2
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.estimator import StitchEstimator

def create_test_image(width_px, height_px, shape_width_px, shape_height_px):
    # White background
    img = np.full((height_px, width_px, 3), 255, dtype=np.uint8)
    
    # Black rectangle in center
    start_x = (width_px - shape_width_px) // 2
    start_y = (height_px - shape_height_px) // 2
    
    cv2.rectangle(img, (start_x, start_y), (start_x + shape_width_px, start_y + shape_height_px), (0, 0, 0), -1)
    
    # Encode to bytes
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()

def test_fill_classification():
    # Create a wide shape (Fill)
    # Target width: 5 inches. 300 PPI.
    # Shape: 1 inch x 1 inch square.
    # Image: 500x500 px (so 1 inch is 100 px if target width is 5 inches)
    # Wait, if target width is 5 inches, and image width is 500px, then 100px = 1 inch.
    # Estimator resizes to target width * 300 PPI = 1500 px width.
    # So if I pass a 500px wide image and say it's 5 inches, it will be upscaled 3x.
    
    # Let's just make the input image simple.
    # 100x100 image. Target width 1.0 inch.
    # Shape: 80x80 px (0.8 x 0.8 inch).
    # Width 0.8 inch > 0.35 inch (Satin Max). Should be Fill.
    
    img_bytes = create_test_image(100, 100, 80, 80)
    estimator = StitchEstimator(img_bytes, target_width_inches=1.0)
    result = estimator.estimate()
    
    print("\n--- Fill Test ---")
    print(f"Total Stitches: {result['stitch_count']}")
    for item in result['details']['breakdown']:
        print(item)
    
    details = result['details']
    assert details['fill_stitches'] > 0
    assert details['satin_stitches'] == 0
    
    # Expected stitches:
    # Area = 0.8 * 0.8 = 0.64 sq inch.
    # Fill Density = 2000.
    # Stitches = 0.64 * 2000 = 1280.
    # Underlay = 20% = 256.
    # Total ~ 1536.
    
    assert 1200 < details['fill_stitches'] < 1400

def test_satin_classification():
    # Create a narrow shape (Satin)
    # Target width 1.0 inch.
    # Shape: 80x15 px (0.8 x 0.15 inch).
    # Width 0.15 inch. Between 0.04 and 0.35. Should be Satin.
    
    img_bytes = create_test_image(100, 100, 80, 15)
    estimator = StitchEstimator(img_bytes, target_width_inches=1.0)
    result = estimator.estimate()
    
    print("\n--- Satin Test ---")
    print(f"Total Stitches: {result['stitch_count']}")
    for item in result['details']['breakdown']:
        print(item)
    
    details = result['details']
    assert details['satin_stitches'] > 0
    assert details['fill_stitches'] == 0
    
    # Expected stitches:
    # Area = 0.8 * 0.15 = 0.12 sq inch.
    # Width = 0.15 inch.
    # Length ~ Area / Width = 0.8 inch.
    # Spacing = 0.0157 inch.
    # Steps = 0.8 / 0.0157 = 50.9.
    # Stitches = 50.9 * 2 = 101.8.
    # Underlay = Length * 25 = 0.8 * 25 = 20.
    # Total ~ 122.
    
    assert 80 < details['satin_stitches'] < 120

if __name__ == "__main__":
    # Manual run if pytest not available or for quick check
    try:
        test_fill_classification()
        print("Fill Test Passed")
        test_satin_classification()
        print("Satin Test Passed")
    except AssertionError as e:
        print(f"Test Failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
