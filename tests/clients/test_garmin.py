from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pytest
import json

from app.clients.garmin import GarminClient, GarminAPIError, GarminTokens
from app.schemas.training import Activity


class TestGarminClient:
    """Test suite for Garmin Connect API client."""

    def test_client_initialization(self):
        """Test client can be initialized with credentials."""
        client = GarminClient(
            email="test@example.com",
            password="test_password",
        )
        assert client.email == "test@example.com"
        assert client.password == "test_password"
        assert client.token_store_path == Path.home() / ".garmin_tokens.json"

    def test_client_custom_token_path(self):
        """Test client can use custom token storage path."""
        custom_path = Path("/tmp/custom_tokens.json")
        client = GarminClient(
            email="test@example.com",
            password="test_password",
            token_store_path=custom_path,
        )
        assert client.token_store_path == custom_path

    def test_from_env_missing_credentials(self):
        """Test from_env raises error when credentials missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GARMIN_EMAIL"):
                GarminClient.from_env()

    @patch.dict("os.environ", {
        "GARMIN_EMAIL": "test@example.com",
        "GARMIN_PASSWORD": "test_password",
    })
    def test_from_env_success(self):
        """Test from_env creates client from environment variables."""
        client = GarminClient.from_env()
        assert client.email == "test@example.com"
        assert client.password == "test_password"

    def test_garmin_tokens_model(self):
        """Test GarminTokens Pydantic model."""
        tokens = GarminTokens(
            oauth1_token={"token": "value1"},
            oauth2_token={"token": "value2"},
        )
        assert tokens.oauth1_token == {"token": "value1"}
        assert tokens.oauth2_token == {"token": "value2"}

    def test_load_tokens_file_not_exists(self, tmp_path):
        """Test loading tokens returns None when file doesn't exist."""
        token_path = tmp_path / "nonexistent.json"
        client = GarminClient("test@example.com", "pass", token_store_path=token_path)
        
        tokens = client._load_tokens()
        
        assert tokens is None

    def test_load_tokens_success(self, tmp_path):
        """Test successfully loading tokens from file."""
        token_path = tmp_path / "tokens.json"
        token_data = {
            "oauth1_token": {"token": "oauth1_value"},
            "oauth2_token": {"token": "oauth2_value"},
        }
        token_path.write_text(json.dumps(token_data))
        
        client = GarminClient("test@example.com", "pass", token_store_path=token_path)
        tokens = client._load_tokens()
        
        assert tokens is not None
        assert tokens.oauth1_token == {"token": "oauth1_value"}
        assert tokens.oauth2_token == {"token": "oauth2_value"}

    def test_save_tokens(self, tmp_path):
        """Test saving tokens to file."""
        token_path = tmp_path / "tokens.json"
        client = GarminClient("test@example.com", "pass", token_store_path=token_path)
        
        tokens = GarminTokens(
            oauth1_token={"token": "oauth1_value"},
            oauth2_token={"token": "oauth2_value"},
        )
        client._save_tokens(tokens)
        
        assert token_path.exists()
        saved_data = json.loads(token_path.read_text())
        assert saved_data["oauth1_token"] == {"token": "oauth1_value"}

    @patch('app.clients.garmin.Garmin')
    def test_login_with_username_password(self, mock_garmin_class, tmp_path):
        """Test login with username and password (no cached tokens)."""
        mock_client = MagicMock()
        mock_client.garth.oauth1_token = {"token": "new1"}
        mock_client.garth.oauth2_token = {"token": "new2"}
        mock_garmin_class.return_value = mock_client
        
        # Use tmp_path to ensure no cached tokens exist
        token_path = tmp_path / "nonexistent_tokens.json"
        client = GarminClient("test@example.com", "test_password", token_store_path=token_path)
        client.login()
        
        assert client.client == mock_client
        mock_client.login.assert_called_once()
        mock_garmin_class.assert_called_with("test@example.com", "test_password")

    @patch('app.clients.garmin.Garmin')
    def test_login_with_cached_tokens(self, mock_garmin_class, tmp_path):
        """Test login using cached tokens."""
        # Set up cached tokens
        token_path = tmp_path / "tokens.json"
        token_data = {
            "oauth1_token": {"token": "cached1"},
            "oauth2_token": {"token": "cached2"},
        }
        token_path.write_text(json.dumps(token_data))
        
        mock_client = MagicMock()
        mock_garmin_class.return_value = mock_client
        
        client = GarminClient("test@example.com", "test_password", token_store_path=token_path)
        client.login()
        
        # Should try to use cached tokens
        mock_client.login.assert_called_once_with({"token": "cached1"})

    def test_ensure_authenticated_calls_login(self):
        """Test _ensure_authenticated calls login if client not set."""
        client = GarminClient("test@example.com", "test_password")
        
        with patch.object(client, 'login') as mock_login:
            client._ensure_authenticated()
            mock_login.assert_called_once()

    def test_ensure_authenticated_skip_if_authenticated(self):
        """Test _ensure_authenticated skips if already authenticated."""
        client = GarminClient("test@example.com", "test_password")
        client.client = Mock()  # Already has client
        
        with patch.object(client, 'login') as mock_login:
            client._ensure_authenticated()
            mock_login.assert_not_called()

    @patch.object(GarminClient, '_ensure_authenticated')
    def test_get_activities(self, mock_ensure_auth):
        """Test getting activities from Garmin."""
        client = GarminClient("test@example.com", "test_password")
        client.client = Mock()
        client.client.get_activities_by_date.return_value = [
            {
                "activityId": 12345,
                "activityType": {"typeKey": "cycling"},
                "startTimeLocal": "2024-02-29T18:22:51",
                "duration": 3600,
                "distance": 30000,
            }
        ]
        
        activities = client.get_activities(
            start_date=date(2024, 2, 29),
            end_date=date(2024, 2, 29),
        )
        
        assert len(activities) == 1
        assert activities[0]["activityId"] == 12345
        client.client.get_activities_by_date.assert_called_once_with(
            "2024-02-29",
            "2024-02-29",
            activitytype=None,
        )

    @patch.object(GarminClient, '_ensure_authenticated')
    def test_get_activity_details(self, mock_ensure_auth):
        """Test getting activity details."""
        client = GarminClient("test@example.com", "test_password")
        client.client = Mock()
        client.client.get_activity_evaluation.return_value = {
            "activityId": 12345,
            "averageHR": 150,
        }
        
        details = client.get_activity_details(12345)
        
        assert details["activityId"] == 12345
        assert details["averageHR"] == 150
        client.client.get_activity_evaluation.assert_called_once_with(12345)

    def test_map_activity_type(self):
        """Test activity type mapping from Garmin to AutoCoach format."""
        client = GarminClient("test@example.com", "test_password")
        
        assert client._map_activity_type("cycling") == "ride"
        assert client._map_activity_type("road_biking") == "ride"
        assert client._map_activity_type("running") == "run"
        assert client._map_activity_type("trail_running") == "run"
        assert client._map_activity_type("swimming") == "swim"
        assert client._map_activity_type("walking") == "run"
        assert client._map_activity_type("unknown_type") == "other"

    def test_convert_to_autocoach_format(self):
        """Test conversion from Garmin activity to AutoCoach format."""
        client = GarminClient("test@example.com", "test_password")
        
        garmin_activity = {
            "activityId": 12345,
            "startTimeLocal": "2024-02-29T18:22:51",
            "activityType": {"typeKey": "cycling"},
            "duration": 3600,  # seconds
            "distance": 30000,  # meters
            "averageHR": 150,
            "averagePower": 250,
            "normalizedPower": 260,
            "elevationGain": 500,
        }
        
        activity_data = client._convert_to_autocoach_format(garmin_activity)
        
        assert activity_data is not None
        assert activity_data["activity_date"] == date(2024, 2, 29)
        assert activity_data["sport"] == "ride"
        assert activity_data["duration_min"] == 60.0
        assert activity_data["distance_km"] == 30.0
        assert activity_data["hr_avg"] == 150
        assert activity_data["power_avg"] == 250
        assert activity_data["normalized_power"] == 260
        assert activity_data["elevation_m"] == 500

    def test_convert_to_autocoach_format_missing_time(self):
        """Test conversion returns None when start time is missing."""
        client = GarminClient("test@example.com", "test_password")
        
        garmin_activity = {
            "activityId": 12345,
            # No startTimeLocal or startTimeGMT
            "duration": 3600,
        }
        
        activity_data = client._convert_to_autocoach_format(garmin_activity)
        
        assert activity_data is None

    @patch.object(GarminClient, 'get_activities')
    def test_fetch_activities_since_with_date(self, mock_get_activities):
        """Test fetching activities since a specific date."""
        client = GarminClient("test@example.com", "test_password")
        
        mock_get_activities.return_value = [
            {
                "activityId": 12345,
                "startTimeLocal": "2024-02-29T18:22:51",
                "activityType": {"typeKey": "cycling"},
                "duration": 3600,
                "distance": 30000,
                "averageHR": 150,
            }
        ]
        
        activities = client.fetch_activities_since(since_date=date(2024, 2, 29))
        
        assert len(activities) == 1
        assert isinstance(activities[0], Activity)
        assert activities[0].activity_date == date(2024, 2, 29)
        assert activities[0].sport == "ride"

    @patch.object(GarminClient, 'get_activities')
    def test_fetch_activities_since_default_days(self, mock_get_activities):
        """Test fetching activities with default days_back."""
        client = GarminClient("test@example.com", "test_password")
        mock_get_activities.return_value = []
        
        client.fetch_activities_since(days_back=7)
        
        # Verify it calculated the correct start date
        expected_start = date.today() - timedelta(days=7)
        mock_get_activities.assert_called_once()
        call_args = mock_get_activities.call_args[0]
        assert call_args[0] == expected_start

    @patch.object(GarminClient, 'get_activities')
    def test_fetch_activities_handles_conversion_errors(self, mock_get_activities):
        """Test fetch_activities_since handles conversion errors gracefully."""
        client = GarminClient("test@example.com", "test_password")
        
        # Return one valid and one invalid activity
        mock_get_activities.return_value = [
            {
                "startTimeLocal": "2024-02-29T18:22:51",
                "activityType": {"typeKey": "cycling"},
                "duration": 3600,
                "distance": 30000,
            },
            {
                # Missing required fields - will fail conversion
                "activityId": 99999,
            }
        ]
        
        activities = client.fetch_activities_since(since_date=date(2024, 2, 29))
        
        # Should only return the valid activity
        assert len(activities) == 1
        assert activities[0].sport == "ride"

