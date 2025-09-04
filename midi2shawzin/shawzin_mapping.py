"""
Shawzin Mapping Constants

Contains character mappings, scale definitions, and chord patterns
for Warframe Shawzin instrument conversion based on official documentation.

Usage:
    from shawzin_mapping import base64_chars, scaleDict, chordDict
    from shawzin_mapping import load_scale_from_json, load_chord_dict
"""

import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Base64 characters used for time encoding in Shawzin format
# Used to encode timing information in Warframe Shawzin format
base64_chars = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
    "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "+", "/"
]

# Scale modulo values for different Shawzin scale types
# These determine the range and mapping behavior for each scale
scaleModulo = [36, 36, 12, 24, 36, 24, 36, 36, 36]

# Default scale mappings for Shawzin scales 1-9
# Each scale maps MIDI note indices to Shawzin characters
scaleDict = {
    # Scale 1: Pentatonic (36 notes)
    1: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w", 6: "s", 7: "x",
        8: "3", 9: "e", 10: "d", 11: "c", 12: "1", 13: "q", 14: "a", 15: "z",
        16: "2", 17: "w", 18: "s", 19: "x", 20: "3", 21: "e", 22: "d", 23: "c",
        24: "1", 25: "q", 26: "a", 27: "z", 28: "2", 29: "w", 30: "s", 31: "x",
        32: "3", 33: "e", 34: "d", 35: "c"
    },
    
    # Scale 2: Heptatonic (36 notes)
    2: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w", 6: "s", 7: "x",
        8: "3", 9: "e", 10: "d", 11: "c", 12: "1", 13: "q", 14: "a", 15: "z",
        16: "2", 17: "w", 18: "s", 19: "x", 20: "3", 21: "e", 22: "d", 23: "c",
        24: "1", 25: "q", 26: "a", 27: "z", 28: "2", 29: "w", 30: "s", 31: "x",
        32: "3", 33: "e", 34: "d", 35: "c"
    },
    
    # Scale 3: Chromatic (12 notes)
    3: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w",
        6: "s", 7: "x", 8: "3", 9: "e", 10: "d", 11: "c"
    },
    
    # Scale 4: Natural Minor (24 notes)
    4: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w", 6: "s", 7: "x",
        8: "3", 9: "e", 10: "d", 11: "c", 12: "1", 13: "q", 14: "a", 15: "z",
        16: "2", 17: "w", 18: "s", 19: "x", 20: "3", 21: "e", 22: "d", 23: "c"
    },
    
    # Scale 5: Dorian (36 notes)
    5: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w", 6: "s", 7: "x",
        8: "3", 9: "e", 10: "d", 11: "c", 12: "1", 13: "q", 14: "a", 15: "z",
        16: "2", 17: "w", 18: "s", 19: "x", 20: "3", 21: "e", 22: "d", 23: "c",
        24: "1", 25: "q", 26: "a", 27: "z", 28: "2", 29: "w", 30: "s", 31: "x",
        32: "3", 33: "e", 34: "d", 35: "c"
    },
    
    # Scale 6: Phrygian (24 notes)
    6: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w", 6: "s", 7: "x",
        8: "3", 9: "e", 10: "d", 11: "c", 12: "1", 13: "q", 14: "a", 15: "z",
        16: "2", 17: "w", 18: "s", 19: "x", 20: "3", 21: "e", 22: "d", 23: "c"
    },
    
    # Scale 7: Yo (36 notes)
    7: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w", 6: "s", 7: "x",
        8: "3", 9: "e", 10: "d", 11: "c", 12: "1", 13: "q", 14: "a", 15: "z",
        16: "2", 17: "w", 18: "s", 19: "x", 20: "3", 21: "e", 22: "d", 23: "c",
        24: "1", 25: "q", 26: "a", 27: "z", 28: "2", 29: "w", 30: "s", 31: "x",
        32: "3", 33: "e", 34: "d", 35: "c"
    },
    
    # Scale 8: Ritusen (36 notes)
    8: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w", 6: "s", 7: "x",
        8: "3", 9: "e", 10: "d", 11: "c", 12: "1", 13: "q", 14: "a", 15: "z",
        16: "2", 17: "w", 18: "s", 19: "x", 20: "3", 21: "e", 22: "d", 23: "c",
        24: "1", 25: "q", 26: "a", 27: "z", 28: "2", 29: "w", 30: "s", 31: "x",
        32: "3", 33: "e", 34: "d", 35: "c"
    },
    
    # Scale 9: Whole Tone (36 notes)
    9: {
        0: "1", 1: "q", 2: "a", 3: "z", 4: "2", 5: "w", 6: "s", 7: "x",
        8: "3", 9: "e", 10: "d", 11: "c", 12: "1", 13: "q", 14: "a", 15: "z",
        16: "2", 17: "w", 18: "s", 19: "x", 20: "3", 21: "e", 22: "d", 23: "c",
        24: "1", 25: "q", 26: "a", 27: "z", 28: "2", 29: "w", 30: "s", 31: "x",
        32: "3", 33: "e", 34: "d", 35: "c"
    }
}

