# AutoCoach - Next Steps Analysis

**Date**: November 3, 2025  
**Status**: Week 1-2 MVP Focus

---

## Current State Summary

### ✅ What's Working

1. **TrainingPeaks OAuth Integration**
   - Basic OAuth2 flow implemented
   - Profile and activities fetching
   - Sandbox/production environment support
   - Converting TP data to canonical Activity format

2. **Core Metrics Engine (Pandas-based)**
   - ✅ TSS aggregation from activities
   - ✅ CTL (42-day EWMA) calculation
   - ✅ ATL (7-day EWMA) calculation  
   - ✅ TSB (CTL - ATL) calculation
   - ✅ Proper handling of missing days (zero-filled time series)
   - ✅ Daily consolidation of multiple workouts

3. **Basic Schemas**
   - Activity model with sport, duration, power, HR, TSS
   - MetricsDaily model (TSS/CTL/ATL/TSB)
   - WeekPlanRequest (planning inputs)

4. **API Endpoints**
   - Health check
   - TrainingPeaks auth + callback
   - Activities fetching with date validation
   - Metrics computation endpoint
   - Manual metrics calculation (POST /metrics/daily)

5. **Testing Foundation**
   - 17/19 tests passing
   - 2 known failures (auth mocking, validation edge case)
   - Test coverage for metrics calculations

---

## ❌ Critical Gaps (Blocks MVP)

### 1. **No File Upload Support** ⚠️ BLOCKER
**Why Critical**: TrainingPeaks API requires approval; athletes can't use the app without file uploads.

**Missing:**
- FIT file parser (Garmin/Wahoo/most devices)
- TCX file parser (TrainingPeaks, older Garmin)
- GPX file parser (basic GPS)
- File upload endpoint (`POST /workouts/upload`)
- Per-second samples extraction and storage

**Required Libraries:**
- `fitparse` for FIT files
- `lxml` for TCX/GPX parsing

**Priority**: **P0** - Start here

---

### 2. **Incomplete Data Model** ⚠️ BLOCKER
**Current**: Only Activity, MetricsDaily, WeekPlanRequest  
**Missing from Canonical Schema:**

```python
# Need to add to app/schemas/training.py:

class Athlete(BaseModel):
    """Athlete profile with thresholds and zones."""
    id: int
    name: str
    sport: str
    ftp: Optional[int] = None  # Cycling functional threshold power
    cp: Optional[int] = None   # Running critical power/pace
    hr_zones: Optional[Dict[str, Tuple[int, int]]] = None
    power_zones: Optional[Dict[str, Tuple[int, int]]] = None
    created_at: datetime

class WorkoutPlanned(BaseModel):
    """Planned workout with structured spec."""
    id: int
    athlete_id: int
    start_time: datetime
    sport: str
    spec_json: Dict  # WorkoutSpec structure
    created_at: datetime

class WorkoutExecuted(BaseModel):
    """Executed workout from file or API."""
    id: int
    athlete_id: int
    source: str  # "file", "trainingpeaks", "strava"
    start_time: datetime
    duration_s: int
    file_ref: Optional[str]  # S3 path or local path
    summary_json: Dict  # TSS, NP, IF, VI, avg power, etc.
    created_at: datetime

class Sample(BaseModel):
    """Per-second workout data."""
    workout_id: int
    t_s: int  # Time offset in seconds
    power_w: Optional[int] = None
    hr_bpm: Optional[int] = None
    pace_mps: Optional[float] = None  # meters per second
    cadence: Optional[int] = None
    altitude_m: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class IntervalDetected(BaseModel):
    """Detected interval from workout execution."""
    id: int
    workout_id: int
    t_start: int  # seconds
    t_end: int    # seconds
    kind: str     # "work", "rest", "warmup", "cooldown"
    targets_json: Optional[Dict] = None  # Matched planned targets
    metrics_json: Dict  # Avg power, NP, time-in-zone, etc.
    created_at: datetime
```

**Priority**: **P0** - Required for file processing

---

### 3. **No Database** ⚠️ BLOCKER
**Current**: All data is in-memory (lost on restart)  
**Needed**: PostgreSQL + TimescaleDB

**Setup Tasks:**
- Install PostgreSQL locally or use Docker
- Install TimescaleDB extension
- Create database schema (see Data Model below)
- Add SQLAlchemy or asyncpg for async DB access
- Create hypertable for `samples` table (time-series optimization)

**Priority**: **P0** - Can start with SQLite for dev, but need Postgres for production

