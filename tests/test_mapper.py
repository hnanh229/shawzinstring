"""
Tests for midi2shawzin.mapper module

Tests note-to-character mapping with closest-pitch algorithms.
"""

import pytest
from midi2shawzin.mapper import (
    ShawzinNote, MappingSettings, ShawzinMapper,
    build_playable_table, map_note_to_shawzin, analyze_note_coverage,
    find_best_scale_for_notes, map_events_to_shawzin_events,
    map_notes_to_shawzin, quick_map_single_note, analyze_scale_compatibility
)
from midi2shawzin.midi_io import Event


class TestPlayableTable:
    """Test playable table generation."""
    
    def test_build_playable_table_basic(self):
        """Test basic playable table generation."""
        table = build_playable_table(scale_id=2)  # Major scale
        
        # Should have entries
        assert len(table) > 0
        
        # Should be sorted by MIDI note
        midi_notes = [midi for midi, char in table]
        assert midi_notes == sorted(midi_notes)
        
        # All MIDI notes should be valid
        for midi, char in table:
            assert 0 <= midi <= 127
            assert char in "123qweasdzxc"
    
    def test_build_playable_table_octave_range(self):
        """Test octave range parameter."""
        # Narrow range
        table_narrow = build_playable_table(scale_id=2, octave_range=(-1, 1))
        
        # Wide range  
        table_wide = build_playable_table(scale_id=2, octave_range=(-3, 4))
        
        # Wide should have more entries
        assert len(table_wide) > len(table_narrow)
    
    def test_build_playable_table_invalid_scale(self):
        """Test invalid scale ID handling."""
        with pytest.raises(ValueError):
            build_playable_table(scale_id=99)
    
    def test_build_playable_table_different_scales(self):
        """Test different scale patterns."""
        scales_to_test = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        
        for scale_id in scales_to_test:
            table = build_playable_table(scale_id)
            
            # Each scale should produce a valid table
            assert len(table) > 0
            
            # No duplicate MIDI notes
            midi_notes = [midi for midi, char in table]
            assert len(midi_notes) == len(set(midi_notes))


class TestNoteMapping:
    """Test individual note mapping."""
    
    def test_map_note_to_shawzin_basic(self):
        """Test basic note mapping."""
        table = build_playable_table(scale_id=2)
        
        # Test middle C (60)
        char, mapped_midi, octave_shift = map_note_to_shawzin(60, table)
        
        assert isinstance(char, str)
        assert char in "123qweasdzxc"
        assert isinstance(mapped_midi, int)
        assert isinstance(octave_shift, int)
    
    def test_map_note_to_shawzin_exact_match(self):
        """Test mapping when exact match exists."""
        table = build_playable_table(scale_id=2)
        
        # If table contains exact MIDI note, should map perfectly
        if table:  # Ensure table not empty
            test_midi, expected_char = table[0]
            char, mapped_midi, octave_shift = map_note_to_shawzin(test_midi, table)
            
            assert char == expected_char
            assert mapped_midi == test_midi
    
    def test_map_note_to_shawzin_empty_table(self):
        """Test mapping with empty table."""
        with pytest.raises(ValueError):
            map_note_to_shawzin(60, [])
    
    def test_map_note_to_shawzin_closest_match(self):
        """Test closest pitch matching."""
        table = build_playable_table(scale_id=2)
        
        # Test note that might not exist exactly
        char, mapped_midi, octave_shift = map_note_to_shawzin(61, table)  # C#
        
        # Should find closest match
        assert isinstance(char, str)
        assert abs(mapped_midi - 61) <= 6  # Within reasonable range


