from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_metrics_daily_endpoint():
    payload = [
        {"activity_date": str(date(2024, 1, 1)), "sport": "ride", "duration_min": 60, "tss": 50},
        {"activity_date": str(date(2024, 1, 2)), "sport": "ride", "duration_min": 60, "tss": 55},
        {"activity_date": str(date(2024, 1, 3)), "sport": "ride", "duration_min": 60, "tss": 60},
    ]
    resp = client.post("/metrics/daily", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # Check that required fields are present (schema now includes optional recovery markers)
    assert "metric_date" in data[0]
    assert "tss" in data[0]
    assert "atl" in data[0]
    assert "ctl" in data[0]
    assert "tsb" in data[0]
    # Verify values are correct
    assert data[0]["tss"] == 50.0


def test_auth_trainingpeaks_missing_credentials():
    """Test auth endpoint returns error when credentials not set."""
    with patch.dict("os.environ", {}, clear=True):
        resp = client.get("/auth/trainingpeaks")
        assert resp.status_code == 400
        assert "TRAININGPEAKS_CLIENT_ID" in resp.json()["detail"]


@patch.dict("os.environ", {
    "TRAININGPEAKS_CLIENT_ID": "test_id",
    "TRAININGPEAKS_CLIENT_SECRET": "test_secret",
})
def test_auth_trainingpeaks_success():
    """Test auth endpoint returns authorization URL when credentials set."""
    with patch("app.clients.trainingpeaks.TrainingPeaksClient.get_authorization_url") as mock_auth:
        mock_auth.return_value = "https://oauth.sandbox.trainingpeaks.com/authorize?client_id=test"
        
        resp = client.get("/auth/trainingpeaks?sandbox=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert "oauth.sandbox.trainingpeaks.com" in data["authorization_url"]


def test_trainingpeaks_endpoints_require_auth():
    """Test TrainingPeaks endpoints require authentication."""
    # Profile endpoint
    resp = client.get("/trainingpeaks/profile")
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json()["detail"]
    
    # Activities endpoint
    resp = client.get("/trainingpeaks/activities?start_date=2024-01-01&end_date=2024-01-07")
    assert resp.status_code == 401
    
    # Metrics endpoint
    resp = client.post("/trainingpeaks/metrics?start_date=2024-01-01&end_date=2024-01-07")
    assert resp.status_code == 401


def test_activities_endpoint_validation():
    """Test activities endpoint validates date parameters."""
    # Invalid date range (end before start)
    resp = client.get("/trainingpeaks/activities?start_date=2024-01-07&end_date=2024-01-01")
    assert resp.status_code == 422  # Validation error from FastAPI
    
    # Valid date range but no auth
    resp = client.get("/trainingpeaks/activities?start_date=2024-01-01&end_date=2024-01-07")
    assert resp.status_code == 401
