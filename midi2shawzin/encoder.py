"""
Shawzin String Encoder

Encodes mapped Shawzin notes to Warframe-compatible string format with
time encoding, delta-time encoding, and chunking for file output.
"""

import math
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from .mapper import ShawzinNote
from .shawzin_mapping import base64_chars


@dataclass
class EncodingSettings:
    """Settings for Shawzin string encoding based on official Warframe limits."""
    seconds_per_measure: float = 4.0      # Duration of one measure in seconds
    seconds_per_tick: float = 0.0625      # Duration of one tick (1/16 note at 120 BPM)
    max_notes_per_chunk: int = 1666       # Maximum notes before starting new chunk (Warframe limit)
    max_length_per_line: int = 256        # Maximum characters per line (Warframe limit)
    max_string_length: int = 256          # Maximum total string length (Warframe limit)
    max_playback_seconds: float = 256.0   # Maximum playback duration (Warframe limit)
    keep_offsets: bool = True             # Whether to preserve timing offsets
    scale_id: int = 1                     # Default scale ID for headers


def time_to_shawzin_time(delta_seconds: float, 
                        seconds_per_measure: float = 4.0,
                        seconds_per_tick: float = 0.0625,
                        base64_chars: List[str] = None) -> str:
    """
    Convert delta time in seconds to Shawzin two-character time encoding.
    
    Uses the same encoding scheme as original Warframe format:
    - First char: measure index (base64)
    - Second char: tick index within measure (base64)
    
    Args:
        delta_seconds: Time since last encoded note
        seconds_per_measure: Duration of one measure
        seconds_per_tick: Duration of one tick
        base64_chars: Base64 character set for encoding
        
    Returns:
        Two-character time string
    """
    if base64_chars is None:
        base64_chars = globals()['base64_chars']
    
    # Calculate total ticks from delta time
    total_ticks = max(0, round(delta_seconds / seconds_per_tick))
    
    # Calculate ticks per measure
    ticks_per_measure = max(1, round(seconds_per_measure / seconds_per_tick))
    
    # Split into measures and ticks within measure
    measure_index = total_ticks // ticks_per_measure
    tick_index = total_ticks % ticks_per_measure
    
    # Encode using base64 characters (with wraparound)
    measure_char = base64_chars[measure_index % len(base64_chars)]
    tick_char = base64_chars[tick_index % len(base64_chars)]
    
    return measure_char + tick_char


def shawzin_time_to_seconds(time_str: str,
                           seconds_per_measure: float = 4.0,
                           seconds_per_tick: float = 0.0625,
                           base64_chars: List[str] = None) -> float:
    """
    Convert Shawzin two-character time encoding back to seconds.
    
    Args:
        time_str: Two-character time string
        seconds_per_measure: Duration of one measure
        seconds_per_tick: Duration of one tick
        base64_chars: Base64 character set for decoding
        
    Returns:
        Time in seconds
    """
    if base64_chars is None:
        base64_chars = globals()['base64_chars']
    
    if len(time_str) != 2:
        raise ValueError(f"Time string must be 2 characters, got {len(time_str)}")
    
    # Decode characters to indices
    try:
        measure_index = base64_chars.index(time_str[0])
        tick_index = base64_chars.index(time_str[1])
    except ValueError as e:
        raise ValueError(f"Invalid character in time string: {e}")
    
    # Calculate ticks per measure
    ticks_per_measure = max(1, round(seconds_per_measure / seconds_per_tick))
    
    # Calculate total ticks
    total_ticks = measure_index * ticks_per_measure + tick_index
    
    # Convert to seconds
    return total_ticks * seconds_per_tick


def event_to_shawzin_token(shawzin_char: str, 
                          quantized_delta_seconds: float,
                          settings: Optional[EncodingSettings] = None) -> str:
    """
    Convert a Shawzin note to a 3-character token.
    
    Format: [note_char][time_char1][time_char2]
    
    Args:
        shawzin_char: Shawzin note character (1-3, q-e, a-d, z-c)
        quantized_delta_seconds: Time since last note
        settings: Encoding settings
        
    Returns:
        3-character token string
    """
    if settings is None:
        settings = EncodingSettings()
    
    # Encode timing
    time_chars = time_to_shawzin_time(
        quantized_delta_seconds,
        settings.seconds_per_measure,
        settings.seconds_per_tick,
        base64_chars
    )
    
    # Combine note and timing
    return shawzin_char + time_chars


