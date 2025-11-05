"""
FIT/TCX/GPX file parsing service for workout data extraction.

This module handles parsing of workout files from various sources:
- FIT files (Garmin, Wahoo, most modern devices) - supports .fit and .fit.gz
- TCX files (TrainingPeaks, older Garmin)
- GPX files (basic GPS tracking)
"""
from __future__ import annotations

import gzip
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from fitparse import FitFile

from app.schemas.training import WorkoutExecuted, Sample
from app.services.metrics import (
    calculate_normalized_power,
    calculate_intensity_factor,
    calculate_variability_index,
    calculate_tss_from_power,
)


class FileParseError(Exception):
    """Raised when file parsing fails."""
    pass


def parse_fit_file(
    file_path: str,
    athlete_id: int,
    ftp: Optional[int] = None
) -> Tuple[WorkoutExecuted, List[Sample]]:
    """
    Parse a FIT file and extract workout data and per-second samples.
    
    Automatically handles both .fit and .fit.gz (gzipped) files.
    
    Args:
        file_path: Path to the .fit or .fit.gz file
        athlete_id: ID of the athlete who performed the workout
        ftp: Functional Threshold Power (optional, for TSS calculation)
        
    Returns:
        Tuple of (WorkoutExecuted, List[Sample])
        
    Raises:
        FileParseError: If file cannot be parsed
        FileNotFoundError: If file doesn't exist
        
    Example:
        >>> # Works with both compressed and uncompressed files
        >>> workout, samples = parse_fit_file("ride.fit", athlete_id=1, ftp=300)
        >>> workout2, samples2 = parse_fit_file("ride.fit.gz", athlete_id=1, ftp=300)
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Handle gzipped files by decompressing to temp file
    temp_file = None
    try:
        if file_path_obj.suffix == '.gz':
            # Create temporary file for decompressed data
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.fit')
            with gzip.open(str(file_path_obj), 'rb') as f_in:
                with open(temp_file.name, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            fit_file_path = temp_file.name
        else:
            fit_file_path = str(file_path_obj)
        
        # Parse the FIT file
        fitfile = FitFile(fit_file_path)
    except gzip.BadGzipFile:
        raise FileParseError("File appears to be corrupted or not a valid gzip file")
    except Exception as e:
        raise FileParseError(f"Failed to open FIT file: {str(e)}")
    finally:
        # Clean up temp file if created
        if temp_file:
            try:
                Path(temp_file.name).unlink()
            except Exception:
                pass  # Ignore cleanup errors
    
    # Extract session-level data (summary)
    session_data = _extract_session_data(fitfile)
    
    # Extract per-record samples (power, HR, cadence, GPS, etc.)
    samples = _extract_samples(fitfile)
    
    if not samples:
        raise FileParseError("No workout data found in FIT file")
    
    # Calculate summary metrics
    duration_s = samples[-1].t_s if samples else 0
    summary_json = _calculate_summary_metrics(samples, session_data, ftp)
    
    # Determine sport type
    sport = session_data.get('sport', 'unknown').lower()
    if sport == 'bike' or sport == 'cycling':
        sport = 'cycling'
    elif sport == 'run' or sport == 'running':
        sport = 'running'
    elif sport == 'swim' or sport == 'swimming':
        sport = 'swimming'
    
    # Create WorkoutExecuted object
    workout = WorkoutExecuted(
        athlete_id=athlete_id,
        source='file',
        start_time=session_data.get('start_time', datetime.now()),
        duration_s=duration_s,
        sport=sport,
        file_ref=str(file_path_obj),
        summary_json=summary_json,
    )
    
    return workout, samples


def _extract_session_data(fitfile: FitFile) -> Dict:
    """Extract session-level summary data from FIT file."""
    session_data = {}
    
    for record in fitfile.get_messages('session'):
        for field in record:
            if field.name == 'start_time':
                session_data['start_time'] = field.value
            elif field.name == 'total_elapsed_time':
                session_data['total_elapsed_time'] = field.value
            elif field.name == 'sport':
                session_data['sport'] = field.value
            elif field.name == 'total_distance':
                session_data['total_distance_m'] = field.value
            elif field.name == 'total_ascent':
                session_data['total_ascent_m'] = field.value
            elif field.name == 'avg_heart_rate':
                session_data['avg_hr'] = field.value
            elif field.name == 'max_heart_rate':
                session_data['max_hr'] = field.value
            elif field.name == 'avg_power':
                session_data['avg_power'] = field.value
            elif field.name == 'max_power':
                session_data['max_power'] = field.value
            elif field.name == 'avg_cadence':
                session_data['avg_cadence'] = field.value
            elif field.name == 'normalized_power':
                session_data['normalized_power'] = field.value
            elif field.name == 'training_stress_score':
                session_data['tss'] = field.value
    
    return session_data


def _extract_samples(fitfile: FitFile) -> List[Sample]:
    """Extract per-second samples from FIT file."""
    samples = []
    start_time = None
    
    for record in fitfile.get_messages('record'):
        # Build sample from record fields
        sample_data = {'t_s': 0}
        timestamp = None
        
        for field in record:
            if field.name == 'timestamp':
                timestamp = field.value
                if start_time is None:
                    start_time = timestamp
                sample_data['t_s'] = int((timestamp - start_time).total_seconds())
            elif field.name == 'power' and field.value is not None:
                sample_data['power_w'] = int(field.value)
            elif field.name == 'heart_rate' and field.value is not None:
                sample_data['hr_bpm'] = int(field.value)
            elif field.name == 'cadence' and field.value is not None:
                sample_data['cadence'] = int(field.value)
            elif field.name == 'speed' and field.value is not None:
                sample_data['pace_mps'] = float(field.value)
            elif field.name == 'altitude' and field.value is not None:
                sample_data['altitude_m'] = float(field.value)
            elif field.name == 'position_lat' and field.value is not None:
                # Convert from semicircles to degrees
                sample_data['lat'] = float(field.value) * (180 / 2**31)
            elif field.name == 'position_long' and field.value is not None:
                # Convert from semicircles to degrees
                sample_data['lon'] = float(field.value) * (180 / 2**31)
            elif field.name == 'temperature' and field.value is not None:
                sample_data['temperature_c'] = float(field.value)
            elif field.name == 'distance' and field.value is not None:
                sample_data['distance_m'] = float(field.value)
        
        # Only add sample if we have a timestamp
        if timestamp is not None:
            # workout_id will be set when saving to database (use 1 as placeholder for validation)
            sample_data['workout_id'] = 1  # Placeholder - will be updated on DB insert
            samples.append(Sample(**sample_data))
    
    return samples


def _calculate_summary_metrics(
    samples: List[Sample],
    session_data: Dict,
    ftp: Optional[int] = None
) -> Dict:
    """Calculate summary metrics from samples and session data."""
    summary = {}
    
    # Extract power samples
    power_samples = [s.power_w for s in samples if s.power_w is not None]
    hr_samples = [s.hr_bpm for s in samples if s.hr_bpm is not None]
    
    # Basic metrics
    if power_samples:
        summary['avg_power'] = sum(power_samples) / len(power_samples)
        summary['max_power'] = max(power_samples)
        
        # Calculate NP, IF, VI
        try:
            np = calculate_normalized_power(power_samples)
            summary['np'] = np
            
            avg_power = summary['avg_power']
            vi = calculate_variability_index(np, avg_power)
            summary['vi'] = vi
            
            if ftp and ftp > 0:
                if_value = calculate_intensity_factor(np, ftp)
                summary['if'] = if_value
                
                duration_s = samples[-1].t_s
                tss = calculate_tss_from_power(duration_s, np, ftp)
                summary['tss'] = tss
        except Exception as e:
            # Log error but don't fail the parse
            summary['power_calc_error'] = str(e)
    
    if hr_samples:
        summary['avg_hr'] = sum(hr_samples) / len(hr_samples)
        summary['max_hr'] = max(hr_samples)
    
    # Add session-level data if available
    if 'total_distance_m' in session_data:
        summary['distance_m'] = session_data['total_distance_m']
    
    if 'total_ascent_m' in session_data:
        summary['elevation_m'] = session_data['total_ascent_m']
    
    # Use device-calculated NP/TSS if our calculations failed
    if 'np' not in summary and 'normalized_power' in session_data:
        summary['np'] = session_data['normalized_power']
    
    if 'tss' not in summary and 'tss' in session_data:
        summary['tss'] = session_data['tss']
    
    return summary


def get_file_type(filename: str) -> str:
    """
    Determine file type from filename extension.
    
    Args:
        filename: Name or path of the file
        
    Returns:
        File type: 'fit', 'tcx', 'gpx', or 'unknown'
    """
    extension = Path(filename).suffix.lower()
    
    if extension == '.fit':
        return 'fit'
    elif extension == '.tcx':
        return 'tcx'
    elif extension == '.gpx':
        return 'gpx'
    else:
        return 'unknown'


def validate_file_type(filename: str) -> bool:
    """
    Check if file type is supported.
    
    Args:
        filename: Name or path of the file
        
    Returns:
        True if supported, False otherwise
    """
    file_type = get_file_type(filename)
    return file_type in ['fit', 'tcx', 'gpx']

