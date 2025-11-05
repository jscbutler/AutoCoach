from datetime import date, datetime
from unittest.mock import Mock, patch
import pytest

from app.clients.trainingpeaks import TrainingPeaksClient, TrainingPeaksAPIError
from app.schemas.training import Activity


class TestTrainingPeaksClient:
    """Test suite for TrainingPeaks API client."""

    def test_client_initialization(self):
        """Test client can be initialized with credentials."""
        client = TrainingPeaksClient(
            client_id="test_id",
            client_secret="test_secret",
            sandbox=True,
        )
        assert client.client_id == "test_id"
        assert client.client_secret == "test_secret"
        assert client.sandbox is True
        assert client.api_base == TrainingPeaksClient.SANDBOX_API_BASE

    def test_client_production_urls(self):
        """Test client uses production URLs when sandbox=False."""
        client = TrainingPeaksClient(
            client_id="test_id",
            client_secret="test_secret",
            sandbox=False,
        )
        assert client.api_base == TrainingPeaksClient.PROD_API_BASE
        assert client.oauth_base == TrainingPeaksClient.PROD_OAUTH_BASE

    def test_from_env_missing_credentials(self):
        """Test from_env raises error when credentials missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TRAININGPEAKS_CLIENT_ID"):
                TrainingPeaksClient.from_env()

    @patch.dict("os.environ", {
        "TRAININGPEAKS_CLIENT_ID": "test_id",
        "TRAININGPEAKS_CLIENT_SECRET": "test_secret",
    })
    def test_from_env_success(self):
        """Test from_env creates client from environment variables."""
        client = TrainingPeaksClient.from_env(sandbox=True)
        assert client.client_id == "test_id"
        assert client.client_secret == "test_secret"

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        client = TrainingPeaksClient("test_id", "test_secret")
        
        with patch.object(client.oauth_session, 'authorization_url') as mock_auth:
            mock_auth.return_value = ("https://example.com/auth", "state123")
            url = client.get_authorization_url()
            
            assert url == "https://example.com/auth"
            mock_auth.assert_called_once()

    def test_map_sport_types(self):
        """Test sport type mapping from TrainingPeaks to AutoCoach format."""
        client = TrainingPeaksClient("test_id", "test_secret")
        
        assert client._map_sport_type("Bike") == "ride"
        assert client._map_sport_type("Run") == "run"
        assert client._map_sport_type("Swim") == "swim"
        assert client._map_sport_type("Unknown") == "other"

    def test_convert_pace(self):
        """Test pace conversion."""
        client = TrainingPeaksClient("test_id", "test_secret")
        
        assert client._convert_pace(5.5) == 5.5
        assert client._convert_pace("invalid") == 0.0

    @patch.object(TrainingPeaksClient, '_make_request')
    def test_fetch_workouts(self, mock_request):
        """Test fetching workouts from API."""
        client = TrainingPeaksClient("test_id", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_request.return_value = [
            {
                "workoutDay": "2024-01-01T00:00:00",
                "workoutTypeDescription": "Bike",
                "totalTimePlanned": 3600,  # 60 minutes in seconds
                "distance": 30000,  # 30km in meters
                "tss": 75.0,
            }
        ]
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        workouts = client.fetch_workouts(start_date, end_date)
        
        assert len(workouts) == 1
        mock_request.assert_called_once_with(
            "GET",
            "/v1/athlete/workouts",
            params={"startDate": "2024-01-01", "endDate": "2024-01-07"}
        )

    @patch.object(TrainingPeaksClient, 'fetch_workouts')
    def test_fetch_activities_conversion(self, mock_fetch):
        """Test conversion from TrainingPeaks workouts to AutoCoach activities."""
        client = TrainingPeaksClient("test_id", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_fetch.return_value = [
            {
                "workoutDay": "2024-01-01T00:00:00",
                "workoutTypeDescription": "Bike", 
                "totalTimePlanned": 3600,  # 1 hour
                "distance": 50000,  # 50km
                "tss": 100.0,
                "averageHeartRate": 150,
                "averagePower": 250,
                "elevation": 500,
                "intensityFactor": 0.8,
            }
        ]
        
        activities = client.fetch_activities(date(2024, 1, 1), date(2024, 1, 1))
        
        assert len(activities) == 1
        activity = activities[0]
        assert isinstance(activity, Activity)
        assert activity.activity_date == date(2024, 1, 1)
        assert activity.sport == "ride"
        assert activity.duration_min == 60.0
        assert activity.distance_km == 50.0
        assert activity.tss == 100.0
        assert activity.hr_avg == 150
        assert activity.power_avg == 250
        assert activity.elevation_m == 500
        assert activity.intensity_factor == 0.8

    def test_make_request_no_token(self):
        """Test _make_request raises error when no token available."""
        client = TrainingPeaksClient("test_id", "test_secret")
        
        with pytest.raises(TrainingPeaksAPIError, match="No access token available"):
            client._make_request("GET", "/test")

    @patch.object(TrainingPeaksClient, '_make_request')
    def test_get_athlete_profile(self, mock_request):
        """Test getting athlete profile."""
        client = TrainingPeaksClient("test_id", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_request.return_value = {"id": 123, "name": "Test Athlete"}
        
        profile = client.get_athlete_profile()
        
        assert profile["id"] == 123
        assert profile["name"] == "Test Athlete"
        mock_request.assert_called_once_with("GET", "/v1/athlete")