# Basic chord dictionary for chord detection
# Maps chord types to semitone intervals from root
chordDict = {
    # Basic triads
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
    
    # Suspended chords
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    
    # Seventh chords
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "dominant7": [0, 4, 7, 10],
    "diminished7": [0, 3, 6, 9],
    "half_diminished7": [0, 3, 6, 10],
    
    # Extended chords
    "major9": [0, 4, 7, 11, 14],
    "minor9": [0, 3, 7, 10, 14],
    "dominant9": [0, 4, 7, 10, 14],
    
    # Power chords
    "power": [0, 7],
    "power_octave": [0, 7, 12],
}

def load_scale_from_json(json_path: str) -> Dict[int, Dict[int, str]]:
    """
    Load scale mappings from JSON file.
    
    Args:
        json_path: Path to JSON file containing scale mappings
        
    Returns:
        Dictionary of scale mappings
        
    Expected JSON structure:
    {
        "1": {
            "0": "1", "1": "q", "2": "a", ...
        },
        "2": {
            "0": "1", "1": "q", ...
        }
    }
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert string keys to integers
        result = {}
        for scale_id, mapping in data.items():
            result[int(scale_id)] = {int(k): v for k, v in mapping.items()}
        
        return result
    except FileNotFoundError:
        print(f"Warning: Scale mapping file not found: {json_path}")
        return scaleDict
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in scale mapping file: {e}")
        return scaleDict

def load_chord_dict(json_path: str) -> Dict[str, List[int]]:
    """
    Load chord dictionary from JSON file.
    
    Args:
        json_path: Path to JSON file containing chord definitions
        
    Returns:
        Dictionary of chord patterns
        
    Expected JSON structure:
    {
        "major": [0, 4, 7],
        "minor": [0, 3, 7],
        ...
    }
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Chord dictionary file not found: {json_path}")
        return chordDict
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in chord dictionary file: {e}")
        return chordDict

# Utility functions for note conversion
def midi_to_pitch_class(midi_note: int) -> int:
    """Convert MIDI note number to pitch class (0-11)."""
    return midi_note % 12

def get_shawzin_char(scale_id: int, note_index: int) -> Optional[str]:
    """
    Get Shawzin character for given scale and note index.
    
    Args:
        scale_id: Shawzin scale ID (1-9)
        note_index: Note index within scale
        
    Returns:
        Shawzin character or None if invalid
    """
    if scale_id not in scaleDict:
        return None
    
    scale_mapping = scaleDict[scale_id]
    modulo = scaleModulo[scale_id - 1]  # scaleModulo is 0-indexed
    
    # Apply modulo to handle note wrapping
    wrapped_index = note_index % modulo
    return scale_mapping.get(wrapped_index)

# Pitch class names for debugging
PITCH_CLASS_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def pitch_class_to_name(pitch_class: int) -> str:
    """Convert pitch class number to note name."""
    return PITCH_CLASS_NAMES[pitch_class % 12]
