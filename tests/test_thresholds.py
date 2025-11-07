"""Tests for threshold management service."""

from datetime import date, timedelta
import pytest

from app.schemas.training import AthleteThreshold
from app.services.thresholds import (
    get_threshold_for_date,
    get_threshold_history_df,
    calculate_ftp_progression,
    validate_threshold_for_tss_calculation,
    ThresholdNotFoundError,
)


class TestAthleteThresholdSchema:
    """Test AthleteThreshold Pydantic model."""
    
    def test_create_cycling_threshold(self):
        """Test creating a cycling threshold with all fields."""
        threshold = AthleteThreshold(
            athlete_id=1,
            effective_date=date(2024, 1, 1),
            sport="cycling",
            ftp=250,
            ftp_source="test",
            lthr=165,
            max_hr=185,
            resting_hr=48,
            hr_source="test",
            notes="20min FTP test",
            is_user_override=False,
        )
        assert threshold.ftp == 250
        assert threshold.sport == "cycling"
        assert threshold.is_user_override is False
    
    def test_create_running_threshold(self):
        """Test creating a running threshold."""
        threshold = AthleteThreshold(
            athlete_id=2,
            effective_date=date(2024, 6, 1),
            sport="running",
            threshold_pace_min_per_km=4.2,
            critical_speed_m_per_s=4.0,
            run_threshold_source="trainingpeaks",
            lthr=170,
            is_user_override=False,
        )
        assert threshold.threshold_pace_min_per_km == 4.2
        assert threshold.sport == "running"
    
    def test_create_swimming_threshold(self):
        """Test creating a swimming threshold."""
        threshold = AthleteThreshold(
            athlete_id=3,
            effective_date=date(2024, 3, 15),
            sport="swimming",
            threshold_pace_100m_s=90.0,
            swim_threshold_source="estimate",
            is_user_override=False,
        )
        assert threshold.threshold_pace_100m_s == 90.0
        assert threshold.sport == "swimming"
    
    def test_invalid_sport_raises_error(self):
        """Test that invalid sport types are rejected."""
        with pytest.raises(ValueError, match="Sport must be one of"):
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 1, 1),
                sport="invalid_sport",
                is_user_override=False,
            )
    
    def test_ftp_validation(self):
        """Test FTP validation constraints."""
        # Valid FTP
        threshold = AthleteThreshold(
            athlete_id=1,
            effective_date=date(2024, 1, 1),
            sport="cycling",
            ftp=250,
            is_user_override=False,
        )
        assert threshold.ftp == 250
        
        # FTP too high should fail
        with pytest.raises(ValueError):
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 1, 1),
                sport="cycling",
                ftp=700,  # > 600 max
                is_user_override=False,
            )


class TestGetThresholdForDate:
    """Test threshold lookup by date."""
    
    def test_single_threshold_lookup(self):
        """Test looking up single threshold."""
        thresholds = [
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 1, 1),
                sport="cycling",
                ftp=250,
                is_user_override=False,
            )
        ]
        
        result = get_threshold_for_date(
            athlete_id=1,
            sport="cycling",
            workout_date=date(2024, 6, 15),
            thresholds=thresholds
        )
        
        assert result is not None
        assert result.ftp == 250
    
    def test_multiple_thresholds_returns_most_recent(self):
        """Test that most recent threshold before workout date is returned."""
        thresholds = [
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 1, 1),
                sport="cycling",
                ftp=250,
                is_user_override=False,
            ),
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 6, 1),
                sport="cycling",
                ftp=270,
                is_user_override=False,
            ),
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 10, 1),
                sport="cycling",
                ftp=285,
                is_user_override=False,
            ),
        ]
        
        # Workout on July 15 should use June 1 threshold (270W)
        result = get_threshold_for_date(
            athlete_id=1,
            sport="cycling",
            workout_date=date(2024, 7, 15),
            thresholds=thresholds
        )
        
        assert result is not None
        assert result.ftp == 270
        assert result.effective_date == date(2024, 6, 1)
    
    def test_no_threshold_before_workout_date_returns_none(self):
        """Test that None is returned if no threshold exists before workout date."""
        thresholds = [
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 6, 1),
                sport="cycling",
                ftp=270,
                is_user_override=False,
            ),
        ]
        
        # Workout on Jan 1 (before any threshold) should return None
        result = get_threshold_for_date(
            athlete_id=1,
            sport="cycling",
            workout_date=date(2024, 1, 1),
            thresholds=thresholds
        )
        
        assert result is None
    
    def test_user_override_takes_precedence(self):
        """Test that user overrides take precedence over API imports."""
        thresholds = [
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 6, 1),
                sport="cycling",
                ftp=265,
                ftp_source="trainingpeaks",
                is_user_override=False,
            ),
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 6, 2),
                sport="cycling",
                ftp=270,
                ftp_source="user_override",
                is_user_override=True,
            ),
        ]
        
        result = get_threshold_for_date(
            athlete_id=1,
            sport="cycling",
            workout_date=date(2024, 7, 1),
            thresholds=thresholds,
            prefer_user_override=True
        )
        
        assert result is not None
        assert result.ftp == 270
        assert result.is_user_override is True
    
    def test_sport_filtering(self):
        """Test that only matching sport thresholds are considered."""
        thresholds = [
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 1, 1),
                sport="cycling",
                ftp=250,
                is_user_override=False,
            ),
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 1, 1),
                sport="running",
                threshold_pace_min_per_km=4.2,
                is_user_override=False,
            ),
        ]
        
        # Cycling workout should get cycling threshold
        result = get_threshold_for_date(
            athlete_id=1,
            sport="cycling",
            workout_date=date(2024, 6, 1),
            thresholds=thresholds
        )
        assert result.ftp == 250
        
        # Running workout should get running threshold
        result = get_threshold_for_date(
            athlete_id=1,
            sport="running",
            workout_date=date(2024, 6, 1),
            thresholds=thresholds
        )
        assert result.threshold_pace_min_per_km == 4.2


