from datetime import date, datetime
from typing import Optional, List, Dict, Tuple

from pydantic import BaseModel, Field, field_validator


class Activity(BaseModel):
    """Legacy activity model for TrainingPeaks integration."""
    activity_date: date = Field(..., description="Activity date")
    sport: str = Field(..., description="Sport type, e.g., run, ride, swim")
    duration_min: float = Field(..., ge=0, description="Duration in minutes")
    distance_km: Optional[float] = Field(None, ge=0)
    tss: Optional[float] = Field(None, ge=0)
    hr_avg: Optional[float] = Field(None, ge=0)
    power_avg: Optional[float] = Field(None, ge=0)
    pace_min_per_km: Optional[float] = Field(None, ge=0)
    elevation_m: Optional[float] = Field(None, ge=0)
    intensity_factor: Optional[float] = Field(None, ge=0)


class Athlete(BaseModel):
    """Athlete profile with thresholds and training zones."""
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    name: str = Field(..., min_length=1, max_length=255, description="Athlete name")
    sport: str = Field(..., description="Primary sport: cycling, running, swimming, triathlon")
    ftp: Optional[int] = Field(None, ge=0, le=600, description="Cycling Functional Threshold Power (watts)")
    cp: Optional[float] = Field(None, ge=0, description="Running Critical Pace (min/km) or Critical Power")
    lthr: Optional[int] = Field(None, ge=0, le=220, description="Lactate Threshold Heart Rate (bpm)")
    max_hr: Optional[int] = Field(None, ge=0, le=220, description="Maximum Heart Rate (bpm)")
    resting_hr: Optional[int] = Field(None, ge=30, le=100, description="Resting Heart Rate (bpm)")
    weight_kg: Optional[float] = Field(None, ge=30, le=200, description="Body weight in kg")
    hr_zones: Optional[Dict[str, Tuple[int, int]]] = Field(
        None, 
        description="Heart rate zones as dict of zone name to (min, max) tuple, e.g., {'Z1': (100, 120)}"
    )
    power_zones: Optional[Dict[str, Tuple[int, int]]] = Field(
        None,
        description="Power zones as dict of zone name to (min, max) tuple, e.g., {'Z2': (150, 200)}"
    )
    pace_zones: Optional[Dict[str, Tuple[float, float]]] = Field(
        None,
        description="Pace zones for running (min/km) as dict of zone name to (min, max) tuple"
    )
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")

    @field_validator('sport')
    @classmethod
    def validate_sport(cls, v: str) -> str:
        allowed_sports = ['cycling', 'running', 'swimming', 'triathlon', 'other']
        if v.lower() not in allowed_sports:
            raise ValueError(f"Sport must be one of: {', '.join(allowed_sports)}")
        return v.lower()


class WorkoutStep(BaseModel):
    """Single step in a workout plan (e.g., warmup, interval, rest, cooldown)."""
    kind: str = Field(..., description="Step type: warmup, work, rest, cooldown, interval_block")
    duration_s: Optional[int] = Field(None, ge=0, description="Duration in seconds (if time-based)")
    duration_distance_m: Optional[float] = Field(None, ge=0, description="Duration in meters (if distance-based)")
    target_power_pct: Optional[int] = Field(None, ge=0, le=300, description="Target power as % of FTP")
    target_power_w: Optional[int] = Field(None, ge=0, description="Target power in watts (absolute)")
    target_hr_pct: Optional[int] = Field(None, ge=0, le=120, description="Target HR as % of LTHR or max")
    target_hr_bpm: Optional[int] = Field(None, ge=0, le=220, description="Target HR in bpm (absolute)")
    target_pace_min_per_km: Optional[float] = Field(None, ge=0, description="Target pace in min/km")
    tolerance_pct: Optional[int] = Field(5, ge=0, le=20, description="Acceptable deviation from target (%)")
    repeats: Optional[int] = Field(1, ge=1, description="Number of repeats (for interval blocks)")
    steps: Optional[List['WorkoutStep']] = Field(None, description="Nested steps (for interval blocks)")


