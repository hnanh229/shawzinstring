"""
Demo script to test MIDI I/O functionality.

Creates a simple MIDI file and demonstrates reading it with our midi_io module.
"""

import sys
import tempfile
import os
from pathlib import Path

# Add the project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import mido
except ImportError:
    print("mido library not installed. Install with: pip install mido==1.2.9")
    sys.exit(1)

from midi2shawzin.midi_io import read_midi, choose_melody_track, get_note_events, merge_note_events

def create_demo_midi():
    """Create a simple demo MIDI file."""
    # Create temporary MIDI file
    temp_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
    temp_file.close()
    
    # Create MIDI with C major scale
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Set tempo to 120 BPM
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(mido.MetaMessage('track_name', name='Demo Melody', time=0))
    
    # C major scale: C-D-E-F-G-A-B-C
    notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C4 to C5
    
    for i, note in enumerate(notes):
        # Each note lasts 240 ticks (0.25 seconds at 120 BPM)
        track.append(mido.Message('note_on', channel=0, note=note, velocity=80, time=0))
        track.append(mido.Message('note_off', channel=0, note=note, velocity=0, time=240))
    
    mid.save(temp_file.name)
    return temp_file.name

def demo_midi_reading():
    """Demonstrate MIDI reading functionality."""
    print("MIDI I/O Demo")
    print("=" * 50)
    
    # Create demo MIDI file
    print("Creating demo MIDI file...")
    midi_file = create_demo_midi()
    
    try:
        # Read MIDI file
        print(f"Reading MIDI file: {midi_file}")
        midi_data = read_midi(midi_file)
        
        print(f"Ticks per beat: {midi_data['ticks_per_beat']}")
        print(f"Default tempo: {midi_data['tempo']} microseconds per beat")
        print(f"Number of tracks: {len(midi_data['tracks'])}")
        
        # Choose melody track
        melody_track_index = choose_melody_track(midi_data)
        print(f"Selected melody track: {melody_track_index}")
        
        # Get events from melody track
        track = midi_data['tracks'][melody_track_index]
        print(f"Track name: {track['name']}")
        print(f"Number of events: {len(track['events'])}")
        
        # Show first few events
        print("\nFirst 10 events:")
        for i, event in enumerate(track['events'][:10]):
            print(f"  {i+1}: {event.type} at {event.time_sec:.3f}s - "
                  f"note={event.note}, vel={event.velocity}, ch={event.channel}")
        
        # Get note events only
        note_events = get_note_events(midi_data, melody_track_index)
        print(f"\nNote events (note_on/note_off): {len(note_events)}")
        
        # Merge note events
        merged_events = merge_note_events(note_events)
        print(f"Merged note events: {len(merged_events)}")
        
        print("\nMerged notes with duration:")
        for i, event in enumerate(merged_events):
            note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][event.note % 12]
            octave = event.note // 12 - 1
            print(f"  {i+1}: {note_name}{octave} at {event.time_sec:.3f}s, "
                  f"duration={event.delta_sec:.3f}s, velocity={event.velocity}")
        
        # Test timing accuracy
        print("\nTiming verification:")
        expected_times = [i * 0.25 for i in range(8)]  # 240 ticks = 0.25 seconds each
        for i, (event, expected) in enumerate(zip(merged_events, expected_times)):
            actual = event.time_sec
            print(f"  Note {i+1}: expected={expected:.3f}s, actual={actual:.3f}s, "
                  f"error={abs(actual-expected)*1000:.1f}ms")
        
    finally:
        # Clean up
        if os.path.exists(midi_file):
            os.unlink(midi_file)
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    demo_midi_reading()
