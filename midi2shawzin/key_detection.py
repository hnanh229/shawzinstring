"""
Musical Key Detection

Analyzes note patterns to detect the most likely musical key and scale using
pitch class histogram analysis and coverage scoring (Krumhansl-Schmuckler-like algorithm).
"""

from typing import Dict, List, Tuple, Optional, Set
from collections import Counter
import math
from .shawzin_mapping import scaleDict, PITCH_CLASS_NAMES
from .midi_io import Event, NoteEvent

# Scale templates: sets of pitch classes for each scale type
# Each scale template defines which pitch classes belong to the scale
SCALE_TEMPLATES = {
    # Scale 1: Pentatonic Minor (Yo scale pattern)
    1: {0, 3, 5, 7, 10},  # Natural minor pentatonic
    
    # Scale 2: Heptatonic (Natural Major)
    2: {0, 2, 4, 5, 7, 9, 11},  # Major scale
    
    # Scale 3: Chromatic (all notes)
    3: {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11},  # All pitch classes
    
    # Scale 4: Natural Minor
    4: {0, 2, 3, 5, 7, 8, 10},  # Natural minor scale
    
    # Scale 5: Dorian
    5: {0, 2, 3, 5, 7, 9, 10},  # Dorian mode
    
    # Scale 6: Phrygian
    6: {0, 1, 3, 5, 7, 8, 10},  # Phrygian mode
    
    # Scale 7: Yo (Pentatonic Major)
    7: {0, 2, 4, 7, 9},  # Major pentatonic
    
    # Scale 8: Ritusen (Japanese scale)
    8: {0, 2, 5, 7, 9},  # Ritusen pentatonic
    
    # Scale 9: Whole Tone
    9: {0, 2, 4, 6, 8, 10},  # Whole tone scale
}

# Scale type names for display
SCALE_NAMES = {
    1: "Pentatonic Minor",
    2: "Major (Heptatonic)", 
    3: "Chromatic",
    4: "Natural Minor",
    5: "Dorian",
    6: "Phrygian", 
    7: "Pentatonic Major",
    8: "Ritusen",
    9: "Whole Tone"
}

def build_pitch_class_histogram(events: List[Event]) -> List[float]:
    """
    Build normalized pitch class histogram from note events.
    
    Args:
        events: List of note events to analyze
        
    Returns:
        List of 12 normalized counts (0.0-1.0) for pitch classes C through B
    """
    # Initialize histogram
    histogram = [0.0] * 12
    total_weight = 0.0
    
    # Process note events
    for event in events:
        if event.note is not None and event.type in ['note_on', 'note']:
            pitch_class = event.note % 12
            
            # Weight by duration and velocity
            duration = getattr(event, 'delta_sec', 0.25)  # Default duration if not available
            velocity = event.velocity if event.velocity > 0 else 80
            
            # Calculate weight: longer and louder notes have more influence
            weight = duration * (velocity / 127.0)
            
            histogram[pitch_class] += weight
            total_weight += weight
    
    # Normalize to probabilities
    if total_weight > 0:
        histogram = [count / total_weight for count in histogram]
    
    return histogram

def get_scale_template(scale_id: int, root: int) -> Set[int]:
    """
    Get scale template transposed to given root.
    
    Args:
        scale_id: Shawzin scale ID (1-9)
        root: Root pitch class (0-11)
        
    Returns:
        Set of pitch classes in the scale
    """
    if scale_id not in SCALE_TEMPLATES:
        # Default to chromatic if unknown scale
        return set(range(12))
    
    base_template = SCALE_TEMPLATES[scale_id]
    # Transpose template to root
    return {(pc + root) % 12 for pc in base_template}

def score_key(histogram: List[float], scale_template: Set[int]) -> float:
    """
    Score how well histogram matches scale template using improved coverage scoring.
    
    Args:
        histogram: Normalized pitch class histogram
        scale_template: Set of pitch classes in scale
        
    Returns:
        Coverage score (0.0-1.0, higher = better match)
    """
    # Coverage score: sum of histogram values for notes in scale
    in_scale_score = sum(histogram[pc] for pc in scale_template)
    
    # Penalty for notes outside scale (stronger penalty)
    out_of_scale_score = sum(histogram[pc] for pc in range(12) if pc not in scale_template)
    
    # Scale size factor: prefer scales that are more specific (smaller scales get bonus)
    scale_size = len(scale_template)
    specificity_bonus = (12 - scale_size) / 12.0 * 0.3  # Bonus for more specific scales
    
    # Completeness: how many scale notes are actually used
    used_scale_notes = len([pc for pc in scale_template if histogram[pc] > 0.01])
    completeness = used_scale_notes / scale_size if scale_size > 0 else 0
    
    # Dominance: how much of the total weight is in the strongest scale notes
    scale_weights = [histogram[pc] for pc in scale_template]
    scale_weights.sort(reverse=True)
    top_3_weight = sum(scale_weights[:min(3, len(scale_weights))])
    
    # Combined score with multiple factors
    base_score = in_scale_score - (0.8 * out_of_scale_score)  # Strong penalty for out-of-scale
    completeness_bonus = 0.2 * completeness
    dominance_bonus = 0.1 * top_3_weight
    
    final_score = base_score + completeness_bonus + dominance_bonus + specificity_bonus
    
    return max(0.0, final_score)  # Ensure non-negative

