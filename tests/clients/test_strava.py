from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
import pytest

from app.clients.strava import StravaClient, StravaAPIError
from app.schemas.training import Activity


class TestStravaClient:
    """Test suite for Strava API client."""

    def test_client_initialization(self):
        """Test client can be initialized with credentials."""
        client = StravaClient(
            client_id="12345",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/auth/callback",
        )
        assert client.client_id == "12345"
        assert client.client_secret == "test_secret"
        assert client.redirect_uri == "http://localhost:8000/auth/callback"

    def test_from_env_missing_credentials(self):
        """Test from_env raises error when credentials missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="STRAVA_CLIENT_ID"):
                StravaClient.from_env()

    @patch.dict("os.environ", {
        "STRAVA_CLIENT_ID": "12345",
        "STRAVA_CLIENT_SECRET": "test_secret",
        "OAUTH_REDIRECT_URI": "https://example.com/callback",
    })
    def test_from_env_success(self):
        """Test from_env creates client from environment variables."""
        client = StravaClient.from_env()
        assert client.client_id == "12345"
        assert client.client_secret == "test_secret"
        assert client.redirect_uri == "https://example.com/callback"

    @patch.dict("os.environ", {
        "STRAVA_CLIENT_ID": "12345",
        "STRAVA_CLIENT_SECRET": "test_secret",
        "STRAVA_ACCESS_TOKEN": "access_token_123",
        "STRAVA_REFRESH_TOKEN": "refresh_token_456",
    })
    def test_from_env_with_tokens(self):
        """Test from_env loads existing tokens."""
        client = StravaClient.from_env()
        assert client.oauth_session.token["access_token"] == "access_token_123"
        assert client.oauth_session.token["refresh_token"] == "refresh_token_456"

    def test_get_authorization_url(self):
        """Test authorization URL generation."""
        client = StravaClient("12345", "test_secret")
        url = client.get_authorization_url()
        
        # Verify URL contains expected components
        assert "www.strava.com/oauth/authorize" in url
        assert "client_id=12345" in url
        assert "scope=read" in url
        # Check for URL-encoded version of activity:read_all
        assert "activity" in url and "read_all" in url

    @patch('requests.post')
    def test_exchange_code_for_token_success(self, mock_post):
        """Test successful token exchange."""
        client = StravaClient("12345", "test_secret")
        
        # Mock successful token response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_at": 1234567890,
            "athlete": {"id": 284379},
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        token = client.exchange_code_for_token("auth_code_123")
        
        assert token["access_token"] == "new_access_token"
        assert token["refresh_token"] == "new_refresh_token"
        assert client.oauth_session.token["access_token"] == "new_access_token"
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["data"]["code"] == "auth_code_123"
        assert call_args[1]["data"]["grant_type"] == "authorization_code"

    def test_map_sport_type(self):
        """Test sport type mapping from Strava to AutoCoach format."""
        client = StravaClient("12345", "test_secret")
        
        assert client._map_sport_type("Ride") == "ride"
        assert client._map_sport_type("VirtualRide") == "ride"
        assert client._map_sport_type("Run") == "run"
        assert client._map_sport_type("VirtualRun") == "run"
        assert client._map_sport_type("Swim") == "swim"
        assert client._map_sport_type("Walk") == "run"
        assert client._map_sport_type("Other") == "other"

    @patch.object(StravaClient, '_make_request')
    def test_get_athlete(self, mock_request):
        """Test getting athlete profile."""
        client = StravaClient("12345", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_request.return_value = {
            "id": 284379,
            "firstname": "Jeff",
            "lastname": "Butler",
            "weight": 84.0,
        }
        
        athlete = client.get_athlete()
        
        assert athlete["id"] == 284379
        assert athlete["firstname"] == "Jeff"
        mock_request.assert_called_once_with("GET", "/athlete")

    @patch.object(StravaClient, '_make_request')
    def test_get_athlete_zones(self, mock_request):
        """Test getting training zones."""
        client = StravaClient("12345", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_request.return_value = {
            "heart_rate": {
                "zones": [
                    {"min": 0, "max": 117},
                    {"min": 117, "max": 146},
                ]
            }
        }
        
        zones = client.get_athlete_zones()
        
        assert "heart_rate" in zones
        assert len(zones["heart_rate"]["zones"]) == 2
        mock_request.assert_called_once_with("GET", "/athlete/zones")

    @patch.object(StravaClient, '_make_request')
    def test_list_activities(self, mock_request):
        """Test listing activities."""
        client = StravaClient("12345", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_request.return_value = [
            {
                "id": 12345,
                "name": "Morning Ride",
                "type": "Ride",
                "start_date": "2025-11-08T10:30:00Z",
                "moving_time": 3600,
                "distance": 30000,
            }
        ]
        
        activities = client.list_activities(page=1, per_page=10)
        
        assert len(activities) == 1
        assert activities[0]["id"] == 12345
        assert activities[0]["type"] == "Ride"
        mock_request.assert_called_once()

    @patch.object(StravaClient, '_make_request')
    def test_get_activity(self, mock_request):
        """Test getting activity details."""
        client = StravaClient("12345", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_request.return_value = {
            "id": 12345,
            "name": "Morning Ride",
            "moving_time": 3600,
            "average_watts": 250,
            "weighted_average_watts": 260,
        }
        
        activity = client.get_activity(12345)
        
        assert activity["id"] == 12345
        assert activity["average_watts"] == 250
        mock_request.assert_called_once_with(
            "GET",
            "/activities/12345",
            params={"include_all_efforts": False}
        )

    @patch.object(StravaClient, '_make_request')
    def test_get_activity_streams(self, mock_request):
        """Test getting activity streams."""
        client = StravaClient("12345", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_request.return_value = {
            "time": {"data": [0, 1, 2]},
            "watts": {"data": [200, 250, 300]},
            "heartrate": {"data": [120, 140, 160]},
        }
        
        streams = client.get_activity_streams(12345)
        
        assert "time" in streams
        assert "watts" in streams
        assert len(streams["time"]["data"]) == 3

    @patch.object(StravaClient, 'list_activities')
    def test_fetch_activities_conversion(self, mock_list):
        """Test conversion from Strava activities to AutoCoach format."""
        client = StravaClient("12345", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_list.return_value = [
            {
                "start_date": "2025-11-08T10:30:00Z",
                "type": "Ride",
                "moving_time": 3600,  # 60 minutes
                "distance": 30000,  # 30km
                "average_heartrate": 150,
                "average_watts": 250,
                "weighted_average_watts": 260,
                "total_elevation_gain": 500,
            }
        ]
        
        activities = client.fetch_activities(
            start_date=date(2025, 11, 8),
            end_date=date(2025, 11, 8),
        )
        
        assert len(activities) == 1
        activity = activities[0]
        assert isinstance(activity, Activity)
        assert activity.activity_date == date(2025, 11, 8)
        assert activity.sport == "ride"
        assert activity.duration_min == 60.0
        assert activity.distance_km == 30.0
        assert activity.hr_avg == 150
        assert activity.power_avg == 250
        assert activity.normalized_power == 260
        assert activity.elevation_m == 500

    def test_make_request_no_token(self):
        """Test _make_request raises error when no token available."""
        client = StravaClient("12345", "test_secret")
        
        with pytest.raises(StravaAPIError, match="No access token available"):
            client._make_request("GET", "/athlete")

    @patch.object(StravaClient, 'get_activity_streams')
    def test_get_activity_samples(self, mock_streams):
        """Test getting activity samples in AutoCoach format."""
        client = StravaClient("12345", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_streams.return_value = {
            "time": {"data": [0, 1, 2]},
            "watts": {"data": [200, 250, 300]},
            "heartrate": {"data": [120, 140, 160]},
            "latlng": {"data": [[53.3, -6.3], [53.31, -6.31], [53.32, -6.32]]},
        }
        
        samples = client.get_activity_samples(12345)
        
        assert len(samples) == 3
        assert samples[0].t_s == 0
        assert samples[0].power_w == 200
        assert samples[0].hr_bpm == 120
        assert samples[0].lat == 53.3
        assert samples[0].lon == -6.3
        
        assert samples[2].t_s == 2
        assert samples[2].power_w == 300

    @patch.object(StravaClient, 'get_activity_streams')
    def test_get_activity_samples_empty(self, mock_streams):
        """Test getting samples with no data returns empty list."""
        client = StravaClient("12345", "test_secret")
        client.oauth_session.token = {"access_token": "fake_token"}
        
        mock_streams.return_value = {}
        
        samples = client.get_activity_samples(12345)
        
        assert samples == []

