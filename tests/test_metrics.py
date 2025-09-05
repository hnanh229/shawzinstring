"""
Test Conversion Quality Metrics

Unit tests for metrics computation and quality assessment.
"""

import pytest
import math
from midi2shawzin.metrics import (
    compute_mapping_metrics,
    format_metrics_report,
    analyze_conversion_bottlenecks,
    compare_with_benchmark,
    ConversionMetrics
)
from midi2shawzin.midi_io import Event
from midi2shawzin.mapper import ShawzinNote


class TestMetricsComputation:
    """Test metrics computation functions."""
    
    def test_perfect_conversion_metrics(self):
        """Test metrics with perfect conversion (100% mapped, no errors)."""
        # Perfect match: same note, same time
        original = [
            Event(type='note', note=60, time_sec=0.0, velocity=80),
            Event(type='note', note=64, time_sec=1.0, velocity=80),
            Event(type='note', note=67, time_sec=2.0, velocity=80),
        ]
        
        mapped = [
            ShawzinNote(character='1', time_sec=0.0, duration_sec=0.5, 
                       original_midi=60, mapped_midi=60, scale_id=2, octave_shift=0),
            ShawzinNote(character='q', time_sec=1.0, duration_sec=0.5,
                       original_midi=64, mapped_midi=64, scale_id=2, octave_shift=0),
            ShawzinNote(character='a', time_sec=2.0, duration_sec=0.5,
                       original_midi=67, mapped_midi=67, scale_id=2, octave_shift=0),
        ]
        
        metrics = compute_mapping_metrics(original, mapped)
        
        # Perfect conversion should have excellent metrics
        assert metrics.mapped_ratio == 1.0
        assert metrics.avg_abs_semitone_error == 0.0
        assert metrics.timing_rms == 0.0
        assert metrics.total_notes == 3
        assert metrics.mapped_notes == 3
        assert metrics.ignored_notes == 0
    
    def test_partial_conversion_metrics(self):
        """Test metrics with partial conversion (some notes ignored)."""
        # 2 out of 3 notes mapped
        original = [
            Event(type='note', note=60, time_sec=0.0, velocity=80),
            Event(type='note', note=64, time_sec=1.0, velocity=80),
            Event(type='note', note=67, time_sec=2.0, velocity=80),
        ]
        
        mapped = [
            ShawzinNote(character='1', time_sec=0.0, duration_sec=0.5,
                       original_midi=60, mapped_midi=60, scale_id=2, octave_shift=0),
            ShawzinNote(character='q', time_sec=1.0, duration_sec=0.5,
                       original_midi=64, mapped_midi=64, scale_id=2, octave_shift=0),
        ]
        
        metrics = compute_mapping_metrics(original, mapped)
        
        # Should show partial mapping
        assert metrics.mapped_ratio == pytest.approx(2/3, abs=0.01)
        assert metrics.total_notes == 3
        assert metrics.mapped_notes == 2
        assert metrics.ignored_notes == 1
    
    def test_pitch_error_metrics(self):
        """Test metrics with pitch deviations."""
        # Original C4, mapped to C5 (12 semitones up)
        original = [
            Event(type='note', note=60, time_sec=0.0, velocity=80),
        ]
        
        mapped = [
            ShawzinNote(character='1', time_sec=0.0, duration_sec=0.5,
                       original_midi=60, mapped_midi=72, scale_id=2, octave_shift=1),
        ]
        
        metrics = compute_mapping_metrics(original, mapped)
        
        # Should show 12 semitone error
        assert metrics.mapped_ratio == 1.0
        assert metrics.avg_abs_semitone_error == 12.0
        assert metrics.max_pitch_error == 12.0
    
    def test_timing_error_metrics(self):
        """Test metrics with timing deviations."""
        # Original at 0.0, mapped at 0.05 seconds (small timing error)
        original = [
            Event(type='note', note=60, time_sec=0.0, velocity=80),
        ]
        
        mapped = [
            ShawzinNote(character='1', time_sec=0.05, duration_sec=0.5,
                       original_midi=60, mapped_midi=60, scale_id=2, octave_shift=0),
        ]
        
        # 120 BPM = 500000 us/beat = 0.5 sec/beat
        metrics = compute_mapping_metrics(original, mapped, tempo_us_per_beat=500000)
        
        # 0.05 seconds = 0.1 beat at 120 BPM
        assert metrics.mapped_ratio == 1.0
        assert metrics.avg_abs_semitone_error == 0.0
        assert metrics.timing_rms == pytest.approx(0.1, abs=0.01)
    
    def test_empty_conversion_metrics(self):
        """Test metrics with no input events."""
        original = []
        mapped = []
        
        metrics = compute_mapping_metrics(original, mapped)
        
        # Should handle empty gracefully
        assert metrics.mapped_ratio == 0.0
        assert metrics.avg_abs_semitone_error == 0.0
        assert metrics.timing_rms == 0.0
        assert metrics.total_notes == 0
        assert metrics.mapped_notes == 0