---

### 4. **Missing NP/IF Calculations** 🔴 HIGH
**Current**: Only TSS/CTL/ATL/TSB  
**Need**: Normalized Power (NP) and Intensity Factor (IF) for cycling

**Formulas:**
```python
def calculate_normalized_power(power_samples: List[float], sample_rate_hz: int = 1) -> float:
    """
    NP = 4th root of (mean of (30s rolling avg power)^4)
    
    This represents the physiological "cost" of variable power efforts.
    """
    # 1. Calculate 30-second rolling average
    window_size = 30 * sample_rate_hz
    rolling_avg = pd.Series(power_samples).rolling(window=window_size).mean()
    
    # 2. Raise to 4th power
    powered = rolling_avg ** 4
    
    # 3. Mean and 4th root
    np_value = powered.mean() ** 0.25
    return np_value

def calculate_intensity_factor(np: float, ftp: int) -> float:
    """IF = Normalized Power / FTP"""
    if ftp <= 0:
        raise ValueError("FTP must be positive")
    return np / ftp

def calculate_variability_index(np: float, avg_power: float) -> float:
    """VI = NP / Average Power (should be 1.0-1.05 for steady efforts)"""
    if avg_power <= 0:
        return 0.0
    return np / avg_power
```

**Priority**: **P1** - Needed for proper TSS calculation from power files

---

### 5. **No Interval Detection** 🔴 HIGH
**Why Needed**: Core feature for compliance scoring

**Algorithm** (from AutocoachOverview.md):
1. Smooth power/pace with 5-10s rolling average
2. Use PELT change-point detection (ruptures library)
3. Enforce minimum duration (e.g., 30s)
4. Merge similar adjacent segments
5. Label work vs rest based on intensity vs FTP/zones
6. Match to planned workout steps by time overlap

**Required Library:**
```bash
pip install ruptures
```

**Priority**: **P1** - Week 4 in 6-week plan, but foundational

---

### 6. **No Compliance Scoring** 🔴 HIGH
**Current**: No pass/fail logic for workouts

**Need to Implement** (per .cursorrules):
- Time-in-zone % calculation
- Target hit % (duration within power/HR band)
- Step pass: ≥80% duration in target AND mean within ±3-5%
- Rest pass: ≤60% of cap for ≥80% of rest
- Session pass: ≥70% of steps pass
- Pa:Hr decoupling for endurance blocks

**Priority**: **P1** - Week 3 in plan

---

### 7. **No WorkoutSpec Parser** 🟡 MEDIUM
**Current**: No structured workout representation

**Need**: 
- JSON schema for workout structure (intervals, targets, repeats)
- LLM integration to parse text → WorkoutSpec (OpenAI/Anthropic API)
- **Rule**: LLM ONLY for parsing, NEVER for calculations

**Example WorkoutSpec:**
```json
{
  "sport": "cycling",
  "steps": [
    {"kind": "warmup", "duration_s": 600, "target": {"power_pct": 50}},
    {
      "kind": "interval_block",
      "repeats": 5,
      "steps": [
        {"kind": "work", "duration_s": 180, "target": {"power_pct": 115, "tolerance": 5}},
        {"kind": "rest", "duration_s": 180, "target": {"power_pct": 50}}
      ]
    },
    {"kind": "cooldown", "duration_s": 600, "target": {"power_pct": 50}}
  ]
}
```

**Priority**: **P1** - Week 3 in plan

---

### 8. **Multi-User Support Missing** 🟡 MEDIUM
**Current**: Global `tp_client` instance (single user only)

**Issues**:
- No token persistence (lost on restart)
- No user sessions/database
- OAuth tokens not encrypted/stored
- Can't support multiple athletes

**Need**:
- User/athlete table
- Token storage (encrypted)
- Session management (JWT or session store)
- Per-request client instantiation

**Priority**: **P2** - Can defer until beta, but add to technical debt

---

### 9. **No "Something's Off" Detector** 🟡 MEDIUM
**Current**: Only TSS/CTL/ATL/TSB

**Need to Add** (per .cursorrules):
- HRV/RHR tracking in daily metrics
- TSB < -20 for >3 days → fatigue warning
- HRV < 20th percentile for 2-3 days → recovery flag
- RHR > 7-day mean + 5 bpm → warning
- RPE mismatch detection (high RPE on easy sessions)
- Monotony risk: `mean(TSS_7d) / std(TSS_7d) > 2`

**Priority**: **P2** - Week 5 in plan

