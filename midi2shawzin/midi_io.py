"""
MIDI Input/Output Operations

Handles reading MIDI files and extracting note events with timing information.
Uses mido library for MIDI file parsing and provides deterministic event output.
"""

from typing import List, Dict, Tuple, Optional, Union
import mido
from dataclasses import dataclass

@dataclass
class Event:
    """Represents a single MIDI event with timing information."""
    type: str           # 'note_on', 'note_off', 'tempo', 'time_signature'
    note: Optional[int] = None      # MIDI note number (0-127) for note events
    time_sec: float = 0.0           # Absolute time in seconds from start
    delta_sec: float = 0.0          # Delta time since previous event
    velocity: int = 0               # Velocity (0-127) for note events
    channel: int = 0                # MIDI channel (0-15)
    track_index: int = 0            # Track number in MIDI file
    tempo: Optional[int] = None     # Microseconds per beat for tempo events
    numerator: Optional[int] = None # Time signature numerator
    denominator: Optional[int] = None # Time signature denominator

def read_midi(filepath: str) -> Dict:
    """
    Read MIDI file and extract events with timing information.
    
    Args:
        filepath: Path to MIDI file
        
    Returns:
        Dictionary containing:
        - ticks_per_beat: MIDI resolution
        - tracks: List of track dictionaries with name and events
        - tempo: Default microseconds per beat
        
    Raises:
        FileNotFoundError: If MIDI file doesn't exist
        ValueError: If MIDI file is corrupted or invalid
    """
    try:
        mid = mido.MidiFile(filepath)
    except Exception as e:
        raise ValueError(f"Could not read MIDI file: {e}")
    
    # Get basic MIDI file info
    ticks_per_beat = mid.ticks_per_beat
    default_tempo = 500000  # Default tempo: 120 BPM (500000 microseconds per beat)
    
    tracks = []
    
    for track_index, track in enumerate(mid.tracks):
        track_name = f"Track {track_index}"
        events = []
        
        # Process track to extract events
        absolute_ticks = 0
        absolute_seconds = 0.0
        current_tempo = default_tempo
        
        for msg in track:
            # Update absolute timing
            absolute_ticks += msg.time
            delta_seconds = ticks_to_seconds(msg.time, ticks_per_beat, current_tempo)
            absolute_seconds += delta_seconds
            
            # Process different message types
            if msg.type == 'note_on' and msg.velocity > 0:
                # Filter out percussion channel (channel 9, which is index 9)
                if msg.channel != 9:
                    event = Event(
                        type='note_on',
                        note=msg.note,
                        time_sec=absolute_seconds,
                        delta_sec=delta_seconds,
                        velocity=msg.velocity,
                        channel=msg.channel,
                        track_index=track_index
                    )
                    events.append(event)
                    
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                # Filter out percussion channel
                if msg.channel != 9:
                    event = Event(
                        type='note_off',
                        note=msg.note,
                        time_sec=absolute_seconds,
                        delta_sec=delta_seconds,
                        velocity=msg.velocity if msg.type == 'note_off' else 0,
                        channel=msg.channel,
                        track_index=track_index
                    )
                    events.append(event)
                    
            elif msg.type == 'set_tempo':
                current_tempo = msg.tempo
                event = Event(
                    type='tempo',
                    time_sec=absolute_seconds,
                    delta_sec=delta_seconds,
                    track_index=track_index,
                    tempo=msg.tempo
                )
                events.append(event)
                
            elif msg.type == 'time_signature':
                event = Event(
                    type='time_signature',
                    time_sec=absolute_seconds,
                    delta_sec=delta_seconds,
                    track_index=track_index,
                    numerator=msg.numerator,
                    denominator=msg.denominator
                )
                events.append(event)
                
            elif msg.type == 'track_name':
                track_name = msg.name
        
        tracks.append({
            'name': track_name,
            'events': events
        })
    
    return {
        'ticks_per_beat': ticks_per_beat,
        'tracks': tracks,
        'tempo': default_tempo
    }

def choose_melody_track(midi_data: Dict) -> int:
    """
    Choose the most likely melody track using heuristics.
    
    Args:
        midi_data: Dictionary returned by read_midi()
        
    Returns:
        Index of the best melody track
        
    Heuristics:
    1. Track with most note_on events
    2. Prefer tracks with higher average pitch
    3. Avoid percussion-heavy tracks
    """
    if not midi_data['tracks']:
        return 0
    
    best_track = 0
    best_score = -1
    
    for i, track in enumerate(midi_data['tracks']):
        events = track['events']
        
        # Count note events
        note_on_count = sum(1 for event in events if event.type == 'note_on')
        
        if note_on_count == 0:
            continue
            
        # Calculate average pitch
        pitches = [event.note for event in events if event.type == 'note_on' and event.note is not None]
        avg_pitch = sum(pitches) / len(pitches) if pitches else 0
        
        # Calculate note density (notes per second)
        total_time = max((event.time_sec for event in events), default=1.0)
        note_density = note_on_count / total_time
        
        # Score calculation: prioritize note count, then pitch, then density
        score = note_on_count * 10 + avg_pitch * 0.1 + note_density
        
        if score > best_score:
            best_score = score
            best_track = i
    
    return best_track

