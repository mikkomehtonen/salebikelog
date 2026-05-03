from pydantic import BaseModel, Field


class PositionCreate(BaseModel):
    name: str = Field(..., description="Address or name of the position")
    latitude: float | None = Field(None, description="Latitude coordinate")
    longitude: float | None = Field(None, description="Longitude coordinate")
    altitude: float | None = Field(None, description="Altitude coordinate")


class PositionResponse(BaseModel):
    id: int
    name: str
    latitude: float | None
    longitude: float | None
    altitude: float | None
    created_at: str
    updated_at: str


class PositionUnmatched(BaseModel):
    name: str
    source: str
    trip_id: int
