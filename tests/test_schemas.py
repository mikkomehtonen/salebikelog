from datetime import datetime

import pytest

from app.schemas.trip import TripCreate, TripResponse


class TestTripCreate:
    def test_valid_data(self):
        data = {
            "bike_id": "TRE00410",
            "serial": "SN123456",
            "length_min": 35,
            "start_time": datetime(2026, 4, 23, 8, 15),
            "end_time": datetime(2026, 4, 23, 8, 50),
            "start_pos": "Helsinki Central Station",
            "end_pos": "Esplanadi",
        }
        trip = TripCreate(**data)
        assert trip.bike_id == "TRE00410"
        assert trip.length_min == 35

    def test_missing_required_field(self):
        with pytest.raises(Exception):
            TripCreate(
                bike_id="TRE00410",
                serial="SN123456",
                length_min=35,
                start_time=datetime(2026, 4, 23, 8, 15),
                end_time=datetime(2026, 4, 23, 8, 50),
                start_pos="Helsinki Central Station",
            )

    def test_wrong_type(self):
        with pytest.raises(Exception):
            TripCreate(
                bike_id="TRE00410",
                serial="SN123456",
                length_min="thirty-five",
                start_time=datetime(2026, 4, 23, 8, 15),
                end_time=datetime(2026, 4, 23, 8, 50),
                start_pos="Helsinki Central Station",
                end_pos="Esplanadi",
            )


class TestTripResponse:
    def test_full_serialization(self):
        response = TripResponse(
            id=1,
            bike_id="TRE00410",
            serial="SN123456",
            length_min=35,
            start_time=datetime(2026, 4, 23, 8, 15),
            end_time=datetime(2026, 4, 23, 8, 50),
            start_pos="Helsinki Central Station",
            end_pos="Esplanadi",
            image_url="uploads/test.png",
            created_at="2026-04-23T08:50:00",
        )
        d = response.model_dump()
        assert d["id"] == 1
        assert d["image_url"] == "uploads/test.png"
        assert "bike_id" in d
