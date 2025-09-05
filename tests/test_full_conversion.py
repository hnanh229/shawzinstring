"""
Test Full MIDI to Shawzin Conversion

Integration tests for complete conversion pipeline.
"""

import pytest
import tempfile
import mido
import os
from pathlib import Path
from midi2shawzin.cli import convert_midi_file
from midi2shawzin import convert_midi_to_shawzin
from midi2shawzin.midi_io import read_midi, choose_melody_track, get_note_events, merge_note_events
from midi2shawzin.key_detection import detect_key_from_events
from midi2shawzin.quantize import quantize_events, QuantizeSettings
from midi2shawzin.mapper import build_playable_table, map_events_to_shawzin_events
from midi2shawzin.encoder import encode_shawzin_melody

class TestFullConversion:
    """Test complete MIDI to Shawzin conversion."""

    def create_synthetic_midi_file(self):
        """Create synthetic MIDI file for testing."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        temp_file.close()
        
        # Create simple MIDI file with mido
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Set tempo to 120 BPM (500000 microseconds per beat)
        track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
        
        # Add short melody: C4, E4, G4, C5
        notes = [60, 64, 67, 72]  # C major chord progression
        for i, note in enumerate(notes):
            # Note on
            track.append(mido.Message('note_on', channel=0, note=note, velocity=64, 
                                    time=240 if i > 0 else 0))
            # Note off after quarter note (240 ticks)
            track.append(mido.Message('note_off', channel=0, note=note, velocity=0, time=240))
        
        # End of track
        track.append(mido.MetaMessage('end_of_track', time=0))
        
        mid.save(temp_file.name)
        return temp_file.name

    def test_synthesize_short_melody_full_pipeline(self):
        """Test synthesized short melody through full pipeline (detect->quantize->map->encode)."""
        midi_file = None
        try:
            # Create synthetic MIDI file
            midi_file = self.create_synthetic_midi_file()
            
            # Step 1: Load MIDI
            midi_data = read_midi(midi_file)
            melody_track = choose_melody_track(midi_data)
            events = get_note_events(midi_data, melody_track)
            events = merge_note_events(events)
            
            # Step 2: Detect key
            key_name, scale_type = detect_key_from_events(events)
            scale_id = 2  # Default to major scale
            
            # Step 3: Quantize  
            quantize_settings = QuantizeSettings(subdivision=16)
            quantized_events = quantize_events(
                events,
                midi_data['ticks_per_beat'],
                midi_data.get('tempo', 500000),
                quantize_settings
            )
            
            # Step 4: Map to Shawzin
            playable_table = build_playable_table(scale_id, octave_range=(3, 6))
            shawzin_events = map_events_to_shawzin_events(quantized_events, playable_table)
            
            # Step 5: Encode
            from midi2shawzin.encoder import events_to_shawzin_text, create_scale_header
            text_chunks = events_to_shawzin_text(shawzin_events, keep_offsets=True)
            scale_header = create_scale_header(scale_id)
            output_text = scale_header + '\n'.join(text_chunks)
            
            # Assertions
            assert output_text is not None and len(output_text) > 0, "Output should be non-empty"
            assert output_text[0].isdigit(), "Output should start with scale header"
            
            # Count tokens (excluding header and newlines)
            tokens = output_text.replace('#', '').replace('\n', '').strip()
            
            # For melody-only mode, number of output tokens should equal number of input notes
            # (allowing for timing tokens which may increase the count)
            assert len(tokens) >= len(events), \
                f"Expected at least {len(events)} tokens, got {len(tokens)} in output: {output_text}"
            
        finally:
            # Clean up
            if midi_file and os.path.exists(midi_file):
                os.unlink(midi_file)
    
    def test_cli_basic_conversion(self):
        """Test basic CLI conversion functionality."""
        # TODO: Create test MIDI file
        # TODO: Run conversion through CLI
        # TODO: Verify output file is created
        pass
        
    def test_api_conversion(self):
        """Test API conversion function."""
        # TODO: Create test MIDI file
        # TODO: Call convert_midi_to_shawzin()
        # TODO: Verify output format
        pass
        
    def test_invalid_input_file(self):
        """Test handling of invalid input files."""
        with pytest.raises(FileNotFoundError):
            convert_midi_file("nonexistent.mid")
            
    def test_output_file_creation(self):
        """Test that output files are created correctly."""
        # TODO: Test output file creation and content
        pass
        
    def test_conversion_with_options(self):
        """Test conversion with various CLI options."""
        # TODO: Test quantization options
        # TODO: Test arpeggiation options
        # TODO: Test pattern detection options
        pass
        
    def test_tempo_override(self):
        """Test tempo override functionality."""
        # TODO: Test that tempo override affects output timing
        pass
        
    def test_large_file_handling(self):
        """Test handling of large MIDI files."""
        # TODO: Create large test file
        # TODO: Verify conversion completes without memory issues
        pass
        
    def test_polyphonic_handling(self):
        """Test handling of polyphonic MIDI files."""
        # TODO: Create MIDI with multiple simultaneous notes
        # TODO: Verify chord handling works correctly
        pass
