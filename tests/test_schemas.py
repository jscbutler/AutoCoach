"""Unit tests for Pydantic schemas in app/schemas/training.py"""
from datetime import date, datetime, timedelta
from typing import Dict

import pytest
from pydantic import ValidationError

from app.schemas.training import (
    Athlete,
    WorkoutStep,
    WorkoutSpec,
    WorkoutPlanned,
    WorkoutExecuted,
    Sample,
    IntervalDetected,
    MetricsDaily,
)


class TestAthleteSchema:
    """Test Athlete model validation and constraints."""

    def test_athlete_with_minimal_fields_creates_successfully(self):
        """Test athlete creation with only required fields."""
        athlete = Athlete(name="John Doe", sport="cycling")
        assert athlete.name == "John Doe"
        assert athlete.sport == "cycling"
        assert athlete.ftp is None
        assert athlete.id is None

    def test_athlete_with_all_fields_creates_successfully(self):
        """Test athlete creation with all optional fields populated."""
        athlete = Athlete(
            id=1,
            name="Jane Smith",
            sport="triathlon",
            ftp=250,
            cp=4.5,
            lthr=165,
            max_hr=190,
            resting_hr=45,
            weight_kg=65.5,
            hr_zones={"Z1": (100, 130), "Z2": (130, 150)},
            power_zones={"Z2": (150, 200), "Z3": (200, 250)},
            pace_zones={"Easy": (5.5, 6.0), "Tempo": (4.5, 5.0)},
            created_at=datetime.now(),
        )
        assert athlete.ftp == 250
        assert athlete.weight_kg == 65.5
        assert athlete.hr_zones["Z1"] == (100, 130)

    def test_athlete_sport_validation_accepts_valid_sports(self):
        """Test that valid sport types are accepted and normalized."""
        valid_sports = ["cycling", "running", "swimming", "triathlon", "other"]
        for sport in valid_sports:
            athlete = Athlete(name="Test", sport=sport)
            assert athlete.sport == sport.lower()

    def test_athlete_sport_validation_rejects_invalid_sport(self):
        """Test that invalid sport types raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Athlete(name="Test", sport="basketball")
        assert "Sport must be one of" in str(exc_info.value)

    def test_athlete_ftp_validation_rejects_negative_value(self):
        """Test that negative FTP raises validation error."""
        with pytest.raises(ValidationError):
            Athlete(name="Test", sport="cycling", ftp=-100)

    def test_athlete_ftp_validation_rejects_unrealistic_high_value(self):
        """Test that unrealistically high FTP raises validation error."""
        with pytest.raises(ValidationError):
            Athlete(name="Test", sport="cycling", ftp=700)

    def test_athlete_hr_validation_rejects_out_of_range_values(self):
        """Test that heart rate values outside valid range are rejected."""
        with pytest.raises(ValidationError):
            Athlete(name="Test", sport="running", max_hr=250)
        
        with pytest.raises(ValidationError):
            Athlete(name="Test", sport="running", resting_hr=20)

    def test_athlete_name_validation_rejects_empty_string(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError):
            Athlete(name="", sport="cycling")


class TestWorkoutStepSchema:
    """Test WorkoutStep model validation."""

    def test_workout_step_with_power_target_creates_successfully(self):
        """Test creating a workout step with power target."""
        step = WorkoutStep(
            kind="work",
            duration_s=300,
            target_power_pct=110,
            tolerance_pct=5
        )
        assert step.kind == "work"
        assert step.duration_s == 300
        assert step.target_power_pct == 110

    def test_workout_step_with_hr_target_creates_successfully(self):
        """Test creating a workout step with heart rate target."""
        step = WorkoutStep(
            kind="warmup",
            duration_s=600,
            target_hr_pct=70
        )
        assert step.target_hr_pct == 70

    def test_workout_step_with_nested_intervals_creates_successfully(self):
        """Test creating interval block with nested steps."""
        step = WorkoutStep(
            kind="interval_block",
            repeats=5,
            steps=[
                WorkoutStep(kind="work", duration_s=180, target_power_pct=115),
                WorkoutStep(kind="rest", duration_s=180, target_power_pct=50),
            ]
        )
        assert step.repeats == 5
        assert len(step.steps) == 2
        assert step.steps[0].kind == "work"

    def test_workout_step_validation_rejects_negative_duration(self):
        """Test that negative duration raises validation error."""
        with pytest.raises(ValidationError):
            WorkoutStep(kind="work", duration_s=-100)


class TestWorkoutSpecSchema:
    """Test WorkoutSpec model validation."""

    def test_workout_spec_with_simple_structure_creates_successfully(self):
        """Test creating a simple workout specification."""
        spec = WorkoutSpec(
            sport="cycling",
            name="Easy Endurance",
            steps=[
                WorkoutStep(kind="warmup", duration_s=600, target_power_pct=50),
                WorkoutStep(kind="work", duration_s=3600, target_power_pct=70),
                WorkoutStep(kind="cooldown", duration_s=600, target_power_pct=50),
            ],
            total_duration_s=4800,
        )
        assert spec.sport == "cycling"
        assert len(spec.steps) == 3
        assert spec.total_duration_s == 4800

    def test_workout_spec_with_interval_block_creates_successfully(self):
        """Test creating workout spec with interval block."""
        spec = WorkoutSpec(
            sport="cycling",
            name="5x3min @ Threshold",
            steps=[
                WorkoutStep(kind="warmup", duration_s=600, target_power_pct=50),
                WorkoutStep(
                    kind="interval_block",
                    repeats=5,
                    steps=[
                        WorkoutStep(kind="work", duration_s=180, target_power_pct=115),
                        WorkoutStep(kind="rest", duration_s=180, target_power_pct=50),
                    ]
                ),
                WorkoutStep(kind="cooldown", duration_s=600, target_power_pct=50),
            ],
        )
        assert spec.steps[1].repeats == 5
        assert spec.steps[1].steps[0].duration_s == 180


class TestWorkoutPlannedSchema:
    """Test WorkoutPlanned model validation."""

    def test_workout_planned_creates_successfully_with_valid_data(self):
        """Test creating a planned workout."""
        planned = WorkoutPlanned(
            athlete_id=1,
            start_time=datetime.now() + timedelta(days=1),
            sport="cycling",
            spec_json={"steps": []},
            notes="Threshold intervals session"
        )
        assert planned.athlete_id == 1
        assert planned.sport == "cycling"

    def test_workout_planned_validation_rejects_invalid_athlete_id(self):
        """Test that zero or negative athlete_id raises validation error."""
        with pytest.raises(ValidationError):
            WorkoutPlanned(
                athlete_id=0,
                start_time=datetime.now(),
                sport="cycling",
                spec_json={}
            )


class TestWorkoutExecutedSchema:
    """Test WorkoutExecuted model validation."""

    def test_workout_executed_creates_successfully_with_minimal_data(self):
        """Test creating an executed workout with required fields only."""
        executed = WorkoutExecuted(
            athlete_id=1,
            source="file",
            start_time=datetime.now(),
            duration_s=3600,
            sport="cycling"
        )
        assert executed.source == "file"
        assert executed.duration_s == 3600

    def test_workout_executed_creates_with_full_summary_json(self):
        """Test creating executed workout with complete summary metrics."""
        executed = WorkoutExecuted(
            athlete_id=1,
            source="strava",
            start_time=datetime.now(),
            duration_s=3600,
            sport="cycling",
            summary_json={
                "avg_power": 220,
                "np": 235,
                "if": 0.85,
                "vi": 1.07,
                "avg_hr": 155,
                "tss": 78.5,
                "distance_m": 45000,
                "elevation_m": 520
            }
        )
        assert executed.summary_json["avg_power"] == 220
        assert executed.summary_json["np"] == 235

    def test_workout_executed_source_validation_normalizes_to_lowercase(self):
        """Test that source is normalized to lowercase."""
        executed = WorkoutExecuted(
            athlete_id=1,
            source="TrainingPeaks",
            start_time=datetime.now(),
            duration_s=3600,
            sport="cycling"
        )
        assert executed.source == "trainingpeaks"

    def test_workout_executed_source_validation_rejects_invalid_source(self):
        """Test that invalid source raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            WorkoutExecuted(
                athlete_id=1,
                source="invalid_source",
                start_time=datetime.now(),
                duration_s=3600,
                sport="cycling"
            )
        assert "Source must be one of" in str(exc_info.value)