class TestCoverageAnalysis:
    """Test note coverage analysis."""
    
    def test_analyze_note_coverage_basic(self):
        """Test basic coverage analysis."""
        table = build_playable_table(scale_id=2)
        notes = [60, 62, 64, 65, 67]  # C major scale
        
        analysis = analyze_note_coverage(notes, table)
        
        assert 'coverage' in analysis
        assert 'avg_deviation' in analysis
        assert 'max_deviation' in analysis
        
        assert 0.0 <= analysis['coverage'] <= 1.0
        assert analysis['avg_deviation'] >= 0.0
        assert analysis['max_deviation'] >= 0.0
    
    def test_analyze_note_coverage_empty_notes(self):
        """Test coverage with empty note list."""
        table = build_playable_table(scale_id=2)
        
        analysis = analyze_note_coverage([], table)
        
        assert analysis['coverage'] == 0.0
        assert analysis['avg_deviation'] == 0.0
        assert analysis['max_deviation'] == 0.0
    
    def test_analyze_note_coverage_perfect_match(self):
        """Test coverage when all notes match perfectly."""
        table = build_playable_table(scale_id=2)
        
        # Use notes from the table itself
        test_notes = [midi for midi, char in table[:5]]  # First 5 notes
        
        analysis = analyze_note_coverage(test_notes, table, max_deviation=0)
        
        # Should be perfect coverage with 0 deviation
        assert analysis['coverage'] == 1.0
        assert analysis['avg_deviation'] == 0.0
        assert analysis['max_deviation'] == 0.0


class TestScaleFinding:
    """Test automatic scale finding."""
    
    def test_find_best_scale_for_notes_major(self):
        """Test finding scale for major key notes."""
        # C major scale notes
        c_major_notes = [60, 62, 64, 65, 67, 69, 71]
        
        best_scale = find_best_scale_for_notes(c_major_notes)
        
        # Should prefer a major-type scale
        assert 1 <= best_scale <= 9
    
    def test_find_best_scale_for_notes_empty(self):
        """Test scale finding with empty notes."""
        best_scale = find_best_scale_for_notes([])
        
        # Should return default (major scale)
        assert best_scale == 2
    
    def test_find_best_scale_for_notes_chromatic(self):
        """Test scale finding with chromatic notes."""
        # All 12 chromatic notes
        chromatic_notes = list(range(60, 72))
        
        best_scale = find_best_scale_for_notes(chromatic_notes)
        
        # Should find a scale that covers most notes
        assert 1 <= best_scale <= 9


class TestEventMapping:
    """Test event-to-shawzin mapping."""
    
    def test_map_events_to_shawzin_events_basic(self):
        """Test basic event mapping."""
        events = [
            Event(type='note', time_sec=0.0, delta_sec=0.5, note=60),
            Event(type='note', time_sec=0.5, delta_sec=0.5, note=62),
            Event(type='note', time_sec=1.0, delta_sec=0.5, note=64)
        ]
        
        table = build_playable_table(scale_id=2)
        shawzin_notes = map_events_to_shawzin_events(events, table)
        
        assert len(shawzin_notes) == 3
        
        for note in shawzin_notes:
            assert isinstance(note, ShawzinNote)
            assert note.character in "123qweasdzxc"
            assert note.time_sec >= 0.0
            assert note.duration_sec >= 0.0
    
    def test_map_events_to_shawzin_events_consistency(self):
        """Test mapping consistency."""
        events = [
            Event(type='note', time_sec=0.0, delta_sec=0.5, note=60),
            Event(type='note', time_sec=1.0, delta_sec=0.5, note=60),  # Same note
        ]
        
        table = build_playable_table(scale_id=2)
        shawzin_notes = map_events_to_shawzin_events(events, table, maintain_consistency=True)
        
        # Same MIDI note should map to same character
        assert shawzin_notes[0].character == shawzin_notes[1].character
        assert shawzin_notes[0].mapped_midi == shawzin_notes[1].mapped_midi
    
    def test_map_events_to_shawzin_events_non_note_events(self):
        """Test filtering of non-note events."""
        events = [
            Event(type='tempo', time_sec=0.0, delta_sec=0.0, tempo=120),
            Event(type='note', time_sec=0.0, delta_sec=0.5, note=60),
            Event(type='time_signature', time_sec=0.5, delta_sec=0.0, numerator=4, denominator=4)
        ]
        
        table = build_playable_table(scale_id=2)
        shawzin_notes = map_events_to_shawzin_events(events, table)
        
        # Should only process note events
        assert len(shawzin_notes) == 1
        assert shawzin_notes[0].original_midi == 60


