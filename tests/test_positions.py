import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db
from app.crud import (
    create_position,
    get_position_by_name,
    get_position_by_id,
    update_position,
    list_positions,
    delete_position,
)
from app.schemas.position import PositionCreate, PositionResponse


TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB.close()
os.environ["DB_PATH"] = TEST_DB.name


@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists(TEST_DB.name):
        os.unlink(TEST_DB.name)
    init_db()
    yield
    if os.path.exists(TEST_DB.name):
        os.unlink(TEST_DB.name)


class TestCreatePosition:
    def test_inserts_and_returns_id(self):
        pos_id = create_position("Helsinki Central Station", 60.17, 24.94, 5.0)
        assert isinstance(pos_id, int)
        assert pos_id > 0

    def test_returns_existing_id_on_duplicate(self):
        pos_id1 = create_position("Esplanadi", 60.16, 24.94, 4.0)
        pos_id2 = create_position("Esplanadi", 60.16, 24.94, 4.0)
        assert pos_id1 == pos_id2

    def test_nullable_coords(self):
        pos_id = create_position("Unknown Location", None, None, None)
        assert isinstance(pos_id, int)
        pos = get_position_by_id(pos_id)
        assert pos["latitude"] is None
        assert pos["longitude"] is None
        assert pos["altitude"] is None


class TestGetPosition:
    def test_get_by_name(self):
        pos_id = create_position("Kaisaniemi", 60.17, 24.95, 6.0)
        pos = get_position_by_name("Kaisaniemi")
        assert pos is not None
        assert pos["name"] == "Kaisaniemi"
        assert pos["latitude"] == 60.17

    def test_get_by_name_not_found(self):
        pos = get_position_by_name("Nonexistent Place")
        assert pos is None

    def test_get_by_id(self):
        pos_id = create_position("Parliament House", 60.169, 24.952, 3.0)
        pos = get_position_by_id(pos_id)
        assert pos is not None
        assert pos["id"] == pos_id

    def test_get_by_id_not_found(self):
        pos = get_position_by_id(99999)
        assert pos is None


class TestUpdatePosition:
    def test_update_coords(self):
        pos_id = create_position("Old Location", 60.16, 24.94, 3.0)
        assert update_position(pos_id, 60.18, 24.96, 7.0) is True
        pos = get_position_by_id(pos_id)
        assert pos["latitude"] == 60.18
        assert pos["longitude"] == 24.96
        assert pos["altitude"] == 7.0

    def test_update_partial_coords(self):
        pos_id = create_position("Partial Location", 60.16, 24.94, 3.0)
        assert update_position(pos_id, None, 24.96, None) is True
        pos = get_position_by_id(pos_id)
        assert pos["latitude"] is None
        assert pos["longitude"] == 24.96
        assert pos["altitude"] is None

    def test_update_nonexistent_returns_false(self):
        assert update_position(99999, 60.0, 24.0, 0.0) is False


class TestListPositions:
    def test_empty_list(self):
        result = list_positions()
        assert result == []

    def test_returns_positions_sorted_by_name(self):
        create_position("Zebra Street", 60.1, 24.9, 1.0)
        create_position("Alpha Street", 60.2, 24.9, 2.0)
        create_position("Middle Street", 60.15, 24.9, 1.5)
        result = list_positions()
        assert len(result) == 3
        assert result[0]["name"] == "Alpha Street"
        assert result[1]["name"] == "Middle Street"
        assert result[2]["name"] == "Zebra Street"

    def test_pagination(self):
        for i in range(5):
            create_position(f"Position {i}", 60.1 + i * 0.01, 24.9, 1.0)
        result = list_positions(limit=2, offset=0)
        assert len(result) == 2
        result = list_positions(limit=2, offset=2)
        assert len(result) == 2


class TestDeletePosition:
    def test_delete_existing(self):
        pos_id = create_position("Delete Me", 60.1, 24.9, 1.0)
        assert delete_position(pos_id) is True

    def test_delete_nonexistent(self):
        assert delete_position(99999) is False

    def test_delete_removes_from_list(self):
        pos_id = create_position("Gone", 60.1, 24.9, 1.0)
        delete_position(pos_id)
        result = list_positions()
        assert len(result) == 0


class TestPositionCreateSchema:
    def test_valid_data(self):
        data = PositionCreate(name="Test", latitude=60.0, longitude=24.0, altitude=5.0)
        assert data.name == "Test"
        assert data.latitude == 60.0

    def test_nullable_fields(self):
        data = PositionCreate(name="Test")
        assert data.latitude is None
        assert data.longitude is None
        assert data.altitude is None

    def test_missing_name_raises(self):
        with pytest.raises(Exception):
            PositionCreate(latitude=60.0, longitude=24.0)


class TestPositionResponseSchema:
    def test_full_serialization(self):
        response = PositionResponse(
            id=1,
            name="Esplanadi",
            latitude=60.16,
            longitude=24.94,
            altitude=4.0,
            created_at="2026-04-23T08:00:00",
            updated_at="2026-04-23T09:00:00",
        )
        d = response.model_dump()
        assert d["id"] == 1
        assert d["name"] == "Esplanadi"
        assert d["latitude"] == 60.16