def ticks_to_seconds(ticks: int, ticks_per_beat: int, tempo_microseconds: int) -> float:
    """
    Convert MIDI ticks to seconds based on tempo.
    
    Args:
        ticks: Number of MIDI ticks
        ticks_per_beat: MIDI resolution (ticks per quarter note)
        tempo_microseconds: Microseconds per quarter note
        
    Returns:
        Time in seconds
    """
    if ticks_per_beat == 0:
        return 0.0
    
    # Convert ticks to beats, then beats to seconds
    beats = ticks / ticks_per_beat
    seconds = beats * (tempo_microseconds / 1_000_000.0)
    return seconds

def get_note_events(midi_data: Dict, track_index: Optional[int] = None) -> List[Event]:
    """
    Extract only note events from MIDI data.
    
    Args:
        midi_data: Dictionary returned by read_midi()
        track_index: Specific track to extract from (None = all tracks)
        
    Returns:
        List of note events (note_on/note_off) sorted by time
    """
    note_events = []
    
    if track_index is not None:
        # Extract from specific track
        if 0 <= track_index < len(midi_data['tracks']):
            events = midi_data['tracks'][track_index]['events']
            note_events.extend(event for event in events 
                             if event.type in ['note_on', 'note_off'])
    else:
        # Extract from all tracks
        for track in midi_data['tracks']:
            events = track['events']
            note_events.extend(event for event in events 
                             if event.type in ['note_on', 'note_off'])
    
    # Sort by time
    note_events.sort(key=lambda e: e.time_sec)
    return note_events

def merge_note_events(events: List[Event]) -> List[Event]:
    """
    Merge note_on and note_off events into note events with duration.
    
    Args:
        events: List of note events (note_on/note_off)
        
    Returns:
        List of note events with duration information
    """
    # Track active notes (note_number -> (start_event, start_time))
    active_notes = {}
    merged_events = []
    
    for event in events:
        note_key = (event.note, event.channel)
        
        if event.type == 'note_on':
            # Start tracking this note
            active_notes[note_key] = event
            
        elif event.type == 'note_off':
            # Find matching note_on and create merged event
            if note_key in active_notes:
                start_event = active_notes.pop(note_key)
                
                # Create merged event with duration
                merged_event = Event(
                    type='note',
                    note=event.note,
                    time_sec=start_event.time_sec,
                    delta_sec=event.time_sec - start_event.time_sec,  # Duration
                    velocity=start_event.velocity,
                    channel=event.channel,
                    track_index=start_event.track_index
                )
                merged_events.append(merged_event)
    
    # Handle notes that never got note_off (assume short duration)
    for start_event in active_notes.values():
        merged_event = Event(
            type='note',
            note=start_event.note,
            time_sec=start_event.time_sec,
            delta_sec=0.1,  # Default short duration
            velocity=start_event.velocity,
            channel=start_event.channel,
            track_index=start_event.track_index
        )
        merged_events.append(merged_event)
    
    # Sort by time
    merged_events.sort(key=lambda e: e.time_sec)
    return merged_events

# Legacy compatibility with old NoteEvent class
@dataclass
class NoteEvent:
    """Legacy NoteEvent class for backward compatibility."""
    note: int           # MIDI note number (0-127)
    velocity: int       # Velocity (0-127)
    time: float         # Time in seconds from start
    duration: float     # Note duration in seconds
    channel: int        # MIDI channel (0-15)
    event_type: str     # 'note_on' or 'note_off'

def read_midi_file(filepath: str) -> List[NoteEvent]:
    """
    Legacy function to read MIDI file and return note events.
    
    Args:
        filepath: Path to MIDI file
        
    Returns:
        List of NoteEvent objects
    """
    midi_data = read_midi(filepath)
    melody_track = choose_melody_track(midi_data)
    events = get_note_events(midi_data, melody_track)
    merged = merge_note_events(events)
    
    # Convert to legacy format
    note_events = []
    for event in merged:
        note_event = NoteEvent(
            note=event.note,
            velocity=event.velocity,
            time=event.time_sec,
            duration=event.delta_sec,
            channel=event.channel,
            event_type='note'
        )
        note_events.append(note_event)
    
    return note_events