class TestGetThresholdHistoryDF:
    """Test threshold history DataFrame generation."""
    
    def test_empty_thresholds_returns_empty_df(self):
        """Test that empty threshold list returns empty DataFrame."""
        df = get_threshold_history_df(athlete_id=1, sport="cycling", thresholds=[])
        assert df.empty
    
    def test_cycling_threshold_history(self):
        """Test cycling threshold history DataFrame."""
        thresholds = [
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 1, 1),
                sport="cycling",
                ftp=250,
                ftp_source="test",
                is_user_override=False,
            ),
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 6, 1),
                sport="cycling",
                ftp=270,
                ftp_source="test",
                is_user_override=False,
            ),
        ]
        
        df = get_threshold_history_df(athlete_id=1, sport="cycling", thresholds=thresholds)
        
        assert len(df) == 2
        assert 'effective_date' in df.columns
        assert 'ftp' in df.columns
        assert 'source' in df.columns
        assert df['ftp'].tolist() == [250, 270]


class TestCalculateFTPProgression:
    """Test FTP progression analysis."""
    
    def test_ftp_progression_calculates_changes(self):
        """Test that FTP progression calculates watts and percentage changes."""
        thresholds = [
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 1, 1),
                sport="cycling",
                ftp=250,
                is_user_override=False,
            ),
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 4, 1),
                sport="cycling",
                ftp=265,
                is_user_override=False,
            ),
            AthleteThreshold(
                athlete_id=1,
                effective_date=date(2024, 7, 1),
                sport="cycling",
                ftp=270,
                is_user_override=False,
            ),
        ]
        
        df = calculate_ftp_progression(athlete_id=1, thresholds=thresholds)
        
        assert len(df) == 3
        assert 'ftp_change_watts' in df.columns
        assert 'ftp_change_pct' in df.columns
        assert df['ftp_change_watts'].iloc[1] == 15.0  # 265 - 250
        assert df['ftp_change_watts'].iloc[2] == 5.0   # 270 - 265


class TestValidateThresholdForTSS:
    """Test threshold validation for TSS calculation."""
    
    def test_none_threshold_raises_error(self):
        """Test that None threshold raises ThresholdNotFoundError."""
        with pytest.raises(ThresholdNotFoundError, match="No cycling threshold found"):
            validate_threshold_for_tss_calculation(
                threshold=None,
                sport="cycling",
                workout_date=date(2024, 1, 1)
            )
    
    def test_invalid_ftp_raises_error(self):
        """Test that zero or negative FTP raises error."""
        threshold = AthleteThreshold(
            athlete_id=1,
            effective_date=date(2024, 1, 1),
            sport="cycling",
            ftp=0,  # Invalid
            is_user_override=False,
        )
        
        with pytest.raises(ThresholdNotFoundError, match="invalid FTP"):
            validate_threshold_for_tss_calculation(
                threshold=threshold,
                sport="cycling",
                workout_date=date(2024, 6, 1)
            )
    
    def test_valid_threshold_passes(self):
        """Test that valid threshold does not raise error."""
        threshold = AthleteThreshold(
            athlete_id=1,
            effective_date=date(2024, 1, 1),
            sport="cycling",
            ftp=250,
            is_user_override=False,
        )
        
        # Should not raise
        validate_threshold_for_tss_calculation(
            threshold=threshold,
            sport="cycling",
            workout_date=date(2024, 6, 1)
        )

