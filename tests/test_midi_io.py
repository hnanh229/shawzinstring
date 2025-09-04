"""
Test MIDI I/O Functions

Unit tests for MIDI file reading and event processing.
"""

import pytest
import tempfile
import os
from pathlib import Path

# We'll test with a synthetic MIDI file created using mido
try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

from midi2shawzin.midi_io import (
    Event,
    read_midi,
    choose_melody_track,
    ticks_to_seconds,
    get_note_events,
    merge_note_events,
    read_midi_file,
    NoteEvent
)

class TestMidiIO:
    """Test MIDI I/O functionality."""
    
    @pytest.fixture
    def sample_midi_file(self):
        """Create a synthetic MIDI file for testing."""
        if not MIDO_AVAILABLE:
            pytest.skip("mido not available for testing")
            
        # Create temporary MIDI file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        temp_file.close()
        
        try:
            # Create simple MIDI file with known content
            mid = mido.MidiFile()
            track = mido.MidiTrack()
            mid.tracks.append(track)
            
            # Set tempo to 120 BPM (500000 microseconds per beat)
            track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
            
            # Add some test notes
            # C4 (note 60) at time 0, duration 480 ticks (1 beat)
            track.append(mido.Message('note_on', channel=0, note=60, velocity=64, time=0))
            track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=480))
            
            # E4 (note 64) at time 480, duration 240 ticks (0.5 beat)
            track.append(mido.Message('note_on', channel=0, note=64, velocity=80, time=0))
            track.append(mido.Message('note_off', channel=0, note=64, velocity=0, time=240))
            
            # G4 (note 67) at time 720, duration 480 ticks (1 beat)
            track.append(mido.Message('note_on', channel=0, note=67, velocity=100, time=0))
            track.append(mido.Message('note_off', channel=0, note=67, velocity=0, time=480))
            
            mid.save(temp_file.name)
            yield temp_file.name
            
        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_ticks_to_seconds(self):
        """Test MIDI tick to seconds conversion."""
        # Test basic conversion
        # 480 ticks per beat, 500000 microseconds per beat = 0.5 seconds per beat
        seconds = ticks_to_seconds(480, 480, 500000)
        assert abs(seconds - 0.5) < 0.001
        
        # Test zero ticks
        seconds = ticks_to_seconds(0, 480, 500000)
        assert seconds == 0.0
        
        # Test different tempo (120 BPM = 500000 microseconds, 240 BPM = 250000 microseconds)
        seconds = ticks_to_seconds(480, 480, 250000)
        assert abs(seconds - 0.25) < 0.001
        
        # Test edge case: zero ticks_per_beat
        seconds = ticks_to_seconds(480, 0, 500000)
        assert seconds == 0.0
    
    @pytest.mark.skipif(not MIDO_AVAILABLE, reason="mido not available")
    def test_read_midi_basic(self, sample_midi_file):
        """Test basic MIDI file reading."""
        result = read_midi(sample_midi_file)
        
        # Check basic structure
        assert 'ticks_per_beat' in result
        assert 'tracks' in result
        assert 'tempo' in result
        
        assert result['ticks_per_beat'] == 480
        assert result['tempo'] == 500000
        assert len(result['tracks']) == 1
        
        # Check track structure
        track = result['tracks'][0]
        assert 'name' in track
        assert 'events' in track
        
        events = track['events']
        assert len(events) > 0
        
        # Check for note events
        note_events = [e for e in events if e.type in ['note_on', 'note_off']]
        assert len(note_events) == 6  # 3 note_on + 3 note_off
    
    @pytest.mark.skipif(not MIDO_AVAILABLE, reason="mido not available")
    def test_event_timing(self, sample_midi_file):
        """Test that event timing is calculated correctly."""
        result = read_midi(sample_midi_file)
        events = result['tracks'][0]['events']
        
        # Find note events
        note_events = [e for e in events if e.type in ['note_on', 'note_off']]
        
        # Check timing of first note (should start at 0)
        first_note_on = next(e for e in note_events if e.type == 'note_on' and e.note == 60)
        assert abs(first_note_on.time_sec - 0.0) < 0.001
        
        # Check timing of first note off (should be at 0.5 seconds)
        first_note_off = next(e for e in note_events if e.type == 'note_off' and e.note == 60)
        assert abs(first_note_off.time_sec - 0.5) < 0.001
    
    @pytest.mark.skipif(not MIDO_AVAILABLE, reason="mido not available")
    def test_choose_melody_track(self, sample_midi_file):
        """Test melody track selection."""
        result = read_midi(sample_midi_file)
        melody_track = choose_melody_track(result)
        
        # With only one track, should return 0
        assert melody_track == 0
    
    @pytest.mark.skipif(not MIDO_AVAILABLE, reason="mido not available")
    def test_get_note_events(self, sample_midi_file):
        """Test note event extraction."""
        result = read_midi(sample_midi_file)
        note_events = get_note_events(result, 0)
        
        # Should get all note events from track 0
        assert len(note_events) == 6  # 3 note_on + 3 note_off
        
        # Events should be sorted by time
        times = [e.time_sec for e in note_events]
        assert times == sorted(times)
    
    @pytest.mark.skipif(not MIDO_AVAILABLE, reason="mido not available")
    def test_merge_note_events(self, sample_midi_file):
        """Test merging note_on/note_off into notes with duration."""
        result = read_midi(sample_midi_file)
        note_events = get_note_events(result, 0)
        merged = merge_note_events(note_events)
        
        # Should get 3 merged note events
        assert len(merged) == 3
        
        # Check first note (C4)
        c4_note = next(e for e in merged if e.note == 60)
        assert abs(c4_note.time_sec - 0.0) < 0.001
        assert abs(c4_note.delta_sec - 0.5) < 0.001  # Duration should be 0.5 seconds
        assert c4_note.velocity == 64
    
    @pytest.mark.skipif(not MIDO_AVAILABLE, reason="mido not available")
    def test_legacy_compatibility(self, sample_midi_file):
        """Test legacy NoteEvent compatibility."""
        note_events = read_midi_file(sample_midi_file)
        
        # Should return list of NoteEvent objects
        assert len(note_events) == 3
        assert all(isinstance(e, NoteEvent) for e in note_events)
        
        # Check first note
        first_note = note_events[0]
        assert first_note.note == 60
        assert abs(first_note.time - 0.0) < 0.001
        assert abs(first_note.duration - 0.5) < 0.001
        assert first_note.velocity == 64
        assert first_note.event_type == 'note'
    
    def test_invalid_midi_file(self):
        """Test handling of invalid MIDI files."""
        with pytest.raises(ValueError):
            read_midi("nonexistent.mid")
    
    def test_empty_tracks(self):
        """Test handling of MIDI data with empty tracks."""
        empty_midi_data = {
            'ticks_per_beat': 480,
            'tracks': [],
            'tempo': 500000
        }
        
        melody_track = choose_melody_track(empty_midi_data)
        assert melody_track == 0
        
        note_events = get_note_events(empty_midi_data)
        assert len(note_events) == 0
