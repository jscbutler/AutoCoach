"""
Strava API Client with OAuth 2.0 authentication.

Provides access to Strava athlete data, activities, and streams.
Simpler and more accessible than TrainingPeaks.
"""

from __future__ import annotations

import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional

import httpx
from authlib.integrations.requests_client import OAuth2Session

from app.schemas.training import Activity, WorkoutExecuted, Sample


class StravaAPIError(Exception):
    """Custom exception for Strava API errors."""
    pass


class StravaClient:
    """Strava API client with OAuth 2.0 authentication.
    
    More accessible than TrainingPeaks - instant API access.
    Rate limits: 100 requests per 15 min, 1000 per day.
    """

    # API endpoints
    API_BASE = "https://www.strava.com/api/v3"
    OAUTH_BASE = "https://www.strava.com/oauth"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8000/auth/callback",
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        
        # OAuth session
        self.oauth_session = OAuth2Session(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="read,activity:read_all,profile:read_all",
        )
        
        # Set tokens if provided
        if access_token and refresh_token:
            self.oauth_session.token = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
            }

    @classmethod
    def from_env(cls) -> "StravaClient":
        """Create client from environment variables."""
        client_id = os.getenv("STRAVA_CLIENT_ID")
        client_secret = os.getenv("STRAVA_CLIENT_SECRET")
        # Use OAUTH_REDIRECT_URI (shared) or fallback to STRAVA_REDIRECT_URI or localhost
        redirect_uri = os.getenv("OAUTH_REDIRECT_URI") or os.getenv("STRAVA_REDIRECT_URI", "http://localhost:8000/auth/callback")
        access_token = os.getenv("STRAVA_ACCESS_TOKEN")
        refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
        
        if not client_id or not client_secret:
            raise ValueError("STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set")
        
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def get_authorization_url(self) -> str:
        """Get OAuth authorization URL for user to approve access."""
        authorization_url, state = self.oauth_session.create_authorization_url(
            f"{self.OAUTH_BASE}/authorize",
            approval_prompt="auto",
        )
        return authorization_url

    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access/refresh tokens."""
        # Make direct POST request to Strava token endpoint
        # authlib's fetch_token doesn't work correctly with Strava
        import requests
        
        token_url = f"{self.OAUTH_BASE}/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "grant_type": "authorization_code",
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token = response.json()
        
        # Update the oauth_session with the new token
        self.oauth_session.token = token
        
        return token

    def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        if not self.oauth_session.token or "refresh_token" not in self.oauth_session.token:
            raise StravaAPIError("No refresh token available")
        
        token = self.oauth_session.refresh_token(
            f"{self.OAUTH_BASE}/token",
            refresh_token=self.oauth_session.token["refresh_token"],
        )
        return token

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make authenticated API request with automatic token refresh."""
        if not self.oauth_session.token:
            raise StravaAPIError("No access token available. Please authenticate first.")
        
        url = f"{self.API_BASE}{endpoint}"
        
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
                    raise StravaAPIError("Authentication failed. Please re-authenticate.")
            else:
                raise StravaAPIError(
                    f"API request failed: {e.response.status_code} - {e.response.text}"
                )
        except Exception as e:
            raise StravaAPIError(f"Request failed: {str(e)}")

    def get_athlete(self) -> Dict[str, Any]:
        """Get the authenticated athlete's profile."""
        return self._make_request("GET", "/athlete")

    def get_athlete_zones(self) -> Dict[str, Any]:
        """Get athlete's training zones (heart rate and power)."""
        return self._make_request("GET", "/athlete/zones")

    def list_activities(
        self,
        before: Optional[int] = None,
        after: Optional[int] = None,
        page: int = 1,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """List athlete's activities.
        
        Args:
            before: Unix timestamp, return activities before this time
            after: Unix timestamp, return activities after this time
            page: Page number
            per_page: Number of items per page (max 200)
        """
        params = {"page": page, "per_page": min(per_page, 200)}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        
        return self._make_request("GET", "/athlete/activities", params=params)

    def get_activity(self, activity_id: int, include_all_efforts: bool = False) -> Dict[str, Any]:
        """Get detailed information about a specific activity.
        
        Args:
            activity_id: The activity ID
            include_all_efforts: Include all segment efforts
        """
        params = {"include_all_efforts": include_all_efforts}
        return self._make_request("GET", f"/activities/{activity_id}", params=params)

    def get_activity_streams(
        self,
        activity_id: int,
        keys: List[str] = None,
        key_by_type: bool = True,
    ) -> Dict[str, Any]:
        """Get activity streams (time-series data).
        
        Args:
            activity_id: The activity ID
            keys: Stream types to include (time, distance, altitude, velocity_smooth,
                  heartrate, cadence, watts, temp, moving, grade_smooth, latlng)
            key_by_type: Return streams keyed by type
        """
        if keys is None:
            keys = ["time", "distance", "altitude", "heartrate", "cadence", "watts", "latlng"]
        
        keys_str = ",".join(keys)
        return self._make_request(
            "GET",
            f"/activities/{activity_id}/streams",
            params={"keys": keys_str, "key_by_type": key_by_type},
        )

    def fetch_activities(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Activity]:
        """Fetch activities and convert to AutoCoach Activity format.
        
        Args:
            start_date: Start date for activities
            end_date: End date for activities
        """
        # Convert dates to Unix timestamps
        after = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        before = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        
        # Fetch activities (handle pagination if needed)
        all_activities = []
        page = 1
        
        while True:
            activities = self.list_activities(after=after, before=before, page=page, per_page=200)
            if not activities:
                break
            all_activities.extend(activities)
            if len(activities) < 200:
                break
            page += 1
        
        # Convert to AutoCoach format
        converted = []
        for activity in all_activities:
            activity_data = {
                "activity_date": datetime.fromisoformat(
                    activity["start_date"].replace("Z", "+00:00")
                ).date(),
                "sport": self._map_sport_type(activity.get("type", "Other")),
                "duration_min": activity.get("moving_time", 0) / 60.0,
            }
            
            # Add optional fields
            if "distance" in activity:
                activity_data["distance_km"] = activity["distance"] / 1000.0
            
            if "average_heartrate" in activity:
                activity_data["hr_avg"] = activity["average_heartrate"]
            
            if "average_watts" in activity:
                activity_data["power_avg"] = activity["average_watts"]
            
            if "weighted_average_watts" in activity:
                activity_data["normalized_power"] = activity["weighted_average_watts"]
            
            if "total_elevation_gain" in activity:
                activity_data["elevation_m"] = activity["total_elevation_gain"]
            
            # Calculate TSS if we have power and FTP
            # Strava doesn't provide TSS directly, we'd need to calculate it
            
            converted.append(Activity(**activity_data))
        
        return converted

    def _map_sport_type(self, strava_type: str) -> str:
        """Map Strava activity types to standardized format."""
        mapping = {
            "Ride": "ride",
            "VirtualRide": "ride",
            "Run": "run",
            "VirtualRun": "run",
            "Swim": "swim",
            "Walk": "run",  # Treat walk as run for now
            "Hike": "run",
            "Other": "other",
        }
        return mapping.get(strava_type, "other")

    def get_activity_samples(self, activity_id: int) -> List[Sample]:
        """Get activity samples (time-series data) in AutoCoach format.
        
        Args:
            activity_id: The Strava activity ID
            
        Returns:
            List of Sample objects with time-series data
        """
        streams = self.get_activity_streams(activity_id)
        
        if not streams:
            return []
        
        # Get stream lengths and validate
        time_stream = streams.get("time", {}).get("data", [])
        if not time_stream:
            return []
        
        num_samples = len(time_stream)
        
        # Extract streams
        distance = streams.get("distance", {}).get("data", [None] * num_samples)
        altitude = streams.get("altitude", {}).get("data", [None] * num_samples)
        heartrate = streams.get("heartrate", {}).get("data", [None] * num_samples)
        cadence = streams.get("cadence", {}).get("data", [None] * num_samples)
        watts = streams.get("watts", {}).get("data", [None] * num_samples)
        latlng = streams.get("latlng", {}).get("data", [None] * num_samples)
        velocity = streams.get("velocity_smooth", {}).get("data", [None] * num_samples)
        
        # Create samples
        samples = []
        for i in range(num_samples):
            # Extract lat/lng if available
            lat, lon = None, None
            if latlng[i] and len(latlng[i]) == 2:
                lat, lon = latlng[i]
            
            sample = Sample(
                workout_id=activity_id,
                t_s=time_stream[i],
                power_w=watts[i],
                hr_bpm=heartrate[i],
                pace_mps=velocity[i],
                cadence=cadence[i],
                altitude_m=altitude[i],
                lat=lat,
                lon=lon,
            )
            samples.append(sample)
        
        return samples

