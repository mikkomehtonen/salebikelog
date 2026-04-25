import os
import uuid
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from .config import UPLOAD_DIR
from .schemas.trip import TripCreate, TripResponse
from .crud import create_trip, get_trip, list_trips, delete_trip
from .analysis import analyze_image, combine_with_date
from .database import init_db

app = FastAPI(title="City Bike Log", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": True}


@app.on_event("startup")
def startup():
    init_db()


@app.post("/api/trips/upload", response_model=TripResponse, status_code=201)
async def upload_trip(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    image_path = UPLOAD_DIR / filename
    image_url = f"uploads/{filename}"

    with open(image_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        extracted = analyze_image(str(image_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data validation failed: {e}")

    trip_id = create_trip(trip_data, image_url)

    trip = get_trip(trip_id)

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
def get_trips(limit: int = 50, offset: int = 0):
    return list_trips(limit=limit, offset=offset)


@app.get("/api/trips/{trip_id}", response_model=TripResponse)
def get_trip_by_id(trip_id: int):
    trip = get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@app.delete("/api/trips/{trip_id}", status_code=204)
def delete_trip_by_id(trip_id: int):
    if not delete_trip(trip_id):
        raise HTTPException(status_code=404, detail="Trip not found")
    return JSONResponse(status_code=204, content=None)