def create_scale_header(scale_id: int) -> str:
    """
    Create scale header string for Warframe Shawzin format.
    
    Args:
        scale_id: Scale ID (1-9)
        
    Returns:
        Scale header string (without # prefix for Warframe compatibility)
    """
    return f"{scale_id}"


def events_to_shawzin_text(events: List[ShawzinNote],
                          max_notes: int = 1666,
                          max_length: int = 256,
                          keep_offsets: bool = True,
                          settings: Optional[EncodingSettings] = None) -> List[str]:
    """
    Convert Shawzin note events to text chunks for file output.
    
    Handles chunking exactly like original format:
    - If note limit exceeded, start new chunk with scale header
    - If line length exceeded, wrap to new line
    
    Args:
        events: List of ShawzinNote objects
        max_notes: Maximum notes before starting new chunk
        max_length: Maximum characters per line
        keep_offsets: Whether to preserve timing offsets
        settings: Encoding settings
        
    Returns:
        List of text chunks (one per output file)
    """
    if settings is None:
        settings = EncodingSettings()
    
    if not events:
        return [create_scale_header(settings.scale_id)]
    
    chunks = []
    current_chunk_lines = []
    current_line = ""
    notes_in_chunk = 0
    last_time = 0.0
    
    # Group events by scale_id for headers
    scale_id = events[0].scale_id if events else settings.scale_id
    
    # Track if we need multiline format  
    # Warframe expects single-line format: scale_id + notes (no newlines)
    needs_multiline = False  # Always use single-line format for Warframe compatibility
    
    if needs_multiline:
        # Use multiline format with header on separate line (disabled for Warframe)
        current_line = create_scale_header(scale_id)
        current_chunk_lines.append(current_line)
        current_line = ""
    else:
        # Use single line format with inline header (Warframe standard)
        current_line = create_scale_header(scale_id)
    
    for event in events:
        # Calculate delta time
        if keep_offsets:
            delta_time = event.time_sec - last_time
            last_time = event.time_sec
        else:
            delta_time = 0.0  # No timing if offsets disabled
        
        # Create token for this event
        token = event_to_shawzin_token(
            event.character,
            delta_time,
            settings
        )
        
        # Check if we need to start a new chunk
        if notes_in_chunk >= max_notes:
            # Finish current chunk
            if current_line:
                current_chunk_lines.append(current_line)
            chunks.append('\n'.join(current_chunk_lines))
            
            # Start new chunk
            current_chunk_lines = []
            header_line = create_scale_header(event.scale_id)
            current_chunk_lines.append(header_line)
            current_line = ""
            notes_in_chunk = 0
            last_time = event.time_sec  # Reset time reference
            
            # Recalculate delta for new chunk
            if keep_offsets:
                delta_time = 0.0  # First note in chunk has no delta
            
            token = event_to_shawzin_token(
                event.character,
                delta_time,
                settings
            )
        
        # Check if adding token would exceed line length
        # Remove hard Warframe limit since longer strings work fine
        if len(current_line) + len(token) > max_length:
            # Start new line
            current_chunk_lines.append(current_line)
            current_line = token
        else:
            # Add to current line
            current_line += token
        
        notes_in_chunk += 1
    
    # Finish final chunk
    if current_line:
        current_chunk_lines.append(current_line)
    if current_chunk_lines:
        chunks.append('\n'.join(current_chunk_lines))
    
    return chunks if chunks else [create_scale_header(scale_id)]


