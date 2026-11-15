import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_dashboard_route():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "AutomatorYT2Insta" in response.text

def test_system_metrics_api():
    with TestClient(app) as client:
        response = client.get("/api/system/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        assert "clips" in data
        assert "instagram" in data
        assert "config" in data

def test_list_videos_and_clips_api():
    with TestClient(app) as client:
        v_res = client.get("/api/videos")
        assert v_res.status_code == 200
        assert isinstance(v_res.json(), list)

        c_res = client.get("/api/clips")
        assert c_res.status_code == 200
        assert isinstance(c_res.json(), list)
