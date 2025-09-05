"""
Command Line Interface for MIDI to Shawzin Conversion

Provides a complete CLI tool for converting MIDI files to Warframe Shawzin format
with various options for key detection, quantization, chord handling, and output modes.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import time

# Import all conversion modules
from .midi_io import read_midi, choose_melody_track, get_note_events, merge_note_events, Event, NoteEvent
from .key_detection import detect_key_from_events, KeyDetector
from .quantize import quantize_events, QuantizeSettings
from .chord_handling import process_chord_events, ChordPolicy
from .mapper import build_playable_table, map_events_to_shawzin_events, find_best_scale_for_notes, ShawzinNote
from .encoder import (
    events_to_shawzin_text, 
    write_shawzin_file,
    ShawzinEncoder,
    EncodingSettings
)
from .pattern_detection import compress_shawzin_tokens, PatternDetector
from .metrics import compute_mapping_metrics, format_metrics_report


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='midi2shawzin',
        description='Convert MIDI files to Warframe Shawzin format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion to melody-only format
  python -m midi2shawzin.cli input.mid -o out.txt --mode melody-only
  
  # Full conversion with key detection and chord processing
  python -m midi2shawzin.cli input.mid --mode full --detect-key --chord-policy arpeggiate
  
  # Convert with specific scale and quantization
  python -m midi2shawzin.cli input.mid --scale-override 2 --quantize-subdivision 16
  
  # Human-readable mode with pattern detection
  python -m midi2shawzin.cli input.mid --mode human --detect-patterns
        """
    )
    
    # Input/Output
    parser.add_argument(
        'input',
        help='Input MIDI file path'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (auto-generated if not specified)'
    )
    
    # Scale and Key Detection
    parser.add_argument(
        '--scale-override',
        type=int,
        choices=range(1, 10),
        help='Override detected scale (1-9)'
    )
    parser.add_argument(
        '--detect-key',
        action='store_true',
        default=True,
        help='Enable automatic key detection (default: enabled)'
    )
    parser.add_argument(
        '--no-detect-key',
        action='store_false',
        dest='detect_key',
        help='Disable automatic key detection'
    )
    
    # Output Modes
    parser.add_argument(
        '--mode',
        choices=['melody-only', 'full', 'human'],
        default='melody-only',
        help='Output mode: melody-only (default), full, or human-readable'
    )
    
    # Timing and Quantization
    parser.add_argument(
        '--quantize-subdivision',
        type=int,
        default=16,
        choices=[4, 8, 16, 32],
        help='Quantization subdivision (4, 8, 16, 32) - default: 16'
    )
    parser.add_argument(
        '--keep-offsets',
        action='store_true',
        default=True,
        help='Keep timing offsets in output (default: enabled)'
    )
    parser.add_argument(
        '--no-keep-offsets',
        action='store_false',
        dest='keep_offsets',
        help='Remove timing offsets from output'
    )
    
    # Chord Handling
    parser.add_argument(
        '--chord-policy',
        choices=['reduce', 'arpeggiate', 'ignore'],
        default='reduce',
        help='Chord handling policy: reduce (default), arpeggiate, or ignore'
    )
    
    # Pattern Detection
    parser.add_argument(
        '--detect-patterns',
        action='store_true',
        help='Enable pattern detection and compression'
    )
    parser.add_argument(
        '--min-pattern-length',
        type=int,
        default=4,
        help='Minimum pattern length for detection (default: 4)'
    )
    
    # Output Control
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show detailed conversion statistics'
    )
    
    return parser