---

### 10. **No Goal Tracking** 🟢 LOW
**Current**: No event targets or progress monitoring

**Need**:
- Goal model (event date, target power/pace, distance)
- Progress tracking against targets
- Readiness indicators (CTL trend, key session completion)

**Priority**: **P3** - Week 6 in plan

---

## Recommended Next Steps (Prioritized)

### Phase 1: MVP Foundation (This Week)

#### **Task 1.1: Complete Canonical Data Model** 
**Estimated Time**: 2-3 hours  
**Action**:
1. Add all missing Pydantic schemas to `app/schemas/training.py`:
   - Athlete
   - WorkoutPlanned
   - WorkoutExecuted
   - Sample
   - IntervalDetected
2. Update MetricsDaily to include HRV, RHR, sleep, RPE fields
3. Write unit tests for schema validation

**Acceptance Criteria**:
- All schemas have type hints
- Validation rules in place (Field constraints)
- Tests cover edge cases (missing fields, invalid ranges)

---

#### **Task 1.2: Database Setup**
**Estimated Time**: 3-4 hours  
**Action**:
1. Create PostgreSQL database (Docker or local)
2. Add SQLAlchemy/asyncpg dependencies
3. Create database models mirroring Pydantic schemas
4. Write migration script (Alembic)
5. Set up TimescaleDB hypertable for samples table
6. Add database connection to FastAPI (dependency injection)

**SQL Schema**:
```sql
CREATE TABLE athlete (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sport VARCHAR(50) NOT NULL,
    thresholds_json JSONB,
    zones_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workout_planned (
    id SERIAL PRIMARY KEY,
    athlete_id INTEGER REFERENCES athlete(id),
    start_time TIMESTAMPTZ NOT NULL,
    sport VARCHAR(50) NOT NULL,
    spec_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE workout_executed (
    id SERIAL PRIMARY KEY,
    athlete_id INTEGER REFERENCES athlete(id),
    source VARCHAR(50) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    duration_s INTEGER NOT NULL,
    file_ref TEXT,
    summary_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE samples (
    workout_id INTEGER REFERENCES workout_executed(id),
    t_s INTEGER NOT NULL,
    power_w INTEGER,
    hr_bpm INTEGER,
    pace_mps REAL,
    cadence INTEGER,
    altitude_m REAL,
    lat REAL,
    lon REAL,
    PRIMARY KEY (workout_id, t_s)
);

-- Convert samples to TimescaleDB hypertable
SELECT create_hypertable('samples', 'workout_id', chunk_time_interval => 1000);

CREATE TABLE intervals_detected (
    id SERIAL PRIMARY KEY,
    workout_id INTEGER REFERENCES workout_executed(id),
    t_start INTEGER NOT NULL,
    t_end INTEGER NOT NULL,
    kind VARCHAR(50) NOT NULL,
    targets_json JSONB,
    metrics_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE metrics_daily (
    id SERIAL PRIMARY KEY,
    athlete_id INTEGER REFERENCES athlete(id),
    date DATE NOT NULL,
    tss REAL,
    ctl REAL,
    atl REAL,
    tsb REAL,
    rhr INTEGER,
    hrv REAL,
    sleep_score REAL,
    rpe INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (athlete_id, date)
);

CREATE INDEX idx_metrics_daily_athlete_date ON metrics_daily(athlete_id, date);
CREATE INDEX idx_workout_executed_athlete ON workout_executed(athlete_id, start_time);
CREATE INDEX idx_samples_workout ON samples(workout_id);
```

**Acceptance Criteria**:
- Database can be created from scratch
- All tables have proper indexes
- Foreign keys enforce referential integrity
- TimescaleDB hypertable created for samples

---

#### **Task 1.3: FIT File Upload & Parser**
**Estimated Time**: 4-6 hours  
**Action**:
1. Add `fitparse` to requirements.txt
2. Create `app/services/file_parser.py`:
   - `parse_fit_file(file_path: str) -> WorkoutExecuted`
   - Extract: start_time, duration, sport
   - Extract samples: power, HR, cadence, GPS per second
   - Calculate summary: avg power, avg HR, TSS (if FTP known)
3. Add endpoint: `POST /workouts/upload` (multipart/form-data)
4. Save file to disk/S3
5. Parse and insert into database (workout_executed + samples)
6. Write unit tests with sample FIT file