class TestSampleSchema:
    """Test Sample model validation."""

    def test_sample_with_power_and_hr_creates_successfully(self):
        """Test creating a sample with power and heart rate data."""
        sample = Sample(
            workout_id=1,
            t_s=120,
            power_w=250,
            hr_bpm=155,
            cadence=90
        )
        assert sample.workout_id == 1
        assert sample.t_s == 120
        assert sample.power_w == 250

    def test_sample_with_gps_data_creates_successfully(self):
        """Test creating a sample with GPS coordinates."""
        sample = Sample(
            workout_id=1,
            t_s=60,
            lat=37.7749,
            lon=-122.4194,
            altitude_m=50.5
        )
        assert sample.lat == 37.7749
        assert sample.lon == -122.4194

    def test_sample_with_all_fields_creates_successfully(self):
        """Test creating a sample with all optional fields."""
        sample = Sample(
            workout_id=1,
            t_s=300,
            power_w=240,
            hr_bpm=160,
            pace_mps=3.5,
            cadence=88,
            altitude_m=125.0,
            lat=40.7128,
            lon=-74.0060,
            temperature_c=22.5,
            distance_m=1050.0
        )
        assert sample.temperature_c == 22.5
        assert sample.distance_m == 1050.0

    def test_sample_validation_rejects_negative_time(self):
        """Test that negative time offset raises validation error."""
        with pytest.raises(ValidationError):
            Sample(workout_id=1, t_s=-10)

    def test_sample_validation_rejects_out_of_range_lat_lon(self):
        """Test that invalid GPS coordinates raise validation error."""
        with pytest.raises(ValidationError):
            Sample(workout_id=1, t_s=0, lat=91.0, lon=0.0)
        
        with pytest.raises(ValidationError):
            Sample(workout_id=1, t_s=0, lat=0.0, lon=-181.0)


