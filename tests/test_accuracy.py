import cv2
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.estimator import StitchEstimator

def create_test_image(width_px, height_px):
    # Create a blank image with alpha channel
    img = np.zeros((height_px, width_px, 4), dtype=np.uint8)
    
    # Draw a filled rectangle (simulate filled area)
    # Let's say 70% coverage
    cv2.rectangle(img, (0, 0), (int(width_px * 0.8), int(height_px * 0.8)), (255, 0, 0, 255), -1)
    
    # Draw some lines to simulate edges/details
    for i in range(0, width_px, 20):
        cv2.line(img, (i, 0), (i, height_px), (0, 255, 0, 255), 2)
        
    # Encode to bytes
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()

def test_estimation():
    # Simulate the CPR design dimensions
    # Width: 3.53 in
    # Height: 4.02 in
    # Stitches: 27990
    
    width_inches = 3.53
    height_inches = 4.02
    
    # Create an image that roughly matches these proportions
    # 100 px per inch
    width_px = int(width_inches * 100)
    height_px = int(height_inches * 100)
    
    image_bytes = create_test_image(width_px, height_px)
    
    estimator = StitchEstimator(image_bytes, width_inches)
    result = estimator.estimate()
    
    print("Test Result:")
    print(f"Estimated Stitches: {result['stitch_count']}")
    print(f"Details: {result['details']}")
    
    # Target is around 28k
    target = 27990
    diff = abs(result['stitch_count'] - target)
    percent_diff = (diff / target) * 100
    
    print(f"Target: {target}")
    print(f"Difference: {diff} ({percent_diff:.2f}%)")

if __name__ == "__main__":
    test_estimation()
