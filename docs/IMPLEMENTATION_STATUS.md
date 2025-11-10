# AutoCoach Implementation Status

## Current State Assessment

### ✅ Already Implemented

1. **Basic TrainingPeaks Client**
   - OAuth2 authentication flow
   - Sandbox/production environment support
   - Basic API methods (profile, workouts, activities)
   - Activity data conversion to canonical format

2. **Core Schemas**
   - `Activity` model with essential fields
   - `MetricsDaily` model for TSS/CTL/ATL/TSB
   - `WeekPlanRequest` for planning inputs

3. **Metrics Calculation**
   - TSS computation from activities
   - CTL/ATL calculation using exponentially weighted moving averages
   - TSB (Training Stress Balance) calculation
   - Pandas-based implementation (following your preference)

4. **Basic API Endpoints**
   - Health check
   - TrainingPeaks OAuth flow (auth/callback)
   - Activities fetching
   - Metrics computation

5. **Testing Foundation**
   - Unit tests for TrainingPeaks client
   - Basic metrics calculation tests
   - Test structure in place

### ❌ Missing from MVP (per AutocoachOverview.md)

1. **Data Model Gaps**
   - No `workout_planned` table/schema
   - No `workout_executed` table/schema (using simplified Activity)
   - No `samples` table for per-second data
   - No `intervals_detected` table
   - No `athlete` table with thresholds/zones
   - No database implementation (only in-memory)

2. **File Upload Support**
   - No FIT/TCX/GPX file upload endpoints
   - No file parsing capabilities
   - This is critical since "TrainingPeaks API needs approval"

3. **Workout Plan Parser**
   - No WorkoutSpec JSON schema
   - No LLM integration for parsing workout text
   - No structured workout representation

4. **Interval Detection**
   - No change-point detection implementation
   - No PELT/ruptures integration
   - No interval scoring logic

5. **Compliance Scoring**
   - No time-in-zone calculations
   - No target hit % metrics
   - No pass/marginal/fail rules

6. **"Something's Off" Detector**
   - No HRV/RHR tracking
   - No RPE integration
   - No monotony calculations
   - No execution drift detection

7. **Storage Infrastructure**
   - No PostgreSQL setup
   - No TimescaleDB for time-series data
   - No data persistence beyond session

8. **Multi-user Support**
   - Global client instance (not per-user)
   - No token storage/management
   - No user session handling

## Priority Actions for Week 1-2 (per 6-week plan)

### Immediate Priorities:
1. **Canonical Schema** - Complete all data models
2. **FIT/TCX/GPX Upload** - Critical for day-one usability
3. **Database Setup** - PostgreSQL + TimescaleDB
4. **Compute NP/IF/TSS** - Extend current metrics
5. **PMC (CTL/ATL/TSB)** - Already done ✅

### Technical Debt:
1. **TrainingPeaks Client**
   - Token persistence
   - Multi-user support
   - Better error handling
   - Rate limiting

2. **Testing**
   - Low coverage on existing code
   - No integration tests
   - No API endpoint tests

3. **Configuration**
   - Environment validation at startup
   - Proper logging setup
   - Error tracking

## Recommendations

1. **Start with File Upload** - Since TrainingPeaks API requires approval, prioritize FIT file parsing
2. **Set up Database** - Current in-memory approach won't scale
3. **Fix Multi-user Support** - Current global client is a blocker for production
4. **Add Comprehensive Tests** - Current coverage is minimal
