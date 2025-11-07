# Threshold Management System

## Overview

AutoCoach uses **date-versioned athlete thresholds** to ensure accurate TSS calculations and workout compliance scoring for historical data.

## Why Date Versioning?

**Problem:** Athlete thresholds change over time
- FTP increases/decreases every 6-12 weeks
- Running threshold pace improves with training
- HR zones shift with fitness adaptations

**Solution:** Store thresholds with `effective_date`
- When analyzing a workout from 3 months ago, use the FTP from that time
- Track threshold progression to visualize fitness gains
- Support both TrainingPeaks imports and manual user overrides

## Schema: `AthleteThreshold`

```python
AthleteThreshold(
    athlete_id=1,
    effective_date=date(2024, 6, 1),  # When this threshold became active
    sport='cycling',                   # cycling, running, or swimming
    
    # Cycling
    ftp=270,                          # Functional Threshold Power (watts)
    ftp_source='test',                # trainingpeaks, test, estimate, user_override
    
    # Running
    threshold_pace_min_per_km=4.2,    # ~1-hour race pace
    critical_speed_m_per_s=4.0,       # Heavy/severe boundary
    run_threshold_source='test',
    
    # Swimming
    threshold_pace_100m_s=90.0,       # CSS pace per 100m
    swim_threshold_source='estimate',
    
    # Heart Rate (applies across sports)
    lthr=165,                         # Lactate threshold HR
    max_hr=185,
    resting_hr=48,
    hr_source='test',
    
    # Metadata
    notes='20min FTP test, felt good',
    is_user_override=False,           # True = user entered, takes precedence
)
```

## Database Table

```sql
CREATE TABLE athlete_thresholds (
    id SERIAL PRIMARY KEY,
    athlete_id INTEGER NOT NULL REFERENCES athletes(id),
    effective_date DATE NOT NULL,
    sport VARCHAR(20) NOT NULL CHECK (sport IN ('cycling', 'running', 'swimming')),
    
    -- Cycling
    ftp INTEGER CHECK (ftp >= 0 AND ftp <= 600),
    ftp_source VARCHAR(50),
    
    -- Running
    threshold_pace_min_per_km FLOAT CHECK (threshold_pace_min_per_km >= 2.0 AND threshold_pace_min_per_km <= 10.0),
    critical_speed_m_per_s FLOAT CHECK (critical_speed_m_per_s >= 2.0 AND critical_speed_m_per_s <= 8.0),
    run_threshold_source VARCHAR(50),
    
    -- Swimming
    threshold_pace_100m_s FLOAT CHECK (threshold_pace_100m_s >= 50.0 AND threshold_pace_100m_s <= 300.0),
    swim_threshold_source VARCHAR(50),
    
    -- Heart Rate
    lthr INTEGER CHECK (lthr >= 100 AND lthr <= 220),
    max_hr INTEGER CHECK (max_hr >= 100 AND max_hr <= 220),
    resting_hr INTEGER CHECK (resting_hr >= 30 AND resting_hr <= 100),
    hr_source VARCHAR(50),
    
    -- Metadata
    notes TEXT,
    is_user_override BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure no duplicate effective_dates for same athlete/sport
    UNIQUE(athlete_id, sport, effective_date)
);

CREATE INDEX idx_athlete_thresholds_lookup ON athlete_thresholds(athlete_id, sport, effective_date DESC);
```

## Usage Examples

### 1. Lookup Threshold for a Workout

```python
from app.services.thresholds import get_threshold_for_date

# Calculate TSS for a ride from July 15, 2024
workout_date = date(2024, 7, 15)
thresholds = db_get_athlete_thresholds(athlete_id=1, sport='cycling')

threshold = get_threshold_for_date(
    athlete_id=1,
    sport='cycling',
    workout_date=workout_date,
    thresholds=thresholds
)

if threshold:
    tss = calculate_tss(power_data, ftp=threshold.ftp)
else:
    raise ThresholdNotFoundError("No FTP found for this date")
```

### 2. TrainingPeaks Import

