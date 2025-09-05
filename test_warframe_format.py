#!/usr/bin/env python3
"""Test script to verify Warframe-compatible format generation."""

from midi2shawzin import *
import tempfile
import mido

def test_warframe_format():
    """Test that the converter generates Warframe-compatible strings."""
    
    # Create a simple test MIDI
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Add a simple C major scale
    notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C D E F G A B C
    time = 0
    for note in notes:
        track.append(mido.Message('note_on', channel=0, note=note, velocity=64, time=time))
        track.append(mido.Message('note_off', channel=0, note=note, velocity=64, time=480))
        time = 0

    # Save and convert
    with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as f:
        mid.save(f.name)
        print(f'Created test MIDI file: {f.name}')
        
        # Read MIDI events
        from midi2shawzin.midi_io import read_midi, get_note_events
        midi_data = read_midi(f.name)
        events = get_note_events(midi_data)
        print(f'Read {len(events)} MIDI events')
        
        # Convert to Shawzin events  
        from midi2shawzin.mapper import map_events_to_shawzin_events, build_playable_table
        
        # Use scale_id 2 for testing (common scale)
        scale_id = 2
        playable_table = build_playable_table(scale_id)
        print(f'Using scale_id: {scale_id}')
        
        shawzin_events = map_events_to_shawzin_events(events, playable_table)
        print(f'Mapped to {len(shawzin_events)} Shawzin events')
        
        # Encode to text
        from midi2shawzin.encoder import events_to_shawzin_text
        chunks = events_to_shawzin_text(shawzin_events)
        
        shawzin_string = chunks[0]
        print('\n=== RESULTS ===')
        print('Generated Shawzin string:')
        print(repr(shawzin_string))
        print('Formatted output:')
        print(shawzin_string)
        print(f'Length: {len(shawzin_string)} characters')
        print(f'Format check: starts with digit = {shawzin_string[0].isdigit()}')
        no_hash = not shawzin_string.startswith('#')
        print(f'Valid for Warframe: No # prefix = {no_hash}')
        
        # Check official Warframe limits
        print(f'Within 256 char limit: {len(shawzin_string) <= 256}')
        
        # Test parsing back
        print('\n=== ROUND-TRIP TEST ===')
        with open('temp_shawzin.txt', 'w') as temp_f:
            temp_f.write(shawzin_string)
        
        from midi2shawzin.encoder import read_shawzin_file
        scale_id, notes = read_shawzin_file('temp_shawzin.txt')
        print(f'Parsed scale_id: {scale_id}')
        print(f'Parsed notes: {notes}')
        
        return shawzin_string

if __name__ == '__main__':
    test_warframe_format()
