#!/usr/bin/env python3
"""Debug pentatonic scale detection"""

from midi2shawzin.midi_io import Event
from midi2shawzin.key_detection import (
    build_pitch_class_histogram, 
    detect_best_scale, 
    analyze_key_confidence,
    SCALE_TEMPLATES,
    get_scale_template
)

# Create C major pentatonic sequence: C-D-E-G-A
events = [
    Event(type='note', note=60, time_sec=0.0, delta_sec=0.5, velocity=80),  # C
    Event(type='note', note=62, time_sec=0.5, delta_sec=0.5, velocity=80),  # D
    Event(type='note', note=64, time_sec=1.0, delta_sec=0.5, velocity=80),  # E
    Event(type='note', note=67, time_sec=1.5, delta_sec=0.5, velocity=80),  # G
    Event(type='note', note=69, time_sec=2.0, delta_sec=0.5, velocity=80),  # A
]

print("Debugging C Major Pentatonic Detection")
print("=" * 50)

# Analyze histogram
histogram = build_pitch_class_histogram(events)
print("\nPitch Class Histogram:")
pitch_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
for i, weight in enumerate(histogram):
    if weight > 0:
        print(f"  {pitch_names[i]}: {weight:.3f}")

# Show relevant scale templates
print("\nRelevant Scale Templates:")
print(f"  Scale 7 (Pentatonic Major): {SCALE_TEMPLATES[7]}")  # {0, 2, 4, 7, 9}
print(f"  Scale 1 (Pentatonic Minor): {SCALE_TEMPLATES[1]}")  # {0, 3, 5, 7, 10}

# Test specific candidates
print("\nTesting specific scale candidates:")

# C major pentatonic (root=0, scale=7)
c_major_pent = get_scale_template(7, 0)  # Should be {0, 2, 4, 7, 9}
print(f"  C Major Pentatonic template: {c_major_pent}")

# A minor pentatonic (root=9, scale=1)
a_minor_pent = get_scale_template(1, 9)  # Should be {9, 0, 2, 4, 7} = {0, 2, 4, 7, 9}
print(f"  A Minor Pentatonic template: {a_minor_pent}")

print(f"\nBoth templates are identical! {c_major_pent == a_minor_pent}")

# Get full analysis
root, scale_id, score = detect_best_scale(events)
print(f"\nDetection result: {pitch_names[root]} {['', 'Pentatonic Minor', 'Major', 'Chromatic', 'Natural Minor', 'Dorian', 'Phrygian', 'Pentatonic Major', 'Ritusen', 'Whole Tone'][scale_id]}")

# Get confidence analysis
confidence = analyze_key_confidence(events, top_n=5)
print(f"\nTop 5 candidates:")
for i, (root, scale_id, score, desc) in enumerate(confidence):
    print(f"  {i+1}. {desc} (score: {score:.3f})")

# Check emphasis
print(f"\nRoot emphasis analysis:")
print(f"  C (root 0) emphasis: {histogram[0]:.3f}")
print(f"  A (root 9) emphasis: {histogram[9]:.3f}")

# Check first/last note bonus
first_note = events[0].note % 12
last_note = events[-1].note % 12
print(f"\nMelodic analysis:")
print(f"  First note: {pitch_names[first_note]} (PC {first_note})")
print(f"  Last note: {pitch_names[last_note]} (PC {last_note})")