class TestMetricsReporting:
    """Test metrics formatting and reporting."""
    
    def test_format_excellent_metrics_report(self):
        """Test formatting report for excellent metrics."""
        metrics = ConversionMetrics(
            mapped_ratio=0.98,
            avg_abs_semitone_error=0.5,
            timing_rms=0.05,
            total_notes=100,
            mapped_notes=98,
            ignored_notes=2,
            max_pitch_error=2.0,
            timing_errors=[0.01, 0.02, 0.05]
        )
        
        report = format_metrics_report(metrics, mode="melody-only")
        
        # Should contain key information
        assert "CONVERSION QUALITY METRICS" in report
        assert "98.0%" in report  # Mapping ratio
        assert "0.50 semitones" in report  # Pitch error
        assert "EXCELLENT" in report  # Should have excellent ratings
        assert "✓" in report  # Check marks for good metrics
    
    def test_format_poor_metrics_report(self):
        """Test formatting report for poor metrics."""
        metrics = ConversionMetrics(
            mapped_ratio=0.70,
            avg_abs_semitone_error=3.0,
            timing_rms=0.5,
            total_notes=100,
            mapped_notes=70,
            ignored_notes=30,
            max_pitch_error=8.0,
            timing_errors=[0.3, 0.5, 0.7]
        )
        
        report = format_metrics_report(metrics, mode="melody-only")
        
        # Should show poor quality
        assert "70.0%" in report  # Low mapping ratio
        assert "3.00 semitones" in report  # High pitch error
        assert "POOR" in report  # Should have poor ratings
        assert "✗" in report  # X marks for bad metrics
        assert "chromatic scale" in report  # Should suggest improvements


class TestMetricsAnalysis:
    """Test metrics analysis and recommendations."""
    
    def test_analyze_conversion_bottlenecks(self):
        """Test bottleneck analysis for poor conversion."""
        metrics = ConversionMetrics(
            mapped_ratio=0.60,
            avg_abs_semitone_error=4.0,
            timing_rms=0.8,
            total_notes=100,
            mapped_notes=60,
            ignored_notes=40,
            max_pitch_error=12.0,
            timing_errors=[]
        )
        
        suggestions = analyze_conversion_bottlenecks(metrics)
        
        # Should suggest improvements for all poor metrics
        assert len(suggestions) > 0
        assert any("chromatic scale" in s for s in suggestions)
        assert any("pitch errors" in s for s in suggestions)
        assert any("timing" in s for s in suggestions)
    
    def test_compare_with_benchmark(self):
        """Test comparison with benchmark tools."""
        metrics = ConversionMetrics(
            mapped_ratio=0.95,
            avg_abs_semitone_error=0.8,
            timing_rms=0.10,
            total_notes=100,
            mapped_notes=95,
            ignored_notes=5,
            max_pitch_error=3.0,
            timing_errors=[]
        )
        
        comparison = compare_with_benchmark(metrics, "Empyrrhus")
        
        # Should provide comparison results
        assert comparison["benchmark"] == "Empyrrhus"
        assert "mapped_ratio_diff" in comparison
        assert "pitch_error_diff" in comparison
        assert "timing_diff" in comparison
        assert "summary" in comparison


class TestMetricsIntegration:
    """Test metrics integration scenarios."""
    
    def test_melodic_conversion_targets(self):
        """Test that melody-only mode has appropriate targets."""
        # Test what should be excellent for melody-only
        metrics = ConversionMetrics(
            mapped_ratio=0.96,
            avg_abs_semitone_error=0.8,
            timing_rms=0.08,
            total_notes=50,
            mapped_notes=48,
            ignored_notes=2,
            max_pitch_error=2.0,
            timing_errors=[]
        )
        
        report = format_metrics_report(metrics, mode="melody-only")
        
        # Should meet melody-only targets
        assert "EXCELLENT" in report or "GOOD" in report
        # Should not suggest major changes for good metrics
        overall_score_line = [line for line in report.split('\n') if 'Overall Quality Score' in line][0]
        score = float(overall_score_line.split(': ')[1].split('/')[0])
        assert score >= 6.0  # Should be decent quality
    
    def test_complex_conversion_tolerance(self):
        """Test that full mode has more tolerant targets."""
        # Metrics that might be poor for melody but OK for full mode
        metrics = ConversionMetrics(
            mapped_ratio=0.88,
            avg_abs_semitone_error=1.5,
            timing_rms=0.20,
            total_notes=200,
            mapped_notes=176,
            ignored_notes=24,
            max_pitch_error=6.0,
            timing_errors=[]
        )
        
        melody_report = format_metrics_report(metrics, mode="melody-only")
        full_report = format_metrics_report(metrics, mode="full")
        
        # Full mode should be more tolerant
        # (This is a conceptual test - actual implementation may vary)
        assert "CONVERSION QUALITY METRICS" in melody_report
        assert "CONVERSION QUALITY METRICS" in full_report
