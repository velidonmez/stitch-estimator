import json
import asyncio
import httpx
import numpy as np
from app.estimator import StitchEstimator
from app.utils import download_image

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

if __name__ == "__main__":
    # Monkey patch json dump to use NumpyEncoder by default or just pass cls=NumpyEncoder
    # But asyncio.run calls extract_features which calls json.dump
    # I'll modify extract_features to use the encoder
    pass

async def extract_features():
    with open('test_data.json', 'r') as f:
        data = json.load(f)
        
    features_data = []
    
    print(f"Extracting features from {len(data)} images...")
    
    async with httpx.AsyncClient() as client:
        for i, item in enumerate(data):
            url = item['image_url']
            expected = item['expected_stitch_count']
            width = item['width']
            
            try:
                # Download image
                response = await client.get(url)
                response.raise_for_status()
                img_bytes = response.content
                
                # Run estimator preprocessing
                estimator = StitchEstimator(img_bytes, target_width_inches=width)
                estimator.process_image()
                
                # 1. Segment Colors
                color_masks = estimator.quantize_colors(k=12)
                
                image_features = {
                    'expected': expected,
                    'width': width,
                    'colors': []
                }
                
                # 2. Analyze each color
                for color_idx, mask in color_masks.items():
                    contours_data = estimator.analyze_contours(mask)
                    # contours_data contains: type, area, length, avg_width, max_width
                    image_features['colors'].append(contours_data)
                    
                features_data.append(image_features)
                print(f"[{i+1}/{len(data)}] Processed {url}")
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                
    with open('features.json', 'w') as f:
        json.dump(features_data, f, indent=2, cls=NumpyEncoder)
        
    print("Features saved to features.json")

if __name__ == "__main__":
    asyncio.run(extract_features())
