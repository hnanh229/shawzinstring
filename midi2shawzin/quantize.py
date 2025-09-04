"""
Musical Quantization Module

Quantizes musical events to a rhythmic grid for better timing accuracy.
Supports various subdivisions, quantization modes, and humanization options.
"""

import random
from typing import List, Literal, Optional, Tuple
from dataclasses import dataclass, replace
from .midi_io import Event


@dataclass
class QuantizeSettings:
    """Settings for quantization process."""
    subdivision: int = 16           # Number of subdivisions per measure (1/16 notes for subdivision=16)
    mode: Literal['nearest', 'floor'] = 'nearest'    # Quantization mode
    humanize_ms: Optional[float] = None              # Add random jitter in milliseconds
    time_signature: Tuple[int, int] = (4, 4)        # Time signature (numerator, denominator)
    preserve_timing: bool = True                     # Keep original delta_sec relationships
    

def seconds_to_beats(seconds: float, tempo_us_per_beat: int) -> float:
    """
    Convert seconds to musical beats based on tempo.
    
    Args:
        seconds: Time in seconds
        tempo_us_per_beat: Tempo in microseconds per beat (from MIDI)
        
    Returns:
        Time in beats (float)
    """
    seconds_per_beat = tempo_us_per_beat / 1_000_000.0
    return seconds / seconds_per_beat


def beats_to_seconds(beats: float, tempo_us_per_beat: int) -> float:
    """
    Convert musical beats to seconds based on tempo.
    
    Args:
        beats: Time in beats
        tempo_us_per_beat: Tempo in microseconds per beat (from MIDI)
        
    Returns:
        Time in seconds (float)
    """
    seconds_per_beat = tempo_us_per_beat / 1_000_000.0
    return beats * seconds_per_beat


def quantize_beat_to_grid(beat: float, subdivision: int, mode: Literal['nearest', 'floor'] = 'nearest') -> float:
    """
    Quantize a beat time to the nearest grid position.
    
    Args:
        beat: Beat time to quantize
        subdivision: Number of subdivisions per measure
        mode: Quantization mode ('nearest' or 'floor')
        
    Returns:
        Quantized beat time
    """
    # Calculate grid resolution (beats per subdivision)
    # For 4/4 time with subdivision=16: 4 beats / 16 subdivisions = 0.25 beats per subdivision
    beats_per_subdivision = 4.0 / subdivision
    
    if mode == 'floor':
        # Floor to nearest grid position
        grid_position = int(beat / beats_per_subdivision)
        return grid_position * beats_per_subdivision
    else:  # mode == 'nearest'
        # Round to nearest grid position
        grid_position = round(beat / beats_per_subdivision)
        return grid_position * beats_per_subdivision


def add_humanization(time_sec: float, humanize_ms: Optional[float]) -> float:
    """
    Add small random jitter to timing for humanization.
    
    Args:
        time_sec: Original time in seconds
        humanize_ms: Maximum jitter in milliseconds (±)
        
    Returns:
        Humanized time in seconds
    """
    if humanize_ms is None or humanize_ms <= 0:
        return time_sec
    
    # Add random jitter between -humanize_ms and +humanize_ms
    jitter_sec = random.uniform(-humanize_ms, humanize_ms) / 1000.0
    return max(0.0, time_sec + jitter_sec)  # Ensure non-negative time


def quantize_events(events: List[Event], 
                   ticks_per_beat: int, 
                   tempo_us_per_beat: int,
                   settings: Optional[QuantizeSettings] = None) -> List[Event]:
    """
    Quantize events to a rhythmic grid.
    
    Args:
        events: List of events to quantize
        ticks_per_beat: MIDI ticks per beat
        tempo_us_per_beat: Tempo in microseconds per beat
        settings: Quantization settings (defaults applied if None)
        
    Returns:
        List of quantized events with updated timing
    """
    if not events:
        return []
        
    if settings is None:
        settings = QuantizeSettings()
    
    quantized_events = []
    
    for event in events:
        # Convert seconds to beats
        beat_time = seconds_to_beats(event.time_sec, tempo_us_per_beat)
        
        # Quantize to grid
        quantized_beat = quantize_beat_to_grid(beat_time, settings.subdivision, settings.mode)
        
        # Convert back to seconds
        quantized_seconds = beats_to_seconds(quantized_beat, tempo_us_per_beat)
        
        # Apply humanization if requested
        final_time = add_humanization(quantized_seconds, settings.humanize_ms)
        
        # Create quantized event
        quantized_event = replace(event, time_sec=final_time)
        quantized_events.append(quantized_event)
    
    # Sort by time to ensure proper ordering
    quantized_events.sort(key=lambda e: e.time_sec)
    
    # Recalculate delta times if preserve_timing is enabled
    if settings.preserve_timing:
        for i in range(len(quantized_events)):
            if i == 0:
                quantized_events[i] = replace(quantized_events[i], delta_sec=quantized_events[i].time_sec)
            else:
                delta = quantized_events[i].time_sec - quantized_events[i-1].time_sec
                quantized_events[i] = replace(quantized_events[i], delta_sec=delta)
    
    return quantized_events


