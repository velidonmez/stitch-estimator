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

    # If no alpha, assume white background is transparent
    # Convert to BGRA
    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    # Define white range
    lower_white = np.array([240, 240, 240, 255])
    upper_white = np.array([255, 255, 255, 255])
    
    # Create mask
    mask = cv2.inRange(img, lower_white, upper_white)
    
    # Set alpha to 0 where mask is white
    img[mask > 0] = [255, 255, 255, 0]
    
    return img
