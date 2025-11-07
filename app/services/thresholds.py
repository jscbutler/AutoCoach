"""Threshold management service for date-versioned athlete thresholds.

Provides lookup functions to get the correct threshold values for any workout date,
supporting both TrainingPeaks import and user overrides.
"""

from datetime import date
from typing import Optional, List
import pandas as pd

from app.schemas.training import AthleteThreshold


class ThresholdNotFoundError(Exception):
    """Raised when no threshold is found for the requested date."""
    pass


def get_threshold_for_date(
    athlete_id: int,
    sport: str,
    workout_date: date,
    thresholds: List[AthleteThreshold],
    prefer_user_override: bool = True
) -> Optional[AthleteThreshold]:
    """Get the threshold that was active on a specific workout date.
    
    Lookback logic: Find the most recent threshold with effective_date <= workout_date.
    User overrides take precedence over TrainingPeaks imports.
    
    Args:
        athlete_id: Athlete ID
        sport: Sport type (cycling, running, swimming)
        workout_date: Date of the workout being analyzed
        thresholds: List of all thresholds for this athlete/sport
        prefer_user_override: If True, user_override thresholds take precedence
        
    Returns:
        The applicable AthleteThreshold, or None if not found
        
    Example:
        >>> thresholds = [
        ...     AthleteThreshold(athlete_id=1, sport='cycling', effective_date=date(2024, 1, 1), ftp=250),
        ...     AthleteThreshold(athlete_id=1, sport='cycling', effective_date=date(2024, 6, 1), ftp=270),
        ... ]
        >>> get_threshold_for_date(1, 'cycling', date(2024, 7, 15), thresholds)
        AthleteThreshold(ftp=270, effective_date=date(2024, 6, 1))  # Most recent before workout
    """
    if not thresholds:
        return None
    
    # Filter to matching athlete and sport
    filtered = [
        t for t in thresholds 
        if t.athlete_id == athlete_id 
        and t.sport.lower() == sport.lower()
        and t.effective_date <= workout_date
    ]
    
    if not filtered:
        return None
    
    # Sort by effective_date descending (most recent first)
    filtered.sort(key=lambda t: t.effective_date, reverse=True)
    
    # Prefer user overrides if requested
    if prefer_user_override:
        user_overrides = [t for t in filtered if t.is_user_override]
        if user_overrides:
            return user_overrides[0]  # Most recent user override
    
    # Return most recent threshold
    return filtered[0]


def get_threshold_history_df(
    athlete_id: int,
    sport: str,
    thresholds: List[AthleteThreshold]
) -> pd.DataFrame:
    """Convert threshold history to a pandas DataFrame for analysis.
    
    Useful for plotting threshold progression over time or detecting
    training adaptations.
    
    Args:
        athlete_id: Athlete ID
        sport: Sport type
        thresholds: List of thresholds
        
    Returns:
        DataFrame with columns: effective_date, ftp/threshold_pace, source, is_user_override
    """
    filtered = [
        t for t in thresholds 
        if t.athlete_id == athlete_id 
        and t.sport.lower() == sport.lower()
    ]
    
    if not filtered:
        return pd.DataFrame()
    
    # Extract relevant fields based on sport
    records = []
    for t in filtered:
        record = {
            'effective_date': t.effective_date,
            'is_user_override': t.is_user_override,
            'lthr': t.lthr,
            'max_hr': t.max_hr,
            'resting_hr': t.resting_hr,
        }
        
        if sport.lower() == 'cycling':
            record['ftp'] = t.ftp
            record['source'] = t.ftp_source
        elif sport.lower() == 'running':
            record['threshold_pace_min_per_km'] = t.threshold_pace_min_per_km
            record['critical_speed_m_per_s'] = t.critical_speed_m_per_s
            record['source'] = t.run_threshold_source
        elif sport.lower() == 'swimming':
            record['threshold_pace_100m_s'] = t.threshold_pace_100m_s
            record['source'] = t.swim_threshold_source
        
        records.append(record)
    
    df = pd.DataFrame(records)
    df = df.sort_values('effective_date')
    return df