def detect_best_scale(events: List[Event], 
                     candidate_scales: Optional[List[int]] = None) -> Tuple[int, int, float]:
    """
    Detect the best-fitting scale for given note events.
    
    Args:
        events: List of note events to analyze
        candidate_scales: List of scale IDs to test (default: all 1-9)
        
    Returns:
        Tuple of (root_pitch_class, scale_id, score)
    """
    if candidate_scales is None:
        candidate_scales = list(range(1, 10))  # All Shawzin scales
    
    # Build pitch class histogram
    histogram = build_pitch_class_histogram(events)
    
    best_candidates = []
    
    # Test all combinations of root and scale
    for scale_id in candidate_scales:
        for root in range(12):
            scale_template = get_scale_template(scale_id, root)
            score = score_key(histogram, scale_template)
            best_candidates.append((score, root, scale_id))
    
    # Sort by score (descending)
    best_candidates.sort(reverse=True)
    
    # Check for ties and apply context-aware tie-breaking
    best_score = best_candidates[0][0]
    tied_candidates = [(root, scale_id) for score, root, scale_id in best_candidates 
                      if abs(score - best_score) < 0.01]
    
    if len(tied_candidates) > 1:
        # For modal relationships (same notes, different tonic), 
        # prefer the root that has more emphasis in the melody
        if len(tied_candidates) <= 4:  # Likely modal relationship
            # Calculate emphasis for each candidate root
            root_emphasis = {}
            for root, scale_id in tied_candidates:
                # Check histogram weight at this root
                emphasis = histogram[root % 12]
                # Add bonus for first/last note being the root
                if events:
                    first_note_pc = events[0].note % 12
                    last_note_pc = events[-1].note % 12
                    if first_note_pc == root:
                        emphasis += 0.2
                    if last_note_pc == root:
                        emphasis += 0.2
                root_emphasis[(root, scale_id)] = emphasis
            
            # Return candidate with highest root emphasis
            best_candidate = max(tied_candidates, key=lambda x: root_emphasis[x])
            return best_candidate[0], best_candidate[1], best_score
        
        # For larger ties, use scale preferences
        # Slightly prefer more common scales but don't override strong melodic evidence
        scale_preferences = [2, 4, 5, 6, 7, 1, 3, 8, 9]  # Major, minor, modes, pentatonic, exotic
        
        for preferred_scale in scale_preferences:
            for root, scale_id in tied_candidates:
                if scale_id == preferred_scale:
                    return root, scale_id, best_score
        
        # If no preference match, return first candidate
        return tied_candidates[0][0], tied_candidates[0][1], best_score
    
    return best_candidates[0][1], best_candidates[0][2], best_candidates[0][0]

def analyze_key_confidence(events: List[Event], 
                          top_n: int = 3) -> List[Tuple[int, int, float, str]]:
    """
    Analyze key detection confidence by returning top N candidates.
    
    Args:
        events: List of note events to analyze
        top_n: Number of top candidates to return
        
    Returns:
        List of tuples: (root, scale_id, score, description)
    """
    histogram = build_pitch_class_histogram(events)
    candidates = []
    
    # Test all combinations
    for scale_id in range(1, 10):
        for root in range(12):
            scale_template = get_scale_template(scale_id, root)
            score = score_key(histogram, scale_template)
            
            root_name = PITCH_CLASS_NAMES[root]
            scale_name = SCALE_NAMES.get(scale_id, f"Scale {scale_id}")
            description = f"{root_name} {scale_name}"
            
            candidates.append((root, scale_id, score, description))
    
    # Sort by score and return top N
    candidates.sort(key=lambda x: x[2], reverse=True)
    return candidates[:top_n]

def get_scale_notes(scale_id: int, root: int, octave: int = 4) -> List[int]:
    """
    Get MIDI note numbers for scale starting at given root and octave.
    
    Args:
        scale_id: Shawzin scale ID
        root: Root pitch class
        octave: Starting octave
        
    Returns:
        List of MIDI note numbers in scale
    """
    scale_template = get_scale_template(scale_id, 0)  # Get base template
    notes = []
    
    # Generate notes for 2 octaves
    for oct_offset in range(2):
        current_octave = octave + oct_offset
        for pc in sorted(scale_template):
            midi_note = (current_octave * 12) + ((pc + root) % 12)
            if midi_note <= 127:  # Valid MIDI range
                notes.append(midi_note)
    
    return notes

class KeyDetector:
    """Detects musical key from note events using pitch class histogram."""
    
    def __init__(self):
        self.pitch_class_histogram: Counter[int] = Counter()
        self.last_analysis: Optional[Tuple[int, int, float]] = None
    
    def detect_key(self, events: List[Event]) -> Tuple[str, str]:
        """
        Detect the most likely key and scale from note events.
        
        Args:
            events: List of note events to analyze
            
        Returns:
            Tuple of (key_name, scale_type) e.g. ("C", "Major (Heptatonic)")
        """
        root, scale_id, score = detect_best_scale(events)
        self.last_analysis = (root, scale_id, score)
        
        key_name = PITCH_CLASS_NAMES[root]
        scale_name = SCALE_NAMES.get(scale_id, f"Scale {scale_id}")
        
        return key_name, scale_name
    
    def get_confidence(self) -> float:
        """Get confidence score of last key detection (0.0-1.0)."""
        if self.last_analysis is None:
            return 0.0
        return min(1.0, self.last_analysis[2])  # Clamp to 1.0

def detect_key_from_events(events: List[Event]) -> Tuple[str, str]:
    """
    Convenience function to detect key from note events.
    
    Args:
        events: List of note events
        
    Returns:
        Tuple of (key_name, scale_type)
    """
    detector = KeyDetector()
    return detector.detect_key(events)