```python
from app.clients.trainingpeaks import TrainingPeaksClient

tp_client = TrainingPeaksClient.from_env()

# Fetch current thresholds from TrainingPeaks
tp_data = tp_client.get_athlete_thresholds()

# Convert to AutoCoach format
thresholds = tp_client.convert_tp_thresholds_to_schema(
    tp_data=tp_data,
    athlete_id=1,
    effective_date=date.today()
)

# Save to database
for threshold in thresholds:
    await db_save_threshold(threshold)
```

### 3. User Override (Manual Entry)

```python
# User completes FTP test and wants to override TrainingPeaks value
new_threshold = AthleteThreshold(
    athlete_id=1,
    effective_date=date(2024, 11, 5),
    sport='cycling',
    ftp=285,  # User tested at 285, TP shows 270
    ftp_source='user_override',
    lthr=168,
    max_hr=186,
    resting_hr=46,
    hr_source='user_override',
    notes='20min test: 285W avg, felt controlled',
    is_user_override=True  # This takes precedence over TP imports
)

await db_save_threshold(new_threshold)
```

### 4. Analyze FTP Progression

```python
from app.services.thresholds import calculate_ftp_progression

thresholds = db_get_athlete_thresholds(athlete_id=1, sport='cycling')

progression_df = calculate_ftp_progression(
    athlete_id=1,
    thresholds=thresholds,
    start_date=date(2024, 1, 1)
)

print(progression_df)
#   effective_date  ftp  ftp_change_watts  ftp_change_pct  days_since_last_test
# 0     2024-01-15  250               NaN             NaN                   NaN
# 1     2024-04-10  265              15.0             6.0                  86.0
# 2     2024-07-20  270               5.0             1.9                 101.0
# 3     2024-11-05  285              15.0             5.6                 108.0
```

## TrainingPeaks API Endpoints (Placeholder)

**Note:** These endpoints are assumed based on typical API patterns. Actual TrainingPeaks API may differ - verify with their documentation.

```python
# Get current thresholds
GET /v1/athlete/thresholds
Response: {
    "ftp": 270,
    "lactateThresholdHeartRate": 165,
    "maximumHeartRate": 185,
    "restingHeartRate": 48,
    "thresholdPace": 4.2,  # min/km
    "unit": "metric"
}

# Get threshold history
GET /v1/athlete/thresholds/history?startDate=2024-01-01&endDate=2024-12-31
Response: [
    {"effectiveDate": "2024-01-15", "ftp": 250, ...},
    {"effectiveDate": "2024-06-01", "ftp": 270, ...}
]
```

## Integration with TSS Calculation

```python
from app.services.metrics import calculate_tss
from app.services.thresholds import get_threshold_for_date, validate_threshold_for_tss_calculation

def calculate_tss_with_threshold_lookup(
    athlete_id: int,
    workout_date: date,
    power_samples: List[float],
    duration_s: int
) -> float:
    """Calculate TSS using date-appropriate FTP."""
    
    # Get thresholds from DB
    thresholds = db_get_athlete_thresholds(athlete_id, sport='cycling')
    
    # Find correct threshold for workout date
    threshold = get_threshold_for_date(
        athlete_id=athlete_id,
        sport='cycling',
        workout_date=workout_date,
        thresholds=thresholds
    )
    
    # Validate
    validate_threshold_for_tss_calculation(threshold, 'cycling', workout_date)
    
    # Calculate TSS
    return calculate_tss(
        power_samples=power_samples,
        duration_s=duration_s,
        ftp=threshold.ftp
    )
```

## Priority Ordering

When multiple thresholds exist for the same date:

1. **User override** (`is_user_override=True`) - highest priority
2. **Test results** (`source='test'`)
3. **TrainingPeaks import** (`source='trainingpeaks'`)
4. **Estimates** (`source='estimate'`) - lowest priority

The `get_threshold_for_date()` function handles this automatically.

## Next Steps

- [ ] Implement database tables and migrations
- [ ] Add API endpoints for threshold CRUD operations
- [ ] Build frontend UI for threshold management
- [ ] Sync with TrainingPeaks on OAuth connection
- [ ] Add threshold validation rules (max_hr > lthr, etc.)
- [ ] Create threshold progression charts

