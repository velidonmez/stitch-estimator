import json
import asyncio
import httpx
import numpy as np
from app.estimator import StitchEstimator
from app.utils import download_image

async def run_benchmark():
    with open('test_data.json', 'r') as f:
        data = json.load(f)
        
    results = []
    total_error = 0
    total_abs_error = 0
    
    print(f"Benchmarking {len(data)} images...")
    
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
                
                # Run estimator
                estimator = StitchEstimator(img_bytes, target_width_inches=width)
                result = estimator.estimate()
                estimated_count = result['stitch_count']
                
                # Calculate error
                error = estimated_count - expected
                abs_error = abs(error)
                percent_error = (error / expected) * 100
                
                total_error += error
                total_abs_error += abs_error
                
                print(f"[{i+1}/{len(data)}] Expected: {expected}, Estimated: {estimated_count}, Error: {error} ({percent_error:.2f}%)")
                
                results.append({
                    'expected': expected,
                    'estimated': estimated_count,
                    'error': error,
                    'percent_error': percent_error
                })
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                
    avg_abs_error = total_abs_error / len(data)
    print(f"\nAverage Absolute Error: {avg_abs_error:.2f}")
    
    # Calculate Mean Absolute Percentage Error (MAPE)
    mape = np.mean([abs(r['percent_error']) for r in results])
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
