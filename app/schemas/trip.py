from datetime import datetime

from pydantic import BaseModel, Field


class TripCreate(BaseModel):
    bike_id: str = Field(..., description="Bike identifier, e.g. TRE00410")
    serial: str = Field(..., description="Bike serial number")
    length_min: int = Field(..., description="Trip duration in minutes")
    start_time: datetime = Field(..., description="Trip start time (ISO 8601)")
    end_time: datetime = Field(..., description="Trip end time (ISO 8601)")
    start_pos: str = Field(..., description="Starting address")
    end_pos: str = Field(..., description="Ending address")


class TripResponse(TripCreate):
    id: int
    image_url: str
    created_at: str
