"""
MIDI to Shawzin Converter

A Python package for converting MIDI files to Warframe Shawzin format.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import main components
from .midi_io import read_midi, Event
from .shawzin_mapping import scaleDict, scaleModulo, get_shawzin_char
from .key_detection import detect_key_from_events
from .quantize import quantize_events
from .chord_handling import process_chord_events
from .mapper import ShawzinMapper, map_notes_to_shawzin

__all__ = [
    "read_midi", "Event", "scaleDict", "scaleModulo", "get_shawzin_char",
    "detect_key_from_events", "quantize_events", "process_chord_events", 
    "ShawzinMapper", "map_notes_to_shawzin"
]
