"""Test setup: temporary database and upload folder so tests never touch demo data."""
import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(_tmp, "test.db")
os.environ["UPLOAD_DIR"] = os.path.join(_tmp, "uploads")
os.environ["ADMIN_PASSWORD"] = "testpw"
os.environ["DEMO_MODE"] = "1"

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def farmer_id(client):
    from datetime import date, timedelta
    r = client.post("/farmers", data={
        "name": "Test Farmer", "mobile": "9876543210", "village": "Kalyandurg", "district": "Anantapur",
        "crop": "groundnut", "sowing_date": (date.today() - timedelta(days=30)).isoformat(),
        "field_name": "", "consent": "on"})
    assert r.status_code == 200, r.text[:300]
    return int(str(r.url).rstrip("/").split("/")[-1])
