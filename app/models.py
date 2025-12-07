from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional

class StitchParameters(BaseModel):
    fill_density: float = 2200.0
    satin_spacing_inch: float = 0.0138
    running_density_per_inch: float = 35.0
    stitches_per_color: int = 20
    underlay_fill_ratio: float = 0.35
    satin_min_width_inch: float = 0.02
    satin_max_width_inch: float = 0.35

class EstimationRequest(BaseModel):
    image_url: HttpUrl
    width_inches: float
    parameters: Optional[StitchParameters] = None

class EstimationResponse(BaseModel):
    stitch_count: int
    details: Dict[str, Any]