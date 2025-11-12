"""
Garmin Connect API Client (Unofficial)

Uses the python-garminconnect library to access Garmin Connect data.
No official API approval needed - uses your Garmin credentials.
"""

from __future__ import annotations

import os
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError
from pydantic import BaseModel

from app.schemas.training import Activity, Sample


class GarminAPIError(Exception):
    """Custom exception for Garmin API errors."""
    pass


class GarminTokens(BaseModel):
    """Model for storing Garmin OAuth tokens."""
    oauth1_token: Dict[str, str]
    oauth2_token: Dict[str, str]


class GarminClient:
    """Garmin Connect API client using unofficial library.
    
    Authenticates with username/password, caches tokens locally.
    """

    def __init__(
        self,
        email: str,
        password: str,
        token_store_path: Optional[Path] = None,
    ) -> None:
        """Initialize Garmin client.
        
        Args:
            email: Garmin account email
            password: Garmin account password
            token_store_path: Path to store authentication tokens (default: .garmin_tokens.json)
        """
        self.email = email
        self.password = password
        self.token_store_path = token_store_path or Path.home() / ".garmin_tokens.json"
        self.client: Optional[Garmin] = None

    @classmethod
    def from_env(cls, token_store_path: Optional[Path] = None) -> "GarminClient":
        """Create client from environment variables."""
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")
        
        if not email or not password:
            raise ValueError("GARMIN_EMAIL and GARMIN_PASSWORD must be set")
        
        return cls(email=email, password=password, token_store_path=token_store_path)

    def _load_tokens(self) -> Optional[GarminTokens]:
        """Load cached tokens from file."""
        if not self.token_store_path.exists():
            return None
        
        try:
            with open(self.token_store_path, 'r') as f:
                data = json.load(f)
                return GarminTokens(**data)
        except Exception as e:
            print(f"Warning: Failed to load cached tokens: {e}")
            return None

    def _save_tokens(self, tokens: GarminTokens) -> None:
        """Save tokens to file."""
        try:
            with open(self.token_store_path, 'w') as f:
                json.dump(tokens.model_dump(), f, indent=2)
            # Make file readable only by owner
            self.token_store_path.chmod(0o600)
        except Exception as e:
            print(f"Warning: Failed to save tokens: {e}")

    def login(self) -> None:
        """Authenticate with Garmin Connect."""
        try:
            # Try to use cached tokens first
            tokens = self._load_tokens()
            if tokens:
                try:
                    self.client = Garmin()
                    self.client.login(tokens.oauth1_token)
                    print("✓ Authenticated using cached tokens")
                    return
                except (GarminConnectAuthenticationError, GarminConnectConnectionError):
                    print("Cached tokens expired, re-authenticating...")
                except Exception:
                    print("Failed to use cached tokens, re-authenticating...")
            
            # Fallback to username/password login
            self.client = Garmin(self.email, self.password)
            self.client.login()
            
            # Cache the new tokens
            try:
                new_tokens = GarminTokens(
                    oauth1_token=self.client.garth.oauth1_token,
                    oauth2_token=self.client.garth.oauth2_token,
                )
                self._save_tokens(new_tokens)
                print("✓ Authenticated with username/password (tokens cached)")
            except Exception as e:
                print(f"Warning: Could not cache tokens: {e}")
            
        except GarminConnectAuthenticationError as e:
            raise GarminAPIError(f"Authentication failed: {e}")
        except Exception as e:
            raise GarminAPIError(f"Login failed: {e}")

    def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated, login if needed."""
        if not self.client:
            self.login()

    def get_activities(
        self,
        start_date: date,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get activities from Garmin Connect.
        
        Args:
            start_date: Start date for activities
            end_date: End date for activities (default: today)
            limit: Maximum number of activities to fetch
            
        Returns:
            List of activity dictionaries
        """
        self._ensure_authenticated()
        
        if end_date is None:
            end_date = date.today()
        
        try:
            # Garmin API uses ISO format strings
            activities = self.client.get_activities_by_date(
                start_date.isoformat(),
                end_date.isoformat(),
                activitytype=None,  # All activity types
            )
            
            # Limit results
            return activities[:limit] if activities else []
            
        except Exception as e:
            raise GarminAPIError(f"Failed to fetch activities: {e}")

    def get_activity_details(self, activity_id: int) -> Dict[str, Any]:
        """Get detailed information for a specific activity.
        
        Args:
            activity_id: Garmin activity ID
            
        Returns:
            Activity details dictionary
        """
        self._ensure_authenticated()
        
        try:
            return self.client.get_activity_evaluation(activity_id)
        except Exception as e:
            raise GarminAPIError(f"Failed to fetch activity {activity_id}: {e}")

    def get_activity_splits(self, activity_id: int) -> List[Dict[str, Any]]:
        """Get activity splits/laps.
        
        Args:
            activity_id: Garmin activity ID
            
        Returns:
            List of split/lap dictionaries
        """
        self._ensure_authenticated()
        
        try:
            return self.client.get_activity_splits(activity_id)
        except Exception as e:
            raise GarminAPIError(f"Failed to fetch splits for {activity_id}: {e}")

    def fetch_activities_since(
        self,
        since_date: Optional[date] = None,
        days_back: int = 3,
    ) -> List[Activity]:
        """Fetch activities since a date and convert to AutoCoach format.
        
        Args:
            since_date: Date to fetch from (if None, uses days_back)
            days_back: Number of days to look back if since_date is None
            
        Returns:
            List of Activity objects in AutoCoach format
        """
        if since_date is None:
            since_date = date.today() - timedelta(days=days_back)
        
        end_date = date.today()
        
        print(f"Fetching Garmin activities from {since_date} to {end_date}...")
        
        activities = self.get_activities(since_date, end_date)
        print(f"✓ Found {len(activities)} Garmin activities")
        
        # Convert to AutoCoach format
        converted = []
        for activity in activities:
            try:
                activity_data = self._convert_to_autocoach_format(activity)
                if activity_data:
                    converted.append(Activity(**activity_data))
            except Exception as e:
                print(f"Warning: Failed to convert activity {activity.get('activityId')}: {e}")
        
        return converted

    def _convert_to_autocoach_format(self, activity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Garmin activity to AutoCoach Activity format.
        
        Args:
            activity: Garmin activity dictionary
            
        Returns:
            Dictionary compatible with Activity schema
        """
        # Extract start time
        start_time_str = activity.get('startTimeLocal') or activity.get('startTimeGMT')
        if not start_time_str:
            return None
        
        activity_date = datetime.fromisoformat(start_time_str.replace('Z', '+00:00')).date()
        
        # Map activity type
        sport = self._map_activity_type(activity.get('activityType', {}).get('typeKey', 'other'))
        
        # Build activity data
        activity_data = {
            "activity_date": activity_date,
            "sport": sport,
            "duration_min": activity.get('duration', 0) / 60.0,  # Convert seconds to minutes
        }
        
        # Add optional fields
        if 'distance' in activity and activity['distance']:
            activity_data["distance_km"] = activity['distance'] / 1000.0  # meters to km
        
        if 'averageHR' in activity and activity['averageHR']:
            activity_data["hr_avg"] = activity['averageHR']
        
        if 'averagePower' in activity and activity['averagePower']:
            activity_data["power_avg"] = activity['averagePower']
        
        if 'normalizedPower' in activity and activity['normalizedPower']:
            activity_data["normalized_power"] = activity['normalizedPower']
        
        if 'elevationGain' in activity and activity['elevationGain']:
            activity_data["elevation_m"] = activity['elevationGain']
        
        # Garmin sometimes provides training effect/load
        if 'trainingEffect' in activity:
            # We could use this but our TSS calculation is more standard
            pass
        
        return activity_data

    def _map_activity_type(self, garmin_type: str) -> str:
        """Map Garmin activity types to standardized format."""
        mapping = {
            "cycling": "ride",
            "road_biking": "ride",
            "mountain_biking": "ride",
            "indoor_cycling": "ride",
            "virtual_ride": "ride",
            "running": "run",
            "trail_running": "run",
            "treadmill_running": "run",
            "virtual_run": "run",
            "swimming": "swim",
            "lap_swimming": "swim",
            "open_water_swimming": "swim",
            "walking": "run",  # Treat as run for now
            "hiking": "run",
            "strength_training": "other",
            "other": "other",
        }
        return mapping.get(garmin_type.lower(), "other")

