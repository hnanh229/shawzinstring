"""
Demo script to test key detection functionality.

Creates synthetic melodies and demonstrates key detection capabilities.
"""

import sys
from pathlib import Path

# Add the project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from midi2shawzin.midi_io import Event
from midi2shawzin.key_detection import (
    detect_best_scale,
    analyze_key_confidence,
    build_pitch_class_histogram,
    get_scale_notes,
    SCALE_NAMES,
    PITCH_CLASS_NAMES
)

def create_scale_melody(root: int, scale_id: int, octave: int = 4) -> list[Event]:
    """Create a melody using notes from specified scale."""
    scale_notes = get_scale_notes(scale_id, root, octave)
    events = []
    
    # Use first 8 notes of scale (or all if fewer)
    melody_notes = scale_notes[:8]
    
    for i, note in enumerate(melody_notes):
        event = Event(
            type='note',
            note=note,
            time_sec=i * 0.5,
            delta_sec=0.4,
            velocity=80,
            channel=0,
            track_index=0
        )
        events.append(event)
    
    return events

def demo_key_detection():
    """Demonstrate key detection functionality."""
    print("Key Detection Demo")
    print("=" * 50)
    
    # Test cases: (root, scale_id, expected_description)
    test_cases = [
        (0, 2, "C Major"),           # C major scale
        (9, 4, "A Natural Minor"),   # A minor scale  
        (0, 7, "C Pentatonic Major"), # C pentatonic major
        (0, 3, "C Chromatic"),       # C chromatic
        (2, 5, "D Dorian"),          # D Dorian
        (5, 6, "F Phrygian"),        # F Phrygian
    ]
    
    for i, (root, scale_id, description) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {description}")
        print("-" * 30)
        
        # Create melody events
        events = create_scale_melody(root, scale_id)
        
        print(f"Created melody with {len(events)} notes:")
        for j, event in enumerate(events[:5]):  # Show first 5 notes
            note_name = PITCH_CLASS_NAMES[event.note % 12]
            octave = event.note // 12 - 1
            print(f"  Note {j+1}: {note_name}{octave} (MIDI {event.note})")
        if len(events) > 5:
            print(f"  ... and {len(events) - 5} more notes")
        
        # Detect key/scale
        detected_root, detected_scale, score = detect_best_scale(events)
        detected_root_name = PITCH_CLASS_NAMES[detected_root]
        detected_scale_name = SCALE_NAMES.get(detected_scale, f"Scale {detected_scale}")
        
        print(f"\nDetection Results:")
        print(f"  Expected: {description}")
        print(f"  Detected: {detected_root_name} {detected_scale_name}")
        print(f"  Confidence: {score:.3f}")
        
        # Check if detection is correct
        expected_root_name = PITCH_CLASS_NAMES[root]
        expected_scale_name = SCALE_NAMES.get(scale_id, f"Scale {scale_id}")
        
        root_correct = detected_root == root
        scale_correct = detected_scale == scale_id
        
        if root_correct and scale_correct:
            print(f"  Result: ✅ CORRECT")
        elif root_correct:
            print(f"  Result: ⚠️  Correct root, wrong scale")
        elif scale_correct:
            print(f"  Result: ⚠️  Correct scale, wrong root")
        else:
            print(f"  Result: ❌ INCORRECT")
        
        # Show top 3 candidates
        print(f"\nTop 3 candidates:")
        candidates = analyze_key_confidence(events, top_n=3)
        for rank, (cand_root, cand_scale, cand_score, description) in enumerate(candidates, 1):
            marker = "👑" if rank == 1 else f" {rank}."
            print(f"  {marker} {description} (score: {cand_score:.3f})")

def demo_histogram_analysis():
    """Demonstrate pitch class histogram analysis."""
    print("\n" + "=" * 50)
    print("Pitch Class Histogram Analysis")
    print("=" * 50)
    
    # Create C major triad (C-E-G) with emphasis
    events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=1.0, velocity=100),  # C (strong)
        Event(type='note', note=64, time_sec=1.0, delta_sec=0.8, velocity=90),   # E (medium)
        Event(type='note', note=67, time_sec=1.8, delta_sec=0.6, velocity=80),   # G (medium)
        Event(type='note', note=72, time_sec=2.4, delta_sec=0.4, velocity=70),   # C (weak)
    ]
    
    print("Analyzing C major triad melody (C-E-G-C):")
    
    # Build histogram
    histogram = build_pitch_class_histogram(events)
    
    print("\nPitch Class Histogram:")
    for pc in range(12):
        note_name = PITCH_CLASS_NAMES[pc]
        value = histogram[pc]
        bar = "█" * int(value * 50)  # Visual bar chart
        print(f"  {note_name:2s}: {value:.3f} {bar}")
    
    # Detect key
    root, scale_id, score = detect_best_scale(events)
    root_name = PITCH_CLASS_NAMES[root]
    scale_name = SCALE_NAMES.get(scale_id, f"Scale {scale_id}")
    
    print(f"\nDetected: {root_name} {scale_name} (confidence: {score:.3f})")

def demo_edge_cases():
    """Test edge cases and ambiguous situations."""
    print("\n" + "=" * 50)
    print("Edge Cases and Ambiguous Situations")
    print("=" * 50)
    
    # Test 1: Single note (very ambiguous)
    print("\nTest 1: Single note (C)")
    events = [Event(type='note', note=60, time_sec=0.0, delta_sec=1.0, velocity=80)]
    root, scale_id, score = detect_best_scale(events)
    print(f"  Detected: {PITCH_CLASS_NAMES[root]} {SCALE_NAMES.get(scale_id)}")
    print(f"  Confidence: {score:.3f} (should be low)")
    
    # Test 2: Two notes (fifth interval - very common)
    print("\nTest 2: Perfect fifth (C-G)")
    events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.5, velocity=80),  # C
        Event(type='note', note=67, time_sec=0.5, delta_sec=0.5, velocity=80),  # G
    ]
    candidates = analyze_key_confidence(events, top_n=3)
    print("  Top candidates:")
    for i, (r, s, score, desc) in enumerate(candidates, 1):
        print(f"    {i}. {desc} (score: {score:.3f})")

if __name__ == "__main__":
    demo_key_detection()
    demo_histogram_analysis()
    demo_edge_cases()
    print("\n" + "=" * 50)
    print("Key detection demo completed!")
