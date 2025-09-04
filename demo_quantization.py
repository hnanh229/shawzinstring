#!/usr/bin/env python3
"""
Quantization Demo

Demonstrates quantization algorithms with various settings and scenarios.
"""

from midi2shawzin.midi_io import Event
from midi2shawzin.quantize import (
    Quantizer,
    QuantizeSettings,
    seconds_to_beats,
    beats_to_seconds,
    detect_tempo_from_events,
    quantize_to_sixteenth_notes,
    quantize_with_humanization
)

def print_timing_comparison(original_events, quantized_events, title="Timing Comparison"):
    """Print before/after timing comparison."""
    print(f"\n{title}")
    print("-" * 50)
    print("Original -> Quantized (Delta)")
    
    for i, (orig, quant) in enumerate(zip(original_events, quantized_events)):
        delta_ms = (quant.time_sec - orig.time_sec) * 1000
        print(f"  Event {i+1}: {orig.time_sec:.3f}s -> {quant.time_sec:.3f}s ({delta_ms:+.1f}ms)")

def demo_basic_quantization():
    """Demonstrate basic quantization functionality."""
    print("=" * 60)
    print("QUANTIZATION DEMO")
    print("=" * 60)
    
    # Create events with slightly off-grid timing
    print("\nTest 1: Basic 1/16 Note Quantization (120 BPM)")
    print("Creating events at slightly off-grid times...")
    
    events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),       # On grid
        Event(type='note', note=62, time_sec=0.123, delta_sec=0.123, velocity=80),   # Near 0.125 (1/16)
        Event(type='note', note=64, time_sec=0.247, delta_sec=0.124, velocity=80),   # Near 0.25 (1/8)
        Event(type='note', note=65, time_sec=0.381, delta_sec=0.134, velocity=80),   # Near 0.375 (3/16)
        Event(type='note', note=67, time_sec=0.501, delta_sec=0.120, velocity=80),   # Near 0.5 (1/4)
    ]
    
    # Quantize to 1/16 notes
    quantized = quantize_to_sixteenth_notes(events, tempo_bpm=120.0)
    print_timing_comparison(events, quantized, "1/16 Note Quantization Results")
    
    # Show grid positions
    quantizer = Quantizer(QuantizeSettings(subdivision=16))
    grid_positions = quantizer.get_grid_positions(duration_beats=2.0)
    print(f"\n1/16 Note Grid Positions (2 beats): {[f'{pos:.3f}' for pos in grid_positions[:9]]}...")

def demo_quantization_modes():
    """Demonstrate different quantization modes."""
    print("\n\nTest 2: Quantization Modes Comparison")
    print("Testing 'nearest' vs 'floor' modes...")
    
    # Events between grid positions
    events = [
        Event(type='note', note=60, time_sec=0.1, delta_sec=0.1, velocity=80),    # Between 0 and 0.125
        Event(type='note', note=62, time_sec=0.2, delta_sec=0.1, velocity=80),   # Between 0.125 and 0.25
        Event(type='note', note=64, time_sec=0.3, delta_sec=0.1, velocity=80),   # Between 0.25 and 0.375
    ]
    
    # Nearest mode
    settings_nearest = QuantizeSettings(subdivision=16, mode='nearest')
    quantizer_nearest = Quantizer(settings_nearest)
    quantized_nearest = quantizer_nearest.quantize(events, tempo_bpm=120.0)
    
    # Floor mode
    settings_floor = QuantizeSettings(subdivision=16, mode='floor')
    quantizer_floor = Quantizer(settings_floor)
    quantized_floor = quantizer_floor.quantize(events, tempo_bpm=120.0)
    
    print_timing_comparison(events, quantized_nearest, "Nearest Mode")
    print_timing_comparison(events, quantized_floor, "Floor Mode")

