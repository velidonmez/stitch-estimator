import json
import numpy as np
import random

def calculate_stitches(features, params):
    total_stitches = 0
    
    FILL_DENSITY = params['fill_density']
    SATIN_SPACING_INCH = params['satin_spacing_inch']
    RUNNING_DENSITY_PER_INCH = params['running_density_per_inch']
    STITCHES_PER_COLOR = params['stitches_per_color']
    UNDERLAY_FILL_RATIO = params['underlay_fill_ratio']
    SATIN_MIN_WIDTH_INCH = params['satin_min_width_inch']
    SATIN_MAX_WIDTH_INCH = params['satin_max_width_inch']
    
    for color_data in features['colors']:
        color_stitches = 0
        
        for item in color_data:
            stitches = 0
            underlay = 0
            
            # Re-classify based on new parameters
            net_area_sq_in = item['area']
            max_width_in = item['max_width']
            perimeter_in = item['length']
            avg_width_in = item['avg_width']
            
            stitch_type = 'fill'
            if net_area_sq_in < 0.0005: 
                stitch_type = 'running'
            elif max_width_in < SATIN_MIN_WIDTH_INCH:
                stitch_type = 'running'
            elif max_width_in <= SATIN_MAX_WIDTH_INCH:
                stitch_type = 'satin'
            else:
                stitch_type = 'fill'
            
            if stitch_type == 'fill':
                stitches = net_area_sq_in * FILL_DENSITY
                underlay = stitches * UNDERLAY_FILL_RATIO
                
            elif stitch_type == 'satin':
                estimated_length = 0
                if avg_width_in > 0:
                    estimated_length = net_area_sq_in / avg_width_in
                
                if estimated_length > 0:
                    steps = estimated_length / SATIN_SPACING_INCH
                    stitches = steps * 2
                    
                    underlay_factor = 1.0
                    if avg_width_in > 0.08:
                        underlay_factor = 2.0
                        
                    underlay = estimated_length * RUNNING_DENSITY_PER_INCH * underlay_factor
                    
            elif stitch_type == 'running':
                length = perimeter_in / 2
                stitches = length * RUNNING_DENSITY_PER_INCH
            
            color_stitches += (stitches + underlay)
        
        if color_stitches > 10:
            total_stitches += STITCHES_PER_COLOR
        
        total_stitches += color_stitches
        
    return int(total_stitches)

def evaluate(params, data):
    errors = []
    for item in data:
        expected = item['expected']
        estimated = calculate_stitches(item, params)
        percent_error = abs(estimated - expected) / expected
        errors.append(percent_error)
    return np.mean(errors) * 100

def optimize():
    with open('features.json', 'r') as f:
        data = json.load(f)
        
    # Initial parameters (defaults)
    best_params = {
        'fill_density': 2200.0,
        'satin_spacing_inch': 0.0138,
        'running_density_per_inch': 35.0,
        'stitches_per_color': 20,
        'underlay_fill_ratio': 0.35,
        'satin_min_width_inch': 0.02,
        'satin_max_width_inch': 0.35
    }
    
    best_error = evaluate(best_params, data)
    print(f"Initial MAPE: {best_error:.2f}%")
    
    # Random Search
    print("Starting Random Search...")
    for i in range(5000):
        current_params = {
            'fill_density': random.uniform(1000, 3000),
            'satin_spacing_inch': random.uniform(0.005, 0.025),
            'running_density_per_inch': random.uniform(10, 60),
            'stitches_per_color': random.randint(5, 50),
            'underlay_fill_ratio': random.uniform(0.1, 0.6),
            'satin_min_width_inch': random.uniform(0.01, 0.05),
            'satin_max_width_inch': random.uniform(0.1, 0.5)
        }
        
        # Enforce min < max
        if current_params['satin_min_width_inch'] >= current_params['satin_max_width_inch']:
            continue
            
        error = evaluate(current_params, data)
        if error < best_error:
            best_error = error
            best_params = current_params
            print(f"New Best MAPE: {best_error:.2f}% at iter {i}")
            
    # Local Refinement
    print("Starting Local Refinement...")
    for i in range(1000):
        current_params = best_params.copy()
        key = random.choice(list(current_params.keys()))
        val = current_params[key]
        
        if isinstance(val, int):
            change = random.randint(-5, 5)
            new_val = val + change
        else:
            change = val * random.uniform(-0.1, 0.1) # +/- 10%
            new_val = val + change
            
        current_params[key] = new_val
        
        # Constraints
        if current_params['satin_min_width_inch'] >= current_params['satin_max_width_inch']:
            continue
            
        error = evaluate(current_params, data)
        if error < best_error:
            best_error = error
            best_params = current_params
            print(f"Refined MAPE: {best_error:.2f}%")
            
    print("\nOptimization Complete!")
    print(f"Final MAPE: {best_error:.2f}%")
    print("Best Parameters:")
    print(json.dumps(best_params, indent=2))

if __name__ == "__main__":
    optimize()
