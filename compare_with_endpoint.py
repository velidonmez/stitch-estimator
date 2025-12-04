import asyncio
import httpx
import urllib.request
from app.estimator import StitchEstimator
import json
import os

TEST_CASES = [
    {"url": "https://storage.printmood.com/408fa110-64af-4b75-a313-31223083a90b.png", "width": 3},
    {"url": "https://storage.printmood.com/408fa110-64af-4b75-a313-31223083a90b.png", "width": 4},
    {"url": "https://storage.printmood.com/f9a364c0-0bca-4002-9b65-f8362385ab68.png", "width": 4},
    {"url": "https://storage.printmood.com/6c633050-8cef-4b83-aaae-4a9cf353e55a.png", "width": 4},
    {"url": "https://storage.printmood.com/291084c5-0a59-41b3-ba4a-e9fdcb6b1939.png", "width": 4},
    {"url": "https://storage.printmood.com/cfe22085-c3e2-46ae-8295-0a72bae8bb92.png", "width": 4},
    {"url": "https://storage.printmood.com/d28989e9-25f6-46f3-b8b9-1c62a62af4b7.png", "width": 4},
    {"url": "https://storage.printmood.com/c2c59795-99fa-4a8a-bfdc-4a59c87d4bf7.png", "width": 4},
    {"url": "https://storage.printmood.com/af9fdbca-4b7b-4776-b758-fe83c7aa232a.png", "width": 4},
    {"url": "https://storage.printmood.com/ed3dfb06-7a42-41a6-95fd-1f927a4322de.png", "width": 3},
    {"url": "https://storage.printmood.com/bbf209a1-02a5-4375-a2c1-406c048ed424.png", "width": 4},
    {"url": "https://storage.printmood.com/87c3e193-8fd4-4f6d-9dae-1d36595b78b0.png", "width": 6},
    {"url": "https://storage.printmood.com/61c1096c-404a-4d8f-a412-a69b6afdd499.png", "width": 6},
    {"url": "https://storage.printmood.com/61c1096c-404a-4d8f-a412-a69b6afdd499.png", "width": 4},
    {"url": "https://storage.printmood.com/9a7464cd-b8fe-428d-b8ff-cdc5846ce7bd.png", "width": 4},
    {"url": "https://storage.printmood.com/2a818506-d775-4de0-bd7a-0f865aaf6dc3.png", "width": 4},
    {"url": "https://storage.printmood.com/701cb1f3-d093-47a1-b8f5-6a8beea6f01c.png", "width": 4},
    {"url": "https://storage.printmood.com/5fafbe05-9e8f-4245-8df6-fc6ebe97dbff.png", "width": 5},
    {"url": "https://storage.printmood.com/5cca0b08-6609-4327-a11d-e92b1246f6ba.png", "width": 4},
    {"url": "https://storage.printmood.com/a51f8340-5435-4a46-a195-52a20369c1f9.png", "width": 4},
    {"url": "https://storage.printmood.com/5f19542f-085b-4268-a88d-7c4585842531.png", "width": 4},
    {"url": "https://storage.printmood.com/fe713a22-e5d9-479d-a772-e23b49a3e60d.png", "width": 5},
    {"url": "https://storage.printmood.com/8da0fc14-001b-44ec-8f4f-a385158efa96.png", "width": 6},
]

REMOTE_URL = "https://www.blankstyle.com/uc_instant_quote_stitches_count_form_submit"
HEADERS = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,tr;q=0.8,es;q=0.7",
    "origin": "https://www.blankstyle.com",
    "priority": "u=1, i",
    "referer": "https://www.blankstyle.com/embroidery-cost-estimator?srsltid=AfmBOopdeeABpOOlK8EedR7iazI7kWSKoemUABQKym-bRmjVcHS3GIcB",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "cookie": "SESSe02e0d711adb0261f50a60dfae9fb581=23effqq5ochc80s60umgmtqj9l; uc_bs_cart_zipcode=09200; referer_uri=https%3A%2F%2Fwww.blankstyle.com%2Fembroidery-cost-estimator%3Fsrsltid%3DAfmBOopdeeABpOOlK8EedR7iazI7kWSKoemUABQKym-bRmjVcHS3GIcB; bstyle_login_popover_shown=2; has_js=1"
}

async def get_remote_estimate(client, image_bytes, width, filename):
    try:
        files = {
            'embroidery-stitches-count': (filename, image_bytes, 'image/png')
        }
        data = {
            'printwidth': str(width),
            'form_id': 'uc_instant_quote_stitches_count_form'
        }
        
        response = await client.post(REMOTE_URL, headers=HEADERS, data=data, files=files, timeout=30.0)
        
        if response.status_code == 200:
            try:
                json_resp = response.json()
                if json_resp.get('status') == 'success':
                    return json_resp['message']['stitch_count']
                else:
                    print(f"Remote API Error for {filename}: {json_resp}")
                    return None
            except json.JSONDecodeError:
                print(f"Failed to decode JSON for {filename}. Status: {response.status_code}")
                return None
        else:
            print(f"HTTP Error {response.status_code} for {filename}")
            return None
            
    except Exception as e:
        print(f"Exception calling remote for {filename}: {e}")
        return None

def get_local_estimate(image_bytes, width):
    try:
        estimator = StitchEstimator(image_bytes, width)
        result = estimator.estimate()
        return result['stitch_count']
    except Exception as e:
        print(f"Local estimation error: {e}")
        return None

async def run_comparison():
    print(f"{'Image':<40} | {'Width':<5} | {'Remote':<10} | {'Local':<10} | {'Diff %':<8}")
    print("-" * 90)
    
    async with httpx.AsyncClient() as client:
        for case in TEST_CASES:
            url = case['url']
            width = case['width']
            filename = url.split('/')[-1]
            
            # Download image
            try:
                # print(f"Processing {filename}...")
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    image_bytes = response.read()
            except Exception as e:
                print(f"Failed to download {url}: {e}")
                continue
                
            # Get Estimates
            remote_count = await get_remote_estimate(client, image_bytes, width, filename)
            local_count = get_local_estimate(image_bytes, width)
            
            if remote_count is not None and local_count is not None:
                diff = local_count - remote_count
                diff_percent = (diff / remote_count) * 100
                
                print(f"{filename:<40} | {width:<5} | {remote_count:<10} | {local_count:<10} | {diff_percent:+.2f}%")
            else:
                print(f"{filename:<40} | {width:<5} | {'N/A':<10} | {local_count if local_count else 'N/A':<10} | N/A")
                
            # Be nice to the remote server
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_comparison())
