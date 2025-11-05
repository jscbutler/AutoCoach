from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

import numpy as np
import pandas as pd

from app.schemas.training import Activity, MetricsDaily


@dataclass
class LoadConstants:
    atl_tau_days: float = 7.0
    ctl_tau_days: float = 42.0


def calculate_normalized_power(power_samples: List[float], sample_rate_hz: int = 1) -> float:
    """
    Calculate Normalized Power (NP) for cycling power data.
    
    NP is the 4th-power mean of 30-second rolling average power, designed to
    represent the physiological "cost" of a variable-power effort.
    
    Formula:
        1. Calculate 30-second rolling average of power
        2. Raise each value to the 4th power
        3. Take the mean of those values
        4. Take the 4th root of the mean
    
    Args:
        power_samples: List of power values in watts (time-ordered)
        sample_rate_hz: Sample rate in Hz (default 1 = 1 sample/second)
        
    Returns:
        Normalized power in watts
        
    Raises:
        ValueError: If power_samples is empty or sample_rate_hz <= 0
        
    Reference:
        Allen, H., & Coggan, A. (2010). Training and Racing with a Power Meter.
    
    Examples:
        >>> # Steady power should have NP ≈ average power
        >>> steady_power = [250] * 3600
        >>> np = calculate_normalized_power(steady_power)
        >>> assert 249 < np < 251
        
        >>> # Variable power should have NP > average power
        >>> variable_power = [200, 300] * 1800
        >>> np = calculate_normalized_power(variable_power)
        >>> assert np > 250  # Higher than average of 250W
    """
    if not power_samples:
        raise ValueError("power_samples cannot be empty")
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    
    # Convert to pandas Series for efficient rolling calculations
    power_series = pd.Series(power_samples, dtype=float)
    
    # Handle edge case: very short workout
    if len(power_samples) < 30 * sample_rate_hz:
        # For workouts < 30 seconds, just use average power
        return float(power_series.mean())
    
    # Calculate 30-second rolling average
    window_size = 30 * sample_rate_hz
    rolling_avg = power_series.rolling(window=window_size, min_periods=1).mean()
    
    # Raise to 4th power
    powered = rolling_avg ** 4
    
    # Take mean and 4th root
    np_value = powered.mean() ** 0.25
    
    return float(np_value)


def calculate_intensity_factor(np: float, ftp: int) -> float:
    """
    Calculate Intensity Factor (IF) for a workout.
    
    IF represents the relative intensity of a workout compared to an athlete's
    Functional Threshold Power (FTP).
    
    Formula:
        IF = Normalized Power / FTP
    
    Args:
        np: Normalized Power in watts
        ftp: Functional Threshold Power in watts
        
    Returns:
        Intensity Factor (dimensionless, typically 0.5-1.2)
        
    Raises:
        ValueError: If FTP is <= 0
        
    Examples:
        >>> calculate_intensity_factor(np=250, ftp=300)
        0.833...  # Recovery/endurance ride
        
        >>> calculate_intensity_factor(np=300, ftp=300)
        1.0  # Threshold effort
        
        >>> calculate_intensity_factor(np=330, ftp=300)
        1.1  # VO2max intervals
    """
    if ftp <= 0:
        raise ValueError("FTP must be positive")
    
    return np / ftp


def calculate_variability_index(np: float, avg_power: float) -> float:
    """
    Calculate Variability Index (VI) for a workout.
    
    VI indicates how variable the power output was during a ride.
    Lower VI = more steady pacing (good for TTs, long rides)
    Higher VI = more variable (typical for intervals, races)
    
    Formula:
        VI = Normalized Power / Average Power
    
    Args:
        np: Normalized Power in watts
        avg_power: Average power in watts
        
    Returns:
        Variability Index (dimensionless, typically 1.00-1.15)
        - 1.00-1.05: Very steady (TT, tempo)
        - 1.05-1.10: Moderate variability (endurance with surges)
        - 1.10+: High variability (intervals, criteriums)
        
    Examples:
        >>> calculate_variability_index(np=250, avg_power=250)
        1.0  # Perfectly steady
        
        >>> calculate_variability_index(np=265, avg_power=250)
        1.06  # Moderate variability
    """
    if avg_power <= 0:
        return 0.0
    
    return np / avg_power


