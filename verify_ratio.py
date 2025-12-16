import json
import numpy as np

with open('benchmark_detailed.json', 'r') as f:
    data = json.load(f)

ratios = [d['estimated'] / d['expected'] for d in data]
avg_ratio = np.mean(ratios)
print(f"Average Ratio (Estimated/Expected): {avg_ratio:.4f}")
