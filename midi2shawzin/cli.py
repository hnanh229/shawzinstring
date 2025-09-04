"""
Command Line Interface

CLI entrypoint for midi2shawzin converter.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .midi_io import read_midi_file
from .key_detection import detect_key_from_events
from .quantize import quantize_to_sixteenth_notes, Quantizer, QuantizeSettings
from .chord_handling import process_chord_events
from .pattern_detection import detect_repetitive_patterns
from .mapper import map_notes_to_shawzin
from .encoder import encode_shawzin_notes

def main():
    """Main CLI entrypoint."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        result = convert_midi_file(
            input_file=args.input,
            output_file=args.output,
            quantize_subdivision=args.quantize,
            arpeggiate_chords=args.arpeggiate,
            detect_patterns=args.patterns,
            tempo_override=args.tempo,
            verbose=args.verbose
        )
        
        if args.verbose:
            print(f"Conversion completed successfully!")
            print(f"Output written to: {args.output}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="midi2shawzin",
        description="Convert MIDI files to Warframe Shawzin format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  midi2shawzin song.mid                    # Convert to song.txt
  midi2shawzin song.mid -o output.txt      # Specify output file
  midi2shawzin song.mid -q 8 -a            # Quantize to 8th notes, arpeggiate chords
  midi2shawzin song.mid -t 140 -v          # Override tempo, verbose output
        """
    )
    
    # Required arguments
    parser.add_argument(
        "input",
        type=str,
        help="Input MIDI file path"
    )
    
    # Optional arguments
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file path (default: input filename with .txt extension)"
    )
    
    parser.add_argument(
        "-q", "--quantize",
        type=int,
        default=16,
        choices=[4, 8, 16, 32],
        help="Quantization subdivision (4=quarter, 8=eighth, 16=sixteenth, 32=thirty-second)"
    )
    
    parser.add_argument(
        "-a", "--arpeggiate",
        action="store_true",
        help="Arpeggiate chords instead of playing simultaneously"
    )
    
    parser.add_argument(
        "-p", "--patterns",
        action="store_true",
        help="Detect and optimize repetitive patterns"
    )
    
    parser.add_argument(
        "-t", "--tempo",
        type=float,
        help="Override tempo (BPM) - auto-detected if not specified"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output with processing details"
    )
    
    return parser

def convert_midi_file(input_file: str,
                     output_file: Optional[str] = None,
                     quantize_subdivision: int = 16,
                     arpeggiate_chords: bool = False,
                     detect_patterns: bool = False,
                     tempo_override: Optional[float] = None,
                     verbose: bool = False) -> str:
    """
    Convert MIDI file to Shawzin format with specified options.
    
    Args:
        input_file: Path to input MIDI file
        output_file: Path to output file (auto-generated if None)
        quantize_subdivision: Quantization grid subdivision
        arpeggiate_chords: Whether to arpeggiate chords
        detect_patterns: Whether to detect repetitive patterns
        tempo_override: Tempo override in BPM
        verbose: Whether to print verbose output
        
    Returns:
        Shawzin format string
        
    TODO: Implement full conversion pipeline
    TODO: Add error handling for each step
    TODO: Provide progress feedback for long files
    """
    if verbose:
        print(f"Loading MIDI file: {input_file}")
    
    # Validate input file
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Generate output filename if not provided
    if output_file is None:
        output_file = Path(input_file).with_suffix(".txt")
    
    # TODO: Implement conversion steps
    # 1. Load MIDI file
    # 2. Detect key/scale
    # 3. Quantize timing
    # 4. Process chords
    # 5. Detect patterns (if enabled)
    # 6. Map to Shawzin notes
    # 7. Encode to final format
    # 8. Write output file
    
    # Placeholder implementation
    result = "# Shawzin conversion not yet implemented\n"
    
    # Write output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    
    return result

if __name__ == "__main__":
    main()