class TestShawzinMapper:
    """Test the main ShawzinMapper class."""
    
    def test_mapper_initialization(self):
        """Test mapper initialization."""
        # Default initialization
        mapper1 = ShawzinMapper()
        assert mapper1.settings is not None
        
        # Custom settings
        settings = MappingSettings(octave_range=(-1, 2))
        mapper2 = ShawzinMapper(settings)
        assert mapper2.settings.octave_range == (-1, 2)
    
    def test_mapper_get_playable_table_caching(self):
        """Test playable table caching."""
        mapper = ShawzinMapper()
        
        # First call should create table
        table1 = mapper.get_playable_table(2)
        assert len(mapper.playable_tables) == 1
        
        # Second call should use cache
        table2 = mapper.get_playable_table(2)
        assert table1 is table2  # Same object reference
        assert len(mapper.playable_tables) == 1
    
    def test_mapper_map_events_basic(self):
        """Test basic event mapping."""
        mapper = ShawzinMapper()
        
        events = [
            Event(type='note', time_sec=0.0, delta_sec=0.5, note=60),
            Event(type='note', time_sec=0.5, delta_sec=0.5, note=64)
        ]
        
        shawzin_notes = mapper.map_events(events)
        
        assert len(shawzin_notes) == 2
        assert all(isinstance(note, ShawzinNote) for note in shawzin_notes)
    
    def test_mapper_map_events_auto_scale(self):
        """Test automatic scale detection."""
        mapper = ShawzinMapper()
        
        # C major triad
        events = [
            Event(type='note', time_sec=0.0, delta_sec=1.0, note=60),  # C
            Event(type='note', time_sec=1.0, delta_sec=1.0, note=64),  # E
            Event(type='note', time_sec=2.0, delta_sec=1.0, note=67)   # G
        ]
        
        shawzin_notes = mapper.map_events(events, scale_id=None)
        
        # Should auto-detect a suitable scale
        assert mapper.current_scale_id is not None
        assert 1 <= mapper.current_scale_id <= 9
    
    def test_mapper_map_events_forced_scale(self):
        """Test mapping with forced scale."""
        mapper = ShawzinMapper()
        
        events = [
            Event(type='note', time_sec=0.0, delta_sec=0.5, note=60)
        ]
        
        shawzin_notes = mapper.map_events(events, scale_id=3)
        
        # Should use forced scale
        assert mapper.current_scale_id == 3
        assert shawzin_notes[0].scale_id == 3
    
    def test_mapper_get_mapping_stats(self):
        """Test mapping statistics."""
        mapper = ShawzinMapper()
        
        # Initially empty
        stats = mapper.get_mapping_stats()
        assert stats['cached_scales'] == 0
        assert stats['current_scale'] is None
        
        # After mapping
        events = [Event(type='note', time_sec=0.0, delta_sec=0.5, note=60)]
        mapper.map_events(events)
        
        stats = mapper.get_mapping_stats()
        assert stats['cached_scales'] >= 1
        assert stats['current_scale'] is not None
    
    def test_mapper_clear_cache(self):
        """Test cache clearing."""
        mapper = ShawzinMapper()
        
        # Create some cached data
        events = [Event(type='note', time_sec=0.0, delta_sec=0.5, note=60)]
        mapper.map_events(events)
        
        assert len(mapper.playable_tables) > 0
        
        # Clear cache
        mapper.clear_cache()
        
        assert len(mapper.playable_tables) == 0
        assert len(mapper.mapping_cache) == 0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_map_notes_to_shawzin(self):
        """Test convenience mapping function."""
        events = [
            Event(type='note', time_sec=0.0, delta_sec=0.5, note=60),
            Event(type='note', time_sec=0.5, delta_sec=0.5, note=62)
        ]
        
        shawzin_notes = map_notes_to_shawzin(events)
        
        assert len(shawzin_notes) == 2
        assert all(isinstance(note, ShawzinNote) for note in shawzin_notes)
    
    def test_quick_map_single_note(self):
        """Test quick single note mapping."""
        char, mapped_midi, octave_shift = quick_map_single_note(60)
        
        assert isinstance(char, str)
        assert char in "123qweasdzxc"
        assert isinstance(mapped_midi, int)
        assert isinstance(octave_shift, int)
    
    def test_quick_map_single_note_different_scales(self):
        """Test single note mapping with different scales."""
        results = []
        
        for scale_id in [1, 2, 3]:
            char, mapped_midi, octave_shift = quick_map_single_note(60, scale_id)
            results.append((char, mapped_midi, octave_shift))
        
        # Different scales might produce different results
        assert len(results) == 3
    
    def test_analyze_scale_compatibility(self):
        """Test scale compatibility analysis."""
        notes = [60, 62, 64, 65, 67, 69, 71]  # C major scale
        
        analysis = analyze_scale_compatibility(notes)
        
        # Should analyze multiple scales
        assert len(analysis) > 0
        
        # Each analysis should have required keys
        for scale_id, result in analysis.items():
            assert 'coverage' in result
            assert 'avg_deviation' in result
            assert 'max_deviation' in result
            assert 1 <= scale_id <= 9


