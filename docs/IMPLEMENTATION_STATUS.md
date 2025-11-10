# AutoCoach Implementation Status

**Last Updated**: November 10, 2025  
**Branch**: main  
**Status**: MVP Phase - Strava Integration Complete ✅

## Current State Assessment

### ✅ Already Implemented

1. **Strava API Integration** 🆕 ⭐
   - Full OAuth 2.0 authentication with token persistence
   - Auto-initialization from environment variables
   - Activity fetching with rich data (power, HR, cadence, GPS)
   - Training zones (heart rate and power)
   - Athlete profile access
   - Time-series streams for interval detection
   - Rate limit awareness (100/15min, 1000/day)
   - **Live & Tested**: Successfully connected to Jeff's Strava account
   - 8 REST API endpoints fully functional

2. **TrainingPeaks Client**
   - OAuth2 authentication flow
   - Sandbox/production environment support
   - Basic API methods (profile, workouts, activities)
   - Activity data conversion to canonical format
   - **Note**: Requires API approval (1-2 weeks) - now secondary to Strava

3. **Core Schemas**
   - `Activity` model with essential fields + normalized_power
   - `MetricsDaily` model for TSS/CTL/ATL/TSB
   - `WorkoutExecuted` with summary data
   - `Sample` model for time-series data
   - `AthleteThreshold` for FTP/LTHR tracking
   - Pydantic validation throughout

4. **Metrics Calculation**
   - Normalized Power (NP) from power samples
   - Intensity Factor (IF)
   - Variability Index (VI)
   - TSS computation from power and FTP
   - CTL/ATL calculation using exponentially weighted moving averages
   - TSB (Training Stress Balance) calculation
   - Pandas-based implementation (vectorized operations)

5. **FIT File Parsing** 🆕
   - Complete FIT file parser using `fitparse`
   - Extracts workout metadata and time-series samples
   - Power, HR, cadence, GPS, altitude data
   - Handles compressed (.fit.gz) files
   - Tested with real workout files

6. **Threshold Management** 🆕
   - Historical FTP tracking with effective dates
   - Automatic threshold selection for workout dates
   - Validation rules for TSS calculations
   - Type-safe threshold operations

7. **API Endpoints**
   - Health check
   - File upload (FIT/TCX/GPX)
   - TrainingPeaks OAuth flow
   - Strava OAuth flow (8 endpoints)
   - Activities fetching (TP + Strava)
   - Metrics computation
   - All endpoints with proper error handling

8. **Testing Foundation** 🆕
   - **94 tests passing** (7 skipped)
   - Unit tests for all clients (TrainingPeaks, Strava)
   - Schema validation tests (37 tests)
   - Metrics calculation tests (22 tests)
   - Threshold management tests (16 tests)
   - API endpoint tests (6 tests)
   - Test harness for integration testing
   - **Coverage**: >80% on new code

### ❌ Missing from MVP (per AutocoachOverview.md)

1. **Database Implementation**
   - No PostgreSQL setup
   - No TimescaleDB for time-series data
   - No data persistence beyond session
   - Schema models exist but not connected to DB
   - Tables needed: `athlete`, `workout_planned`, `workout_executed`, `samples`, `intervals_detected`, `metrics_daily`

2. **Workout Plan Parser**
   - No WorkoutSpec JSON schema for structured workouts
   - No LLM integration for parsing workout text
   - Need to convert coach text → structured intervals

3. **Interval Detection**
   - No change-point detection implementation
   - No PELT algorithm (`ruptures` library not integrated)
   - No automatic interval segmentation
   - Needed for matching executed vs planned workouts

4. **Compliance Scoring**
   - No time-in-zone calculations
   - No target hit % metrics (step pass/fail logic)
   - No power/pace/HR band compliance checks
   - No rest interval validation
   - No Pa:Hr decoupling detection

5. **"Something's Off" Detector**
   - No HRV/RHR tracking
   - No RPE integration
   - No monotony calculations (TSS_mean / TSS_std)
   - No execution drift detection (power decay, Pa:Hr)
   - No fatigue warnings (TSB < -20 for 3+ days)

6. **Multi-user Support**
   - Token persistence works but uses global client
   - No per-user session management
   - No user database/authentication
   - Single-user mode only

7. **TCX/GPX File Support**
   - FIT files work ✅
   - TCX parsing not implemented
   - GPX parsing not implemented
   - Need `lxml` for XML-based formats

## Week 1-2 Progress ✅

### Completed:
- ✅ **Data Source**: Strava API fully integrated (instant access, no approval needed)
- ✅ **Canonical Schema**: All core models complete with type hints
- ✅ **FIT File Parsing**: Full support for power, HR, GPS data
- ✅ **Metrics Calculation**: NP, IF, VI, TSS, CTL, ATL, TSB all working
- ✅ **Threshold Management**: Historical FTP tracking with validation
- ✅ **Test Coverage**: 94 tests passing, >80% coverage on new code
- ✅ **Documentation**: OAuth setup guides, quick starts, API docs

### What Changed from Original Plan:
- **Pivoted from TrainingPeaks → Strava**: Instant API access vs 1-2 week approval
- **Proved the Stack**: FastAPI + Pandas + Pydantic all working well
- **Established Patterns**: OAuth flows, token persistence, auto-initialization

## Next Steps (Week 3-4)

### Immediate Priorities:
1. **PostgreSQL + TimescaleDB Setup** ⏭️ NEXT
   - Docker Compose for local dev
   - Schema migrations (Alembic)
   - Connect Pydantic models to SQLAlchemy
   - TimescaleDB hypertable for `samples`

2. **Interval Detection Algorithm** ⏭️ HIGH PRIORITY
   - Install `ruptures` library
   - Implement PELT change-point detection
   - Smooth power/pace data (5-10s rolling avg)
   - Segment workouts into work/rest intervals
   - Label intervals by intensity

3. **Workout Plan Parser** ⏭️ MVP BLOCKER
   - Design `WorkoutSpec` JSON schema
   - LLM integration for text → JSON (OpenAI/Anthropic)
   - Structured workout representation
   - Example: "3x8min @ FTP, 3min easy" → JSON

4. **Compliance Scoring** ⏭️ MVP CORE FEATURE
   - Time-in-band calculations (power/HR/pace)
   - Step pass/fail logic (≥80% in target, mean within ±3-5%)
   - Rest interval validation
   - Session-level pass rate

5. **"Something's Off" Detector** ⏭️ VALUE ADD
   - HRV/RHR daily tracking
   - RPE mismatch detection
   - Monotony calculations
   - Fatigue warnings (TSB < -20 for 3+ days)

### Technical Improvements:
1. **Multi-user Support**
   - User authentication (simple token-based initially)
   - Per-user token storage in DB
   - Session management
   
2. **TCX/GPX Support**
   - Add `lxml` for XML parsing
   - TCX parser (TrainingPeaks format)
   - GPX parser (basic GPS tracks)

3. **React Frontend** (Week 5-6)
   - Vite + React setup
   - PMC chart visualization
   - Activity list and detail views
   - Workout compliance dashboard

## Recommendations

1. **Database First**: All other features need data persistence
2. **Interval Detection**: Enables compliance scoring and workout matching
3. **Keep Momentum**: We have a working data pipeline, now build analysis on top
4. **Stay Focused on MVP**: Defer advanced features (webhooks, real-time sync, etc.)
