from __future__ import annotations

import os
import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv, set_key
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import RedirectResponse

from app.schemas.training import Activity, MetricsDaily, WorkoutExecuted, Sample
from app.services.metrics import compute_metrics_daily
from app.services.file_parser import parse_fit_file, FileParseError
from app.clients.trainingpeaks import TrainingPeaksClient, TrainingPeaksAPIError
from app.clients.strava import StravaClient, StravaAPIError

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="AutoCoach API", version="0.1.0")

# Global client instances (in production, this should be managed per user)
tp_client: Optional[TrainingPeaksClient] = None
strava_client: Optional[StravaClient] = None


@app.get("/")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/workouts/upload")
async def upload_workout(
    file: UploadFile = File(..., description="FIT/TCX/GPX file (.fit, .fit.gz, .tcx, .gpx)"),
    athlete_id: int = Form(..., description="Athlete ID"),
    ftp: Optional[int] = Form(None, description="Functional Threshold Power (for TSS calculation)"),
):
    """
    Upload and parse a workout file (FIT, TCX, or GPX).
    
    Supports compressed files (.fit.gz).
    Returns workout summary and sample count.
    """
    # Validate file type
    allowed_extensions = {'.fit', '.gz', '.tcx', '.gpx'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        # Check if it's .fit.gz
        if not file.filename.lower().endswith('.fit.gz'):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: .fit, .fit.gz, .tcx, .gpx"
            )
    
    # Create uploads directory if it doesn't exist
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # Save uploaded file temporarily
    temp_file_path = uploads_dir / file.filename
    try:
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse the file (currently only FIT supported)
        if file.filename.lower().endswith(('.fit', '.fit.gz')):
            try:
                workout, samples = parse_fit_file(
                    str(temp_file_path),
                    athlete_id=athlete_id,
                    ftp=ftp
                )
                
                return {
                    "message": "Workout uploaded and parsed successfully",
                    "workout": workout.model_dump(),
                    "sample_count": len(samples),
                    "file_path": str(temp_file_path),
                }
            except FileParseError as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse FIT file: {str(e)}")
        else:
            # TCX/GPX support coming soon
            raise HTTPException(
                status_code=501,
                detail="TCX/GPX parsing not yet implemented. Use FIT files for now."
            )
    
    except Exception as e:
        # Clean up temp file on error
        if temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/metrics/daily", response_model=List[MetricsDaily])
async def metrics_daily(activities: List[Activity]) -> List[MetricsDaily]:
    return compute_metrics_daily(activities)


@app.get("/auth/trainingpeaks")
async def auth_trainingpeaks(sandbox: bool = Query(True, description="Use sandbox environment")):
    """Initiate TrainingPeaks OAuth flow."""
    global tp_client
    
    try:
        tp_client = TrainingPeaksClient.from_env(sandbox=sandbox)
        auth_url = tp_client.get_authorization_url()
        return {"authorization_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize OAuth: {str(e)}")


