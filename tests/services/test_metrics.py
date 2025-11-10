from datetime import date, timedelta

import pytest

from app.schemas.training import Activity
from app.services.metrics import (
    activities_to_dataframe,
    compute_chronic_and_acute_loads,
    compute_metrics_daily,
    calculate_normalized_power,
    calculate_intensity_factor,
    calculate_variability_index,
    calculate_tss_from_power,
)


def test_metrics_pipeline_monotonic_loading():
    # Build 14 days with increasing TSS
    start = date(2024, 1, 1)
    activities = []
    for i in range(14):
        activities.append(
            Activity(
                activity_date=start + timedelta(days=i),
                sport="ride",
                duration_min=60.0,
                tss=50.0 + i * 5.0,
            )
        )

    daily = activities_to_dataframe(activities)
    metrics = compute_chronic_and_acute_loads(daily)

    assert len(metrics) == 14
    # End-of-period ctl should be > atl alpha smoothing creates slower response
    assert metrics.iloc[-1]["ctl"] > 0
    assert metrics.iloc[-1]["atl"] > 0

    results = compute_metrics_daily(activities)
    assert results[-1].ctl >= results[-2].ctl


def test_empty_activities_returns_empty_metrics():
    results = compute_metrics_daily([])
    assert results == []


# ============================================================================
# Power Metrics Tests (NP, IF, VI, TSS)
# ============================================================================

class TestNormalizedPower:
    """Tests for Normalized Power (NP) calculation."""

    def test_normalized_power_steady_effort_equals_average(self):
        """Test that NP ≈ average power for steady efforts."""
        steady_power = [250.0] * 3600  # 1 hour at 250W
        np = calculate_normalized_power(steady_power)
        assert 249.0 < np < 251.0

    def test_normalized_power_variable_effort_exceeds_average(self):
        """Test that NP > average power for variable efforts."""
        # Create realistic intervals: 3 min @ 350W, 3 min @ 150W (avg = 250W)
        # The longer intervals (> 30s) will show NP > average
        intervals = ([350.0] * 180 + [150.0] * 180) * 10  # 10 intervals
        np = calculate_normalized_power(intervals)
        avg = sum(intervals) / len(intervals)
        assert np > avg  # NP should be > 250W average due to 4th-power weighting

    def test_normalized_power_with_intervals(self):
        """Test NP with interval workout."""
        warmup = [150.0] * 600  # 10 min @ 150W
        intervals = ([300.0] * 180 + [100.0] * 180) * 5  # 5×(3min@300W / 3min@100W)
        cooldown = [150.0] * 600  # 10 min @ 150W
        power = warmup + intervals + cooldown
        
        np = calculate_normalized_power(power)
        avg = sum(power) / len(power)
        assert np > avg

    def test_normalized_power_short_workout_returns_average(self):
        """Test that very short workouts (< 30s) return average power."""
        short_power = [250.0] * 20
        np = calculate_normalized_power(short_power)
        assert np == 250.0

    def test_normalized_power_empty_list_raises_error(self):
        """Test that empty power list raises ValueError."""
        with pytest.raises(ValueError, match="power_samples cannot be empty"):
            calculate_normalized_power([])

    def test_normalized_power_invalid_sample_rate_raises_error(self):
        """Test that invalid sample rate raises ValueError."""
        with pytest.raises(ValueError, match="sample_rate_hz must be positive"):
            calculate_normalized_power([250.0] * 100, sample_rate_hz=0)


class TestIntensityFactor:
    """Tests for Intensity Factor (IF) calculation."""

    def test_intensity_factor_at_ftp_equals_one(self):
        """Test that IF = 1.0 when NP equals FTP."""
        if_value = calculate_intensity_factor(np=300.0, ftp=300)
        assert if_value == 1.0

    def test_intensity_factor_recovery_ride(self):
        """Test IF for recovery ride (typically 0.55-0.65)."""
        if_value = calculate_intensity_factor(np=180.0, ftp=300)
        assert 0.55 < if_value < 0.65

    def test_intensity_factor_threshold_workout(self):
        """Test IF for threshold workout (typically 0.95-1.05)."""
        if_value = calculate_intensity_factor(np=295.0, ftp=300)
        assert 0.95 < if_value < 1.0

    def test_intensity_factor_zero_ftp_raises_error(self):
        """Test that zero FTP raises ValueError."""
        with pytest.raises(ValueError, match="FTP must be positive"):
            calculate_intensity_factor(np=250.0, ftp=0)


class TestVariabilityIndex:
    """Tests for Variability Index (VI) calculation."""

    def test_variability_index_steady_effort_equals_one(self):
        """Test that VI = 1.0 for perfectly steady efforts."""
        vi = calculate_variability_index(np=250.0, avg_power=250.0)
        assert vi == 1.0

    def test_variability_index_intervals_high_variability(self):
        """Test VI for interval workout (typically 1.10-1.20)."""
        vi = calculate_variability_index(np=280.0, avg_power=250.0)
        assert 1.10 < vi < 1.15

    def test_variability_index_zero_avg_power_returns_zero(self):
        """Test that zero average power returns 0."""
        vi = calculate_variability_index(np=250.0, avg_power=0.0)
        assert vi == 0.0


class TestTSSFromPower:
    """Tests for Training Stress Score (TSS) calculation from power."""

    def test_tss_one_hour_at_ftp_equals_100(self):
        """Test that 1 hour at FTP = 100 TSS (by definition)."""
        tss = calculate_tss_from_power(duration_s=3600, np=300.0, ftp=300)
        assert 99.5 < tss < 100.5

    def test_tss_30_min_at_ftp_equals_50(self):
        """Test that 30 minutes at FTP ≈ 50 TSS."""
        tss = calculate_tss_from_power(duration_s=1800, np=300.0, ftp=300)
        assert 49.5 < tss < 50.5

    def test_tss_recovery_ride(self):
        """Test TSS for easy recovery ride."""
        tss = calculate_tss_from_power(duration_s=3600, np=180.0, ftp=300)
        assert 30 < tss < 40

    def test_tss_zero_ftp_raises_error(self):
        """Test that zero FTP raises ValueError."""
        with pytest.raises(ValueError, match="FTP must be positive"):
            calculate_tss_from_power(duration_s=3600, np=250.0, ftp=0)

    def test_tss_negative_duration_raises_error(self):
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration_s cannot be negative"):
            calculate_tss_from_power(duration_s=-100, np=250.0, ftp=300)

    def test_tss_zero_duration_returns_zero(self):
        """Test that zero duration returns 0 TSS."""
        tss = calculate_tss_from_power(duration_s=0, np=250.0, ftp=300)
        assert tss == 0.0


class TestIntegratedPowerMetrics:
    """Integration tests for combined power metrics."""

    def test_power_metrics_for_steady_tempo_ride(self):
        """Test full power metrics for a steady tempo ride."""
        power = [255.0] * 3600  # 1 hour @ 85% FTP
        duration_s = len(power)
        ftp = 300
        
        np = calculate_normalized_power(power)
        avg_power = sum(power) / len(power)
        if_value = calculate_intensity_factor(np, ftp)
        vi = calculate_variability_index(np, avg_power)
        tss = calculate_tss_from_power(duration_s, np, ftp)
        
        assert abs(np - avg_power) < 2  # NP ≈ avg for steady
        assert 0.84 < if_value < 0.86  # Should match 85% FTP
        assert 0.99 <= vi <= 1.02  # Very low variability (allow exactly 1.0)
        assert 70 < tss < 75  # Moderate TSS
