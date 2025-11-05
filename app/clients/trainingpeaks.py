from __future__ import annotations

import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

import httpx
from authlib.integrations.requests_client import OAuth2Session

from app.schemas.training import Activity


class TrainingPeaksAPIError(Exception):
    """Custom exception for TrainingPeaks API errors."""
    pass


class TrainingPeaksClient:
    """TrainingPeaks API client with OAuth 2.0 authentication.
    
    Supports both sandbox and production environments.
    Requires approved API access from TrainingPeaks.
    """

    # API endpoints
    SANDBOX_API_BASE = "https://api.sandbox.trainingpeaks.com"
    PROD_API_BASE = "https://api.trainingpeaks.com"
    SANDBOX_OAUTH_BASE = "https://oauth.sandbox.trainingpeaks.com"
    PROD_OAUTH_BASE = "https://oauth.trainingpeaks.com"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8000/auth/callback",
        sandbox: bool = True,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sandbox = sandbox
        
        # Set base URLs based on environment
        self.api_base = self.SANDBOX_API_BASE if sandbox else self.PROD_API_BASE
        self.oauth_base = self.SANDBOX_OAUTH_BASE if sandbox else self.PROD_OAUTH_BASE
        
        # OAuth session
        self.oauth_session = OAuth2Session(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )
        
        # Set tokens if provided
        if access_token and refresh_token:
            self.oauth_session.token = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
            }

    @classmethod
    def from_env(cls, sandbox: bool = True) -> "TrainingPeaksClient":
        """Create client from environment variables."""
        client_id = os.getenv("TRAININGPEAKS_CLIENT_ID")
        client_secret = os.getenv("TRAININGPEAKS_CLIENT_SECRET")
        redirect_uri = os.getenv("TRAININGPEAKS_REDIRECT_URI", "http://localhost:8000/auth/callback")
        access_token = os.getenv("TRAININGPEAKS_ACCESS_TOKEN")
        refresh_token = os.getenv("TRAININGPEAKS_REFRESH_TOKEN")
        
        if not client_id or not client_secret:
            raise ValueError("TRAININGPEAKS_CLIENT_ID and TRAININGPEAKS_CLIENT_SECRET must be set")
        
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            sandbox=sandbox,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def get_authorization_url(self, scopes: List[str] = None) -> str:
        """Get OAuth authorization URL for user to approve access."""
        if scopes is None:
            # Default scopes for reading workout data
            scopes = ["read:athlete", "read:workouts", "read:metrics"]
        
        authorization_url, state = self.oauth_session.authorization_url(
            f"{self.oauth_base}/oauth/authorize",
            scope=" ".join(scopes),
        )
        return authorization_url

    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access/refresh tokens."""
        token = self.oauth_session.fetch_token(
            f"{self.oauth_base}/oauth/token",
            authorization_response=f"{self.redirect_uri}?code={authorization_code}",
        )
        return token

    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        if not self.oauth_session.token or "refresh_token" not in self.oauth_session.token:
            raise TrainingPeaksAPIError("No refresh token available")
        
        token = self.oauth_session.refresh_token(f"{self.oauth_base}/oauth/token")
        return token

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request."""
        if not self.oauth_session.token:
            raise TrainingPeaksAPIError("No access token available. Please authenticate first.")
        
        url = f"{self.api_base}{endpoint}"
        
        try:
            response = self.oauth_session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Try to refresh token once
                try:
                    self.refresh_access_token()
                    response = self.oauth_session.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
                except Exception:
                    raise TrainingPeaksAPIError("Authentication failed. Please re-authenticate.")
            else:
                raise TrainingPeaksAPIError(f"API request failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise TrainingPeaksAPIError(f"Request failed: {str(e)}")

    def get_athlete_profile(self) -> Dict[str, Any]:
        """Get the authenticated athlete's profile."""
        return self._make_request("GET", "/v1/athlete")

    def fetch_workouts(
        self,
        start_date: date,
        end_date: date,
        athlete_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch workouts for a date range.
        
        Args:
            start_date: Start date for workout query
            end_date: End date for workout query
            athlete_id: Optional athlete ID (uses authenticated athlete if None)
        """
        params = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
        
        if athlete_id:
            endpoint = f"/v1/athletes/{athlete_id}/workouts"
        else:
            endpoint = "/v1/athlete/workouts"
        
        return self._make_request("GET", endpoint, params=params)

    def get_workout_details(self, workout_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific workout."""
        return self._make_request("GET", f"/v1/workouts/{workout_id}")

    def fetch_activities(
        self,
        start_date: date,
        end_date: date,
        athlete_id: Optional[str] = None,
    ) -> List[Activity]:
        """Fetch activities and convert to AutoCoach Activity format."""
        workouts = self.fetch_workouts(start_date, end_date, athlete_id)
        activities = []
        
        for workout in workouts:
            # Map TrainingPeaks workout data to AutoCoach Activity schema
            activity_data = {
                "activity_date": datetime.fromisoformat(workout.get("workoutDay", "")).date(),
                "sport": self._map_sport_type(workout.get("workoutTypeDescription", "Other")),
                "duration_min": float(workout.get("totalTimePlanned", 0)) / 60.0,  # Convert seconds to minutes
            }
            
            # Add optional fields if available
            if "distance" in workout:
                activity_data["distance_km"] = float(workout["distance"]) / 1000.0  # Convert meters to km
            
            if "tss" in workout:
                activity_data["tss"] = float(workout["tss"])
            
            if "averageHeartRate" in workout:
                activity_data["hr_avg"] = float(workout["averageHeartRate"])
            
            if "averagePower" in workout:
                activity_data["power_avg"] = float(workout["averagePower"])
            
            if "averagePace" in workout:
                # Convert pace from various formats to min/km
                activity_data["pace_min_per_km"] = self._convert_pace(workout["averagePace"])
            
            if "elevation" in workout:
                activity_data["elevation_m"] = float(workout["elevation"])
            
            if "intensityFactor" in workout:
                activity_data["intensity_factor"] = float(workout["intensityFactor"])
            
            activities.append(Activity(**activity_data))
        
        return activities

    def _map_sport_type(self, tp_sport: str) -> str:
        """Map TrainingPeaks sport types to standardized format."""
        sport_mapping = {
            "Bike": "ride",
            "Run": "run", 
            "Swim": "swim",
            "Other": "other",
            # Add more mappings as needed
        }
        return sport_mapping.get(tp_sport, "other")

    def _convert_pace(self, pace_value: Any) -> float:
        """Convert TrainingPeaks pace to minutes per kilometer."""
        # This is a placeholder - actual implementation depends on TP pace format
        if isinstance(pace_value, (int, float)):
            return float(pace_value)
        # Add string parsing logic if needed
        return 0.0

    def get_daily_metrics(
        self,
        start_date: date,
        end_date: date,
        athlete_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch daily metrics like HRV, sleep, etc."""
        params = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
        
        if athlete_id:
            endpoint = f"/v1/athletes/{athlete_id}/metrics"
        else:
            endpoint = "/v1/athlete/metrics"
        
        return self._make_request("GET", endpoint, params=params)