@app.get("/auth/callback")
async def auth_callback(code: str = Query(..., description="Authorization code from TrainingPeaks")):
    """Handle OAuth callback and exchange code for tokens."""
    global tp_client
    
    if not tp_client:
        raise HTTPException(status_code=400, detail="OAuth flow not initiated")
    
    try:
        token = tp_client.exchange_code_for_token(code)
        return {
            "message": "Authentication successful",
            "access_token": token.get("access_token", "")[:20] + "...",  # Truncated for security
            "expires_in": token.get("expires_in"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code for token: {str(e)}")


@app.get("/trainingpeaks/profile")
async def get_tp_profile():
    """Get TrainingPeaks athlete profile."""
    global tp_client
    
    if not tp_client or not tp_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with TrainingPeaks")
    
    try:
        profile = tp_client.get_athlete_profile()
        return profile
    except TrainingPeaksAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/trainingpeaks/activities", response_model=List[Activity])
async def get_tp_activities(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    athlete_id: Optional[str] = Query(None, description="Optional athlete ID"),
):
    """Fetch activities from TrainingPeaks."""
    global tp_client
    
    if not tp_client or not tp_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with TrainingPeaks")
    
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    if (end_date - start_date).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
    
    try:
        activities = tp_client.fetch_activities(start_date, end_date, athlete_id)
        return activities
    except TrainingPeaksAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/trainingpeaks/metrics", response_model=List[MetricsDaily])
async def compute_tp_metrics(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    athlete_id: Optional[str] = Query(None, description="Optional athlete ID"),
):
    """Fetch TrainingPeaks activities and compute metrics."""
    global tp_client
    
    if not tp_client or not tp_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with TrainingPeaks")
    
    try:
        activities = tp_client.fetch_activities(start_date, end_date, athlete_id)
        metrics = compute_metrics_daily(activities)
        return metrics
    except TrainingPeaksAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Strava OAuth Endpoints
# ============================================================================

@app.get("/auth/strava")
async def auth_strava():
    """Initiate Strava OAuth flow."""
    global strava_client
    
    try:
        strava_client = StravaClient.from_env()
        auth_url = strava_client.get_authorization_url()
        return {"authorization_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize OAuth: {str(e)}")


@app.get("/auth/strava/callback")
async def auth_strava_callback(code: str = Query(..., description="Authorization code from Strava")):
    """Handle Strava OAuth callback and exchange code for tokens."""
    global strava_client
    
    if not strava_client:
        raise HTTPException(status_code=400, detail="OAuth flow not initiated")
    
    try:
        token = strava_client.exchange_code_for_token(code)
        
        # Debug: log the token response structure
        print(f"DEBUG: Token response keys: {token.keys() if token else 'None'}")
        print(f"DEBUG: Token response: {str(token)[:200]}")
        
        # Save tokens to .env file for persistence
        env_path = Path(__file__).parent.parent / ".env"
        access_token = token.get("access_token", "")
        refresh_token = token.get("refresh_token", "")
        
        print(f"DEBUG: access_token length: {len(access_token) if access_token else 0}")
        print(f"DEBUG: refresh_token length: {len(refresh_token) if refresh_token else 0}")
        
        if access_token and refresh_token:
            set_key(env_path, "STRAVA_ACCESS_TOKEN", access_token)
            set_key(env_path, "STRAVA_REFRESH_TOKEN", refresh_token)
            
            # Reload the client with the new tokens
            strava_client = StravaClient.from_env()
            print("DEBUG: Tokens saved and client reloaded")
        else:
            print("DEBUG: Tokens not saved - one or both are empty")
        
        return {
            "message": "Authentication successful",
            "access_token": access_token[:20] + "..." if access_token else "EMPTY",
            "expires_in": token.get("expires_in"),
            "athlete": token.get("athlete", {}),
            "debug_keys": list(token.keys()) if token else [],
        }
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in callback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Failed to exchange code for token: {str(e)}")


@app.get("/strava/athlete")
async def get_strava_athlete():
    """Get Strava athlete profile."""
    global strava_client
    
    # Auto-initialize client from env if not already done
    if not strava_client:
        try:
            strava_client = StravaClient.from_env()
        except ValueError:
            raise HTTPException(status_code=401, detail="Not authenticated with Strava. Please run OAuth flow first.")
    
    if not strava_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with Strava")
    
    try:
        athlete = strava_client.get_athlete()
        return athlete
    except StravaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/strava/zones")
async def get_strava_zones():
    """Get Strava athlete training zones."""
    global strava_client
    
    # Auto-initialize client from env if not already done
    if not strava_client:
        try:
            strava_client = StravaClient.from_env()
        except ValueError:
            raise HTTPException(status_code=401, detail="Not authenticated with Strava. Please run OAuth flow first.")
    
    if not strava_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with Strava")
    
    try:
        zones = strava_client.get_athlete_zones()
        return zones
    except StravaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/strava/activities", response_model=List[Activity])
async def get_strava_activities(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Fetch activities from Strava."""
    global strava_client
    
    # Auto-initialize client from env if not already done
    if not strava_client:
        try:
            strava_client = StravaClient.from_env()
        except ValueError:
            raise HTTPException(status_code=401, detail="Not authenticated with Strava. Please run OAuth flow first.")
    
    if not strava_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with Strava")
    
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    if (end_date - start_date).days > 365:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")
    
    try:
        activities = strava_client.fetch_activities(start_date, end_date)
        return activities
    except StravaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/strava/activity/{activity_id}")
async def get_strava_activity_detail(activity_id: int):
    """Get detailed Strava activity."""
    global strava_client
    
    # Auto-initialize client from env if not already done
    if not strava_client:
        try:
            strava_client = StravaClient.from_env()
        except ValueError:
            raise HTTPException(status_code=401, detail="Not authenticated with Strava. Please run OAuth flow first.")
    
    if not strava_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with Strava")
    
    try:
        activity = strava_client.get_activity(activity_id, include_all_efforts=True)
        return activity
    except StravaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/strava/activity/{activity_id}/streams")
async def get_strava_activity_streams(activity_id: int):
    """Get Strava activity streams (time-series data)."""
    global strava_client
    
    # Auto-initialize client from env if not already done
    if not strava_client:
        try:
            strava_client = StravaClient.from_env()
        except ValueError:
            raise HTTPException(status_code=401, detail="Not authenticated with Strava. Please run OAuth flow first.")
    
    if not strava_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with Strava")
    
    try:
        streams = strava_client.get_activity_streams(activity_id)
        return streams
    except StravaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/strava/metrics", response_model=List[MetricsDaily])
async def compute_strava_metrics(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Fetch Strava activities and compute metrics."""
    global strava_client
    
    # Auto-initialize client from env if not already done
    if not strava_client:
        try:
            strava_client = StravaClient.from_env()
        except ValueError:
            raise HTTPException(status_code=401, detail="Not authenticated with Strava. Please run OAuth flow first.")
    
    if not strava_client.oauth_session.token:
        raise HTTPException(status_code=401, detail="Not authenticated with Strava")
    
    try:
        activities = strava_client.fetch_activities(start_date, end_date)
        metrics = compute_metrics_daily(activities)
        return metrics
    except StravaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