class WorkoutSpec(BaseModel):
    """Structured workout specification (parsed from text or created manually)."""
    sport: str = Field(..., description="Sport type: cycling, running, swimming")
    name: Optional[str] = Field(None, description="Workout name/description")
    steps: List[WorkoutStep] = Field(..., description="Ordered list of workout steps")
    total_duration_s: Optional[int] = Field(None, ge=0, description="Total planned duration in seconds")
    total_tss: Optional[float] = Field(None, ge=0, description="Planned Training Stress Score")


class WorkoutPlanned(BaseModel):
    """Planned workout with structured specification."""
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    athlete_id: int = Field(..., ge=1, description="Foreign key to athlete")
    start_time: datetime = Field(..., description="Planned start date/time")
    sport: str = Field(..., description="Sport type: cycling, running, swimming")
    spec_json: Dict = Field(..., description="WorkoutSpec as JSON (use WorkoutSpec.model_dump())")
    notes: Optional[str] = Field(None, max_length=2000, description="Coach notes or workout description")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")


class WorkoutExecuted(BaseModel):
    """Executed workout from file upload or API sync."""
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    athlete_id: int = Field(..., ge=1, description="Foreign key to athlete")
    source: str = Field(..., description="Data source: file, trainingpeaks, strava, garmin")
    start_time: datetime = Field(..., description="Actual workout start time")
    duration_s: int = Field(..., ge=0, description="Actual duration in seconds")
    sport: str = Field(..., description="Sport type: cycling, running, swimming")
    file_ref: Optional[str] = Field(None, max_length=500, description="File path or S3 URL")
    summary_json: Dict = Field(
        default_factory=dict,
        description="Summary metrics: avg_power, np, if, vi, avg_hr, tss, distance_m, elevation_m"
    )
    planned_workout_id: Optional[int] = Field(None, description="Foreign key to workout_planned (if matched)")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")

    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        allowed_sources = ['file', 'trainingpeaks', 'strava', 'garmin', 'wahoo', 'other']
        if v.lower() not in allowed_sources:
            raise ValueError(f"Source must be one of: {', '.join(allowed_sources)}")
        return v.lower()


class Sample(BaseModel):
    """Per-second (or per-record) workout data sample."""
    workout_id: int = Field(..., ge=1, description="Foreign key to workout_executed")
    t_s: int = Field(..., ge=0, description="Time offset from workout start in seconds")
    power_w: Optional[int] = Field(None, ge=0, le=2000, description="Power in watts")
    hr_bpm: Optional[int] = Field(None, ge=0, le=220, description="Heart rate in beats per minute")
    pace_mps: Optional[float] = Field(None, ge=0, description="Pace in meters per second")
    cadence: Optional[int] = Field(None, ge=0, le=300, description="Cadence (rpm for cycling, spm for running)")
    altitude_m: Optional[float] = Field(None, description="Altitude in meters")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    distance_m: Optional[float] = Field(None, ge=0, description="Cumulative distance in meters")


class IntervalDetected(BaseModel):
    """Detected interval segment from workout analysis."""
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    workout_id: int = Field(..., ge=1, description="Foreign key to workout_executed")
    t_start: int = Field(..., ge=0, description="Interval start time in seconds")
    t_end: int = Field(..., ge=0, description="Interval end time in seconds")
    kind: str = Field(..., description="Interval type: work, rest, warmup, cooldown, other")
    targets_json: Optional[Dict] = Field(None, description="Matched planned targets (if any)")
    metrics_json: Dict = Field(
        default_factory=dict,
        description="Interval metrics: avg_power, np, avg_hr, time_in_zone, compliance_pct"
    )
    planned_step_index: Optional[int] = Field(None, description="Index of matched WorkoutSpec step")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")

    @field_validator('t_end')
    @classmethod
    def validate_end_after_start(cls, v: int, info) -> int:
        if 't_start' in info.data and v <= info.data['t_start']:
            raise ValueError("t_end must be greater than t_start")
        return v


