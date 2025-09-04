"""
Chord Handling Module

Processes polyphonic MIDI events for Shawzin conversion by reducing chords 
or converting them to arpeggios. Handles simultaneous notes intelligently.
"""

from typing import List, Dict, Tuple, Literal, Optional
from dataclasses import dataclass, replace
from collections import defaultdict
from .midi_io import Event
from .shawzin_mapping import chordDict, get_shawzin_char


@dataclass
class ChordPolicy:
    """Policy settings for chord processing."""
    max_chord_notes: int = 3                           # Maximum notes in a chord
    reduction_mode: Literal['reduce', 'arpeggiate'] = 'reduce'   # How to handle large chords
    arpeggio_spread_ms: float = 20.0                   # Time spread for arpeggio (ms)
    prefer_melody: bool = True                         # Prioritize highest note in reduction
    preserve_bass: bool = True                         # Always keep lowest note
    simultaneity_threshold: float = 1e-3               # Time epsilon for simultaneous detection (seconds)


def group_simultaneous(events: List[Event], eps: float = 1e-3) -> List[List[Event]]:
    """
    Group events that occur at the same quantized time.
    
    Args:
        events: List of events to group
        eps: Time epsilon for considering events simultaneous (seconds)
        
    Returns:
        List of groups, where each group contains simultaneous events
    """
    if not events:
        return []
    
    # Sort events by time
    sorted_events = sorted(events, key=lambda e: e.time_sec)
    
    groups = []
    current_group = [sorted_events[0]]
    current_time = sorted_events[0].time_sec
    
    for event in sorted_events[1:]:
        if abs(event.time_sec - current_time) <= eps:
            # Add to current group
            current_group.append(event)
        else:
            # Start new group
            groups.append(current_group)
            current_group = [event]
            current_time = event.time_sec
    
    # Add final group
    if current_group:
        groups.append(current_group)
    
    return groups


def analyze_chord_structure(notes: List[int]) -> Dict[str, int]:
    """
    Analyze chord structure to identify important notes.
    
    Args:
        notes: List of MIDI note numbers
        
    Returns:
        Dictionary with chord analysis: root, third, fifth, melody, bass
    """
    if not notes:
        return {}
    
    sorted_notes = sorted(notes)
    analysis = {
        'bass': sorted_notes[0],           # Lowest note
        'melody': sorted_notes[-1],        # Highest note
        'root': sorted_notes[0],           # Assume bass is root for simplicity
    }
    
    # Find third and fifth intervals from all notes (not just middle ones)
    if len(sorted_notes) >= 3:
        # Look for notes that form triadic intervals from root
        for note in sorted_notes:
            interval_from_root = (note - analysis['root']) % 12
            if interval_from_root in [3, 4]:  # Minor or major third
                analysis['third'] = note
            elif interval_from_root in [7]:   # Perfect fifth
                analysis['fifth'] = note
    
    return analysis


def reduce_chord(notes_in_chord: List[int], 
                policy: Literal['reduce', 'arpeggiate'] = 'reduce',
                max_notes: int = 3) -> List[int]:
    """
    Reduce chord to specified number of notes using musical intelligence.
    
    Args:
        notes_in_chord: List of MIDI note numbers in the chord
        policy: Reduction policy ('reduce' or 'arpeggiate')
        max_notes: Maximum number of notes to keep
        
    Returns:
        List of reduced MIDI note numbers
    """
    if len(notes_in_chord) <= max_notes:
        return notes_in_chord
    
    if policy == 'arpeggiate':
        # For arpeggiation, return all notes (timing handled elsewhere)
        return sorted(notes_in_chord)
    
    # Reduction mode: intelligently pick most important notes
    analysis = analyze_chord_structure(notes_in_chord)
    
    # Priority order: bass (root), melody (top), then third/fifth
    selected_notes = []
    
    # Always include bass/root
    selected_notes.append(analysis['bass'])
    
    # Always include melody if different from bass
    if analysis['melody'] != analysis['bass']:
        selected_notes.append(analysis['melody'])
    
    # Add third or fifth if we have room and they exist
    remaining_slots = max_notes - len(selected_notes)
    if remaining_slots > 0:
        candidates = []
        if 'third' in analysis:
            candidates.append(analysis['third'])
        if 'fifth' in analysis:
            candidates.append(analysis['fifth'])
        
        # Add middle notes if no clear third/fifth
        if not candidates:
            middle_notes = [n for n in sorted(notes_in_chord) 
                          if n not in selected_notes]
            # Prefer notes closer to the middle of the range
            middle_notes.sort(key=lambda n: abs(n - (analysis['bass'] + analysis['melody']) / 2))
            candidates = middle_notes
        
        # Add candidates up to remaining slots
        for note in candidates[:remaining_slots]:
            if note not in selected_notes:
                selected_notes.append(note)
    
    return sorted(selected_notes)


