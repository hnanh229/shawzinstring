"""
Note to Shawzin Character Mapping

Maps MIDI note events to Shawzin character sequences using closest-pitch matching
with octave-shift heuristics for optimal playability.
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
from .midi_io import Event
from .shawzin_mapping import scaleDict, scaleModulo, get_shawzin_char, base64_chars


@dataclass
class ShawzinNote:
    """Represents a note mapped to Shawzin format."""
    character: str         # Shawzin character (1-3, q-e, a-d, z-c)
    time_sec: float       # Note timing in seconds
    duration_sec: float   # Note duration in seconds  
    original_midi: int    # Original MIDI note number
    mapped_midi: int      # Mapped MIDI note (after octave shifts)
    scale_id: int         # Shawzin scale ID used
    octave_shift: int     # Number of octaves shifted


@dataclass
class MappingSettings:
    """Settings for note mapping process."""
    octave_range: Tuple[int, int] = (-2, 3)     # Octave range for mapping
    prefer_top_string: bool = True              # Prefer higher notes
    maintain_consistency: bool = True           # Cache mappings for consistency
    max_deviation_semitones: int = 2            # Max acceptable pitch deviation


def build_playable_table(scale_id: int, 
                        octave_range: Tuple[int, int] = (-2, 3),
                        base_octave: int = 4) -> List[Tuple[int, str]]:
    """
    Build a table of playable MIDI notes to Shawzin characters for a given scale.
    
    Args:
        scale_id: Shawzin scale ID (1-9)
        octave_range: Tuple of (min_octave_offset, max_octave_offset)
        base_octave: Base octave for scale mapping
        
    Returns:
        List of (midi_note, shawzin_char) tuples, sorted by MIDI note
    """
    if scale_id not in scaleDict:
        raise ValueError(f"Invalid scale_id: {scale_id}")
    
    playable_table = []
    scale_chars = scaleDict[scale_id]
    scale_length = scaleModulo[scale_id - 1]  # scaleModulo is 0-indexed
    
    # Generate mappings across octave range
    min_octave = base_octave + octave_range[0]
    max_octave = base_octave + octave_range[1]
    
    # Create a table mapping MIDI notes to characters
    # We use a set to avoid duplicates
    seen_notes = set()
    
    for octave in range(min_octave, max_octave + 1):
        base_midi = octave * 12  # C note for this octave
        
        for char_idx in range(scale_length):
            if char_idx in scale_chars:
                char = scale_chars[char_idx]
                
                # Calculate MIDI note - use simple chromatic mapping
                midi_note = base_midi + (char_idx % 12)
                
                # Ensure valid MIDI range and not duplicate
                if 0 <= midi_note <= 127 and midi_note not in seen_notes:
                    playable_table.append((midi_note, char))
                    seen_notes.add(midi_note)
    
    # Sort by MIDI note for efficient searching
    playable_table.sort(key=lambda x: x[0])
    
    return playable_table


def map_note_to_shawzin(note_midi: int, 
                       playable_table: List[Tuple[int, str]]) -> Tuple[str, int, int]:
    """
    Map a MIDI note to the closest Shawzin character.
    
    Args:
        note_midi: MIDI note number to map
        playable_table: List of (midi_note, shawzin_char) tuples
        
    Returns:
        Tuple of (shawzin_char, nearest_midi, octave_shift)
    """
    if not playable_table:
        raise ValueError("Empty playable table")
    
    # Find closest MIDI note in playable table
    best_midi = None
    best_char = None
    min_distance = float('inf')
    
    for midi_note, char in playable_table:
        distance = abs(midi_note - note_midi)
        if distance < min_distance:
            min_distance = distance
            best_midi = midi_note
            best_char = char
    
    # Calculate octave shift
    octave_shift = (best_midi - note_midi) // 12
    if (best_midi - note_midi) % 12 > 6:  # Handle wrap-around
        octave_shift += 1
    elif (best_midi - note_midi) % 12 < -6:
        octave_shift -= 1
    
    return best_char, best_midi, octave_shift


def analyze_note_coverage(notes: List[int], 
                         playable_table: List[Tuple[int, str]],
                         max_deviation: int = 2) -> Dict[str, float]:
    """
    Analyze how well a playable table covers a set of notes.
    
    Args:
        notes: List of MIDI note numbers to analyze
        playable_table: Playable table to test
        max_deviation: Maximum acceptable semitone deviation
        
    Returns:
        Dictionary with coverage statistics
    """
    if not notes:
        return {'coverage': 0.0, 'avg_deviation': 0.0, 'max_deviation': 0.0}
    
    covered_notes = 0
    total_deviation = 0
    max_dev = 0
    
    for note in notes:
        char, nearest_midi, _ = map_note_to_shawzin(note, playable_table)
        deviation = abs(nearest_midi - note)
        
        if deviation <= max_deviation:
            covered_notes += 1
        
        total_deviation += deviation
        max_dev = max(max_dev, deviation)
    
    coverage = covered_notes / len(notes)
    avg_deviation = total_deviation / len(notes)
    
    return {
        'coverage': coverage,
        'avg_deviation': avg_deviation,
        'max_deviation': max_dev
    }


def find_best_scale_for_notes(notes: List[int], 
                             octave_range: Tuple[int, int] = (-2, 3)) -> int:
    """
    Find the best Shawzin scale for a given set of notes.
    
    Args:
        notes: List of MIDI note numbers
        octave_range: Octave range for mapping
        
    Returns:
        Best scale ID (1-9)
    """
    if not notes:
        return 2  # Default to major scale
    
    best_scale = 2
    best_score = -1
    
    for scale_id in range(1, 10):
        try:
            playable_table = build_playable_table(scale_id, octave_range)
            analysis = analyze_note_coverage(notes, playable_table)
            
            # Score based on coverage and deviation
            score = analysis['coverage'] - (analysis['avg_deviation'] / 12.0)
            
            if score > best_score:
                best_score = score
                best_scale = scale_id
        except (ValueError, KeyError):
            continue  # Skip invalid scales
    
    return best_scale


def map_events_to_shawzin_events(events: List[Event],
                                playable_table: List[Tuple[int, str]],
                                prefer_top_string: bool = True,
                                maintain_consistency: bool = True) -> List[ShawzinNote]:
    """
    Map note events to Shawzin notes with consistency caching.
    
    Args:
        events: List of note events
        playable_table: Playable mapping table
        prefer_top_string: Prefer higher pitch mappings
        maintain_consistency: Cache mappings for same MIDI notes
        
    Returns:
        List of ShawzinNote objects
    """
    shawzin_notes = []
    mapping_cache = {}  # Cache for consistent mapping
    
    for event in events:
        if event.type != 'note':
            continue
            
        if event.note is None:
            continue
            
        midi_note = event.note
        
        # Check cache for consistency
        if maintain_consistency and midi_note in mapping_cache:
            char, mapped_midi, octave_shift = mapping_cache[midi_note]
        else:
            # Find best mapping
            char, mapped_midi, octave_shift = map_note_to_shawzin(midi_note, playable_table)
            
            # Cache the mapping
            if maintain_consistency:
                mapping_cache[midi_note] = (char, mapped_midi, octave_shift)
        
        # Create ShawzinNote
        shawzin_note = ShawzinNote(
            character=char,
            time_sec=event.time_sec,
            duration_sec=event.delta_sec,  # Use delta as duration approximation
            original_midi=midi_note,
            mapped_midi=mapped_midi,
            scale_id=1,  # Will be set by caller
            octave_shift=octave_shift
        )
        
        shawzin_notes.append(shawzin_note)
    
    return shawzin_notes


class ShawzinMapper:
    """Advanced mapper with caching and optimization."""
    
    def __init__(self, settings: Optional[MappingSettings] = None):
        """Initialize mapper with settings."""
        self.settings = settings or MappingSettings()
        self.playable_tables = {}  # Cache for playable tables
        self.mapping_cache = {}    # Cache for note mappings
        self.current_scale_id = None
        
    def get_playable_table(self, scale_id: int) -> List[Tuple[int, str]]:
        """Get or create playable table for scale."""
        if scale_id not in self.playable_tables:
            self.playable_tables[scale_id] = build_playable_table(
                scale_id, 
                self.settings.octave_range
            )
        return self.playable_tables[scale_id]
    
    def map_events(self, events: List[Event], scale_id: Optional[int] = None) -> List[ShawzinNote]:
        """
        Map events to Shawzin notes with automatic scale selection.
        
        Args:
            events: List of note events
            scale_id: Force specific scale (auto-detect if None)
            
        Returns:
            List of ShawzinNote objects
        """
        if not events:
            return []
        
        # Extract MIDI notes for analysis
        note_events = [e for e in events if e.type == 'note']
        midi_notes = [e.note for e in note_events]
        
        # Determine best scale
        if scale_id is None:
            scale_id = find_best_scale_for_notes(midi_notes, self.settings.octave_range)
        
        self.current_scale_id = scale_id
        
        # Get playable table for scale
        playable_table = self.get_playable_table(scale_id)
        
        # Map events
        shawzin_notes = map_events_to_shawzin_events(
            events,
            playable_table,
            self.settings.prefer_top_string,
            self.settings.maintain_consistency
        )
        
        # Update scale_id in notes
        for note in shawzin_notes:
            note.scale_id = scale_id
        
        return shawzin_notes
    
    def get_mapping_stats(self) -> Dict[str, any]:
        """Get mapping statistics."""
        return {
            'cached_scales': len(self.playable_tables),
            'cached_mappings': len(self.mapping_cache),
            'current_scale': self.current_scale_id
        }
    
    def clear_cache(self):
        """Clear all caches."""
        self.playable_tables.clear()
        self.mapping_cache.clear()


# Convenience functions
def map_notes_to_shawzin(events: List[Event], 
                        scale_id: Optional[int] = None,
                        octave_range: Tuple[int, int] = (-2, 3)) -> List[ShawzinNote]:
    """
    Convenience function to map note events to Shawzin format.
    
    Args:
        events: Input note events
        scale_id: Force specific scale (auto-detect if None)
        octave_range: Octave range for mapping
        
    Returns:
        List of Shawzin notes
    """
    settings = MappingSettings(octave_range=octave_range)
    mapper = ShawzinMapper(settings)
    return mapper.map_events(events, scale_id)


def quick_map_single_note(midi_note: int, 
                         scale_id: int = 2,
                         octave_range: Tuple[int, int] = (-2, 3)) -> Tuple[str, int, int]:
    """
    Quick mapping for a single MIDI note.
    
    Args:
        midi_note: MIDI note number
        scale_id: Shawzin scale ID
        octave_range: Octave range for mapping
        
    Returns:
        Tuple of (character, mapped_midi, octave_shift)
    """
    playable_table = build_playable_table(scale_id, octave_range)
    return map_note_to_shawzin(midi_note, playable_table)


def analyze_scale_compatibility(notes: List[int]) -> Dict[int, Dict[str, float]]:
    """
    Analyze how well different scales work for a set of notes.
    
    Args:
        notes: List of MIDI note numbers
        
    Returns:
        Dictionary mapping scale_id to analysis results
    """
    results = {}
    
    for scale_id in range(1, 10):
        try:
            playable_table = build_playable_table(scale_id)
            analysis = analyze_note_coverage(notes, playable_table)
            results[scale_id] = analysis
        except (ValueError, KeyError):
            continue
    
    return results
