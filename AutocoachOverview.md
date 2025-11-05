# AutoCoach - Training Analysis Platform

## What to Build First (Tight MVP)

### 1. Data In → Canonical Model

- **Accept**: TrainingPeaks (if you can get access), Strava, Garmin, or plain FIT/TCX/GPX uploads
- **Normalize** to a single schema:
  - `athlete`
  - `workout_planned`
  - `workout_executed`
  - `samples` (per-second)
  - `intervals_detected`
  - `metrics_daily` (RHR, HRV, etc.)
  - `thresholds` (FTP/CP, HR zones)
- **Reality check**: TrainingPeaks API needs approval; don't assume access on day 1. Build a file-upload path and a Strava fallback first
- **Strava**: Workable, but rate limits + newer API terms (e.g., no AI model training on their data, show data only to the user) mean you shouldn't depend on them for server-side analytics at scale. Plan your cache and backfill carefully
- **Garmin Health API**: Powerful (sleep, HR, HRV), but it's a licensed/commercial program—budget/time accordingly. Aggregators exist if you don't want to integrate each vendor

### 2. Plan Parser → "WorkoutSpec" JSON

- Convert free-text workout descriptions into a structured spec your engine can score against
- **Example (cycling)**: warm-up → 5×(3′ @ 115–120% FTP / 3′ easy) → cool-down
- Use an LLM only to extract structure; never trust it for numbers you can compute
- Keep the schema tight (sport, steps, targets, bands, repeats)

### 3. Interval Detection (when laps aren't marked)

- **Power/pace change-point detection** with constraints:
  - Smooth series (e.g., 5–10 s rolling), then segment using a PELT/ruptures-style cost on mean/variance with min-duration guards
  - Merge near-duplicates; label "work" vs "rest" by intensity bands vs athlete thresholds
  - Score each planned step vs the detected interval that best overlaps it

### 4. Compliance & Review Scoring

**For each step:**
- Time-in-zone %
- Target hit %
- Average vs target
- Variability (stdev / target)
- Pass/marginal/fail rules

**Session metrics:**
- NP, IF, TSS, VI
- Pa:Hr/decoupling (for steady endurance)
- Cadence discipline
- Indoor vs outdoor flags

**Quick refs (cycling):**
- `NP ≈ 4th-power mean of 30-s smoothed power`
- `IF = NP / FTP`
- `TSS ≈ (sec × NP × IF) / (FTP × 3600) × 100`
- For the season view: CTL/ATL are EWMAs of daily TSS (≈42-day and 7-day time constants), `TSB = CTL − ATL`

### 5. "Something's Off" Detector (early, interpretable rules)

- **Acute vs chronic load**: TSB < −20 for >3 days → high fatigue risk; rapid ATL spikes vs last week (tune to sport/athlete)
- **HRV & RHR**: 3-day HRV rolling mean < 20th percentile of 60-day baseline or RHR +5 bpm vs 7-day mean → recovery caution (only act when both agree for 2–3 days to reduce false alarms). Garmin HRV available via Health API/partners
- **RPE mismatch**: High RPE on objectively easy IF/low TSS sessions → flag possible non-training stress
- **Monotony**: mean(TSS 7d)/sd(TSS 7d) > ~2 → suggest variation
- **Execution drift**: Endurance step Pa:Hr > ~5% or power decays across intervals → aerobic durability/poor fueling flags

### 6. Goal Tracking

- Represent goals as constraints: date, event type, target (time, power over duration, pace, HR cap)
- Track readiness using CP/FTP trend, event-specific key session templates (e.g., marathon long run + tempo, 20–40/20 cycling VO2, swim CSS tests)
- Show deltas to goal targets with confidence bands

## Architecture That Will Scale (and fit your stack)

- **Ingestion**: FastAPI + background workers (RQ/Celery) for pulls, webhooks where possible, plus FIT/TCX upload
- **Storage**: PostgreSQL + TimescaleDB for samples; parquet for raw mirrors; materialized views for day/interval rollups
- **Analytics**: Python (pandas/numba) for feature calc; ruptures for change-points; scikit for simple anomaly models later
- **App**: React (Vite) dashboard
  - Views: Today Review, Workout Detail, Signals, Goals Roadmap, Trends (PMC)
- **Auth & privacy**: Per-source OAuth, token vaulting, and strict data-use flags (e.g., opt-out of any AI training if source forbids—Strava explicitly does)

## Data Model (minimal, enough for MVP)

```sql
athlete(id, sport, thresholds_json, zones_json)
workout_planned(id, athlete_id, start_time, sport, spec_json)
workout_executed(id, athlete_id, source, start_time, duration_s, file_ref, summary_json)
samples(workout_id, t_s, power_w, hr_bpm, pace_mps, cadence, altitude, …)
intervals_detected(id, workout_id, t_start, t_end, kind, targets_json, metrics_json)
metrics_daily(athlete_id, date, tss, ctl, atl, tsb, rhr, hrv, sleep, notes_rpe)
```

## Scoring Rules (first pass, practical)

- **Step pass**: ≥80% of the step duration within target band and mean within ±3% (threshold/tempo) or ±5–8% (VO2/anaerobic)
- **Rest pass**: ≤60% of cap (power/HR) for ≥80% of the rest
- **Endurance block**: Decoupling ≤5% and cadence within target range → pass
- **Session pass**: ≥70% passes on steps, no red flags ("off" detector)

## Where People Go Wrong (and better paths)

- **Depending on one platform**: TrainingPeaks access isn't guaranteed; Strava terms limit what you can do with AI. Ship FIT/TCX upload + Garmin/Strava basic connectors first so athletes can use it day one
- **Letting the LLM "analyze the workout"**: Use it to parse the plan text only. All scoring and numbers must come from your engine to avoid hallucinations and to stay explainable
- **Overreacting to single-day HRV/RHR**: Use rolling baselines and 2–3 consecutive signals before nagging people
- **ACWR/monotony as gospel**: Keep thresholds conservative; treat them as prompts for review, not hard stops

## 6-Week Build Plan

- **Week 1–2**: Canonical schema + FIT/TCX/GPX upload; compute NP/IF/TSS + PMC (CTL/ATL/TSB)
- **Week 3**: Plan-text → WorkoutSpec (LLM) and rule-based compliance
- **Week 4**: Interval detector + overlap matching
- **Week 5**: "Off" detector v1 (RHR/HRV/RPE/TSB rules) + daily signals view
- **Week 6**: Goal model + roadmap view; coach-style summaries grounded in numbers (no invented claims)

## Next Concrete Step

If you're game, I'll sketch the WorkoutSpec JSON schema, the interval detection pseudocode, and the TimescaleDB table DDL so you can drop it into your stack and start ingesting a couple of sample workouts immediately.