def create_arpeggio_events(chord_events: List[Event], 
                          spread_ms: float = 20.0) -> List[Event]:
    """
    Convert simultaneous chord events into arpeggiated sequence.
    
    Args:
        chord_events: List of simultaneous events forming a chord
        spread_ms: Time spread for arpeggio in milliseconds
        
    Returns:
        List of events with staggered timing
    """
    if len(chord_events) <= 1:
        return chord_events
    
    # Sort by pitch (ascending for arpeggio)
    sorted_events = sorted(chord_events, key=lambda e: e.note)
    
    # Calculate time offsets
    base_time = sorted_events[0].time_sec
    time_step = spread_ms / 1000.0 / (len(sorted_events) - 1)
    
    arpeggiated_events = []
    for i, event in enumerate(sorted_events):
        new_time = base_time + (i * time_step)
        
        # Calculate new delta_sec
        if i == 0:
            new_delta = new_time
        else:
            new_delta = new_time - arpeggiated_events[i-1].time_sec
        
        arpeggiated_event = replace(event, 
                                  time_sec=new_time,
                                  delta_sec=new_delta)
        arpeggiated_events.append(arpeggiated_event)
    
    return arpeggiated_events


def map_chord_to_shawzin(notes: List[int], chord_dict: Optional[Dict] = None) -> Optional[str]:
    """
    Map chord to Shawzin character if direct mapping exists.
    
    Args:
        notes: List of MIDI note numbers
        chord_dict: Chord mapping dictionary (uses default if None)
        
    Returns:
        Shawzin character if mapping exists, None otherwise
    """
    if chord_dict is None:
        chord_dict = chordDict
    
    if not notes:
        return None
    
    # Convert to pitch classes and sort
    pitch_classes = sorted([note % 12 for note in notes])
    
    # Create chord signature (pitch class set)
    chord_signature = tuple(pitch_classes)
    
    # Look for direct mapping in chord dictionary
    # Note: This is a simplified approach - actual chordDict structure may vary
    for chord_pattern, shawzin_char in chord_dict.items():
        if isinstance(chord_pattern, (list, tuple)):
            pattern_pcs = sorted([pc % 12 for pc in chord_pattern])
            if tuple(pattern_pcs) == chord_signature:
                return shawzin_char
    
    return None


def process_chord_events(events: List[Event], policy: ChordPolicy) -> List[Event]:
    """
    Process a group of simultaneous events according to chord policy.
    
    Args:
        events: List of simultaneous events
        policy: Chord processing policy
        
    Returns:
        List of processed events (reduced or arpeggiated)
    """
    if len(events) <= 1:
        return events
    
    # Extract note numbers
    notes = [event.note for event in events if event.type == 'note']
    
    if len(notes) <= policy.max_chord_notes:
        # Small enough chord - check for direct mapping
        shawzin_char = map_chord_to_shawzin(notes)
        if shawzin_char:
            # Direct chord mapping exists - keep all notes
            return events
    
    # Apply reduction or arpeggiation
    if policy.reduction_mode == 'arpeggiate':
        return create_arpeggio_events(events, policy.arpeggio_spread_ms)
    else:  # reduce
        reduced_notes = reduce_chord(notes, 'reduce', policy.max_chord_notes)
        
        # Filter events to keep only reduced notes
        reduced_events = []
        for event in events:
            if event.type != 'note' or event.note in reduced_notes:
                reduced_events.append(event)
                
        return reduced_events