def detect_tempo_from_events(events: List[Event], min_tempo: float = 60.0, max_tempo: float = 200.0) -> float:
    """
    Detect likely tempo from event timing patterns.
    
    Args:
        events: List of events to analyze
        min_tempo: Minimum reasonable tempo (BPM)
        max_tempo: Maximum reasonable tempo (BPM)
        
    Returns:
        Estimated tempo in BPM
    """
    if len(events) < 2:
        return 120.0  # Default tempo
    
    # Calculate intervals between consecutive events
    intervals = []
    for i in range(1, len(events)):
        interval = events[i].time_sec - events[i-1].time_sec
        if interval > 0.05:  # Ignore very short intervals (< 50ms)
            intervals.append(interval)
    
    if not intervals:
        return 120.0
    
    # Find the most common interval (likely beat duration)
    # Use histogram approach for robustness
    from collections import Counter
    
    # Round intervals to 10ms precision for grouping
    rounded_intervals = [round(interval, 2) for interval in intervals]
    interval_counts = Counter(rounded_intervals)
    
    # Get most common interval
    most_common_interval = interval_counts.most_common(1)[0][0]
    
    # Convert to BPM (assuming most common interval is quarter note)
    estimated_bpm = 60.0 / most_common_interval
    
    # Clamp to reasonable range
    estimated_bpm = max(min_tempo, min(max_tempo, estimated_bpm))
    
    return estimated_bpm


class Quantizer:
    """Quantizer class for processing musical events."""
    
    def __init__(self, settings: Optional[QuantizeSettings] = None):
        """Initialize quantizer with settings."""
        self.settings = settings or QuantizeSettings()
        self.last_tempo = 120.0  # Default tempo in BPM
    
    def quantize(self, events: List[Event], 
                tempo_bpm: Optional[float] = None,
                ticks_per_beat: int = 480) -> List[Event]:
        """
        Quantize events using stored settings.
        
        Args:
            events: Events to quantize
            tempo_bpm: Tempo in BPM (will detect if None)
            ticks_per_beat: MIDI ticks per beat
            
        Returns:
            Quantized events
        """
        if not events:
            return []
        
        # Detect tempo if not provided
        if tempo_bpm is None:
            tempo_bpm = detect_tempo_from_events(events)
        
        self.last_tempo = tempo_bpm
        
        # Convert BPM to microseconds per beat
        tempo_us_per_beat = int(60_000_000 / tempo_bpm)
        
        return quantize_events(events, ticks_per_beat, tempo_us_per_beat, self.settings)
    
    def get_grid_positions(self, duration_beats: float = 4.0) -> List[float]:
        """
        Get all grid positions for visualization/debugging.
        
        Args:
            duration_beats: Duration in beats to generate grid for
            
        Returns:
            List of grid positions in beats
        """
        beats_per_subdivision = 4.0 / self.settings.subdivision
        positions = []
        
        current_beat = 0.0
        while current_beat <= duration_beats:
            positions.append(current_beat)
            current_beat += beats_per_subdivision
            
        return positions


# Convenience functions for common quantizations
def quantize_to_sixteenth_notes(events: List[Event], tempo_bpm: float = 120.0) -> List[Event]:
    """Quantize events to 1/16 note grid."""
    settings = QuantizeSettings(subdivision=16, mode='nearest')
    quantizer = Quantizer(settings)
    return quantizer.quantize(events, tempo_bpm)


def quantize_to_eighth_notes(events: List[Event], tempo_bpm: float = 120.0) -> List[Event]:
    """Quantize events to 1/8 note grid."""
    settings = QuantizeSettings(subdivision=8, mode='nearest')
    quantizer = Quantizer(settings)
    return quantizer.quantize(events, tempo_bpm)


def quantize_with_humanization(events: List[Event], 
                              tempo_bpm: float = 120.0,
                              jitter_ms: float = 5.0) -> List[Event]:
    """Quantize events with subtle humanization."""
    settings = QuantizeSettings(subdivision=16, mode='nearest', humanize_ms=jitter_ms)
    quantizer = Quantizer(settings)
    return quantizer.quantize(events, tempo_bpm)