def calculate_tss_from_power(duration_s: int, np: float, ftp: int) -> float:
    """
    Calculate Training Stress Score (TSS) from power data.
    
    TSS quantifies the training load of a workout, accounting for both
    duration and intensity.
    
    Formula:
        TSS = (duration_s × NP × IF) / (FTP × 3600) × 100
        where IF = NP / FTP
    
    Simplified:
        TSS = (duration_s × NP²) / (FTP² × 36)
    
    Args:
        duration_s: Workout duration in seconds
        np: Normalized Power in watts
        ftp: Functional Threshold Power in watts
        
    Returns:
        Training Stress Score (dimensionless)
        - < 150: Easy recovery to moderate
        - 150-300: Challenging workout
        - > 300: Very hard/epic workout
        
    Raises:
        ValueError: If ftp <= 0 or duration_s < 0
        
    Examples:
        >>> # 1 hour at FTP = 100 TSS
        >>> calculate_tss_from_power(duration_s=3600, np=300, ftp=300)
        100.0
        
        >>> # 1 hour at 85% FTP ≈ 72 TSS
        >>> calculate_tss_from_power(duration_s=3600, np=255, ftp=300)
        72.25
    """
    if ftp <= 0:
        raise ValueError("FTP must be positive")
    if duration_s < 0:
        raise ValueError("duration_s cannot be negative")
    
    intensity_factor = np / ftp
    tss = (duration_s * np * intensity_factor) / (ftp * 3600) * 100
    
    return float(tss)


def activities_to_dataframe(activities: List[Activity]) -> pd.DataFrame:
    if not activities:
        return pd.DataFrame(columns=["date", "tss"]).astype({"date": "datetime64[ns]", "tss": "float64"})

    frame = pd.DataFrame([a.model_dump() for a in activities])
    frame["date"] = pd.to_datetime(frame["activity_date"])  # normalize

    if "tss" not in frame.columns:
        frame["tss"] = pd.NA

    # Fill missing TSS conservatively using simple proxies if duration and intensity are available
    # This is a placeholder; later we can add sport-specific load models
    frame["tss"] = frame["tss"].astype("float64")
    if "duration_min" in frame.columns:
        duration_factor = frame["duration_min"].fillna(0.0) / 60.0
        if "intensity_factor" in frame.columns:
            intensity_factor = frame["intensity_factor"].astype("float64").fillna(0.7)
        else:
            intensity_factor = pd.Series([0.7] * len(frame), dtype="float64")
        frame["tss"] = frame["tss"].fillna(100.0 * duration_factor * intensity_factor)

    # Consolidate to daily TSS in case of multiple workouts per day
    daily = (
        frame.groupby(frame["date"].dt.date)["tss"].sum().rename_axis("date").reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])  # ensure datetime index compatibility
    return daily


def compute_chronic_and_acute_loads(
    daily_tss: pd.DataFrame,
    constants: LoadConstants | None = None,
) -> pd.DataFrame:
    if constants is None:
        constants = LoadConstants()

    if daily_tss.empty:
        return pd.DataFrame(columns=["date", "tss", "atl", "ctl", "tsb"]).astype(
            {"date": "datetime64[ns]", "tss": "float64", "atl": "float64", "ctl": "float64", "tsb": "float64"}
        )

    df = daily_tss.copy()
    df = df.sort_values("date")

    # Ensure continuous daily index to avoid gaps skewing EWMs
    full_index = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
    df = df.set_index("date").reindex(full_index).fillna({"tss": 0.0})

    # EWM with alpha = 1/tau (Banister model)
    atl_alpha = 1.0 / constants.atl_tau_days
    ctl_alpha = 1.0 / constants.ctl_tau_days

    df["atl"] = df["tss"].ewm(alpha=atl_alpha, adjust=False).mean()
    df["ctl"] = df["tss"].ewm(alpha=ctl_alpha, adjust=False).mean()
    df["tsb"] = df["ctl"] - df["atl"]

    df = df.reset_index().rename(columns={"index": "date"})
    return df[["date", "tss", "atl", "ctl", "tsb"]]


def compute_metrics_daily(activities: List[Activity]) -> List[MetricsDaily]:
    daily = activities_to_dataframe(activities)
    metrics_df = compute_chronic_and_acute_loads(daily)
    results: List[MetricsDaily] = []
    for row in metrics_df.itertuples(index=False):
        results.append(
            MetricsDaily(
                metric_date=row.date.date() if isinstance(row.date, pd.Timestamp) else row.date,
                tss=float(row.tss),
                atl=float(row.atl),
                ctl=float(row.ctl),
                tsb=float(row.tsb),
            )
        )
    return results