def process_all_chords(events: List[Event], 
                      policy: Optional[ChordPolicy] = None) -> List[Event]:
    """
    Process all chords in a list of events.
    
    Args:
        events: List of all events
        policy: Chord processing policy (default applied if None)
        
    Returns:
        List of processed events with chords handled
    """
    if policy is None:
        policy = ChordPolicy()
    
    # Group simultaneous events
    chord_groups = group_simultaneous(events, policy.simultaneity_threshold)
    
    processed_events = []
    
    for group in chord_groups:
        # Process each group according to policy
        processed_group = process_chord_events(group, policy)
        processed_events.extend(processed_group)
    
    # Sort final events by time
    processed_events.sort(key=lambda e: e.time_sec)
    
    # Recalculate delta times
    for i in range(len(processed_events)):
        if i == 0:
            processed_events[i] = replace(processed_events[i], 
                                        delta_sec=processed_events[i].time_sec)
        else:
            delta = processed_events[i].time_sec - processed_events[i-1].time_sec
            processed_events[i] = replace(processed_events[i], delta_sec=delta)
    
    return processed_events


class ChordProcessor:
    """Chord processor with configurable policies."""
    
    def __init__(self, policy: Optional[ChordPolicy] = None):
        """Initialize processor with policy."""
        self.policy = policy or ChordPolicy()
        self.processed_chords = 0
        self.arpeggiated_chords = 0
        self.reduced_chords = 0
    
    def process(self, events: List[Event]) -> List[Event]:
        """Process events with current policy."""
        self.reset_stats()
        result = process_all_chords(events, self.policy)
        self._update_stats(events, result)
        return result
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.processed_chords = 0
        self.arpeggiated_chords = 0
        self.reduced_chords = 0
    
    def _update_stats(self, original_events: List[Event], processed_events: List[Event]):
        """Update processing statistics."""
        original_groups = group_simultaneous(original_events, self.policy.simultaneity_threshold)
        processed_groups = group_simultaneous(processed_events, self.policy.simultaneity_threshold)
        
        for orig_group, proc_group in zip(original_groups, processed_groups):
            if len(orig_group) > 1:
                self.processed_chords += 1
                if len(proc_group) > len(orig_group):
                    self.arpeggiated_chords += 1
                elif len(proc_group) < len(orig_group):
                    self.reduced_chords += 1
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return {
            'processed_chords': self.processed_chords,
            'arpeggiated_chords': self.arpeggiated_chords,
            'reduced_chords': self.reduced_chords
        }


# Convenience functions for common chord processing patterns
def reduce_chords_to_melody_bass(events: List[Event]) -> List[Event]:
    """Reduce chords to melody (top) and bass (bottom) notes only."""
    policy = ChordPolicy(
        max_chord_notes=2,
        reduction_mode='reduce',
        prefer_melody=True,
        preserve_bass=True
    )
    return process_all_chords(events, policy)


def arpeggiate_all_chords(events: List[Event], spread_ms: float = 25.0) -> List[Event]:
    """Convert all chords to arpeggios."""
    policy = ChordPolicy(
        max_chord_notes=1,  # Force arpeggiation of all chords
        reduction_mode='arpeggiate',
        arpeggio_spread_ms=spread_ms
    )
    return process_all_chords(events, policy)


def conservative_chord_reduction(events: List[Event]) -> List[Event]:
    """Conservative chord reduction - keep up to 3 notes, prefer direct mappings."""
    policy = ChordPolicy(
        max_chord_notes=3,
        reduction_mode='reduce',
        prefer_melody=True,
        preserve_bass=True
    )
    return process_all_chords(events, policy)
