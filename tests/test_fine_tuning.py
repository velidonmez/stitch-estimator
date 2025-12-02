import cv2
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.estimator import StitchEstimator

def create_cpr_simulation(width_px, height_px):
    # CPR Simulation: High complexity, lots of edges
    img = np.zeros((height_px, width_px, 4), dtype=np.uint8)
    
    # 70% coverage
    cv2.rectangle(img, (0, 0), (int(width_px * 0.8), int(height_px * 0.8)), (255, 0, 0, 255), -1)
    
    # Lots of lines to simulate detail/text
    for i in range(0, width_px, 10): # Dense lines
        cv2.line(img, (i, 0), (i, height_px), (0, 255, 0, 255), 2)
    for i in range(0, height_px, 10):
        cv2.line(img, (0, i), (width_px, i), (0, 255, 0, 255), 2)
        
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()

def create_cd_simulation(width_px, height_px):
    # CD Simulation: Medium complexity, blocky letters
    img = np.zeros((height_px, width_px, 4), dtype=np.uint8)
    
    # Draw "C"
    cv2.rectangle(img, (20, 20), (width_px-20, height_px-20), (0, 0, 255, 255), -1)
    cv2.rectangle(img, (80, 80), (width_px-20, height_px-80), (0, 0, 0, 0), -1) # Cutout
    
    # Draw "D" (simplified)
    # Just adding more blocky area to match approx 50-60% coverage
    cv2.rectangle(img, (int(width_px/2), 50), (width_px-50, height_px-50), (0, 255, 0, 255), -1)
    
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()

def run_test():
    print("Running Fine-Tuning Tests...\n")
    
    # Case 1: CPR (Target ~28k)
    cpr_width = 3.53
    cpr_height = 4.02
    cpr_target = 27990
    
    cpr_img = create_cpr_simulation(int(cpr_width*100), int(cpr_height*100))
    cpr_est = StitchEstimator(cpr_img, cpr_width)
    cpr_res = cpr_est.estimate()
    
    print(f"--- CPR Case ---")
    print(f"Target: {cpr_target}")
    print(f"Estimate: {cpr_res['stitch_count']}")
    print(f"Details: {cpr_res['details']}")
    print(f"Error: {cpr_res['stitch_count'] - cpr_target} ({(cpr_res['stitch_count'] - cpr_target)/cpr_target*100:.1f}%)")
    # print(f"Ratio (Edge/Area): {cpr_res['details']['edge_length_inches'] / cpr_res['details']['filled_area_sq_inches']:.2f}\n")

    # Case 2: CD (Target ~15.5k)
    cd_width = 3.06
    cd_height = 4.02
    cd_target = 15445
    
    cd_img = create_cd_simulation(int(cd_width*100), int(cd_height*100))
    cd_est = StitchEstimator(cd_img, cd_width)
    cd_res = cd_est.estimate()
    
    print(f"--- CD Case ---")
    print(f"Target: {cd_target}")
    print(f"Estimate: {cd_res['stitch_count']}")
    print(f"Details: {cd_res['details']}")
    print(f"Error: {cd_res['stitch_count'] - cd_target} ({(cd_res['stitch_count'] - cd_target)/cd_target*100:.1f}%)")
    # print(f"Ratio (Edge/Area): {cd_res['details']['edge_length_inches'] / cd_res['details']['filled_area_sq_inches']:.2f}\n")

if __name__ == "__main__":
    run_test()
