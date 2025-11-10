#!/usr/bin/env python3
"""Test harness for AutoCoach integration testing.

This script:
1. Connects to TrainingPeaks to fetch athlete thresholds and metrics
2. Parses the sample FIT file 
3. Calculates training metrics (NP, IF, TSS, VI)
4. Displays useful summary information

Usage:
    python test_harness.py --file UploadFiles/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz
    python test_harness.py --tp-sync  # Sync from TrainingPeaks
"""

import argparse
import gzip
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import sys

from dotenv import load_dotenv

from app.clients.trainingpeaks import TrainingPeaksClient, TrainingPeaksAPIError
from app.services.file_parser import parse_fit_file, FileParseError
from app.services.metrics import (
    calculate_normalized_power,
    calculate_intensity_factor,
    calculate_variability_index,
    calculate_tss_from_power,
)
from app.schemas.training import AthleteThreshold, Activity
from app.services.thresholds import get_threshold_for_date, validate_threshold_for_tss_calculation

# Load environment variables
load_dotenv()


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---\n")


def format_seconds(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_pace(meters_per_second: float) -> str:
    """Format pace as min:sec per km."""
    if meters_per_second <= 0:
        return "N/A"
    min_per_km = 1000 / (meters_per_second * 60)
    minutes = int(min_per_km)
    seconds = int((min_per_km - minutes) * 60)
    return f"{minutes}:{seconds:02d} /km"


def test_trainingpeaks_connection() -> Optional[TrainingPeaksClient]:
    """Test TrainingPeaks API connection and fetch athlete data."""
    print_section("TrainingPeaks API Test")
    
    try:
        client = TrainingPeaksClient.from_env(sandbox=True)
        print("✓ TrainingPeaks client initialized")
        print(f"  API Base: {client.api_base}")
        print(f"  OAuth Base: {client.oauth_base}")
        
        # Check if we have tokens
        if not client.oauth_session.token:
            print("\n⚠ No access token found in environment")
            print("  To authenticate:")
            print("  1. Set TRAININGPEAKS_CLIENT_ID and TRAININGPEAKS_CLIENT_SECRET")
            print("  2. Run OAuth flow through /trainingpeaks/authorize endpoint")
            print("  3. Set TRAININGPEAKS_ACCESS_TOKEN and TRAININGPEAKS_REFRESH_TOKEN")
            return None
        
        print("✓ Access token found")
        
        # Try to fetch athlete profile
        print("\nFetching athlete profile...")
        try:
            profile = client.get_athlete_profile()
            print(f"✓ Authenticated as: {profile.get('name', 'Unknown')}")
            print(f"  Athlete ID: {profile.get('id', 'N/A')}")
            print(f"  Email: {profile.get('email', 'N/A')}")
            
            # Try to fetch thresholds
            print("\nFetching athlete thresholds...")
            thresholds = client.get_athlete_thresholds()
            print(f"✓ Thresholds retrieved")
            
            if 'ftp' in thresholds or 'functionalThresholdPower' in thresholds:
                ftp = thresholds.get('ftp') or thresholds.get('functionalThresholdPower')
                print(f"  FTP: {ftp}W")
            
            if 'lactateThresholdHeartRate' in thresholds:
                print(f"  LTHR: {thresholds.get('lactateThresholdHeartRate')} bpm")
            
            if 'thresholdPace' in thresholds:
                print(f"  Threshold Pace: {thresholds.get('thresholdPace')} min/km")
            
            return client
            
        except TrainingPeaksAPIError as e:
            print(f"✗ API Error: {e}")
            return None
        
    except ValueError as e:
        print(f"✗ Configuration Error: {e}")
        print("  Please set TRAININGPEAKS_CLIENT_ID and TRAININGPEAKS_CLIENT_SECRET in .env")
        return None
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        return None


def analyze_fit_file(file_path: str, ftp: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Parse and analyze a FIT file."""
    print_section(f"FIT File Analysis: {Path(file_path).name}")
    
    try:
        # Check if file is gzipped
        path_obj = Path(file_path)
        if not path_obj.exists():
            print(f"✗ File not found: {file_path}")
            return None
        
        print(f"✓ File found: {path_obj}")
        print(f"  Size: {path_obj.stat().st_size / 1024:.1f} KB")
        
        # Parse FIT file
        print("\nParsing FIT file...")
        # Using athlete_id=1 for test harness (would come from user context in production)
        workout, samples = parse_fit_file(file_path, athlete_id=1, ftp=ftp)
        
        print(f"✓ FIT file parsed successfully")
        
        # Display summary info
        print_subsection("Workout Summary")
        print(f"Sport: {workout.sport}")
        print(f"Start Time: {workout.start_time}")
        print(f"Duration: {format_seconds(workout.duration_s)}")
        
        summary_json = workout.summary_json
        if 'distance_m' in summary_json and summary_json['distance_m']:
            print(f"Distance: {summary_json['distance_m'] / 1000:.2f} km")
        
        if 'elevation_m' in summary_json and summary_json['elevation_m']:
            print(f"Elevation Gain: {summary_json['elevation_m']:.0f} m")
        
        # Display sample statistics
        print_subsection("Data Samples")
        print(f"Total Samples: {len(samples)}")
        
        # Power statistics
        power_samples = [s.power_w for s in samples if s.power_w and s.power_w > 0]
        if power_samples:
            print(f"\nPower Data: {len(power_samples)} samples")
            print(f"  Average: {sum(power_samples) / len(power_samples):.0f}W")
            print(f"  Max: {max(power_samples):.0f}W")
            print(f"  Min: {min(power_samples):.0f}W")
            
            # Calculate advanced metrics
            print_subsection("Advanced Power Metrics")
            
            try:
                np_value = calculate_normalized_power(power_samples)
                print(f"Normalized Power (NP): {np_value:.0f}W")
                
                avg_power = sum(power_samples) / len(power_samples)
                vi = calculate_variability_index(np_value, avg_power)
                print(f"Variability Index (VI): {vi:.3f}")
                
                if vi < 1.05:
                    print("  → Very steady effort (time trial / threshold)")
                elif vi < 1.10:
                    print("  → Steady effort (tempo)")
                elif vi < 1.20:
                    print("  → Variable effort (group ride)")
                else:
                    print("  → Very variable effort (criterium / intervals)")
                
                if ftp:
                    intensity_factor = calculate_intensity_factor(np_value, ftp)
                    print(f"\nIntensity Factor (IF): {intensity_factor:.3f}")
                    
                    if intensity_factor < 0.75:
                        print("  → Recovery / Easy")
                    elif intensity_factor < 0.85:
                        print("  → Endurance / Tempo")
                    elif intensity_factor < 0.95:
                        print("  → Threshold / Sweet Spot")
                    elif intensity_factor < 1.05:
                        print("  → FTP / Threshold")
                    else:
                        print("  → VO2max / Anaerobic")
                    
                    tss = calculate_tss_from_power(workout.duration_s, np_value, ftp)
                    print(f"\nTraining Stress Score (TSS): {tss:.0f}")
                    
                    if tss < 150:
                        print("  → Low stress workout")
                    elif tss < 300:
                        print("  → Medium stress workout")
                    elif tss < 450:
                        print("  → High stress workout")
                    else:
                        print("  → Very high stress workout")
                else:
                    print("\n⚠ No FTP provided - cannot calculate IF and TSS")
                    print("  Provide FTP with --ftp flag or sync from TrainingPeaks")
                
            except Exception as e:
                print(f"✗ Error calculating metrics: {e}")
        
        # Heart rate statistics
        hr_samples = [s.hr_bpm for s in samples if s.hr_bpm and s.hr_bpm > 0]
        if hr_samples:
            print_subsection("Heart Rate Data")
            print(f"Samples: {len(hr_samples)}")
            print(f"Average: {sum(hr_samples) / len(hr_samples):.0f} bpm")
            print(f"Max: {max(hr_samples)} bpm")
            print(f"Min: {min(hr_samples)} bpm")
        
        # Cadence statistics
        cadence_samples = [s.cadence for s in samples if s.cadence and s.cadence > 0]
        if cadence_samples:
            print_subsection("Cadence Data")
            print(f"Samples: {len(cadence_samples)}")
            print(f"Average: {sum(cadence_samples) / len(cadence_samples):.0f} rpm")
            print(f"Max: {max(cadence_samples)} rpm")
        
        # Speed/Pace statistics  
        speed_samples = [s.pace_mps for s in samples if s.pace_mps and s.pace_mps > 0]
        if speed_samples:
            print_subsection("Speed/Pace Data")
            avg_speed = sum(speed_samples) / len(speed_samples)
            print(f"Average Speed: {avg_speed * 3.6:.1f} km/h")
            print(f"Average Pace: {format_pace(avg_speed)}")
            print(f"Max Speed: {max(speed_samples) * 3.6:.1f} km/h")
        
        # GPS track info
        gps_samples = [s for s in samples if s.lat and s.lon]
        if gps_samples:
            print_subsection("GPS Data")
            print(f"GPS Samples: {len(gps_samples)}")
            print(f"Start: ({gps_samples[0].lat:.6f}, {gps_samples[0].lon:.6f})")
            print(f"End: ({gps_samples[-1].lat:.6f}, {gps_samples[-1].lon:.6f})")
        
        return {
            'workout': workout,
            'samples': samples,
            'power_samples': power_samples if 'power_samples' in locals() else [],
            'hr_samples': hr_samples if 'hr_samples' in locals() else [],
        }
        
    except FileParseError as e:
        print(f"✗ File Parse Error: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def fetch_tp_threshold_for_date(
    client: TrainingPeaksClient, 
    workout_date: date
) -> Optional[int]:
    """Fetch FTP/threshold from TrainingPeaks for a specific date.
    
    Args:
        client: Authenticated TrainingPeaks client
        workout_date: Date to get thresholds for
        
    Returns:
        FTP value in watts, or None if not available
    """
    print_subsection(f"TrainingPeaks Threshold for {workout_date}")
    
    try:
        # Try to get threshold history for a date range around the workout
        start_date = workout_date - timedelta(days=30)
        end_date = workout_date + timedelta(days=1)
        
        threshold_history = client.get_threshold_history(start_date, end_date)
        
        if threshold_history:
            print(f"✓ Found {len(threshold_history)} threshold records")
            
            # Find the threshold active on workout date
            # (most recent threshold before or on the workout date)
            active_threshold = None
            for threshold in sorted(threshold_history, key=lambda x: x.get('effectiveDate', ''), reverse=True):
                threshold_date_str = threshold.get('effectiveDate', '')
                if threshold_date_str:
                    threshold_date = date.fromisoformat(threshold_date_str.split('T')[0])
                    if threshold_date <= workout_date:
                        active_threshold = threshold
                        break
            
            if active_threshold:
                ftp = active_threshold.get('ftp') or active_threshold.get('functionalThresholdPower')
                if ftp:
                    print(f"✓ Active FTP on {workout_date}: {ftp}W")
                    effective_date = active_threshold.get('effectiveDate', 'Unknown')
                    print(f"  (Set on: {effective_date})")
                    return int(ftp)
        
        # Fallback: Get current thresholds
        print("  No threshold history found, trying current thresholds...")
        thresholds = client.get_athlete_thresholds()
        ftp = thresholds.get('ftp') or thresholds.get('functionalThresholdPower')
        
        if ftp:
            print(f"✓ Current FTP: {ftp}W")
            print("  ⚠ Warning: Using current FTP, may not match workout date")
            return int(ftp)
        
        print("  ✗ No FTP found")
        return None
        
    except TrainingPeaksAPIError as e:
        print(f"  ✗ API Error: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected Error: {e}")
        return None


def fetch_tp_daily_metrics(
    client: TrainingPeaksClient,
    workout_date: date
) -> Optional[Dict[str, Any]]:
    """Fetch daily metrics from TrainingPeaks for a specific date.
    
    Args:
        client: Authenticated TrainingPeaks client
        workout_date: Date to get metrics for
        
    Returns:
        Dictionary of metrics, or None if not available
    """
    print_subsection(f"TrainingPeaks Daily Metrics for {workout_date}")
    
    try:
        metrics = client.get_daily_metrics(workout_date, workout_date)
        
        if metrics and len(metrics) > 0:
            daily = metrics[0]
            print(f"✓ Daily metrics found")
            
            if 'tss' in daily:
                print(f"  TSS: {daily['tss']}")
            if 'hrv' in daily:
                print(f"  HRV: {daily['hrv']}")
            if 'restingHeartRate' in daily or 'rhr' in daily:
                rhr = daily.get('restingHeartRate') or daily.get('rhr')
                print(f"  Resting HR: {rhr} bpm")
            if 'sleepScore' in daily or 'sleepQuality' in daily:
                sleep = daily.get('sleepScore') or daily.get('sleepQuality')
                print(f"  Sleep: {sleep}")
            if 'rpe' in daily or 'perceivedExertion' in daily:
                rpe = daily.get('rpe') or daily.get('perceivedExertion')
                print(f"  RPE: {rpe}")
            
            return daily
        else:
            print("  No daily metrics found for this date")
            return None
            
    except TrainingPeaksAPIError as e:
        print(f"  ✗ API Error: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected Error: {e}")
        return None


def fetch_tp_workout_for_date(
    client: TrainingPeaksClient,
    workout_date: date
) -> Optional[Activity]:
    """Fetch workout from TrainingPeaks for a specific date.
    
    Args:
        client: Authenticated TrainingPeaks client
        workout_date: Date to get workout for
        
    Returns:
        Activity object from TrainingPeaks, or None if not available
    """
    print_subsection(f"TrainingPeaks Workout for {workout_date}")
    
    try:
        activities = client.fetch_activities(workout_date, workout_date)
        
        if activities and len(activities) > 0:
            print(f"✓ Found {len(activities)} workout(s) on {workout_date}")
            
            # Display all workouts found
            for i, activity in enumerate(activities, 1):
                print(f"\nWorkout {i}:")
                print(f"  Sport: {activity.sport}")
                print(f"  Duration: {activity.duration_min:.1f} min")
                if activity.distance_km:
                    print(f"  Distance: {activity.distance_km:.2f} km")
                if activity.tss:
                    print(f"  TSS: {activity.tss:.0f}")
                if activity.power_avg:
                    print(f"  Avg Power: {activity.power_avg:.0f}W")
                if activity.hr_avg:
                    print(f"  Avg HR: {activity.hr_avg:.0f} bpm")
                if activity.intensity_factor:
                    print(f"  IF: {activity.intensity_factor:.3f}")
            
            # Return first activity (most likely match)
            return activities[0]
        else:
            print("  No workouts found for this date")
            return None
            
    except TrainingPeaksAPIError as e:
        print(f"  ✗ API Error: {e}")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected Error: {e}")
        return None


def compare_workouts(
    local_data: Dict[str, Any],
    tp_activity: Optional[Activity],
    tp_ftp: Optional[int]
) -> None:
    """Compare local FIT file data with TrainingPeaks data.
    
    Args:
        local_data: Dictionary containing parsed FIT file data
        tp_activity: Activity from TrainingPeaks (if available)
        tp_ftp: FTP from TrainingPeaks (if available)
    """
    print_section("Comparison: Local FIT File vs TrainingPeaks")
    
    if not tp_activity:
        print("⚠ No TrainingPeaks workout data available for comparison")
        print("  Only showing local FIT file data")
        return
    
    workout = local_data['workout']
    power_samples = local_data.get('power_samples', [])
    
    print_subsection("Duration")
    local_duration_min = workout.duration_s / 60
    print(f"Local FIT:      {local_duration_min:.1f} min")
    print(f"TrainingPeaks:  {tp_activity.duration_min:.1f} min")
    diff = abs(local_duration_min - tp_activity.duration_min)
    if diff < 1:
        print(f"✓ Match (diff: {diff:.2f} min)")
    else:
        print(f"⚠ Difference: {diff:.1f} min")
    
    # Compare power metrics if available
    if power_samples and tp_activity.power_avg:
        print_subsection("Average Power")
        local_avg = sum(power_samples) / len(power_samples)
        print(f"Local FIT:      {local_avg:.0f}W")
        print(f"TrainingPeaks:  {tp_activity.power_avg:.0f}W")
        diff_pct = abs(local_avg - tp_activity.power_avg) / tp_activity.power_avg * 100
        if diff_pct < 2:
            print(f"✓ Match (diff: {diff_pct:.1f}%)")
        else:
            print(f"⚠ Difference: {diff_pct:.1f}%")
    
    # Compare TSS if both have FTP
    if power_samples and tp_ftp:
        print_subsection("Training Stress Score (TSS)")
        
        # Calculate local TSS
        local_np = calculate_normalized_power(power_samples)
        local_tss = calculate_tss_from_power(workout.duration_s, local_np, tp_ftp)
        
        print(f"Local FIT:      {local_tss:.0f}")
        if tp_activity.tss:
            print(f"TrainingPeaks:  {tp_activity.tss:.0f}")
            diff_pct = abs(local_tss - tp_activity.tss) / tp_activity.tss * 100
            if diff_pct < 5:
                print(f"✓ Close match (diff: {diff_pct:.1f}%)")
            else:
                print(f"⚠ Difference: {diff_pct:.1f}%")
        else:
            print("TrainingPeaks:  Not available")
        
        # Compare NP if available
        if tp_activity.normalized_power:
            print_subsection("Normalized Power (NP)")
            print(f"Local FIT:      {local_np:.0f}W")
            print(f"TrainingPeaks:  {tp_activity.normalized_power:.0f}W")
            diff_pct = abs(local_np - tp_activity.normalized_power) / tp_activity.normalized_power * 100
            if diff_pct < 2:
                print(f"✓ Match (diff: {diff_pct:.1f}%)")
            else:
                print(f"⚠ Difference: {diff_pct:.1f}%")
    
    # Compare distance if available
    local_distance_km = workout.summary_json.get('distance_m', 0) / 1000
    if local_distance_km > 0 and tp_activity.distance_km:
        print_subsection("Distance")
        print(f"Local FIT:      {local_distance_km:.2f} km")
        print(f"TrainingPeaks:  {tp_activity.distance_km:.2f} km")
        diff_pct = abs(local_distance_km - tp_activity.distance_km) / tp_activity.distance_km * 100
        if diff_pct < 1:
            print(f"✓ Match (diff: {diff_pct:.2f}%)")
        else:
            print(f"⚠ Difference: {diff_pct:.2f}%")


def main():
    """Main test harness entry point."""
    parser = argparse.ArgumentParser(
        description="AutoCoach Test Harness - Integration Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze sample FIT file with manual FTP
  python test_harness.py --file data/sample_workouts/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz --ftp 250
  
  # Test TrainingPeaks connection
  python test_harness.py --tp-test
  
  # Full integration test: Compare FIT file with TrainingPeaks data
  python test_harness.py --file data/sample_workouts/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz --tp-compare
        """
    )
    
    parser.add_argument(
        '--file', 
        type=str,
        help='Path to FIT/TCX/GPX file to analyze'
    )
    parser.add_argument(
        '--ftp',
        type=int,
        help='Manual FTP value for TSS calculation (overrides TrainingPeaks)'
    )
    parser.add_argument(
        '--tp-test',
        action='store_true',
        help='Test TrainingPeaks API connection'
    )
    parser.add_argument(
        '--tp-sync',
        action='store_true',
        help='Sync thresholds from TrainingPeaks (current)'
    )
    parser.add_argument(
        '--tp-compare',
        action='store_true',
        help='Compare FIT file with TrainingPeaks data (fetches FTP, metrics, and workout for the date)'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    print_section("AutoCoach Test Harness")
    print("Integration testing tool for TrainingPeaks, file parsing, and metrics")
    
    tp_client = None
    ftp_from_tp = None
    tp_activity = None
    tp_metrics = None
    
    # Test TrainingPeaks connection if requested
    if args.tp_test or args.tp_sync or args.tp_compare:
        tp_client = test_trainingpeaks_connection()
        
        if tp_client and args.tp_sync:
            try:
                thresholds = tp_client.get_athlete_thresholds()
                ftp_from_tp = thresholds.get('ftp') or thresholds.get('functionalThresholdPower')
                if ftp_from_tp:
                    print(f"\n✓ FTP from TrainingPeaks: {ftp_from_tp}W")
            except Exception as e:
                print(f"\n⚠ Could not fetch FTP from TrainingPeaks: {e}")
    
    # Analyze FIT file if provided
    local_data = None
    if args.file:
        # Determine which FTP to use for initial analysis
        ftp_to_use = args.ftp or ftp_from_tp
        local_data = analyze_fit_file(args.file, ftp=ftp_to_use)
        
        # If tp-compare is requested, fetch TrainingPeaks data for comparison
        if args.tp_compare and local_data and tp_client:
            print_section("TrainingPeaks Data Fetch")
            
            # Extract workout date from parsed FIT file
            workout = local_data['workout']
            workout_date = workout.start_time.date()
            
            print(f"Fetching TrainingPeaks data for workout on {workout_date}...")
            
            # Fetch FTP for the workout date
            ftp_from_tp = fetch_tp_threshold_for_date(tp_client, workout_date)
            
            # Fetch daily metrics
            tp_metrics = fetch_tp_daily_metrics(tp_client, workout_date)
            
            # Fetch workout from TrainingPeaks
            tp_activity = fetch_tp_workout_for_date(tp_client, workout_date)
            
            # Compare the data
            if ftp_from_tp or tp_activity:
                compare_workouts(local_data, tp_activity, ftp_from_tp)
            else:
                print_section("Comparison")
                print("⚠ Not enough TrainingPeaks data available for comparison")
                print("  Either FTP or workout data is required")
        
        if local_data and not args.tp_compare:
            print_section("Analysis Complete")
            print("✓ FIT file analysis completed successfully")
            if not ftp_to_use:
                print("\n💡 Tip: Use --tp-compare to fetch FTP and compare with TrainingPeaks data")
    
    print("\n")


if __name__ == "__main__":
    main()

