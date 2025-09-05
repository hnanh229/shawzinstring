#!/usr/bin/env python3
"""Test the converter with real MIDI samples."""

import os
from pathlib import Path
from midi2shawzin.cli import main as cli_main
import sys

def test_real_midi_sample():
    """Test conversion of a real MIDI sample."""
    
    # Test with the Warframe song - very fitting!
    midi_file = r"examples\midi_samples\AnyConv.com__We All Lift Together (From -Warframe-) - YouTube.midi"
    
    if not os.path.exists(midi_file):
        print(f"MIDI file not found: {midi_file}")
        return
    
    print(f"Testing conversion of: {midi_file}")
    print(f"File size: {os.path.getsize(midi_file)} bytes")
    
    # Create output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test melody mode (single output file)
    output_path = os.path.join(output_dir, "warframe_song_melody")
    
    print("\n=== TESTING MELODY MODE ===")
    
    # Use CLI to convert
    old_argv = sys.argv
    try:
        sys.argv = [
            'midi2shawzin',
            midi_file,
            '--output', output_path,
            '--mode', 'melody-only',
            '--verbose'
        ]
        
        cli_main()
        
    except SystemExit as e:
        if e.code == 0:
            print("Conversion completed successfully!")
        else:
            print(f"Conversion failed with exit code: {e.code}")
            return
    except Exception as e:
        print(f"Error during conversion: {e}")
        return
    finally:
        sys.argv = old_argv
    
    # Check output
    output_file = output_path  # CLI creates file without .txt extension
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n=== CONVERSION RESULTS ===")
        print(f"Output file: {output_file}")
        print(f"Content length: {len(content)} characters")
        print(f"Number of lines: {len(content.splitlines())}")
        
        # Show first part of the content
        lines = content.splitlines()
        print(f"\nFirst few lines:")
        for i, line in enumerate(lines[:5]):
            print(f"Line {i+1}: {line}")
        
        if len(lines) > 5:
            print(f"... and {len(lines) - 5} more lines")
        
        # Warframe compatibility checks
        print(f"\n=== WARFRAME COMPATIBILITY ===")
        print(f"✓ No # prefix: {not content.startswith('#')}")
        print(f"✓ Within 256 char limit: {len(content) <= 256} (actual: {len(content)})")
        print(f"✓ Starts with digit: {content[0].isdigit() if content else False}")
        
        # If too long, show chunking info
        if len(content) > 256:
            print(f"⚠️  Content exceeds 256 chars - would need chunking for Warframe")
            chunks = [content[i:i+256] for i in range(0, len(content), 256)]
            print(f"   Would create {len(chunks)} chunks")
            for i, chunk in enumerate(chunks[:3]):
                print(f"   Chunk {i+1}: {len(chunk)} chars")
        
        print(f"\n=== SAMPLE OUTPUT ===")
        preview = content[:200] + "..." if len(content) > 200 else content
        print(preview)
        
        return True
    else:
        print(f"Output file not created: {output_file}")
        return False

if __name__ == '__main__':
    test_real_midi_sample()