def main():
    """Main CLI entrypoint."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        start_time = time.time()
        
        result = convert_midi_file(
            input_file=args.input,
            output_file=args.output,
            scale_override=args.scale_override,
            detect_key=args.detect_key,
            mode=args.mode,
            quantize_subdivision=args.quantize_subdivision,
            keep_offsets=args.keep_offsets,
            chord_policy=args.chord_policy,
            detect_patterns=args.detect_patterns,
            min_pattern_length=args.min_pattern_length,
            verbose=args.verbose,
            show_stats=args.stats
        )
        
        elapsed_time = time.time() - start_time
        
        if args.verbose:
            print(f"\nConversion completed in {elapsed_time:.2f} seconds")
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def convert_midi_file(input_file: str,
                     output_file: Optional[str] = None,
                     scale_override: Optional[int] = None,
                     detect_key: bool = True,
                     mode: str = 'melody-only',
                     quantize_subdivision: int = 16,
                     keep_offsets: bool = True,
                     chord_policy: str = 'reduce',
                     detect_patterns: bool = False,
                     min_pattern_length: int = 4,
                     verbose: bool = False,
                     show_stats: bool = False) -> Dict[str, Any]:
    """
    Convert MIDI file to Shawzin format with specified options.
    
    Args:
        input_file: Path to input MIDI file
        output_file: Path to output file (auto-generated if None)
        scale_override: Override detected scale (1-9)
        detect_key: Whether to detect key automatically
        mode: Output mode ('melody-only', 'full', 'human')
        quantize_subdivision: Quantization grid subdivision
        keep_offsets: Whether to keep timing offsets
        chord_policy: Chord handling policy ('reduce', 'arpeggiate', 'ignore')
        detect_patterns: Whether to detect repetitive patterns
        min_pattern_length: Minimum pattern length for detection
        verbose: Whether to print verbose output
        show_stats: Whether to show detailed statistics
        
    Returns:
        Dictionary with conversion results and statistics
    """
    if verbose:
        print(f"Loading MIDI file: {input_file}")
    
    # Validate input file
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Generate output filename if not provided
    if output_file is None:
        output_file = input_path.with_suffix(".txt")
    else:
        output_file = Path(output_file)
    
    # Initialize statistics
    stats = {
        'input_file': str(input_path),
        'output_file': str(output_file),
        'notes_processed': 0,
        'notes_converted': 0,
        'notes_ignored': 0,
        'impossible_notes': 0,
        'chords_processed': 0,
        'patterns_detected': 0,
        'compression_ratio': 1.0,
        'tracks_processed': 0,
        'scale_used': None,
        'key_detected': None
    }
    
    try:
        # Step 1: Load MIDI file
        if verbose:
            print("Step 1: Loading MIDI events...")
        
        midi_data = read_midi(input_file)
        melody_track = choose_melody_track(midi_data)
        events = get_note_events(midi_data, melody_track)
        events = merge_note_events(events)
        stats['notes_processed'] = len([e for e in events if isinstance(e, NoteEvent)])
        stats['tracks_processed'] = len(set(e.track for e in events if hasattr(e, 'track')))
        
        if verbose:
            print(f"  Loaded {len(events)} events from {stats['tracks_processed']} tracks")
        
        # Step 2: Key/Scale Detection
        if verbose:
            print("Step 2: Detecting key and scale...")
        
        if detect_key and not scale_override:
            key_name, scale_type = detect_key_from_events(events)
            # For CLI purposes, we'll use a default scale mapping
            scale_id = 2  # Default scale
            stats['key_detected'] = f"{key_name} {scale_type}"
            if verbose:
                print(f"  Detected key: {key_name} {scale_type} (Scale {scale_id})")
        else:
            scale_id = scale_override or 2  # Default to scale 2
            stats['key_detected'] = f"Override/Default (Scale {scale_id})"
            if verbose:
                print(f"  Using scale: {scale_id}")
        
        stats['scale_used'] = scale_id
        
        # Step 3: Quantize timing
        if verbose:
            print("Step 3: Quantizing timing...")
        
        quantize_settings = QuantizeSettings(subdivision=quantize_subdivision)
        if not keep_offsets:
            quantized_events = quantize_events(
                events, 
                midi_data['ticks_per_beat'], 
                midi_data.get('tempo', 500000),
                quantize_settings
            )
        else:
            quantized_events = events
        
        if verbose:
            print(f"  Quantized to {quantize_subdivision}th note grid")
        
        # Step 4: Process chords
        if verbose:
            print("Step 4: Processing chords...")
        
        chord_settings = ChordPolicy()
        if chord_policy == 'reduce':
            chord_settings.reduce_chords = True
            chord_settings.arpeggiate_chords = False
        elif chord_policy == 'arpeggiate':
            chord_settings.reduce_chords = False
            chord_settings.arpeggiate_chords = True
        else:  # ignore
            chord_settings.reduce_chords = False
            chord_settings.arpeggiate_chords = False
        
        processed_events = process_chord_events(quantized_events, chord_settings)
        chord_count = len([e for e in processed_events if hasattr(e, 'chord_info')])
        stats['chords_processed'] = chord_count
        
        if verbose:
            print(f"  Processed {chord_count} chords using policy: {chord_policy}")
        
        # Step 5: Map to Shawzin notes
        if verbose:
            print("Step 5: Mapping to Shawzin notes...")
        
        # Build playable table for detected scale
        playable_table = build_playable_table(scale_id, octave_range=(3, 6))
        
        shawzin_events = map_events_to_shawzin_events(processed_events, playable_table)
        
        # Count conversion results
        stats['notes_converted'] = len(shawzin_events)
        stats['notes_ignored'] = stats['notes_processed'] - stats['notes_converted']
        
        if verbose:
            print(f"  Converted {stats['notes_converted']}/{stats['notes_processed']} notes")
            if stats['notes_ignored'] > 0:
                print(f"  Ignored {stats['notes_ignored']} notes (out of range or unmappable)")
        
        # Step 6: Encode to Shawzin format
        if verbose:
            print("Step 6: Encoding to Shawzin format...")
        
        encoding_settings = EncodingSettings()
        encoding_settings.scale_id = scale_id
        
        if mode == 'melody-only':
            shawzin_lines = events_to_shawzin_text(
                shawzin_events,
                keep_offsets=keep_offsets,
                settings=encoding_settings
            )
        elif mode == 'full':
            encoder = ShawzinEncoder(encoding_settings)
            shawzin_lines = encoder.encode_events(shawzin_events, mode='full')
        else:  # human mode
            encoder = ShawzinEncoder(encoding_settings)
            shawzin_lines = encoder.encode_events(shawzin_events, mode='melody')
        
        if verbose:
            print(f"  Generated {len(shawzin_lines)} output lines")
        
        # Step 7: Pattern detection (if enabled)
        if detect_patterns:
            if verbose:
                print("Step 7: Detecting patterns...")
            
            # Extract tokens from lines for pattern detection
            all_tokens = []
            for line in shawzin_lines:
                if not line.startswith('#'):
                    # Remove whitespace and split into 3-character tokens
                    clean_line = ''.join(line.split())
                    tokens = [clean_line[i:i+3] for i in range(0, len(clean_line), 3) if i+2 < len(clean_line)]
                    all_tokens.extend(tokens)
            
            detector = PatternDetector(
                min_pattern_length=min_pattern_length,
                enable_compression=True
            )
            
            compressed_tokens, patterns_dict = detector.compress_tokens(all_tokens)
            
            stats['patterns_detected'] = len(patterns_dict)
            stats['compression_ratio'] = len(compressed_tokens) / len(all_tokens) if all_tokens else 1.0
            
            if verbose:
                print(f"  Detected {stats['patterns_detected']} patterns")
                print(f"  Compression ratio: {stats['compression_ratio']:.2%}")
            
            # TODO: Integrate compressed tokens back into output format
            # For now, we'll use original lines
        
        # Step 8: Write output file
        if verbose:
            print("Step 8: Writing output file...")
        
        if mode == 'human':
            # Write human-readable format
            content = f"# Shawzin Conversion - {input_path.name}\n"
            content += f"# Scale: {scale_id} ({stats['key_detected']})\n"
            content += f"# Notes: {stats['notes_converted']}/{stats['notes_processed']}\n"
            content += f"# Mode: {mode}\n\n"
            content += '\n'.join(shawzin_lines)
        else:
            # Write standard Shawzin format
            content = '\n'.join(shawzin_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if verbose:
            print(f"  Written to: {output_file}")
        
        # Step 9: Compute quality metrics
        if verbose:
            print("Step 9: Computing quality metrics...")
        
        # Compute conversion quality metrics
        metrics = compute_mapping_metrics(
            original_events=events,
            mapped_events=shawzin_events,
            ticks_per_beat=midi_data['ticks_per_beat'],
            tempo_us_per_beat=midi_data.get('tempo', 500000)
        )
        
        # Print summary
        print("\n" + "="*50)
        print("CONVERSION SUMMARY")
        print("="*50)
        print(f"Input:           {stats['input_file']}")
        print(f"Output:          {stats['output_file']}")
        print(f"Scale Used:      {stats['scale_used']} ({stats['key_detected']})")
        print(f"Notes Converted: {stats['notes_converted']}")
        print(f"Notes Ignored:   {stats['notes_ignored']}")
        if stats['impossible_notes'] > 0:
            print(f"Impossible Notes: {stats['impossible_notes']}")
        print(f"Chords Processed: {stats['chords_processed']}")
        if detect_patterns:
            print(f"Patterns Found:   {stats['patterns_detected']}")
            print(f"Compression:      {stats['compression_ratio']:.1%}")
        print("="*50)
        
        # Print quality metrics report
        print("")
        metrics_report = format_metrics_report(
            metrics, 
            mode=mode,
            include_recommendations=True
        )
        print(metrics_report)
        
        if show_stats:
            print("\nDETAILED STATISTICS")
            print("-"*30)
            for key, value in stats.items():
                print(f"{key:20}: {value}")
        
        return stats
        
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    sys.exit(main())
