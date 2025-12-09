import httpx
import numpy as np
import cv2

async def download_image(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content

def decode_image(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    return img

def remove_background(img: np.ndarray) -> np.ndarray:
    # If image has alpha channel, use it
    if img.shape[2] == 4:
        return img

    # If no alpha, assume background is uniform and connected to corners
    # Convert to BGRA
    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    # Flood fill from all 4 corners to catch background
    h, w = img.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    
    # Tolerance for flood fill (loDiff, upDiff)
    # 20 is a reasonable tolerance for compression artifacts
    flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE
    
    # Corners: Top-Left, Top-Right, Bottom-Left, Bottom-Right
    seeds = [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]
    
    for seed in seeds:
        # Check if seed is already filled (mask is set)
        # Mask is (h+2, w+2), seed is (x,y). Mask index is (y+1, x+1)
        if mask[seed[1]+1, seed[0]+1] == 0:
            cv2.floodFill(img, mask, seed, (0, 0, 0, 0), (20, 20, 20), (20, 20, 20), flags)
            
    # The mask has 255 where filled.
    # We need to set alpha to 0 where mask is 255.
    # Mask is 2 pixels larger. Crop it.
    mask_cropped = mask[1:-1, 1:-1]
    
    img[mask_cropped == 255] = [255, 255, 255, 0]
    
    return img

def trim_image(img: np.ndarray) -> np.ndarray:
    """
    Trims empty (transparent) spaces around the image.
    """
    # Check if image has alpha channel
    if img.shape[2] != 4:
        return img
        
    # Get alpha channel
    alpha = img[:, :, 3]
    
    # Find non-zero alpha values
    coords = cv2.findNonZero(alpha)
    
    if coords is None:
        # Image is fully transparent
        return img
        
    # Get bounding box
    x, y, w, h = cv2.boundingRect(coords)
    
    # Crop image
    trimmed_img = img[y:y+h, x:x+w]
    
    return trimmed_img
