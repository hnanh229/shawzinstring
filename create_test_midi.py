#!/usr/bin/env python3
"""
Create a simple test MIDI file for demonstrating the metrics system.
"""

import mido
import os

def create_simple_melody():
    """Create a simple C major scale melody."""
    # Create a new MIDI file with one track
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Set tempo (120 BPM)
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    
    # C major scale: C4 D4 E4 F4 G4 A4 B4 C5
    notes = [60, 62, 64, 65, 67, 69, 71, 72]
    
    # Add notes with timing (quarter notes)
    ticks_per_beat = mid.ticks_per_beat
    quarter_note = ticks_per_beat
    
    for i, note in enumerate(notes):
        # Note on
        track.append(mido.Message('note_on', channel=0, note=note, velocity=80, time=0))
        # Note off after quarter note
        track.append(mido.Message('note_off', channel=0, note=note, velocity=80, time=quarter_note))
    
    return mid

if __name__ == '__main__':
    # Create the test file
    midi_file = create_simple_melody()
    output_path = 'simple_melody.mid'
    midi_file.save(output_path)
    print(f"Created test MIDI file: {output_path}")
    
    # Print file info
    print(f"File size: {os.path.getsize(output_path)} bytes")
    print(f"Tracks: {len(midi_file.tracks)}")
    print(f"Ticks per beat: {midi_file.ticks_per_beat}")
    print(f"Length: {midi_file.length:.2f} seconds")
