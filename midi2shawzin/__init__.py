"""
MIDI to Shawzin Converter

A Python package for converting MIDI files to Warframe Shawzin format.
"""

__version__ = "0.2.0"
__author__ = "HN_Anh"
__email__ = "vl2anh1@gmail.com"

# Import main components
from .midi_io import read_midi, Event
from .shawzin_mapping import scaleDict, scaleModulo, get_shawzin_char
from .key_detection import detect_key_from_events
from .quantize import quantize_events
from .chord_handling import process_chord_events
from .mapper import ShawzinMapper, map_notes_to_shawzin

def convert_midi_to_shawzin(midi_file: str, output_file: str = None, **kwargs) -> str:
    """
    High-level function to convert MIDI to Shawzin format.
    
    Args:
        midi_file: Path to input MIDI file
        output_file: Optional output file path
        **kwargs: Additional options (mode, scale_override, etc.)
        
    Returns:
        Shawzin format string
    """
    from .cli import convert_midi_file
    
    # Set defaults
    if output_file is None:
        output_file = midi_file.replace('.mid', '.txt').replace('.midi', '.txt')
    
    result = convert_midi_file(
        input_file=midi_file,
        output_file=output_file,
        **kwargs
    )
    
    return result['shawzin_text']

__all__ = [
    "read_midi", "Event", "scaleDict", "scaleModulo", "get_shawzin_char",
    "detect_key_from_events", "quantize_events", "process_chord_events", 
    "ShawzinMapper", "map_notes_to_shawzin", "convert_midi_to_shawzin"
]
