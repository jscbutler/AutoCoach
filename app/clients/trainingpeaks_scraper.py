"""
TrainingPeaks Web Scraper (Browser Session)

Unofficial approach: Reuses browser cookies to fetch workout data
that TrainingPeaks shows in the UI. No API approval needed.

For single-user MVP use only.
"""

from __future__ import annotations

import os
import json
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

import requests
from pydantic import BaseModel


class TrainingPeaksScraperError(Exception):
    """Custom exception for TP scraper errors."""
    pass


class TPWorkoutDescription(BaseModel):
    """Model for a TrainingPeaks workout description (pre-activity text)."""
    workout_id: str
    date: date
    sport: str
    title: Optional[str] = None
    description: Optional[str] = None  # The coach's text we want!
    structured_workout: Optional[Dict[str, Any]] = None  # Builder steps if available
    duration_planned: Optional[float] = None  # minutes
    distance_planned: Optional[float] = None  # km
    tss_planned: Optional[float] = None


class TrainingPeaksScraper:
    """Scraper for TrainingPeaks using browser session cookies.
    
    This mimics browser requests to get workout data without API approval.
    Requires you to log in via browser first and copy cookies.
    """

    BASE_URL = "https://home.trainingpeaks.com"
    API_BASE = "https://api.trainingpeaks.com"

    def __init__(
        self,
        session_cookie: Optional[str] = None,
        cookie_file: Optional[Path] = None,
    ) -> None:
        """Initialize scraper with browser session.
        
        Args:
            session_cookie: The session cookie value from browser
            cookie_file: Path to file containing cookies (JSON)
        """
        self.session = requests.Session()
        self.cookie_file = cookie_file or Path.home() / ".tp_cookies.json"
        
        if session_cookie:
            self._set_session_cookie(session_cookie)
        elif self.cookie_file.exists():
            self._load_cookies_from_file()

    @classmethod
    def from_env(cls) -> "TrainingPeaksScraper":
        """Create scraper from environment variables."""
        session_cookie = os.getenv("TP_SESSION_COOKIE")
        cookie_file = os.getenv("TP_COOKIE_FILE")
        
        return cls(
            session_cookie=session_cookie,
            cookie_file=Path(cookie_file) if cookie_file else None,
        )

    def _set_session_cookie(self, cookie_value: str) -> None:
        """Set the session cookie for authenticated requests."""
        self.session.cookies.set(
            "TPSessionCookie",  # Adjust name based on what TP actually uses
            cookie_value,
            domain=".trainingpeaks.com",
        )

    def _load_cookies_from_file(self) -> None:
        """Load cookies from JSON file."""
        try:
            with open(self.cookie_file, 'r') as f:
                cookies_data = json.load(f)
                for cookie in cookies_data:
                    self.session.cookies.set(
                        cookie['name'],
                        cookie['value'],
                        domain=cookie.get('domain', '.trainingpeaks.com'),
                    )
        except Exception as e:
            print(f"Warning: Failed to load cookies: {e}")

    def save_cookies_from_browser(self, cookies: List[Dict[str, Any]]) -> None:
        """Save cookies from browser DevTools export.
        
        Args:
            cookies: List of cookie dicts with 'name', 'value', 'domain'
        """
        try:
            with open(self.cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            self.cookie_file.chmod(0o600)  # Readable only by owner
            print(f"✓ Cookies saved to {self.cookie_file}")
        except Exception as e:
            raise TrainingPeaksScraperError(f"Failed to save cookies: {e}")

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated request to TrainingPeaks."""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise TrainingPeaksScraperError(
                    "Authentication failed. Cookies may be expired. "
                    "Log in to TrainingPeaks in your browser and copy fresh cookies."
                )
            raise TrainingPeaksScraperError(f"Request failed: {e}")
        except Exception as e:
            raise TrainingPeaksScraperError(f"Request error: {e}")

    def get_workout_by_id(self, workout_id: str) -> TPWorkoutDescription:
        """Get workout details by ID.
        
        This fetches the same data TP shows in the workout detail view.
        
        Args:
            workout_id: The TrainingPeaks workout ID
            
        Returns:
            TPWorkoutDescription with all available workout data
        """
        # URL pattern discovered from browser DevTools
        # Adjust this based on actual TP API endpoints
        url = f"{self.API_BASE}/v1/workouts/{workout_id}"
        
        data = self._make_request("GET", url)
        
        return self._parse_workout_response(data)

    def get_workouts_for_date_range(
        self,
        start_date: date,
        end_date: date,
        athlete_id: Optional[str] = None,
    ) -> List[TPWorkoutDescription]:
        """Get all workouts in a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            athlete_id: Optional athlete ID (if you have multiple athletes)
            
        Returns:
            List of workout descriptions
        """
        # URL pattern from browser (adjust based on actual endpoint)
        url = f"{self.API_BASE}/v1/athlete/workouts"
        params = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }
        if athlete_id:
            params["athleteId"] = athlete_id
        
        data = self._make_request("GET", url, params=params)
        
        workouts = []
        for workout_data in data:
            try:
                workout = self._parse_workout_response(workout_data)
                workouts.append(workout)
            except Exception as e:
                print(f"Warning: Failed to parse workout: {e}")
        
        return workouts

    def get_workout_for_date(
        self,
        workout_date: date,
        athlete_id: Optional[str] = None,
    ) -> Optional[TPWorkoutDescription]:
        """Get workout for a specific date (convenience method).
        
        Args:
            workout_date: The date to fetch workout for
            athlete_id: Optional athlete ID
            
        Returns:
            Workout description or None if no workout on that date
        """
        workouts = self.get_workouts_for_date_range(
            workout_date,
            workout_date,
            athlete_id,
        )
        return workouts[0] if workouts else None

    def _parse_workout_response(self, data: Dict[str, Any]) -> TPWorkoutDescription:
        """Parse workout response from TP API.
        
        This extracts the key fields we care about:
        - The description text (for LLM parsing)
        - Structured workout if available
        - Planned metrics
        """
        # Extract date
        workout_date_str = data.get("workoutDay") or data.get("date")
        if workout_date_str:
            workout_date = datetime.fromisoformat(workout_date_str.replace('Z', '+00:00')).date()
        else:
            workout_date = date.today()
        
        # Extract description - this is what we really want!
        description = data.get("description") or data.get("preActivityComments") or data.get("workoutDescription")
        
        # Extract structured workout if available
        structured = None
        if "structure" in data or "workoutSteps" in data:
            structured = data.get("structure") or data.get("workoutSteps")
        
        return TPWorkoutDescription(
            workout_id=str(data.get("workoutId") or data.get("id", "unknown")),
            date=workout_date,
            sport=self._map_sport(data.get("workoutTypeDescription", "Other")),
            title=data.get("title") or data.get("workoutName"),
            description=description,  # The coach's text!
            structured_workout=structured,
            duration_planned=data.get("totalTimePlanned", 0) / 60.0 if data.get("totalTimePlanned") else None,
            distance_planned=data.get("distance", 0) / 1000.0 if data.get("distance") else None,
            tss_planned=data.get("tss"),
        )

    def _map_sport(self, tp_sport: str) -> str:
        """Map TP sport to AutoCoach format."""
        mapping = {
            "Bike": "ride",
            "Run": "run",
            "Swim": "swim",
            "Other": "other",
        }
        return mapping.get(tp_sport, "other")

    def fetch_workout_descriptions_for_parsing(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Fetch workout descriptions ready for LLM parsing.
        
        This returns the workout text in a format ready to send to an LLM
        for conversion to structured WorkoutSpec JSON.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of dicts with date, sport, and description text
        """
        workouts = self.get_workouts_for_date_range(start_date, end_date)
        
        results = []
        for workout in workouts:
            if workout.description:  # Only include if there's text to parse
                results.append({
                    "date": workout.date.isoformat(),
                    "sport": workout.sport,
                    "title": workout.title,
                    "description": workout.description,
                    "planned_duration": workout.duration_planned,
                    "planned_tss": workout.tss_planned,
                })
        
        return results


def setup_cookies_from_browser_export():
    """Interactive helper to set up cookies from browser export.
    
    Instructions:
    1. Log in to TrainingPeaks in Chrome
    2. Open DevTools (F12) → Application tab → Cookies
    3. Copy all cookies for trainingpeaks.com
    4. Run this function and paste the cookies
    """
    print("=" * 70)
    print("TrainingPeaks Cookie Setup")
    print("=" * 70)
    print()
    print("Steps:")
    print("1. Log in to TrainingPeaks in your browser")
    print("2. Open DevTools (F12)")
    print("3. Go to: Application → Storage → Cookies → https://trainingpeaks.com")
    print("4. Copy all cookies (or use a browser extension to export as JSON)")
    print()
    print("Paste cookies as JSON (list of {name, value, domain} dicts):")
    print("Press Ctrl+D when done")
    print()
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    cookie_json = "\n".join(lines)
    
    try:
        cookies = json.loads(cookie_json)
        scraper = TrainingPeaksScraper()
        scraper.save_cookies_from_browser(cookies)
        print()
        print("✓ Setup complete! You can now use TrainingPeaksScraper.")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Make sure you pasted valid JSON")