**Endpoint**:
```python
@app.post("/workouts/upload")
async def upload_workout(
    file: UploadFile = File(...),
    athlete_id: int = Form(...),
    db: Session = Depends(get_db)
):
    # Validate file type (FIT/TCX/GPX)
    # Save file
    # Parse file
    # Insert workout_executed and samples
    # Return workout summary
    pass
```

**Acceptance Criteria**:
- Can upload .fit file via API
- Extracts per-second power/HR/cadence data
- Stores in database (workout_executed + samples tables)
- Returns workout summary (duration, avg power, TSS estimate)
- Tests with real FIT file from Garmin/Wahoo

---

#### **Task 1.4: Implement NP/IF Calculations**
**Estimated Time**: 2-3 hours  
**Action**:
1. Add functions to `app/services/metrics.py`:
   - `calculate_normalized_power(power_samples, sample_rate_hz)`
   - `calculate_intensity_factor(np, ftp)`
   - `calculate_variability_index(np, avg_power)`
   - `calculate_tss_from_power(duration_s, np, ftp)`
2. Update `compute_metrics_daily()` to use NP-based TSS when power data available
3. Write comprehensive unit tests (steady power, variable power, edge cases)

**Test Cases**:
- Steady power (VI should be ~1.00)
- Variable intervals (VI should be 1.05-1.15)
- Empty power samples (should raise ValueError)
- Single sample (edge case handling)

**Acceptance Criteria**:
- NP calculated correctly vs manual spreadsheet
- TSS from power data matches TrainingPeaks calculation
- All edge cases handled with clear errors

---

### Phase 2: Core Features (Next Week)

#### **Task 2.1: Interval Detection**
**Estimated Time**: 6-8 hours  
**Action**:
1. Add `ruptures` to requirements.txt
2. Create `app/services/interval_detection.py`
3. Implement PELT-based change-point detection
4. Add interval labeling (work/rest based on FTP zones)
5. Write tests with synthetic and real workout data

---

#### **Task 2.2: WorkoutSpec Schema + Parser**
**Estimated Time**: 4-6 hours  
**Action**:
1. Design WorkoutSpec JSON schema
2. Add Pydantic model for WorkoutSpec
3. Integrate OpenAI/Anthropic API for text parsing
4. Add endpoint: `POST /workouts/parse` (text → WorkoutSpec JSON)
5. Write tests with common workout descriptions

---

#### **Task 2.3: Compliance Scoring Engine**
**Estimated Time**: 8-10 hours  
**Action**:
1. Create `app/services/compliance.py`
2. Implement time-in-zone calculations
3. Implement step pass/fail rules
4. Match detected intervals to planned steps
5. Generate compliance report with pass/fail/marginal ratings

---

### Phase 3: Polish (Later)

- Multi-user support + token persistence
- "Something's Off" detector
- Goal tracking system
- React dashboard (PMC charts, workout detail views)

---

## Technical Debt to Address

1. **Fix Failing Tests**
   - `test_activities_endpoint_validation` - auth mocking issue
   - `test_get_authorization_url` - Authlib API change

2. **Global tp_client**
   - Refactor to per-request instance or user session

3. **Error Handling**
   - Add structured logging (structlog)
   - Improve error messages
   - Add retry logic for API calls

4. **Configuration**
   - Validate env vars at startup
   - Use Pydantic Settings for config management

5. **Documentation**
   - Add docstrings to all functions
   - Document API endpoints (OpenAPI)
   - Create developer setup guide

---

## Success Metrics

### Week 1-2 Goals:
- ✅ Can upload FIT file
- ✅ Extracts per-second samples
- ✅ Calculates NP, IF, TSS from power data
- ✅ Stores in PostgreSQL + TimescaleDB
- ✅ Computes CTL/ATL/TSB from uploaded workouts
- ✅ >80% test coverage on new code

### MVP Complete (Week 6):
- Athletes can upload workouts (no API dependency)
- Intervals detected automatically
- Compliance scored vs planned workouts
- Fatigue/recovery warnings ("Something's Off")
- Basic React dashboard with PMC chart

---

## Conclusion

**Start Here:**
1. ✅ Complete data model schemas (2-3 hours)
2. ✅ Set up PostgreSQL + TimescaleDB (3-4 hours)
3. ✅ Implement FIT file upload + parser (4-6 hours)
4. ✅ Add NP/IF calculations (2-3 hours)

**Total Estimated Time for Phase 1**: 11-16 hours (1-2 days of focused work)

This will unblock the core MVP and allow athletes to start using the platform immediately without waiting for TrainingPeaks API approval.

