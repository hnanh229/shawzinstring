"""
Test Quantization Functions

Unit tests for note timing quantization.
"""

import pytest
import random
from midi2shawzin.quantize import (
    Quantizer,
    QuantizeSettings,
    seconds_to_beats,
    beats_to_seconds,
    quantize_beat_to_grid,
    add_humanization,
    quantize_events,
    detect_tempo_from_events,
    quantize_to_sixteenth_notes,
    quantize_to_eighth_notes,
    quantize_with_humanization
)
from midi2shawzin.midi_io import Event


class TestQuantizer:
    """Test quantization functionality."""
    
    def test_quantize_settings_defaults(self):
        """Test default quantization settings."""
        settings = QuantizeSettings()
        assert settings.subdivision == 16
        assert settings.mode == 'nearest'
        assert settings.humanize_ms is None
        assert settings.time_signature == (4, 4)
        assert settings.preserve_timing is True
        
    def test_quantizer_initialization(self):
        """Test quantizer initialization."""
        quantizer = Quantizer()
        assert quantizer.settings is not None
        assert quantizer.last_tempo == 120.0
        
    def test_seconds_to_beats_conversion(self):
        """Test seconds to beats conversion."""
        # 120 BPM = 500,000 us per beat
        tempo_us_per_beat = 500_000
        
        # 1 second at 120 BPM = 2 beats (since 1 beat = 0.5 seconds)
        beats = seconds_to_beats(1.0, tempo_us_per_beat)
        assert beats == pytest.approx(2.0)
        
        # 0.5 seconds = 1 beat
        beats = seconds_to_beats(0.5, tempo_us_per_beat)
        assert beats == pytest.approx(1.0)
        
    def test_beats_to_seconds_conversion(self):
        """Test beats to seconds conversion."""
        # 120 BPM = 500,000 us per beat
        tempo_us_per_beat = 500_000
        
        # 2 beats at 120 BPM = 1 second
        seconds = beats_to_seconds(2.0, tempo_us_per_beat)
        assert seconds == pytest.approx(1.0)
        
        # 1 beat = 0.5 seconds
        seconds = beats_to_seconds(1.0, tempo_us_per_beat)
        assert seconds == pytest.approx(0.5)
        
    def test_quantize_beat_to_grid_nearest(self):
        """Test beat quantization to grid with nearest mode."""
        # For subdivision=16 in 4/4: 4 beats / 16 subdivisions = 0.25 beats per subdivision
        
        # Test exact grid positions
        assert quantize_beat_to_grid(0.0, 16, 'nearest') == pytest.approx(0.0)
        assert quantize_beat_to_grid(0.25, 16, 'nearest') == pytest.approx(0.25)
        assert quantize_beat_to_grid(0.5, 16, 'nearest') == pytest.approx(0.5)
        
        # Test between grid positions (should round to nearest)
        assert quantize_beat_to_grid(0.1, 16, 'nearest') == pytest.approx(0.0)  # Closer to 0
        assert quantize_beat_to_grid(0.15, 16, 'nearest') == pytest.approx(0.25)  # Closer to 0.25
        assert quantize_beat_to_grid(0.4, 16, 'nearest') == pytest.approx(0.5)  # Closer to 0.5
        
    def test_quantize_beat_to_grid_floor(self):
        """Test beat quantization to grid with floor mode."""
        # Test floor mode always rounds down
        assert quantize_beat_to_grid(0.1, 16, 'floor') == pytest.approx(0.0)
        assert quantize_beat_to_grid(0.24, 16, 'floor') == pytest.approx(0.0)
        assert quantize_beat_to_grid(0.26, 16, 'floor') == pytest.approx(0.25)
        assert quantize_beat_to_grid(0.49, 16, 'floor') == pytest.approx(0.25)
        
    def test_add_humanization(self):
        """Test humanization jitter."""
        # Without humanization
        assert add_humanization(1.0, None) == 1.0
        assert add_humanization(1.0, 0.0) == 1.0
        
        # With humanization - check range
        random.seed(42)  # For reproducible tests
        humanized_times = [add_humanization(1.0, 10.0) for _ in range(100)]
        
        # All times should be within expected range (1.0 ± 0.01 seconds)
        for time in humanized_times:
            assert 0.99 <= time <= 1.01
            
        # Should add variety (not all the same)
        assert len(set(round(t, 4) for t in humanized_times)) > 1
        
    def test_quantize_simple_notes(self):
        """Test quantization of simple note sequence."""
        # Create events at slightly off-grid times
        events = [
            Event(type='note', note=60, time_sec=0.123, delta_sec=0.123, velocity=80),    # Near 0.125 (1/8 at 120bpm)
            Event(type='note', note=62, time_sec=0.247, delta_sec=0.124, velocity=80),    # Near 0.25 (1/4)
            Event(type='note', note=64, time_sec=0.501, delta_sec=0.254, velocity=80),    # Near 0.5 (1/2)
        ]
        
        # 120 BPM = 500,000 us per beat
        tempo_us_per_beat = 500_000
        ticks_per_beat = 480
        
        settings = QuantizeSettings(subdivision=16, mode='nearest')
        quantized = quantize_events(events, ticks_per_beat, tempo_us_per_beat, settings)
        
        # At 120 BPM, 1/16 notes are 0.125 seconds apart
        # Expected quantized times: 0.125, 0.25, 0.5
        assert quantized[0].time_sec == pytest.approx(0.125, abs=1e-6)
        assert quantized[1].time_sec == pytest.approx(0.25, abs=1e-6)
        assert quantized[2].time_sec == pytest.approx(0.5, abs=1e-6)
        
        # Check delta times are recalculated
        assert quantized[0].delta_sec == pytest.approx(0.125, abs=1e-6)
        assert quantized[1].delta_sec == pytest.approx(0.125, abs=1e-6)  # 0.25 - 0.125
        assert quantized[2].delta_sec == pytest.approx(0.25, abs=1e-6)   # 0.5 - 0.25
        
    def test_quantize_with_floor_mode(self):
        """Test quantization with floor mode."""
        events = [
            Event(type='note', note=60, time_sec=0.123, delta_sec=0.123, velocity=80),    # Should floor to 0.0
            Event(type='note', note=62, time_sec=0.247, delta_sec=0.124, velocity=80),    # Should floor to 0.125
        ]
        
        tempo_us_per_beat = 500_000  # 120 BPM
        ticks_per_beat = 480
        
        settings = QuantizeSettings(subdivision=16, mode='floor')
        quantized = quantize_events(events, ticks_per_beat, tempo_us_per_beat, settings)
        
        # Floor mode: 0.123 -> 0.0, 0.247 -> 0.125
        assert quantized[0].time_sec == pytest.approx(0.0, abs=1e-6)
        assert quantized[1].time_sec == pytest.approx(0.125, abs=1e-6)
        
    def test_tempo_detection(self):
        """Test automatic tempo detection from note events."""
        # Create events at 120 BPM (0.5 seconds per beat)
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=62, time_sec=0.5, delta_sec=0.5, velocity=80),
            Event(type='note', note=64, time_sec=1.0, delta_sec=0.5, velocity=80),
            Event(type='note', note=65, time_sec=1.5, delta_sec=0.5, velocity=80),
        ]
        
        detected_tempo = detect_tempo_from_events(events)
        assert detected_tempo == pytest.approx(120.0, abs=1.0)
        
        # Test 90 BPM (0.667 seconds per beat)
        events_90bpm = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=62, time_sec=0.667, delta_sec=0.667, velocity=80),
            Event(type='note', note=64, time_sec=1.333, delta_sec=0.666, velocity=80),
        ]
        
        detected_tempo = detect_tempo_from_events(events_90bpm)
        assert detected_tempo == pytest.approx(90.0, abs=2.0)
        
    def test_quantizer_interface(self):
        """Test Quantizer class interface."""
        quantizer = Quantizer()
        
        events = [
            Event(type='note', note=60, time_sec=0.123, delta_sec=0.123, velocity=80),
            Event(type='note', note=62, time_sec=0.247, delta_sec=0.124, velocity=80),
        ]
        
        quantized = quantizer.quantize(events, tempo_bpm=120.0)
        
        assert len(quantized) == 2
        assert quantized[0].time_sec == pytest.approx(0.125, abs=1e-6)
        assert quantized[1].time_sec == pytest.approx(0.25, abs=1e-6)
        assert quantizer.last_tempo == 120.0
        
    def test_get_grid_positions(self):
        """Test grid position generation."""
        settings = QuantizeSettings(subdivision=16)
        quantizer = Quantizer(settings)
        
        positions = quantizer.get_grid_positions(duration_beats=1.0)
        
        # For subdivision=16, should have positions every 0.25 beats
        expected_positions = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        assert len(positions) == len(expected_positions)
        for actual, expected in zip(positions, expected_positions):
            assert actual == pytest.approx(expected, abs=1e-6)
            
    def test_convenience_functions(self):
        """Test convenience quantization functions."""
        events = [
            Event(type='note', note=60, time_sec=0.123, delta_sec=0.123, velocity=80),
            Event(type='note', note=62, time_sec=0.247, delta_sec=0.124, velocity=80),
        ]
        
        # Test sixteenth note quantization
        quantized_16th = quantize_to_sixteenth_notes(events, tempo_bpm=120.0)
        assert quantized_16th[0].time_sec == pytest.approx(0.125, abs=1e-6)
        
        # Test eighth note quantization (subdivision=8 means 1/8 note grid)
        # At 120 BPM, 1/8 notes are 0.25 seconds apart: 0.0, 0.25, 0.5, etc.
        # 0.123 is closer to 0.0, 0.247 is closer to 0.25
        quantized_8th = quantize_to_eighth_notes(events, tempo_bpm=120.0)
        assert quantized_8th[0].time_sec == pytest.approx(0.0, abs=1e-6)   # 0.123 -> 0.0
        assert quantized_8th[1].time_sec == pytest.approx(0.25, abs=1e-6)  # 0.247 -> 0.25
        
        # Test humanized quantization
        random.seed(42)
        quantized_human = quantize_with_humanization(events, tempo_bpm=120.0, jitter_ms=5.0)
        # Should be close to quantized position but with small variation
        assert abs(quantized_human[0].time_sec - 0.125) <= 0.01  # Within 10ms
        
    def test_empty_events_handling(self):
        """Test handling of empty event lists."""
        assert quantize_events([], 480, 500_000) == []
        
        quantizer = Quantizer()
        assert quantizer.quantize([]) == []
        
    def test_single_event_tempo_detection(self):
        """Test tempo detection with insufficient events."""
        events = [Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80)]
        
        detected_tempo = detect_tempo_from_events(events)
        assert detected_tempo == 120.0  # Should return default
        
    def test_preserve_timing_disabled(self):
        """Test quantization with preserve_timing disabled."""
        events = [
            Event(type='note', note=60, time_sec=0.123, delta_sec=0.123, velocity=80),
            Event(type='note', note=62, time_sec=0.247, delta_sec=0.124, velocity=80),
        ]
        
        settings = QuantizeSettings(subdivision=16, preserve_timing=False)
        quantized = quantize_events(events, 480, 500_000, settings)
        
        # Delta times should be preserved from original (not recalculated)
        assert quantized[0].delta_sec == pytest.approx(0.123, abs=1e-6)
        assert quantized[1].delta_sec == pytest.approx(0.124, abs=1e-6)
