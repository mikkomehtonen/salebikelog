import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.schemas.trip import TripCreate
from app.database import init_db
from app.crud import create_trip, get_trip, list_trips, delete_trip

TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB.close()
os.environ["DB_PATH"] = TEST_DB.name


@pytest.fixture
def trip_data():
    return TripCreate(
        bike_id="TRE00410",
        serial="SN123456",
        length_min=35,
        start_time=datetime(2026, 4, 23, 8, 15),
        end_time=datetime(2026, 4, 23, 8, 50),
        start_pos="Helsinki Central Station",
        end_pos="Esplanadi",
    )


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    if os.path.exists(TEST_DB.name):
        os.unlink(TEST_DB.name)


class TestCreateTrip:
    def test_inserts_and_returns_id(self, trip_data):
        trip_id = create_trip(trip_data, "uploads/test.png")
        assert isinstance(trip_id, int)
        assert trip_id > 0

    def test_creates_multiple_trips(self, trip_data):
        id1 = create_trip(trip_data, "uploads/test1.png")
        id2 = create_trip(trip_data, "uploads/test2.png")
        assert id1 != id2


class TestGetTrip:
    def test_get_existing_trip(self, trip_data):
        trip_id = create_trip(trip_data, "uploads/test.png")
        trip = get_trip(trip_id)
        assert trip is not None
        assert trip["bike_id"] == "TRE00410"
        assert trip["image_url"] == "uploads/test.png"

    def test_get_missing_trip(self):
        trip = get_trip(99999)
        assert trip is None


class TestListTrips:
    def test_empty_list(self):
        result = list_trips()
        assert result == []

    def test_returns_trips_descending(self, trip_data):
        create_trip(trip_data, "uploads/test1.png")
        create_trip(trip_data, "uploads/test2.png")
        result = list_trips()
        assert len(result) == 2

    def test_pagination(self, trip_data):
        for i in range(5):
            d = TripCreate(
                bike_id="TRE00410",
                serial=f"SN{i:04d}",
                length_min=30,
                start_time=datetime(2026, 4, 23, 8, 0),
                end_time=datetime(2026, 4, 23, 8, 30),
                start_pos="A",
                end_pos="B",
            )
            create_trip(d, "uploads/test.png")
        result = list_trips(limit=2, offset=0)
        assert len(result) == 2
        result = list_trips(limit=2, offset=2)
        assert len(result) == 2


class TestDeleteTrip:
    def test_delete_existing(self, trip_data):
        trip_id = create_trip(trip_data, "uploads/test.png")
        assert delete_trip(trip_id) is True

    def test_delete_missing(self):
        assert delete_trip(99999) is False

    def test_delete_removes_from_list(self, trip_data):
        trip_id = create_trip(trip_data, "uploads/test.png")
        delete_trip(trip_id)
        result = list_trips()
        assert len(result) == 0