class AthleteThreshold(BaseModel):
    """Date-versioned athlete thresholds for accurate historical analysis.
    
    When scoring a workout, use the threshold that was effective on that date.
    Supports TrainingPeaks import and manual user overrides.
    """
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    athlete_id: int = Field(..., ge=1, description="Foreign key to athlete")
    effective_date: date = Field(..., description="Date when these thresholds became active")
    sport: str = Field(..., description="Sport type: cycling, running, swimming")
    
    # Cycling thresholds
    ftp: Optional[int] = Field(None, ge=0, le=600, description="Functional Threshold Power (watts)")
    ftp_source: Optional[str] = Field(None, description="Source: trainingpeaks, test, estimate, user_override")
    
    # Running thresholds
    threshold_pace_min_per_km: Optional[float] = Field(
        None, ge=2.0, le=10.0, 
        description="Threshold pace for running (min/km) - roughly hour race pace"
    )
    critical_speed_m_per_s: Optional[float] = Field(
        None, ge=2.0, le=8.0,
        description="Critical speed (m/s) - boundary between heavy/severe domains"
    )
    run_threshold_source: Optional[str] = Field(None, description="Source of running threshold")
    
    # Swimming thresholds  
    threshold_pace_100m_s: Optional[float] = Field(
        None, ge=50.0, le=300.0,
        description="CSS (Critical Swim Speed) pace per 100m in seconds"
    )
    swim_threshold_source: Optional[str] = Field(None, description="Source of swim threshold")
    
    # Heart rate thresholds (apply across sports)
    lthr: Optional[int] = Field(None, ge=100, le=220, description="Lactate Threshold Heart Rate (bpm)")
    max_hr: Optional[int] = Field(None, ge=100, le=220, description="Maximum Heart Rate (bpm)")
    resting_hr: Optional[int] = Field(None, ge=30, le=100, description="Resting Heart Rate (bpm)")
    hr_source: Optional[str] = Field(None, description="Source of HR thresholds")
    
    # Metadata
    notes: Optional[str] = Field(None, max_length=500, description="Test notes or methodology")
    is_user_override: bool = Field(
        default=False, 
        description="True if manually entered by user (takes precedence over API imports)"
    )
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @field_validator('sport')
    @classmethod
    def validate_sport(cls, v: str) -> str:
        allowed = ['cycling', 'running', 'swimming']
        if v.lower() not in allowed:
            raise ValueError(f"Sport must be one of {allowed}")
        return v.lower()


class MetricsDaily(BaseModel):
    """Daily aggregated training metrics including recovery markers."""
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    athlete_id: Optional[int] = Field(None, ge=1, description="Foreign key to athlete")
    metric_date: date = Field(..., description="Date of metrics")
    tss: float = Field(..., ge=0, description="Training Stress Score")
    atl: float = Field(..., ge=0, description="Acute Training Load (7-day EWMA)")
    ctl: float = Field(..., ge=0, description="Chronic Training Load (42-day EWMA)")
    tsb: float = Field(..., description="Training Stress Balance (CTL - ATL)")
    rhr: Optional[int] = Field(None, ge=30, le=100, description="Resting Heart Rate (bpm)")
    hrv: Optional[float] = Field(None, ge=0, le=200, description="Heart Rate Variability (ms)")
    sleep_score: Optional[float] = Field(None, ge=0, le=100, description="Sleep quality score (0-100)")
    sleep_duration_min: Optional[int] = Field(None, ge=0, le=1440, description="Sleep duration in minutes")
    rpe: Optional[int] = Field(None, ge=1, le=10, description="Rate of Perceived Exertion (1-10)")
    notes: Optional[str] = Field(None, max_length=2000, description="Athlete notes/feelings")
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")


class WeekPlanRequest(BaseModel):
    """Request model for generating a weekly training plan."""
    start_date: date = Field(..., description="Week start date")
    end_date: date = Field(..., description="Week end date")
    goal_event_date: Optional[date] = Field(None, description="Target event date")
    available_hours_by_day: Dict[str, float] = Field(
        default_factory=dict,
        description="Mapping of weekday name to available hours (e.g., {'Mon':1.0, 'Tue':0.5})",
    )
    preferred_sport_mix: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional mix of sports by proportion, e.g., {'ride':0.5,'run':0.4,'swim':0.1}",
    )