def calculate_ftp_progression(
    athlete_id: int,
    thresholds: List[AthleteThreshold],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> pd.DataFrame:
    """Calculate FTP progression metrics for analysis.
    
    Returns DataFrame with:
    - effective_date
    - ftp
    - ftp_change_watts (vs previous)
    - ftp_change_pct (vs previous)
    - days_since_last_test
    
    Args:
        athlete_id: Athlete ID
        thresholds: List of thresholds
        start_date: Optional filter start
        end_date: Optional filter end
        
    Returns:
        DataFrame with progression analysis
    """
    df = get_threshold_history_df(athlete_id, 'cycling', thresholds)
    
    if df.empty or 'ftp' not in df.columns:
        return pd.DataFrame()
    
    # Apply date filters
    if start_date:
        df = df[df['effective_date'] >= start_date]
    if end_date:
        df = df[df['effective_date'] <= end_date]
    
    # Calculate changes
    df = df.sort_values('effective_date').reset_index(drop=True)
    df['ftp_change_watts'] = df['ftp'].diff()
    df['ftp_change_pct'] = (df['ftp'].pct_change() * 100).round(1)
    df['days_since_last_test'] = df['effective_date'].diff().dt.days
    
    return df


def validate_threshold_for_tss_calculation(
    threshold: Optional[AthleteThreshold],
    sport: str,
    workout_date: date
) -> None:
    """Validate that a threshold is suitable for TSS calculation.
    
    Raises ThresholdNotFoundError with helpful message if invalid.
    
    Args:
        threshold: The threshold to validate (or None)
        sport: Sport type
        workout_date: Date of workout
        
    Raises:
        ThresholdNotFoundError: If threshold is missing or invalid
    """
    if threshold is None:
        raise ThresholdNotFoundError(
            f"No {sport} threshold found for workout on {workout_date}. "
            f"Please set athlete thresholds before this date or use manual override."
        )
    
    # Check sport-specific requirements
    if sport.lower() == 'cycling':
        if not threshold.ftp or threshold.ftp <= 0:
            raise ThresholdNotFoundError(
                f"Cycling threshold on {threshold.effective_date} has invalid FTP: {threshold.ftp}"
            )
    elif sport.lower() == 'running':
        if not threshold.threshold_pace_min_per_km or threshold.threshold_pace_min_per_km <= 0:
            raise ThresholdNotFoundError(
                f"Running threshold on {threshold.effective_date} has invalid threshold pace"
            )
    elif sport.lower() == 'swimming':
        if not threshold.threshold_pace_100m_s or threshold.threshold_pace_100m_s <= 0:
            raise ThresholdNotFoundError(
                f"Swimming threshold on {threshold.effective_date} has invalid CSS"
            )


# Database query helpers (to be implemented with SQLAlchemy later)
# These are placeholders for when we set up the database

async def db_get_athlete_thresholds(
    athlete_id: int,
    sport: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[AthleteThreshold]:
    """Query thresholds from database (placeholder for DB implementation).
    
    Args:
        athlete_id: Athlete ID
        sport: Optional sport filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of matching AthleteThreshold objects
    """
    # TODO: Implement with SQLAlchemy once database is set up
    # Query: SELECT * FROM athlete_thresholds WHERE athlete_id=? AND ...
    raise NotImplementedError("Database queries not yet implemented")


async def db_save_threshold(threshold: AthleteThreshold) -> AthleteThreshold:
    """Save or update threshold in database (placeholder).
    
    Args:
        threshold: Threshold to save
        
    Returns:
        Saved threshold with generated ID
    """
    # TODO: Implement with SQLAlchemy
    # INSERT or UPDATE athlete_thresholds
    raise NotImplementedError("Database saves not yet implemented")

