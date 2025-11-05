"""Unit tests for FIT file parsing."""
from pathlib import Path

import pytest

from app.services.file_parser import parse_fit_file, FileParseError
from app.schemas.training import WorkoutExecuted, Sample


class TestFitFileParser:
    """Tests for FIT file parsing functionality."""
    
    def test_parse_real_fit_gz_file_from_upload_folder(self):
        """Test parsing a real gzipped FIT file from UploadFiles folder."""
        fit_file_path = Path(__file__).parent.parent / "UploadFiles" / "Purple Patch- Nancy & Frank Duet.fit.gz"
        
        # Skip test if file doesn't exist
        if not fit_file_path.exists():
            pytest.skip(f"Test FIT file not found: {fit_file_path}")
        
        # Parse the file with FTP for TSS calculation
        workout, samples = parse_fit_file(
            str(fit_file_path),
            athlete_id=1,
            ftp=250  # Example FTP
        )
        
        # Verify workout metadata
        assert isinstance(workout, WorkoutExecuted)
        assert workout.athlete_id == 1
        assert workout.source == 'file'
        assert workout.duration_s > 0
        assert workout.sport in ['cycling', 'running', 'swimming', 'unknown']
        
        # Verify summary metrics exist
        assert 'avg_power' in workout.summary_json or 'avg_hr' in workout.summary_json
        assert 'distance_m' in workout.summary_json
        
        # Verify samples were extracted
        assert isinstance(samples, list)
        assert len(samples) > 0
        assert all(isinstance(s, Sample) for s in samples)
        
        # Verify first sample
        first_sample = samples[0]
        assert first_sample.workout_id == 1
        assert first_sample.t_s == 0
        
        # Print summary for manual inspection
        print(f"\n📊 Workout Summary:")
        print(f"  Duration: {workout.duration_s}s ({workout.duration_s / 60:.1f} min)")
        print(f"  Sport: {workout.sport}")
        print(f"  Samples: {len(samples)}")
        if 'avg_power' in workout.summary_json:
            print(f"  Avg Power: {workout.summary_json['avg_power']:.1f}W")
        if 'np' in workout.summary_json:
            print(f"  Normalized Power: {workout.summary_json['np']:.1f}W")
        if 'if' in workout.summary_json:
            print(f"  Intensity Factor: {workout.summary_json['if']:.3f}")
        if 'tss' in workout.summary_json:
            print(f"  TSS: {workout.summary_json['tss']:.1f}")
        if 'avg_hr' in workout.summary_json:
            print(f"  Avg HR: {workout.summary_json['avg_hr']:.0f} bpm")
        if 'distance_m' in workout.summary_json:
            print(f"  Distance: {workout.summary_json['distance_m'] / 1000:.2f} km")
    
    def test_parse_fit_file_missing_file_raises_error(self):
        """Test that parsing non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_fit_file("nonexistent.fit", athlete_id=1)
    
    def test_parse_fit_file_with_ftp_calculates_metrics(self):
        """Test that providing FTP enables TSS calculation."""
        fit_file_path = Path(__file__).parent.parent / "UploadFiles" / "Purple Patch- Nancy & Frank Duet.fit.gz"
        
        if not fit_file_path.exists():
            pytest.skip("Test FIT file not found")
        
        # Parse with FTP
        workout_with_ftp, _ = parse_fit_file(str(fit_file_path), athlete_id=1, ftp=250)
        
        # Check that power metrics were calculated if power data exists
        if 'avg_power' in workout_with_ftp.summary_json and workout_with_ftp.summary_json['avg_power'] > 0:
            assert 'np' in workout_with_ftp.summary_json
            assert 'if' in workout_with_ftp.summary_json
            assert 'vi' in workout_with_ftp.summary_json
            assert 'tss' in workout_with_ftp.summary_json
            assert workout_with_ftp.summary_json['tss'] > 0
    
    def test_parse_fit_file_without_ftp_still_works(self):
        """Test that parsing works without FTP (no TSS calculation)."""
        fit_file_path = Path(__file__).parent.parent / "UploadFiles" / "Purple Patch- Nancy & Frank Duet.fit.gz"
        
        if not fit_file_path.exists():
            pytest.skip("Test FIT file not found")
        
        # Parse without FTP
        workout, samples = parse_fit_file(str(fit_file_path), athlete_id=1, ftp=None)
        
        # Should still extract basic data
        assert workout.duration_s > 0
        assert len(samples) > 0
        assert 'distance_m' in workout.summary_json
    
    def test_samples_have_correct_structure(self):
        """Test that extracted samples have expected data fields."""
        fit_file_path = Path(__file__).parent.parent / "UploadFiles" / "Purple Patch- Nancy & Frank Duet.fit.gz"
        
        if not fit_file_path.exists():
            pytest.skip("Test FIT file not found")
        
        _, samples = parse_fit_file(str(fit_file_path), athlete_id=1)
        
        # Check that samples have reasonable data
        sample_with_data = None
        for sample in samples[:100]:  # Check first 100 samples
            if sample.power_w or sample.hr_bpm or sample.lat:
                sample_with_data = sample
                break
        
        if sample_with_data:
            # At least one type of data should be present
            has_data = (
                sample_with_data.power_w is not None or
                sample_with_data.hr_bpm is not None or
                sample_with_data.lat is not None or
                sample_with_data.pace_mps is not None
            )
            assert has_data, "Samples should contain at least one data field"
    
    def test_samples_are_time_ordered(self):
        """Test that samples are in correct time order."""
        fit_file_path = Path(__file__).parent.parent / "UploadFiles" / "Purple Patch- Nancy & Frank Duet.fit.gz"
        
        if not fit_file_path.exists():
            pytest.skip("Test FIT file not found")
        
        _, samples = parse_fit_file(str(fit_file_path), athlete_id=1)
        
        # Verify samples are time-ordered
        for i in range(1, min(len(samples), 100)):
            assert samples[i].t_s >= samples[i-1].t_s, "Samples should be in time order"
    
    def test_workout_duration_matches_last_sample(self):
        """Test that workout duration matches the last sample timestamp."""
        fit_file_path = Path(__file__).parent.parent / "UploadFiles" / "Purple Patch- Nancy & Frank Duet.fit.gz"
        
        if not fit_file_path.exists():
            pytest.skip("Test FIT file not found")
        
        workout, samples = parse_fit_file(str(fit_file_path), athlete_id=1)
        
        if samples:
            # Duration should approximately match last sample time
            # Allow some tolerance for rounding
            assert abs(workout.duration_s - samples[-1].t_s) <= 1


class TestFitFileParserEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_parse_fit_file_handles_gz_extension_correctly(self):
        """Test that .fit.gz extension is properly detected and handled."""
        fit_file_path = Path(__file__).parent.parent / "UploadFiles" / "Purple Patch- Nancy & Frank Duet.fit.gz"
        
        if not fit_file_path.exists():
            pytest.skip("Test FIT file not found")
        
        # Should successfully parse gzipped file
        workout, samples = parse_fit_file(str(fit_file_path), athlete_id=1)
        assert workout is not None
        assert len(samples) > 0
    
    def test_parse_invalid_file_raises_parse_error(self):
        """Test that parsing invalid file raises FileParseError."""
        # Create a temporary invalid file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fit', delete=False) as f:
            f.write("This is not a valid FIT file")
            temp_path = f.name
        
        try:
            with pytest.raises(FileParseError):
                parse_fit_file(temp_path, athlete_id=1)
        finally:
            Path(temp_path).unlink()