def demo_humanization():
    """Demonstrate humanization effects."""
    print("\n\nTest 3: Humanization Effects")
    print("Adding subtle timing variations...")
    
    # Perfect grid timing
    events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=62, time_sec=0.125, delta_sec=0.125, velocity=80),
        Event(type='note', note=64, time_sec=0.25, delta_sec=0.125, velocity=80),
        Event(type='note', note=65, time_sec=0.375, delta_sec=0.125, velocity=80),
    ]
    
    # Apply humanization
    humanized = quantize_with_humanization(events, tempo_bpm=120.0, jitter_ms=5.0)
    
    print_timing_comparison(events, humanized, "Humanization (±5ms)")
    
    print("\nHumanization Variations (same input, different random results):")
    for i in range(3):
        varied = quantize_with_humanization(events, tempo_bpm=120.0, jitter_ms=8.0)
        print(f"  Variation {i+1}: {[f'{e.time_sec:.3f}' for e in varied]}")

def demo_tempo_detection():
    """Demonstrate tempo detection."""
    print("\n\nTest 4: Automatic Tempo Detection")
    print("Detecting tempo from event timing patterns...")
    
    # Create events at different tempos
    tempos_to_test = [90, 120, 140, 180]
    
    for bpm in tempos_to_test:
        beat_duration = 60.0 / bpm
        events = [
            Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
            Event(type='note', note=62, time_sec=beat_duration, delta_sec=beat_duration, velocity=80),
            Event(type='note', note=64, time_sec=beat_duration*2, delta_sec=beat_duration, velocity=80),
            Event(type='note', note=65, time_sec=beat_duration*3, delta_sec=beat_duration, velocity=80),
        ]
        
        detected_bpm = detect_tempo_from_events(events)
        error = abs(detected_bpm - bpm)
        print(f"  Expected: {bpm} BPM, Detected: {detected_bpm:.1f} BPM (error: {error:.1f})")

def demo_subdivision_comparison():
    """Compare different subdivision settings."""
    print("\n\nTest 5: Subdivision Comparison")
    print("Same events quantized to different grid resolutions...")
    
    # Events with complex timing
    events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=62, time_sec=0.083, delta_sec=0.083, velocity=80),   # Near 1/12 (triplet)
        Event(type='note', note=64, time_sec=0.167, delta_sec=0.084, velocity=80),   # Near 1/6
        Event(type='note', note=65, time_sec=0.333, delta_sec=0.166, velocity=80),   # Near 1/3
    ]
    
    subdivisions = [8, 16, 32]
    
    for subdivision in subdivisions:
        settings = QuantizeSettings(subdivision=subdivision, mode='nearest')
        quantizer = Quantizer(settings)
        quantized = quantizer.quantize(events, tempo_bpm=120.0)
        
        print(f"\nSubdivision {subdivision} (1/{subdivision//4} notes):")
        for i, (orig, quant) in enumerate(zip(events, quantized)):
            print(f"  Event {i+1}: {orig.time_sec:.3f}s -> {quant.time_sec:.3f}s")

def demo_edge_cases():
    """Test edge cases and error conditions."""
    print("\n\nTest 6: Edge Cases")
    print("Testing boundary conditions...")
    
    # Empty events
    quantizer = Quantizer()
    result = quantizer.quantize([])
    print(f"  Empty events: {len(result)} events returned")
    
    # Single event
    single_event = [Event(type='note', note=60, time_sec=1.0, delta_sec=1.0, velocity=80)]
    result = quantizer.quantize(single_event, tempo_bpm=120.0)
    print(f"  Single event: {result[0].time_sec:.3f}s (quantized)")
    
    # Very fast tempo
    fast_events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=62, time_sec=0.1, delta_sec=0.1, velocity=80),
    ]
    detected_tempo = detect_tempo_from_events(fast_events)
    print(f"  Fast tempo detection: {detected_tempo:.1f} BPM (clamped)")
    
    # Very slow tempo
    slow_events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=62, time_sec=2.0, delta_sec=2.0, velocity=80),
    ]
    detected_tempo = detect_tempo_from_events(slow_events)
    print(f"  Slow tempo detection: {detected_tempo:.1f} BPM (clamped)")

if __name__ == "__main__":
    demo_basic_quantization()
    demo_quantization_modes()
    demo_humanization()
    demo_tempo_detection()
    demo_subdivision_comparison()
    demo_edge_cases()
    
    print("\n" + "=" * 60)
    print("QUANTIZATION DEMO COMPLETED")
    print("=" * 60)
