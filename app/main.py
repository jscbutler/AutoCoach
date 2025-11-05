from __future__ import annotations

import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import RedirectResponse

from app.schemas.training import Activity, MetricsDaily, WorkoutExecuted, Sample
from app.services.metrics import compute_metrics_daily
from app.services.file_parser import parse_fit_file, FileParseError
from app.clients.trainingpeaks import TrainingPeaksClient, TrainingPeaksAPIError

app = FastAPI(title="AutoCoach API", version="0.1.0")

# Global client instance (in production, this should be managed per user)
tp_client: Optional[TrainingPeaksClient] = None


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
