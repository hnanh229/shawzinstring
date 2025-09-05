"""
Test Key Detection Functions

Unit tests for musical key detection algorithms.
"""

import pytest
from collections import Counter
from midi2shawzin.midi_io import Event
from midi2shawzin.key_detection import (
    KeyDetector,
    detect_key_from_events,
    build_pitch_class_histogram,
    get_scale_template,
    score_key,
    detect_best_scale,
    analyze_key_confidence,
    get_scale_notes,
    SCALE_TEMPLATES,
    SCALE_NAMES
)


class TestKeyDetection:
    """Test cases for key detection functionality."""
    
    def test_key_detector_initialization(self):
        """Test KeyDetector initialization."""
        detector = KeyDetector()
        assert detector.pitch_class_histogram == Counter()
        assert detector.last_analysis is None
    
    def test_build_pitch_class_histogram(self):
        """Test pitch class histogram building."""
        # Create test events with known pitches
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=1.0, velocity=80),  # C
            Event(type='note', note=62, time_sec=1.0, delta_sec=1.0, velocity=80),  # D
            Event(type='note', note=64, time_sec=2.0, delta_sec=1.0, velocity=80),  # E
            Event(type='note', note=60, time_sec=3.0, delta_sec=1.0, velocity=80),  # C again
        ]
        
        histogram = build_pitch_class_histogram(events)
        
        # Check histogram properties
        assert len(histogram) == 12
        assert histogram[0] > histogram[2]  # C should have more weight than D (appears twice)
        assert histogram[2] > 0  # D should have some weight
        assert histogram[4] > 0  # E should have some weight
        assert sum(histogram) == pytest.approx(1.0, abs=1e-6)  # Should be normalized
    
    def test_get_scale_template(self):
        """Test scale template generation."""
        # Test C major scale
        c_major = get_scale_template(2, 0)  # Scale 2 is major, root 0 is C
        expected = {0, 2, 4, 5, 7, 9, 11}  # C major notes
        assert c_major == expected
        
        # Test D major scale (transposed)
        d_major = get_scale_template(2, 2)  # Scale 2 is major, root 2 is D
        expected = {2, 4, 6, 7, 9, 11, 1}  # D major notes
        assert d_major == expected
    
    def test_score_key(self):
        """Test key scoring function."""
        # Create histogram with strong C major pattern
        histogram = [0.3, 0.0, 0.2, 0.0, 0.2, 0.1, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0]
        
        # Test against C major template
        c_major_template = {0, 2, 4, 5, 7, 9, 11}
        score = score_key(histogram, c_major_template)
        
        assert score > 0.5  # Should have good score
        assert isinstance(score, float)
    
    def test_detect_c_major_scale(self):
        """Test detection of C major scale."""
        # Create C major scale events
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.5, velocity=80),  # C
            Event(type='note', note=62, time_sec=0.5, delta_sec=0.5, velocity=80),  # D
            Event(type='note', note=64, time_sec=1.0, delta_sec=0.5, velocity=80),  # E
            Event(type='note', note=65, time_sec=1.5, delta_sec=0.5, velocity=80),  # F
            Event(type='note', note=67, time_sec=2.0, delta_sec=0.5, velocity=80),  # G
            Event(type='note', note=69, time_sec=2.5, delta_sec=0.5, velocity=80),  # A
            Event(type='note', note=71, time_sec=3.0, delta_sec=0.5, velocity=80),  # B
            Event(type='note', note=72, time_sec=3.5, delta_sec=0.5, velocity=80),  # C
        ]
        
        root, scale_id, score = detect_best_scale(events)
        
        # Should detect C (root=0) and major scale (scale_id=2)
        assert root == 0  # C
        assert scale_id == 2  # Major (heptatonic)
        assert score > 0.8  # High confidence

    def test_detect_c_major_melody_synthetic(self):
        """Test detection with synthetic C major melody (C4,E4,G4,C5) using mido-style input."""
        # Create C major chord/melody as specified: C4, E4, G4, C5
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.5, velocity=80),  # C4
            Event(type='note', note=64, time_sec=0.5, delta_sec=0.5, velocity=80),  # E4
            Event(type='note', note=67, time_sec=1.0, delta_sec=0.5, velocity=80),  # G4
            Event(type='note', note=72, time_sec=1.5, delta_sec=0.5, velocity=80),  # C5
        ]
        
        root, scale_id, score = detect_best_scale(events)
        
        # Should detect C (root=0) and major scale
        assert root == 0  # C
        # C major chord fits best with pentatonic major (scale 7) due to limited notes
        assert scale_id in [2, 7]  # Major scale or pentatonic major
        assert score > 0.5  # Should have reasonable confidence
    
    def test_detect_a_minor_scale(self):
        """Test detection of A minor scale."""
        # Create A minor scale events (relative minor of C major)
        events = [
            Event(type='note', note=57, time_sec=0.0, delta_sec=0.5, velocity=80),  # A
            Event(type='note', note=59, time_sec=0.5, delta_sec=0.5, velocity=80),  # B
            Event(type='note', note=60, time_sec=1.0, delta_sec=0.5, velocity=80),  # C
            Event(type='note', note=62, time_sec=1.5, delta_sec=0.5, velocity=80),  # D
            Event(type='note', note=64, time_sec=2.0, delta_sec=0.5, velocity=80),  # E
            Event(type='note', note=65, time_sec=2.5, delta_sec=0.5, velocity=80),  # F
            Event(type='note', note=67, time_sec=3.0, delta_sec=0.5, velocity=80),  # G
        ]
        
        root, scale_id, score = detect_best_scale(events)
        
        # Should detect A (root=9) and natural minor (scale_id=4)
        assert root == 9  # A
        assert scale_id == 4  # Natural minor
        assert score > 0.7  # Good confidence
    
    def test_detect_chromatic_scale(self):
        """Test detection of chromatic scale."""
        # Create chromatic scale events
        events = []
        for i in range(12):
            events.append(Event(
                type='note', 
                note=60 + i, 
                time_sec=i * 0.2, 
                delta_sec=0.2, 
                velocity=80
            ))
        
        root, scale_id, score = detect_best_scale(events)
        
        # Should detect chromatic scale (scale_id=3)
        assert scale_id == 3  # Chromatic
        assert score > 0.8  # High confidence
    
    def test_detect_pentatonic_scale(self):
        """Test detection of pentatonic scale."""
        # Create C major pentatonic scale events - start and end on C for clarity
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.5, velocity=80),  # C
            Event(type='note', note=62, time_sec=0.5, delta_sec=0.5, velocity=80),  # D
            Event(type='note', note=64, time_sec=1.0, delta_sec=0.5, velocity=80),  # E
            Event(type='note', note=67, time_sec=1.5, delta_sec=0.5, velocity=80),  # G
            Event(type='note', note=69, time_sec=2.0, delta_sec=0.5, velocity=80),  # A
            Event(type='note', note=72, time_sec=2.5, delta_sec=0.5, velocity=80),  # C (octave)
        ]
        
        root, scale_id, score = detect_best_scale(events)
        
        # Should detect C (root=0) and pentatonic major (scale_id=7)
        assert root == 0  # C
        assert scale_id == 7  # Pentatonic Major
        assert score > 0.8  # Good confidence
    
    def test_analyze_key_confidence(self):
        """Test confidence analysis with multiple candidates."""
        # Create C major scale events
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.5, velocity=80),  # C
            Event(type='note', note=62, time_sec=0.5, delta_sec=0.5, velocity=80),  # D
            Event(type='note', note=64, time_sec=1.0, delta_sec=0.5, velocity=80),  # E
            Event(type='note', note=65, time_sec=1.5, delta_sec=0.5, velocity=80),  # F
            Event(type='note', note=67, time_sec=2.0, delta_sec=0.5, velocity=80),  # G
        ]
        
        candidates = analyze_key_confidence(events, top_n=3)
        
        assert len(candidates) == 3
        assert all(len(candidate) == 4 for candidate in candidates)  # (root, scale_id, score, description)
        assert candidates[0][2] >= candidates[1][2] >= candidates[2][2]  # Scores should be sorted
    
    def test_get_scale_notes(self):
        """Test scale note generation."""
        # Test C major scale notes
        notes = get_scale_notes(2, 0, octave=4)  # C major starting at C4
        
        assert 60 in notes  # C4
        assert 62 in notes  # D4
        assert 64 in notes  # E4
        assert len(notes) >= 7  # Should have at least one octave
    
    def test_key_detector_interface(self):
        """Test KeyDetector interface methods."""
        detector = KeyDetector()
        
        # Create simple C major events
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.5, velocity=80),  # C
            Event(type='note', note=64, time_sec=0.5, delta_sec=0.5, velocity=80),  # E
            Event(type='note', note=67, time_sec=1.0, delta_sec=0.5, velocity=80),  # G
        ]
        
        key_name, scale_name = detector.detect_key(events)
        
        assert isinstance(key_name, str)
        assert isinstance(scale_name, str)
        assert detector.get_confidence() > 0
    
    def test_legacy_compatibility(self):
        """Test legacy function interface."""
        # Create simple events
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.5, velocity=80),  # C
            Event(type='note', note=64, time_sec=0.5, delta_sec=0.5, velocity=80),  # E
        ]
        
        key_name, scale_name = detect_key_from_events(events)
        
        assert isinstance(key_name, str)
        assert isinstance(scale_name, str)
