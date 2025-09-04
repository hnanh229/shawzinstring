# MIDI to Shawzin Converter

Converts MIDI files to Warframe Shawzin format compatible with the game's music system.

## Features

- MIDI file parsing and event extraction
- Automatic key/scale detection
- Note quantization to musical grid
- Chord handling and arpeggiation
- Pattern detection for repetitive sections
- Direct mapping to Shawzin character format
- Base64 time encoding compatible with Warframe

## Installation

```bash
pip install midi2shawzin
```

## Usage

### Command Line

```bash
midi2shawzin input.mid                    # Convert to input.txt
midi2shawzin input.mid -o output.txt      # Specify output file
midi2shawzin input.mid -q 8 -a            # Quantize to 8th notes, arpeggiate chords
midi2shawzin input.mid -t 140 -v          # Override tempo, verbose output
```

### Python API

```python
from midi2shawzin import convert_midi_to_shawzin

result = convert_midi_to_shawzin("input.mid")
print(result)
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Custom Scale and Chord Mappings

You can provide custom scale and chord mappings using JSON files:

### Custom Scale Mapping

Create a JSON file with the structure shown in `sample_scale_mapping.json`:

```python
from midi2shawzin.shawzin_mapping import load_scale_from_json

custom_scales = load_scale_from_json("my_custom_scales.json")
```

### Custom Chord Dictionary

Create a JSON file with the structure shown in `sample_chord_dict.json`:

```python
from midi2shawzin.shawzin_mapping import load_chord_dict

custom_chords = load_chord_dict("my_custom_chords.json")
```

## Project Structure

- `midi2shawzin/` - Main package
  - `shawzin_mapping.py` - Shawzin character mapping constants
  - `midi_io.py` - MIDI file I/O operations
  - `key_detection.py` - Musical key detection algorithms
  - `quantize.py` - Note timing quantization
  - `chord_handling.py` - Chord processing and arpeggiation
  - `pattern_detection.py` - Repetitive pattern detection
  - `mapper.py` - Note to Shawzin character mapping
  - `encoder.py` - Final Shawzin format encoding
  - `cli.py` - Command line interface

## License

MIT License