class TestIntervalDetectedSchema:
    """Test IntervalDetected model validation."""

    def test_interval_detected_creates_successfully_with_minimal_data(self):
        """Test creating a detected interval with required fields."""
        interval = IntervalDetected(
            workout_id=1,
            t_start=600,
            t_end=900,
            kind="work",
            metrics_json={"avg_power": 280}
        )
        assert interval.t_start == 600
        assert interval.t_end == 900
        assert interval.kind == "work"

    def test_interval_detected_with_targets_and_metrics_creates_successfully(self):
        """Test creating interval with matched targets and full metrics."""
        interval = IntervalDetected(
            workout_id=1,
            t_start=600,
            t_end=900,
            kind="work",
            targets_json={"power_pct": 115, "tolerance": 5},
            metrics_json={
                "avg_power": 285,
                "np": 290,
                "avg_hr": 170,
                "time_in_zone": 0.92,
                "compliance_pct": 95
            },
            planned_step_index=2
        )
        assert interval.metrics_json["compliance_pct"] == 95
        assert interval.planned_step_index == 2

    def test_interval_detected_validation_rejects_end_before_start(self):
        """Test that t_end <= t_start raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            IntervalDetected(
                workout_id=1,
                t_start=900,
                t_end=600,
                kind="work",
                metrics_json={}
            )
        assert "t_end must be greater than t_start" in str(exc_info.value)

    def test_interval_detected_validation_rejects_equal_start_and_end(self):
        """Test that t_end == t_start raises validation error."""
        with pytest.raises(ValidationError):
            IntervalDetected(
                workout_id=1,
                t_start=600,
                t_end=600,
                kind="work",
                metrics_json={}
            )


class TestMetricsDailySchema:
    """Test MetricsDaily model validation with recovery markers."""

    def test_metrics_daily_with_training_load_only_creates_successfully(self):
        """Test creating daily metrics with TSS/CTL/ATL/TSB only."""
        metrics = MetricsDaily(
            metric_date=date.today(),
            tss=85.5,
            atl=72.3,
            ctl=98.7,
            tsb=26.4
        )
        assert metrics.tss == 85.5
        assert metrics.tsb == 26.4

    def test_metrics_daily_with_recovery_markers_creates_successfully(self):
        """Test creating daily metrics with HRV, RHR, and sleep data."""
        metrics = MetricsDaily(
            athlete_id=1,
            metric_date=date.today(),
            tss=120.0,
            atl=95.5,
            ctl=105.2,
            tsb=9.7,
            rhr=48,
            hrv=68.5,
            sleep_score=85.0,
            sleep_duration_min=450,
            rpe=7,
            notes="Felt tired, but completed workout"
        )
        assert metrics.rhr == 48
        assert metrics.hrv == 68.5
        assert metrics.sleep_score == 85.0
        assert metrics.rpe == 7

    def test_metrics_daily_validation_rejects_negative_tss(self):
        """Test that negative TSS raises validation error."""
        with pytest.raises(ValidationError):
            MetricsDaily(
                metric_date=date.today(),
                tss=-10.0,
                atl=50.0,
                ctl=80.0,
                tsb=30.0
            )

    def test_metrics_daily_validation_rejects_invalid_rpe(self):
        """Test that RPE outside 1-10 range raises validation error."""
        with pytest.raises(ValidationError):
            MetricsDaily(
                metric_date=date.today(),
                tss=100.0,
                atl=50.0,
                ctl=80.0,
                tsb=30.0,
                rpe=0
            )
        
        with pytest.raises(ValidationError):
            MetricsDaily(
                metric_date=date.today(),
                tss=100.0,
                atl=50.0,
                ctl=80.0,
                tsb=30.0,
                rpe=11
            )

    def test_metrics_daily_validation_rejects_invalid_hrv(self):
        """Test that unrealistic HRV values raise validation error."""
        with pytest.raises(ValidationError):
            MetricsDaily(
                metric_date=date.today(),
                tss=100.0,
                atl=50.0,
                ctl=80.0,
                tsb=30.0,
                hrv=-5.0
            )

    def test_metrics_daily_allows_negative_tsb(self):
        """Test that negative TSB (fatigue) is allowed."""
        metrics = MetricsDaily(
            metric_date=date.today(),
            tss=150.0,
            atl=120.0,
            ctl=95.0,
            tsb=-25.0  # Negative TSB indicates fatigue
        )
        assert metrics.tsb == -25.0


class TestSchemaIntegration:
    """Integration tests for schema relationships."""

    def test_workout_spec_can_be_embedded_in_workout_planned(self):
        """Test that WorkoutSpec can be serialized and stored in WorkoutPlanned."""
        spec = WorkoutSpec(
            sport="cycling",
            name="Test Workout",
            steps=[
                WorkoutStep(kind="warmup", duration_s=600, target_power_pct=50),
                WorkoutStep(kind="work", duration_s=1800, target_power_pct=85),
            ]
        )
        
        planned = WorkoutPlanned(
            athlete_id=1,
            start_time=datetime.now(),
            sport="cycling",
            spec_json=spec.model_dump()
        )
        
        assert "steps" in planned.spec_json
        assert len(planned.spec_json["steps"]) == 2

    def test_sample_data_can_be_aggregated_for_interval_metrics(self):
        """Test that multiple samples can represent an interval."""
        samples = [
            Sample(workout_id=1, t_s=i, power_w=250 + i, hr_bpm=150 + i//10)
            for i in range(0, 300, 1)  # 5 minutes of data
        ]
        
        assert len(samples) == 300
        avg_power = sum(s.power_w for s in samples) / len(samples)
        assert 370 < avg_power < 430  # Rough check