def write_shawzin_file(output_path: str, 
                      shawzin_chunks: List[str],
                      mode: str = 'melody') -> List[str]:
    """
    Write Shawzin string chunks to file(s).
    
    Args:
        output_path: Base output path (without extension)
        shawzin_chunks: List of text chunks to write
        mode: Output mode ('melody' for single file, 'full' for multiple files)
        
    Returns:
        List of written file paths
    """
    output_path = Path(output_path)
    written_files = []
    
    if mode == 'melody' or len(shawzin_chunks) == 1:
        # Single file output
        file_path = output_path.with_suffix('.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(shawzin_chunks[0])
        written_files.append(str(file_path))
    
    else:
        # Multiple file output (full mode)
        for i, chunk in enumerate(shawzin_chunks):
            if i == 0:
                file_path = output_path.with_suffix('.txt')
            else:
                file_path = output_path.with_name(f"{output_path.stem}_{i+1}.txt")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(chunk)
            written_files.append(str(file_path))
    
    return written_files


def read_shawzin_file(file_path: str) -> Tuple[int, List[Tuple[str, float]]]:
    """
    Read and parse a Shawzin format file.
    
    Args:
        file_path: Path to Shawzin file
        
    Returns:
        Tuple of (scale_id, list of (character, time_seconds) pairs)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if not content:
        raise ValueError("Empty file")
    
    # Find scale header - could be on its own line or at start of content
    lines = content.split('\n')
    first_line = lines[0].strip()
    
    # Check if first character is a scale ID (1-9)
    if first_line and first_line[0].isdigit():
        scale_char = first_line[0]
        scale_id = int(scale_char)
        if not (1 <= scale_id <= 9):
            raise ValueError(f"Scale ID must be 1-9, got {scale_id}")
        
        # Check if it's a header-only line or contains content
        if len(first_line) == 1:
            # Header on its own line
            token_content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
        else:
            # Header inline with content
            token_content = first_line[1:]  # Rest after scale ID
            if len(lines) > 1:
                token_content += '\n' + '\n'.join(lines[1:])
    else:
        # Fallback: assume scale 1 if no header found
        scale_id = 1
        token_content = content
    
    # Filter out whitespace and newlines, keep only valid token characters
    filtered_content = ''.join(c for c in token_content if c.isalnum())
    
    # Parse note tokens
    notes = []
    current_time = 0.0
    
    # Process in 3-character chunks
    for i in range(0, len(filtered_content), 3):
        if i + 2 < len(filtered_content):
            token = filtered_content[i:i+3]
            char = token[0]
            time_str = token[1:3]
            
            # Decode timing
            delta_seconds = shawzin_time_to_seconds(time_str)
            current_time += delta_seconds
            
            notes.append((char, current_time))
    
    return scale_id, notes


class ShawzinEncoder:
    """Advanced Shawzin string encoder with multiple output modes."""
    
    def __init__(self, settings: Optional[EncodingSettings] = None):
        """Initialize encoder with settings."""
        self.settings = settings or EncodingSettings()
        self.stats = {
            'notes_encoded': 0,
            'chunks_created': 0,
            'total_duration': 0.0
        }
    
    def encode_events(self, events: List[ShawzinNote], 
                     mode: str = 'melody') -> List[str]:
        """
        Encode Shawzin note events to string format.
        
        Args:
            events: List of ShawzinNote objects
            mode: Encoding mode ('melody' or 'full')
            
        Returns:
            List of encoded text chunks
        """
        # Adjust settings based on mode
        if mode == 'melody':
            # Melody mode: more permissive chunking
            max_notes = self.settings.max_notes_per_chunk * 2
            keep_offsets = True
        else:
            # Full mode: strict chunking
            max_notes = self.settings.max_notes_per_chunk
            keep_offsets = self.settings.keep_offsets
        
        # Encode to text chunks
        chunks = events_to_shawzin_text(
            events,
            max_notes=max_notes,
            max_length=self.settings.max_length_per_line,
            keep_offsets=keep_offsets,
            settings=self.settings
        )
        
        # Update statistics
        self.stats['notes_encoded'] = len(events)
        self.stats['chunks_created'] = len(chunks)
        if events:
            self.stats['total_duration'] = max(e.time_sec for e in events)
        
        return chunks
    
    def encode_to_file(self, events: List[ShawzinNote], 
                      output_path: str,
                      mode: str = 'melody') -> List[str]:
        """
        Encode events and write to file(s).
        
        Args:
            events: List of ShawzinNote objects
            output_path: Base output path
            mode: Output mode ('melody' or 'full')
            
        Returns:
            List of written file paths
        """
        chunks = self.encode_events(events, mode)
        return write_shawzin_file(output_path, chunks, mode)
    
    def get_encoding_stats(self) -> Dict[str, Any]:
        """Get encoding statistics."""
        return self.stats.copy()
    
    def validate_encoding(self, original_events: List[ShawzinNote],
                         file_path: str) -> Dict[str, Any]:
        """
        Validate encoded file by reading it back and comparing.
        
        Args:
            original_events: Original events that were encoded
            file_path: Path to encoded file
            
        Returns:
            Validation results dictionary
        """
        try:
            scale_id, decoded_notes = read_shawzin_file(file_path)
            
            # Compare note counts
            original_count = len(original_events)
            decoded_count = len(decoded_notes)
            
            # Compare timing accuracy (within tolerance)
            timing_errors = []
            for i, (original, (char, time)) in enumerate(zip(original_events, decoded_notes)):
                if i < len(decoded_notes):
                    time_error = abs(original.time_sec - time)
                    timing_errors.append(time_error)
            
            avg_timing_error = sum(timing_errors) / len(timing_errors) if timing_errors else 0.0
            max_timing_error = max(timing_errors) if timing_errors else 0.0
            
            return {
                'valid': True,
                'scale_id': scale_id,
                'original_notes': original_count,
                'decoded_notes': decoded_count,
                'note_accuracy': decoded_count / original_count if original_count > 0 else 0.0,
                'avg_timing_error': avg_timing_error,
                'max_timing_error': max_timing_error,
                'timing_precision': avg_timing_error < self.settings.seconds_per_tick
            }
        
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }


# Convenience functions
def encode_shawzin_melody(events: List[ShawzinNote], 
                         output_path: str) -> List[str]:
    """
    Convenience function to encode melody-only output.
    
    Args:
        events: List of ShawzinNote objects
        output_path: Output file path
        
    Returns:
        List of written file paths
    """
    encoder = ShawzinEncoder()
    return encoder.encode_to_file(events, output_path, mode='melody')


def encode_shawzin_full(events: List[ShawzinNote], 
                       output_path: str) -> List[str]:
    """
    Convenience function to encode full-mode output.
    
    Args:
        events: List of ShawzinNote objects
        output_path: Output file path
        
    Returns:
        List of written file paths
    """
    encoder = ShawzinEncoder()
    return encoder.encode_to_file(events, output_path, mode='full')


def quick_encode_token(char: str, delta_seconds: float) -> str:
    """
    Quick encoding of a single note token.
    
    Args:
        char: Shawzin character
        delta_seconds: Time since last note
        
    Returns:
        3-character token
    """
    return event_to_shawzin_token(char, delta_seconds)


def analyze_timing_accuracy(events: List[ShawzinNote],
                           settings: Optional[EncodingSettings] = None) -> Dict[str, float]:
    """
    Analyze timing accuracy for a sequence of events.
    
    Args:
        events: List of ShawzinNote objects
        settings: Encoding settings
        
    Returns:
        Dictionary with timing analysis
    """
    if settings is None:
        settings = EncodingSettings()
    
    if not events:
        return {'quantization_error': 0.0, 'max_error': 0.0, 'precision': 1.0}
    
    quantization_errors = []
    
    for i, event in enumerate(events):
        if i > 0:
            # Calculate delta time
            delta_time = event.time_sec - events[i-1].time_sec
            
            # Encode and decode to see quantization error
            token = event_to_shawzin_token(event.character, delta_time, settings)
            decoded_time = shawzin_time_to_seconds(token[1:3])
            
            error = abs(delta_time - decoded_time)
            quantization_errors.append(error)
    
    if not quantization_errors:
        return {'quantization_error': 0.0, 'max_error': 0.0, 'precision': 1.0}
    
    avg_error = sum(quantization_errors) / len(quantization_errors)
    max_error = max(quantization_errors)
    precision = 1.0 - (avg_error / settings.seconds_per_tick)
    
    return {
        'quantization_error': avg_error,
        'max_error': max_error,
        'precision': max(0.0, precision)
    }
