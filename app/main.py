from fastapi import FastAPI, HTTPException
from .models import EstimationRequest, EstimationResponse
from .utils import download_image
from .estimator import StitchEstimator
import uvicorn

app = FastAPI(title="Embroidery Stitch Estimator")

@app.post("/estimate", response_model=EstimationResponse)
async def estimate_stitches(request: EstimationRequest):
    try:
        # Download image
        image_bytes = await download_image(str(request.image_url))
        
        # Initialize estimator
        estimator = StitchEstimator(image_bytes, request.width_inches)
        
        # Get estimation
        result = estimator.estimate()
        
        return EstimationResponse(
            stitch_count=result["stitch_count"],
            details=result["details"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
