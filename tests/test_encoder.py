"""
Tests for midi2shawzin.encoder module

Tests Shawzin string encoding with time encoding, chunking, and file output.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import List
from midi2shawzin.encoder import (
    EncodingSettings, ShawzinEncoder,
    time_to_shawzin_time, shawzin_time_to_seconds, event_to_shawzin_token,
    create_scale_header, events_to_shawzin_text, write_shawzin_file,
    read_shawzin_file, encode_shawzin_melody, encode_shawzin_full,
    quick_encode_token, analyze_timing_accuracy
)
from midi2shawzin.mapper import ShawzinNote
from midi2shawzin.shawzin_mapping import base64_chars


class TestTimeEncoding:
    """Test time encoding and decoding functions."""
    
    def test_time_to_shawzin_time_basic(self):
        """Test basic time encoding."""
        # Test zero time
        time_str = time_to_shawzin_time(0.0)
        assert len(time_str) == 2
        assert time_str[0] in base64_chars
        assert time_str[1] in base64_chars
        
        # Test small time
        time_str = time_to_shawzin_time(0.0625)  # One tick
        assert len(time_str) == 2
    
    def test_time_to_shawzin_time_precision(self):
        """Test time encoding precision."""
        # Test various time values
        test_times = [0.0, 0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0]
        
        for time_val in test_times:
            encoded = time_to_shawzin_time(time_val)
            decoded = shawzin_time_to_seconds(encoded)
            
            # Should be reasonably close (within one tick)
            assert abs(decoded - time_val) <= 0.0625
    
    def test_shawzin_time_to_seconds_basic(self):
        """Test basic time decoding."""
        # Test with known encodings
        time_str = base64_chars[0] + base64_chars[0]  # "AA"
        decoded = shawzin_time_to_seconds(time_str)
        assert decoded == 0.0
        
        # Test with one tick
        time_str = base64_chars[0] + base64_chars[1]  # "AB"
        decoded = shawzin_time_to_seconds(time_str)
        assert decoded == 0.0625
    
    def test_time_encoding_roundtrip(self):
        """Test encoding-decoding roundtrip."""
        test_times = [0.0, 0.125, 0.5, 1.0, 2.5, 8.0]
        
        for original_time in test_times:
            encoded = time_to_shawzin_time(original_time)
            decoded = shawzin_time_to_seconds(encoded)
            
            # Should round-trip within quantization error
            assert abs(decoded - original_time) <= 0.0625
    
    def test_time_encoding_edge_cases(self):
        """Test edge cases for time encoding."""
        # Negative time should be treated as zero
        encoded = time_to_shawzin_time(-1.0)
        decoded = shawzin_time_to_seconds(encoded)
        assert decoded == 0.0
        
        # Very large time should wrap around gracefully
        encoded = time_to_shawzin_time(1000.0)
        assert len(encoded) == 2
        assert all(char in base64_chars for char in encoded)
    
    def test_time_decoding_invalid_input(self):
        """Test time decoding with invalid input."""
        # Wrong length
        with pytest.raises(ValueError):
            shawzin_time_to_seconds("A")
        
        with pytest.raises(ValueError):
            shawzin_time_to_seconds("ABC")
        
        # Invalid characters
        with pytest.raises(ValueError):
            shawzin_time_to_seconds("!@")


class TestTokenEncoding:
    """Test token encoding functions."""
    
    def test_event_to_shawzin_token_basic(self):
        """Test basic token encoding."""
        token = event_to_shawzin_token("1", 0.0)
        
        assert len(token) == 3
        assert token[0] == "1"
        assert token[1] in base64_chars
        assert token[2] in base64_chars
    
    def test_event_to_shawzin_token_timing(self):
        """Test token encoding with different timings."""
        test_chars = ["1", "q", "a", "z"]
        test_times = [0.0, 0.125, 0.5, 1.0]
        
        for char in test_chars:
            for time_val in test_times:
                token = event_to_shawzin_token(char, time_val)
                
                assert len(token) == 3
                assert token[0] == char
                # Decode timing to verify
                decoded_time = shawzin_time_to_seconds(token[1:3])
                assert abs(decoded_time - time_val) <= 0.0625
    
    def test_quick_encode_token(self):
        """Test quick token encoding function."""
        token = quick_encode_token("2", 0.25)
        
        assert len(token) == 3
        assert token[0] == "2"
        
        # Should be same as full function
        full_token = event_to_shawzin_token("2", 0.25)
        assert token == full_token
    
    def test_create_scale_header(self):
        """Test scale header creation."""
        for scale_id in range(1, 10):
            header = create_scale_header(scale_id)
            assert header == f"{scale_id}"


class TestEventsToText:
    """Test events to text conversion."""
    
    def create_test_events(self, count: int = 5) -> List[ShawzinNote]:
        """Create test events."""
        events = []
        for i in range(count):
            event = ShawzinNote(
                character=["1", "q", "a", "z", "2"][i % 5],
                time_sec=i * 0.5,
                duration_sec=0.4,
                original_midi=60 + i,
                mapped_midi=60 + i,
                scale_id=2,
                octave_shift=0
            )
            events.append(event)
        return events
    
    def test_events_to_shawzin_text_basic(self):
        """Test basic events to text conversion."""
        events = self.create_test_events(3)
        
        chunks = events_to_shawzin_text(events)
        
        assert len(chunks) >= 1
        assert chunks[0].startswith("2")  # Scale header
    
    def test_events_to_shawzin_text_empty(self):
        """Test conversion with empty events."""
        chunks = events_to_shawzin_text([])
        
        assert len(chunks) == 1
        assert chunks[0].startswith("1")
    
    def test_events_to_shawzin_text_chunking(self):
        """Test chunking behavior."""
        # Create many events to force chunking
        events = self.create_test_events(100)
        
        chunks = events_to_shawzin_text(events, max_notes=50)
        
        # Should create multiple chunks
        assert len(chunks) >= 2
        
        # Each chunk should start with scale header
        for chunk in chunks:
            # First line should be the scale header (just the number)
            first_line = chunk.split('\n')[0]
            assert first_line.isdigit()
    
    def test_events_to_shawzin_text_line_length(self):
        """Test line length limiting."""
        events = self.create_test_events(20)
        
        chunks = events_to_shawzin_text(events, max_length=50)
        
        # Check line lengths
        for chunk in chunks:
            lines = chunk.split('\n')
            for line in lines:
                assert len(line) <= 50
    
    def test_events_to_shawzin_text_no_offsets(self):
        """Test conversion without timing offsets."""
        events = self.create_test_events(5)
        
        chunks = events_to_shawzin_text(events, keep_offsets=False)
        
        assert len(chunks) >= 1
        # Without offsets, all timing should be zero
        content = chunks[0]
        lines = content.split('\n')
        
        # Check that timing characters indicate zero time
        for line in lines[1:]:  # Skip header
            if len(line) >= 3:
                for i in range(1, len(line), 3):
                    if i + 2 < len(line):
                        time_chars = line[i+1:i+3]
                        decoded_time = shawzin_time_to_seconds(time_chars)
                        assert decoded_time == 0.0


class TestFileIO:
    """Test file input/output functions."""
    
    def test_write_shawzin_file_melody_mode(self):
        """Test writing file in melody mode."""
        chunks = ["#2", "1AA2BB3CC"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test")
            written_files = write_shawzin_file(output_path, chunks, mode='melody')
            
            assert len(written_files) == 1
            assert written_files[0].endswith('.txt')
            assert os.path.exists(written_files[0])
            
            # Check content
            with open(written_files[0], 'r') as f:
                content = f.read()
                assert content == chunks[0]
    
    def test_write_shawzin_file_full_mode(self):
        """Test writing file in full mode."""
        chunks = ["#2\n1AA2BB3CC", "#2\nqDDeEEaFF"]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test")
            written_files = write_shawzin_file(output_path, chunks, mode='full')
            
            assert len(written_files) == 2
            
            # Check first file
            with open(written_files[0], 'r') as f:
                content = f.read()
                assert content == chunks[0]
            
            # Check second file
            with open(written_files[1], 'r') as f:
                content = f.read()
                assert content == chunks[1]
    
    def test_read_shawzin_file_basic(self):
        """Test reading Shawzin file."""
        content = "2\n1AA2BB3CC"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            scale_id, notes = read_shawzin_file(temp_path)
            
            assert scale_id == 2
            assert len(notes) >= 1
            
            # Check first note
            char, time = notes[0]
            assert char in "123qweasdzxc"
            assert time >= 0.0
        
        finally:
            os.unlink(temp_path)
    
    def test_read_shawzin_file_invalid(self):
        """Test reading invalid Shawzin file."""
        content = "invalid content without header"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Should fallback to scale_id = 1 for invalid content
            scale_id, notes = read_shawzin_file(temp_path)
            assert scale_id == 1  # Fallback behavior
        
        finally:
            os.unlink(temp_path)


class TestShawzinEncoder:
    """Test the main ShawzinEncoder class."""
    
    def create_test_events(self, count: int = 5) -> List[ShawzinNote]:
        """Create test events."""
        events = []
        for i in range(count):
            event = ShawzinNote(
                character=["1", "q", "a", "z", "2"][i % 5],
                time_sec=i * 0.5,
                duration_sec=0.4,
                original_midi=60 + i,
                mapped_midi=60 + i,
                scale_id=2,
                octave_shift=0
            )
            events.append(event)
        return events
    
    def test_encoder_initialization(self):
        """Test encoder initialization."""
        # Default initialization
        encoder1 = ShawzinEncoder()
        assert encoder1.settings is not None
        
        # Custom settings
        settings = EncodingSettings(seconds_per_tick=0.125)
        encoder2 = ShawzinEncoder(settings)
        assert encoder2.settings.seconds_per_tick == 0.125
    
    def test_encode_events_melody_mode(self):
        """Test encoding in melody mode."""
        encoder = ShawzinEncoder()
        events = self.create_test_events(10)
        
        chunks = encoder.encode_events(events, mode='melody')
        
        assert len(chunks) >= 1
        assert encoder.stats['notes_encoded'] == 10
        assert encoder.stats['chunks_created'] >= 1
    
    def test_encode_events_full_mode(self):
        """Test encoding in full mode."""
        encoder = ShawzinEncoder()
        events = self.create_test_events(10)
        
        chunks = encoder.encode_events(events, mode='full')
        
        assert len(chunks) >= 1
        assert encoder.stats['notes_encoded'] == 10
    
    def test_encode_to_file(self):
        """Test encoding to file."""
        encoder = ShawzinEncoder()
        events = self.create_test_events(5)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test")
            written_files = encoder.encode_to_file(events, output_path)
            
            assert len(written_files) >= 1
            assert all(os.path.exists(f) for f in written_files)
    
    def test_get_encoding_stats(self):
        """Test encoding statistics."""
        encoder = ShawzinEncoder()
        events = self.create_test_events(8)
        
        # Before encoding
        stats = encoder.get_encoding_stats()
        assert stats['notes_encoded'] == 0
        
        # After encoding
        encoder.encode_events(events)
        stats = encoder.get_encoding_stats()
        assert stats['notes_encoded'] == 8
        assert stats['total_duration'] > 0.0
    
    def test_validate_encoding(self):
        """Test encoding validation."""
        encoder = ShawzinEncoder()
        events = self.create_test_events(5)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test")
            written_files = encoder.encode_to_file(events, output_path)
            
            # Validate the encoding
            validation = encoder.validate_encoding(events, written_files[0])
            
            assert validation['valid'] is True
            assert validation['scale_id'] == 2
            assert validation['original_notes'] == 5
            assert validation['note_accuracy'] > 0.8  # Should be high accuracy


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def create_test_events(self, count: int = 3) -> List[ShawzinNote]:
        """Create test events."""
        events = []
        for i in range(count):
            event = ShawzinNote(
                character=["1", "q", "a"][i % 3],
                time_sec=i * 0.5,
                duration_sec=0.4,
                original_midi=60 + i,
                mapped_midi=60 + i,
                scale_id=2,
                octave_shift=0
            )
            events.append(event)
        return events
    
    def test_encode_shawzin_melody(self):
        """Test melody encoding convenience function."""
        events = self.create_test_events()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "melody")
            written_files = encode_shawzin_melody(events, output_path)
            
            assert len(written_files) == 1
            assert os.path.exists(written_files[0])
    
    def test_encode_shawzin_full(self):
        """Test full encoding convenience function."""
        events = self.create_test_events()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "full")
            written_files = encode_shawzin_full(events, output_path)
            
            assert len(written_files) >= 1
            assert all(os.path.exists(f) for f in written_files)
    
    def test_analyze_timing_accuracy(self):
        """Test timing accuracy analysis."""
        events = self.create_test_events(5)
        
        analysis = analyze_timing_accuracy(events)
        
        assert 'quantization_error' in analysis
        assert 'max_error' in analysis
        assert 'precision' in analysis
        
        assert analysis['quantization_error'] >= 0.0
        assert analysis['max_error'] >= 0.0
        assert 0.0 <= analysis['precision'] <= 1.0
    
    def test_analyze_timing_accuracy_empty(self):
        """Test timing analysis with empty events."""
        analysis = analyze_timing_accuracy([])
        
        assert analysis['quantization_error'] == 0.0
        assert analysis['max_error'] == 0.0
        assert analysis['precision'] == 1.0


class TestEncodingConsistency:
    """Test encoding consistency and musical correctness."""
    
    def test_synthetic_melody_encoding(self):
        """Test encoding a synthetic melody and verify tokens."""
        # Create a simple C major scale
        notes = ["1", "q", "a", "z", "2", "w", "s", "x"]
        events = []
        
        for i, note in enumerate(notes):
            event = ShawzinNote(
                character=note,
                time_sec=i * 0.5,  # Quarter notes at 120 BPM
                duration_sec=0.4,
                original_midi=60 + i,
                mapped_midi=60 + i,
                scale_id=2,
                octave_shift=0
            )
            events.append(event)
        
        chunks = events_to_shawzin_text(events)
        
        assert len(chunks) >= 1
        assert chunks[0].startswith("2")
        
        # Parse the encoded content
        lines = chunks[0].split('\n')
        content = ''.join(lines[1:])  # Skip header
        
        # Should have tokens for each note
        token_count = len(content) // 3
        assert token_count == len(notes)
        
        # Check first few tokens
        for i in range(min(3, token_count)):
            token = content[i*3:(i+1)*3]
            assert len(token) == 3
            assert token[0] == notes[i]
    
    def test_timing_consistency(self):
        """Test that timing encoding is consistent."""
        # Create events with specific timing
        events = []
        times = [0.0, 0.5, 1.0, 1.5, 2.0]  # Regular quarter notes
        
        for i, time in enumerate(times):
            event = ShawzinNote(
                character="1",
                time_sec=time,
                duration_sec=0.4,
                original_midi=60,
                mapped_midi=60,
                scale_id=2,
                octave_shift=0
            )
            events.append(event)
        
        chunks = events_to_shawzin_text(events)
        
        # Parse and decode timing
        lines = chunks[0].split('\n')
        content = ''.join(lines[1:])
        
        decoded_times = []
        current_time = 0.0
        
        for i in range(0, len(content), 3):
            if i + 2 < len(content):
                token = content[i:i+3]
                time_str = token[1:3]
                delta = shawzin_time_to_seconds(time_str)
                current_time += delta
                decoded_times.append(current_time)
        
        # Check timing accuracy
        for original, decoded in zip(times[1:], decoded_times):  # Skip first (always 0)
            assert abs(original - decoded) <= 0.125  # Within reasonable tolerance
    
    def test_scale_header_consistency(self):
        """Test that scale headers are consistent."""
        for scale_id in range(1, 10):
            events = [
                ShawzinNote(
                    character="1",
                    time_sec=0.0,
                    duration_sec=0.5,
                    original_midi=60,
                    mapped_midi=60,
                    scale_id=scale_id,
                    octave_shift=0
                )
            ]
            
            chunks = events_to_shawzin_text(events)
            
            assert chunks[0].startswith(f"{scale_id}")
    
    def test_round_trip_consistency(self):
        """Test that encode-decode round trip is consistent."""
        # Create test events
        events = []
        for i in range(5):
            event = ShawzinNote(
                character=["1", "q", "a", "z", "2"][i],
                time_sec=i * 0.5,
                duration_sec=0.4,
                original_midi=60 + i,
                mapped_midi=60 + i,
                scale_id=2,
                octave_shift=0
            )
            events.append(event)
        
        # Encode to file
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "roundtrip")
            encoder = ShawzinEncoder()
            written_files = encoder.encode_to_file(events, output_path)
            
            # Read back and compare
            scale_id, decoded_notes = read_shawzin_file(written_files[0])
            
            assert scale_id == 2
            assert len(decoded_notes) == len(events)
            
            # Check character consistency
            for original, (decoded_char, decoded_time) in zip(events, decoded_notes):
                assert original.character == decoded_char
                # Timing should be reasonably close
                assert abs(original.time_sec - decoded_time) <= 0.125


if __name__ == '__main__':
    pytest.main([__file__])
