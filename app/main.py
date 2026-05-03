import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .analysis import analyze_image, combine_with_date
from .config import UPLOAD_DIR
from .crud import (
    create_position,
    create_trip,
    delete_position,
    delete_trip,
    get_position_by_id,
    get_trip,
    get_unmatched_positions,
    list_positions,
    list_trips,
    update_position,
)
from .database import init_db
from .schemas.position import PositionCreate, PositionResponse, PositionUnmatched
from .schemas.trip import TripCreate, TripResponse

app = FastAPI(title="City Bike Log", version="1.0.0")


@app.get("/health")
def health_check() -> dict[str, bool]:
    return {"status": True}


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/api/trips/upload", response_model=TripResponse, status_code=201)
async def upload_trip(file: UploadFile = File(...)) -> TripResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    ext = os.path.splitext(file.filename or "")[1] if file.filename else ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    upload_dir: Path = Path(UPLOAD_DIR)
    image_path = upload_dir / filename
    image_url = f"uploads/{filename}"

    with open(image_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        extracted = analyze_image(str(image_path))
    except (ValueError, RuntimeError) as e:
        msg = f"Analysis failed: {e}"
        raise HTTPException(status_code=500, detail=msg) from e

    start_time_str = combine_with_date(extracted["start_time"])
    end_time_str = combine_with_date(extracted["end_time"])

    try:
        trip_data = TripCreate(
            bike_id=extracted["bike_id"],
            serial=extracted["serial"],
            length_min=extracted["length_min"],
            start_time=datetime.fromisoformat(start_time_str),
            end_time=datetime.fromisoformat(end_time_str),
            start_pos=extracted["start_pos"],
            end_pos=extracted["end_pos"],
        )
    except (ValueError, KeyError) as e:
        msg = f"Data validation failed: {e}"
        raise HTTPException(status_code=500, detail=msg) from e

    trip_id = create_trip(trip_data, image_url)

    trip = get_trip(trip_id)
    if trip is None:
        raise HTTPException(status_code=500, detail="Trip was created but not found")

    return TripResponse(
        id=trip["id"],
        bike_id=trip["bike_id"],
        serial=trip["serial"],
        length_min=trip["length_min"],
        start_time=datetime.fromisoformat(trip["start_time"]),
        end_time=datetime.fromisoformat(trip["end_time"]),
        start_pos=trip["start_pos"],
        end_pos=trip["end_pos"],
        image_url=trip["image_url"],
        created_at=trip["created_at"],
    )


@app.get("/api/trips", response_model=list[TripResponse])
def get_trips(limit: int = 50, offset: int = 0) -> list[TripResponse]:
    return cast("list[TripResponse]", list_trips(limit=limit, offset=offset))


@app.get("/api/trips/{trip_id}", response_model=TripResponse)
def get_trip_by_id(trip_id: int) -> TripResponse:
    trip = get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip  # type: ignore[return-value]


@app.delete("/api/trips/{trip_id}", status_code=204)
def delete_trip_by_id(trip_id: int) -> JSONResponse:
    if not delete_trip(trip_id):
        raise HTTPException(status_code=404, detail="Trip not found")
    return JSONResponse(status_code=204, content=None)


@app.get("/api/positions", response_model=list[PositionResponse])
def get_positions(limit: int = 50, offset: int = 0) -> list[PositionResponse]:
    return list_positions(limit=limit, offset=offset)  # type: ignore[return-value]


@app.get("/api/positions/unmatched", response_model=list[PositionUnmatched])
def get_unmatched_positions_endpoint() -> list[dict[str, Any]]:
    return get_unmatched_positions()


@app.get("/api/positions/{position_id}", response_model=PositionResponse)
def get_position(position_id: int) -> PositionResponse:
    pos = get_position_by_id(position_id)
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")
    return pos  # type: ignore[return-value]


@app.post("/api/positions", response_model=PositionResponse, status_code=201)
def create_position_endpoint(data: PositionCreate) -> PositionResponse:
    pos_id = create_position(data.name, data.latitude, data.longitude, data.altitude)
    pos = get_position_by_id(pos_id)
    if pos is None:
        raise HTTPException(status_code=500, detail="Position was created but not found")
    return pos  # type: ignore[return-value]


@app.patch("/api/positions/{position_id}", response_model=PositionResponse)
def update_position_endpoint(position_id: int, data: PositionCreate) -> PositionResponse:
    if not update_position(position_id, data.latitude, data.longitude, data.altitude):
        raise HTTPException(status_code=404, detail="Position not found")
    pos = get_position_by_id(position_id)
    if pos is None:
        raise HTTPException(status_code=500, detail="Position not found after update")
    return pos  # type: ignore[return-value]


@app.delete("/api/positions/{position_id}", status_code=204)
def delete_position_endpoint(position_id: int) -> JSONResponse:
    if not delete_position(position_id):
        raise HTTPException(status_code=404, detail="Position not found")
    return JSONResponse(status_code=204, content=None)
