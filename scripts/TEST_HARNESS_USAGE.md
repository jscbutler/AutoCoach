# Test Harness Usage Guide

## Overview

The AutoCoach test harness is an integration testing tool that can:
1. Parse FIT/TCX/GPX workout files
2. Calculate training metrics (NP, IF, TSS, VI)
3. Connect to TrainingPeaks API
4. Compare local file data with TrainingPeaks data

## Sample Workout

**Location**: `data/sample_workouts/Purple Patch- Nancy & Frank Duet.fit.gz`

**Workout Details**:
- **Date**: February 29, 2024 @ 18:22:51
- **Sport**: Cycling
- **Duration**: 60 minutes
- **Distance**: 34.36 km
- **Power**: 204W average, 228W normalized (NP)
- **TSS**: 83 (with FTP=250W)

## Usage Examples

### 1. Basic FIT File Analysis (No TrainingPeaks)

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach python scripts/test_harness.py \
  --file data/sample_workouts/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz \
  --ftp 250
```

**What it does**:
- Parses the FIT file
- Calculates power metrics (NP, IF, VI)
- Calculates TSS using the provided FTP
- Shows heart rate, cadence, speed/pace statistics

### 2. Test TrainingPeaks Connection

```bash
PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach python scripts/test_harness.py --tp-test
```

**What it does**:
- Tests TrainingPeaks API connection
- Shows athlete profile (if authenticated)
- Displays current thresholds (FTP, LTHR, etc.)

**Requirements**:
- `.env` file with:
  - `TRAININGPEAKS_CLIENT_ID`
  - `TRAININGPEAKS_CLIENT_SECRET`
  - `TRAININGPEAKS_ACCESS_TOKEN` (after OAuth flow)
  - `TRAININGPEAKS_REFRESH_TOKEN` (after OAuth flow)

### 3. Sync Current Thresholds from TrainingPeaks

```bash
PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach python scripts/test_harness.py \
  --file data/sample_workouts/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz \
  --tp-sync
```

**What it does**:
- Fetches current FTP from TrainingPeaks
- Analyzes FIT file using TrainingPeaks FTP
- Calculates TSS with the fetched FTP

### 4. Full TrainingPeaks Comparison (The Big One!)

```bash
PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach python scripts/test_harness.py \
  --file data/sample_workouts/Purple\ Patch-\ Nancy\ \&\ Frank\ Duet.fit.gz \
  --tp-compare
```

**What it does**:
1. Parses the local FIT file
2. Extracts workout date: **2024-02-29**
3. Fetches from TrainingPeaks for that date:
   - **FTP/Threshold** active on Feb 29, 2024 (historical threshold)
   - **Daily Metrics** (HRV, RHR, sleep, RPE)
   - **Workout Data** (TSS, power, duration, etc.)
4. Compares local vs TrainingPeaks:
   - Duration
   - Average Power
   - Normalized Power (NP)
   - Training Stress Score (TSS)
   - Distance
5. Shows differences with visual indicators:
   - ✓ Match (< 2% difference for power, < 1% for distance)
   - ⚠ Difference (shows percentage)

**Expected Output Sections**:
```
================================================================================
  FIT File Analysis
================================================================================
[Shows local file parsing results]

================================================================================
  TrainingPeaks Data Fetch
================================================================================
--- TrainingPeaks Threshold for 2024-02-29 ---
✓ Active FTP on 2024-02-29: 265W
  (Set on: 2024-02-15)

--- TrainingPeaks Daily Metrics for 2024-02-29 ---
✓ Daily metrics found
  TSS: 83
  HRV: 72
  Resting HR: 48 bpm
  Sleep: 85

--- TrainingPeaks Workout for 2024-02-29 ---
✓ Found 1 workout(s) on 2024-02-29
Workout 1:
  Sport: ride
  Duration: 60.0 min
  Distance: 34.36 km
  TSS: 83
  Avg Power: 204W
  IF: 0.914

================================================================================
  Comparison: Local FIT File vs TrainingPeaks
================================================================================
--- Duration ---
Local FIT:      60.0 min
TrainingPeaks:  60.0 min
✓ Match (diff: 0.00 min)

