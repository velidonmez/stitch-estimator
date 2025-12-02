from pydantic import BaseModel, HttpUrl
from typing import Dict, Any

class EstimationRequest(BaseModel):
    image_url: HttpUrl
    width_inches: float

class EstimationResponse(BaseModel):
    stitch_count: int
    details: Dict[str, Any]
