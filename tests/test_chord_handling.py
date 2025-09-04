"""
Test Chord Handling Functions

Unit tests for chord processing, reduction, and arpeggiation.
"""

import pytest
from midi2shawzin.chord_handling import (
    ChordPolicy,
    ChordProcessor,
    group_simultaneous,
    analyze_chord_structure,
    reduce_chord,
    create_arpeggio_events,
    map_chord_to_shawzin,
    process_chord_events,
    process_all_chords,
    reduce_chords_to_melody_bass,
    arpeggiate_all_chords,
    conservative_chord_reduction
)
from midi2shawzin.midi_io import Event


class TestChordHandling:
    """Test chord handling functionality."""
    
    def test_chord_policy_defaults(self):
        """Test default chord policy settings."""
        policy = ChordPolicy()
        assert policy.max_chord_notes == 3
        assert policy.reduction_mode == 'reduce'
        assert policy.arpeggio_spread_ms == 20.0
        assert policy.prefer_melody is True
        assert policy.preserve_bass is True
        assert policy.simultaneity_threshold == 1e-3
    
    def test_group_simultaneous_basic(self):
        """Test basic simultaneous event grouping."""
        # Create events with some simultaneous
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=64, time_sec=0.0, delta_sec=0.0, velocity=80),   # Simultaneous with first
            Event(type='note', note=67, time_sec=0.0, delta_sec=0.0, velocity=80),   # Simultaneous with first
            Event(type='note', note=72, time_sec=0.5, delta_sec=0.5, velocity=80),   # Different time
        ]
        
        groups = group_simultaneous(events, eps=1e-3)
        
        assert len(groups) == 2
        assert len(groups[0]) == 3  # First group has 3 simultaneous notes
        assert len(groups[1]) == 1  # Second group has 1 note
        assert groups[0][0].note == 60
        assert groups[0][1].note == 64
        assert groups[0][2].note == 67
        assert groups[1][0].note == 72
    
    def test_group_simultaneous_with_epsilon(self):
        """Test grouping with different epsilon values."""
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=64, time_sec=0.002, delta_sec=0.002, velocity=80),  # 2ms later
            Event(type='note', note=67, time_sec=0.010, delta_sec=0.008, velocity=80),  # 10ms later
        ]
        
        # With tight epsilon (1ms), should create separate groups
        groups_tight = group_simultaneous(events, eps=0.001)
        assert len(groups_tight) == 3
        
        # With loose epsilon (20ms), should group all together
        groups_loose = group_simultaneous(events, eps=0.020)
        assert len(groups_loose) == 1
        assert len(groups_loose[0]) == 3
    
    def test_analyze_chord_structure(self):
        """Test chord structure analysis."""
        # C major triad: C-E-G
        notes = [60, 64, 67]  # C4, E4, G4
        analysis = analyze_chord_structure(notes)
        
        assert analysis['bass'] == 60    # Lowest note
        assert analysis['melody'] == 67  # Highest note
        assert analysis['root'] == 60    # Root (bass)
        assert 'third' in analysis       # Should find third
        assert 'fifth' in analysis       # Should find fifth
        
        # Check intervals
        assert (analysis['third'] - analysis['root']) % 12 == 4   # Major third
        assert (analysis['fifth'] - analysis['root']) % 12 == 7   # Perfect fifth
    
    def test_analyze_chord_structure_single_note(self):
        """Test chord analysis with single note."""
        notes = [60]
        analysis = analyze_chord_structure(notes)
        
        assert analysis['bass'] == 60
        assert analysis['melody'] == 60
        assert analysis['root'] == 60
        assert 'third' not in analysis
        assert 'fifth' not in analysis
    
    def test_reduce_chord_basic(self):
        """Test basic chord reduction."""
        # 4-note chord that should be reduced to 3
        notes = [60, 64, 67, 72]  # C-E-G-C (octave)
        
        reduced = reduce_chord(notes, policy='reduce', max_notes=3)
        
        assert len(reduced) <= 3
        assert 60 in reduced   # Should keep bass
        assert 72 in reduced   # Should keep melody
        
        # Check that it's sorted
        assert reduced == sorted(reduced)
    
    def test_reduce_chord_small_chord(self):
        """Test reduction of chord that's already small enough."""
        notes = [60, 64, 67]  # 3-note chord
        
        reduced = reduce_chord(notes, policy='reduce', max_notes=3)
        
        assert reduced == notes  # Should be unchanged
    
    def test_reduce_chord_arpeggiate_policy(self):
        """Test that arpeggiate policy returns all notes."""
        notes = [60, 64, 67, 72, 76]  # 5-note chord
        
        reduced = reduce_chord(notes, policy='arpeggiate', max_notes=3)
        
        assert len(reduced) == 5  # Should return all notes
        assert reduced == sorted(notes)
    
    def test_create_arpeggio_events(self):
        """Test arpeggio creation from simultaneous events."""
        # Create simultaneous chord events
        chord_events = [
            Event(type='note', note=60, time_sec=1.0, delta_sec=1.0, velocity=80),  # C
            Event(type='note', note=64, time_sec=1.0, delta_sec=0.0, velocity=80),  # E
            Event(type='note', note=67, time_sec=1.0, delta_sec=0.0, velocity=80),  # G
        ]
        
        arpeggiated = create_arpeggio_events(chord_events, spread_ms=30.0)
        
        assert len(arpeggiated) == 3
        
        # Check timing progression
        assert arpeggiated[0].time_sec == 1.0        # First note at original time
        assert arpeggiated[1].time_sec > 1.0         # Second note later
        assert arpeggiated[2].time_sec > arpeggiated[1].time_sec  # Third note latest
        
        # Check pitch order (should be ascending)
        assert arpeggiated[0].note == 60  # C
        assert arpeggiated[1].note == 64  # E
        assert arpeggiated[2].note == 67  # G
        
        # Check delta times are recalculated
        assert arpeggiated[0].delta_sec == 1.0
        assert arpeggiated[1].delta_sec > 0
        assert arpeggiated[2].delta_sec > 0
    
    def test_create_arpeggio_single_note(self):
        """Test arpeggio creation with single note."""
        single_event = [Event(type='note', note=60, time_sec=1.0, delta_sec=1.0, velocity=80)]
        
        result = create_arpeggio_events(single_event)
        
        assert result == single_event  # Should be unchanged
    
    def test_process_chord_events_reduction(self):
        """Test chord event processing with reduction."""
        # Create 4-note simultaneous chord
        events = [
            Event(type='note', note=60, time_sec=1.0, delta_sec=1.0, velocity=80),  # C
            Event(type='note', note=64, time_sec=1.0, delta_sec=0.0, velocity=80),  # E
            Event(type='note', note=67, time_sec=1.0, delta_sec=0.0, velocity=80),  # G
            Event(type='note', note=72, time_sec=1.0, delta_sec=0.0, velocity=80),  # C (octave)
        ]
        
        policy = ChordPolicy(max_chord_notes=3, reduction_mode='reduce')
        processed = process_chord_events(events, policy)
        
        assert len(processed) <= 3  # Should be reduced
        
        # Should preserve bass and melody
        notes = [e.note for e in processed]
        assert 60 in notes  # Bass
        assert 72 in notes  # Melody
    
    def test_process_chord_events_arpeggiation(self):
        """Test chord event processing with arpeggiation."""
        # Create simultaneous chord
        events = [
            Event(type='note', note=60, time_sec=1.0, delta_sec=1.0, velocity=80),  # C
            Event(type='note', note=64, time_sec=1.0, delta_sec=0.0, velocity=80),  # E
            Event(type='note', note=67, time_sec=1.0, delta_sec=0.0, velocity=80),  # G
        ]
        
        policy = ChordPolicy(max_chord_notes=2, reduction_mode='arpeggiate')
        processed = process_chord_events(events, policy)
        
        assert len(processed) == 3  # All notes preserved
        
        # Should have different times
        times = [e.time_sec for e in processed]
        assert len(set(times)) > 1  # Not all the same time
        
        # Should be in ascending pitch order
        notes = [e.note for e in processed]
        assert notes == sorted(notes)
    
    def test_process_all_chords(self):
        """Test processing of multiple chord groups."""
        events = [
            # First chord at t=0
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=64, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=67, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=72, time_sec=0.0, delta_sec=0.0, velocity=80),
            
            # Second chord at t=1.0
            Event(type='note', note=65, time_sec=1.0, delta_sec=1.0, velocity=80),  # F
            Event(type='note', note=69, time_sec=1.0, delta_sec=0.0, velocity=80),  # A
            Event(type='note', note=72, time_sec=1.0, delta_sec=0.0, velocity=80),  # C
            Event(type='note', note=77, time_sec=1.0, delta_sec=0.0, velocity=80),  # F
        ]
        
        policy = ChordPolicy(max_chord_notes=3, reduction_mode='reduce')
        processed = process_all_chords(events, policy)
        
        # Should have processed both chords
        groups = group_simultaneous(processed, policy.simultaneity_threshold)
        assert len(groups) == 2
        
        # Each group should have at most 3 notes
        assert len(groups[0]) <= 3
        assert len(groups[1]) <= 3
    
    def test_chord_processor_class(self):
        """Test ChordProcessor class interface."""
        processor = ChordProcessor()
        
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=64, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=67, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=72, time_sec=0.0, delta_sec=0.0, velocity=80),
        ]
        
        processed = processor.process(events)
        stats = processor.get_stats()
        
        assert len(processed) <= len(events)
        assert stats['processed_chords'] >= 0
        assert stats['reduced_chords'] >= 0
        assert stats['arpeggiated_chords'] >= 0
    
    def test_convenience_functions(self):
        """Test convenience chord processing functions."""
        # Create test chord
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),  # C
            Event(type='note', note=64, time_sec=0.0, delta_sec=0.0, velocity=80),  # E
            Event(type='note', note=67, time_sec=0.0, delta_sec=0.0, velocity=80),  # G
            Event(type='note', note=72, time_sec=0.0, delta_sec=0.0, velocity=80),  # C
        ]
        
        # Test melody-bass reduction
        melody_bass = reduce_chords_to_melody_bass(events)
        assert len(melody_bass) <= 2
        
        # Test arpeggiation
        arpeggiated = arpeggiate_all_chords(events, spread_ms=20.0)
        times = [e.time_sec for e in arpeggiated]
        assert len(set(times)) > 1  # Should have different times
        
        # Test conservative reduction
        conservative = conservative_chord_reduction(events)
        assert len(conservative) <= 3
    
    def test_empty_events_handling(self):
        """Test handling of empty event lists."""
        assert group_simultaneous([]) == []
        assert process_all_chords([]) == []
        
        processor = ChordProcessor()
        assert processor.process([]) == []
    
    def test_single_note_events(self):
        """Test processing of single note events."""
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=64, time_sec=1.0, delta_sec=1.0, velocity=80),
        ]
        
        processed = process_all_chords(events)
        assert len(processed) == 2  # Should be unchanged
        assert processed[0].note == 60
        assert processed[1].note == 64
    
    def test_chord_structure_edge_cases(self):
        """Test chord structure analysis edge cases."""
        # Empty notes
        assert analyze_chord_structure([]) == {}
        
        # Two notes
        analysis = analyze_chord_structure([60, 67])
        assert analysis['bass'] == 60
        assert analysis['melody'] == 67
        assert analysis['root'] == 60
        
        # Large chord with many intervals
        notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale
        analysis = analyze_chord_structure(notes)
        assert analysis['bass'] == 60
        assert analysis['melody'] == 72
        assert 'third' in analysis or 'fifth' in analysis  # Should find some intervals
    
    def test_arpeggio_timing_precision(self):
        """Test precise timing in arpeggio creation."""
        events = [
            Event(type='note', note=60, time_sec=2.0, delta_sec=2.0, velocity=80),
            Event(type='note', note=64, time_sec=2.0, delta_sec=0.0, velocity=80),
        ]
        
        arpeggiated = create_arpeggio_events(events, spread_ms=100.0)  # 100ms spread
        
        assert arpeggiated[0].time_sec == 2.0
        assert arpeggiated[1].time_sec == pytest.approx(2.1, abs=1e-3)  # 100ms later
        
        # Check delta calculation
        assert arpeggiated[1].delta_sec == pytest.approx(0.1, abs=1e-3)