--- Average Power ---
Local FIT:      204W
TrainingPeaks:  204W
✓ Match (diff: 0.0%)

--- Training Stress Score (TSS) ---
Local FIT:      83
TrainingPeaks:  83
✓ Close match (diff: 0.0%)

--- Normalized Power (NP) ---
Local FIT:      228W
TrainingPeaks:  228W
✓ Match (diff: 0.0%)

--- Distance ---
Local FIT:      34.36 km
TrainingPeaks:  34.36 km
✓ Match (diff: 0.00%)
```

## Key Features

### Threshold History
The harness fetches **historical thresholds** from TrainingPeaks, not just current values. This means:
- It finds the FTP that was active on the workout date
- Handles threshold changes over time
- Falls back to current FTP if history unavailable

### Daily Metrics
Fetches recovery markers for context:
- **HRV** (Heart Rate Variability)
- **RHR** (Resting Heart Rate)
- **Sleep Score/Quality**
- **RPE** (Rate of Perceived Exertion)

### Smart Comparison
The comparison logic:
- Handles missing data gracefully
- Shows percentage differences
- Uses appropriate thresholds (2% for power, 5% for TSS, 1% for distance)
- Visual indicators (✓ for match, ⚠ for difference)

## Validation Use Cases

### 1. Verify Parsing Accuracy
Compare local FIT file parsing with TrainingPeaks to ensure:
- Power metrics match (NP, avg power)
- Duration is correct
- Distance is accurate

### 2. Verify TSS Calculations
- Use historical FTP from TrainingPeaks
- Compare local TSS calculation with TrainingPeaks TSS
- Ensure algorithms match

### 3. Threshold Management Testing
- Verify correct threshold is used for a specific date
- Test threshold history retrieval
- Validate threshold change tracking

### 4. Integration Testing
- End-to-end test of TrainingPeaks OAuth
- Test API endpoint calls
- Validate data transformation from TP format to AutoCoach format

## Troubleshooting

### "No module named 'app'"
**Solution**: Always use `PYTHONPATH=/Users/jeffbutler/Dev/AutoCoach` when running the script

### "Not authenticated with TrainingPeaks"
**Solution**: 
1. Set up `.env` file with TrainingPeaks credentials
2. Complete OAuth flow through FastAPI endpoints
3. Add tokens to `.env`:
   ```
   TRAININGPEAKS_ACCESS_TOKEN=your_token_here
   TRAININGPEAKS_REFRESH_TOKEN=your_refresh_token_here
   ```

### "No workouts found for this date"
**Possible causes**:
- Workout wasn't uploaded to TrainingPeaks
- Date mismatch (check timezone)
- Workout uploaded but not yet synced

### Comparison shows large differences
**Investigate**:
- FTP mismatch (check which FTP is being used)
- Sampling rate differences
- Calculation algorithm differences (especially for NP)

## Development Tips

### Adding New Comparison Metrics
Edit `compare_workouts()` in `test_harness.py` to add new comparisons:
```python
# Example: Add HR comparison
if local_data.get('hr_samples') and tp_activity.hr_avg:
    print_subsection("Average Heart Rate")
    local_avg_hr = sum(local_data['hr_samples']) / len(local_data['hr_samples'])
    print(f"Local FIT:      {local_avg_hr:.0f} bpm")
    print(f"TrainingPeaks:  {tp_activity.hr_avg:.0f} bpm")
    # ... comparison logic
```

### Testing Without TrainingPeaks
Always test basic file parsing first:
```bash
python scripts/test_harness.py --file your_file.fit.gz --ftp 250
```

### Automating Comparisons
The test harness can be integrated into CI/CD pipelines:
```bash
# Run comparison and check exit code
PYTHONPATH=. python scripts/test_harness.py --file test.fit.gz --tp-compare
if [ $? -eq 0 ]; then
    echo "✓ Comparison successful"
else
    echo "✗ Comparison failed"
    exit 1
fi
```

## Next Steps

1. **Set up TrainingPeaks OAuth** to enable comparison features
2. **Upload more sample workouts** with known metrics for regression testing
3. **Add threshold history** to database for long-term tracking
4. **Automate comparisons** in test suite for continuous validation

