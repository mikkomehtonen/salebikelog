import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set test DB path before any app imports
TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB.close()
os.environ["DB_PATH"] = TEST_DB.name

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def db_path():
    yield TEST_DB.name


@pytest.fixture(scope="session")
def upload_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture(scope="function", autouse=True)
def seed_db(db_path):
    if os.path.exists(db_path):
        os.unlink(db_path)
    from app.database import init_db

    init_db()
    yield


@pytest.fixture(scope="session")
def client(db_path, upload_dir):
    from app.main import app

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.config.DB_PATH", db_path)
        mp.setattr("app.database.DB_PATH", db_path)
        mp.setattr("app.main.UPLOAD_DIR", upload_dir)

        from unittest.mock import patch

        with patch("app.main.analyze_image") as mock_analyze:
            mock_analyze.return_value = {
                "length_min": 35,
                "start_time": "08:15",
                "end_time": "08:50",
                "start_pos": "Helsinki Central Station",
                "end_pos": "Esplanadi",
                "bike_id": "TRE00410",
                "serial": "SN123456",
            }
            yield TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def cleanup_db(db_path):
    yield
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_image():
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