class TestMappingAccuracy:
    """Test mapping accuracy and musical correctness."""
    
    def test_major_scale_mapping_accuracy(self):
        """Test accuracy for major scale mapping."""
        # C major scale
        c_major = [60, 62, 64, 65, 67, 69, 71, 72]
        
        table = build_playable_table(scale_id=2)  # Major scale
        analysis = analyze_note_coverage(c_major, table, max_deviation=2)
        
        # Should have good coverage for major scale
        assert analysis['coverage'] >= 0.7  # At least 70% coverage
        assert analysis['avg_deviation'] <= 2.0  # Average within 2 semitones
    
    def test_chromatic_mapping_accuracy(self):
        """Test accuracy for chromatic notes."""
        # Chromatic scale
        chromatic = list(range(60, 72))
        
        # Test multiple scales
        best_coverage = 0
        for scale_id in range(1, 10):
            try:
                table = build_playable_table(scale_id)
                analysis = analyze_note_coverage(chromatic, table, max_deviation=2)
                best_coverage = max(best_coverage, analysis['coverage'])
            except (ValueError, KeyError):
                continue
        
        # At least one scale should handle chromatic reasonably
        assert best_coverage > 0.5
    
    def test_octave_range_coverage(self):
        """Test coverage across octave ranges."""
        # Test notes across multiple octaves
        notes = [48, 60, 72, 84, 96]  # C notes in different octaves
        
        table = build_playable_table(scale_id=2, octave_range=(-2, 3))
        analysis = analyze_note_coverage(notes, table, max_deviation=1)
        
        # Should cover notes across octaves well
        assert analysis['coverage'] >= 0.8
    
    def test_mapping_consistency_across_octaves(self):
        """Test that octave mapping is consistent."""
        # Same pitch class in different octaves
        c_notes = [48, 60, 72, 84]  # C in different octaves
        
        table = build_playable_table(scale_id=2)
        mapped_chars = []
        
        for note in c_notes:
            char, mapped_midi, octave_shift = map_note_to_shawzin(note, table)
            mapped_chars.append(char)
        
        # Should tend to map to similar characters (allowing some variation)
        # At least some consistency expected
        unique_chars = len(set(mapped_chars))
        assert unique_chars <= 3  # Not too much variation


if __name__ == '__main__':
    pytest.main([__file__])
