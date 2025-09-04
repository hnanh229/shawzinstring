"""
Test Shawzin Mapping Functions

Unit tests for character mapping and constants.
"""

import pytest
from midi2shawzin.shawzin_mapping import (
    base64_chars,
    scaleModulo,
    scaleDict,
    chordDict,
    load_scale_from_json,
    load_chord_dict,
    midi_to_pitch_class,
    pitch_class_to_name,
    get_shawzin_char
)

class TestShawzinMapping:
    """Test shawzin mapping constants and functions."""
    
    def test_base64_chars_completeness(self):
        """Test that base64_chars contains all expected characters."""
        assert len(base64_chars) == 64
        assert "A" in base64_chars
        assert "Z" in base64_chars
        assert "a" in base64_chars
        assert "z" in base64_chars
        assert "0" in base64_chars
        assert "9" in base64_chars
        assert "+" in base64_chars
        assert "/" in base64_chars
        
    def test_scale_modulo_structure(self):
        """Test scale modulo values."""
        assert len(scaleModulo) == 9
        expected_modulos = [36, 36, 12, 24, 36, 24, 36, 36, 36]
        assert scaleModulo == expected_modulos
        
    def test_scale_dict_structure(self):
        """Test scale dictionary contains expected scales."""
        assert len(scaleDict) == 9
        for scale_id in range(1, 10):
            assert scale_id in scaleDict
            assert len(scaleDict[scale_id]) <= scaleModulo[scale_id - 1]
            
    def test_chord_dict_structure(self):
        """Test chord dictionary contains basic chord types."""
        basic_chords = ["major", "minor", "diminished", "augmented"]
        for chord in basic_chords:
            assert chord in chordDict
            assert len(chordDict[chord]) >= 3  # At least triad
            
    def test_midi_to_pitch_class(self):
        """Test MIDI note to pitch class conversion."""
        assert midi_to_pitch_class(60) == 0  # C4 -> C
        assert midi_to_pitch_class(61) == 1  # C#4 -> C#
        assert midi_to_pitch_class(72) == 0  # C5 -> C
        assert midi_to_pitch_class(0) == 0   # C-1 -> C
        
    def test_pitch_class_to_name(self):
        """Test pitch class to note name conversion."""
        assert pitch_class_to_name(0) == "C"
        assert pitch_class_to_name(1) == "C#"
        assert pitch_class_to_name(11) == "B"
        assert pitch_class_to_name(12) == "C"  # Wraps around
        
    def test_get_shawzin_char(self):
        """Test getting Shawzin character for scale and index."""
        # Test valid scale and index
        char = get_shawzin_char(1, 0)
        assert char == "1"
        
        char = get_shawzin_char(3, 1)  # Chromatic scale
        assert char == "q"
        
        # Test invalid scale
        char = get_shawzin_char(10, 0)
        assert char is None
        
        # Test modulo wrapping
        char1 = get_shawzin_char(3, 0)   # Index 0
        char2 = get_shawzin_char(3, 12)  # Index 12 (wraps to 0 for chromatic)
        assert char1 == char2
        
    def test_load_functions_with_missing_files(self):
        """Test load functions handle missing files gracefully."""
        scales = load_scale_from_json("nonexistent.json")
        assert scales == scaleDict  # Should return default
        
        chords = load_chord_dict("nonexistent.json")
        assert chords == chordDict  # Should return default
