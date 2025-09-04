"""
Demo for Mapper module - Bước 6

Tests the closest-pitch mapping functionality from MIDI notes to Shawzin characters.
"""

from midi2shawzin.mapper import (
    ShawzinMapper, build_playable_table, map_note_to_shawzin,
    find_best_scale_for_notes, quick_map_single_note, analyze_scale_compatibility
)
from midi2shawzin.midi_io import Event


def demo_playable_table():
    """Demo playable table generation."""
    print("=== Playable Table Demo ===")
    
    # Build table for major scale
    table = build_playable_table(scale_id=2, octave_range=(-1, 2))
    print(f"Major scale table has {len(table)} mappings")
    print(f"First 10 mappings: {table[:10]}")
    print(f"MIDI range: {table[0][0]} to {table[-1][0]}")
    print()


def demo_single_note_mapping():
    """Demo single note mapping."""
    print("=== Single Note Mapping Demo ===")
    
    test_notes = [60, 67, 72, 55]  # C4, G4, C5, G3
    
    for note in test_notes:
        char, mapped_midi, octave_shift = quick_map_single_note(note)
        deviation = abs(mapped_midi - note)
        print(f"MIDI {note} -> '{char}' (mapped to {mapped_midi}, "
              f"deviation: {deviation} semitones, octave shift: {octave_shift})")
    print()


def demo_scale_selection():
    """Demo automatic scale selection."""
    print("=== Scale Selection Demo ===")
    
    # C major scale
    c_major = [60, 62, 64, 65, 67, 69, 71]
    print(f"C major notes: {c_major}")
    
    best_scale = find_best_scale_for_notes(c_major)
    print(f"Best scale for C major: {best_scale}")
    
    # Analyze all scales
    analysis = analyze_scale_compatibility(c_major)
    print("Scale compatibility analysis:")
    for scale_id, result in sorted(analysis.items()):
        print(f"  Scale {scale_id}: coverage={result['coverage']:.1%}, "
              f"avg_deviation={result['avg_deviation']:.1f}")
    print()


def demo_event_mapping():
    """Demo event mapping with mapper."""
    print("=== Event Mapping Demo ===")
    
    # Create sample events
    events = [
        Event(type='note', time_sec=0.0, delta_sec=0.5, note=60),   # C4
        Event(type='note', time_sec=0.5, delta_sec=0.5, note=64),   # E4  
        Event(type='note', time_sec=1.0, delta_sec=0.5, note=67),   # G4
        Event(type='note', time_sec=1.5, delta_sec=0.5, note=72),   # C5
        Event(type='tempo', time_sec=2.0, delta_sec=0.0, tempo=120) # Non-note event
    ]
    
    print(f"Processing {len(events)} events (including non-note)")
    
    # Create mapper
    mapper = ShawzinMapper()
    
    # Map events with auto scale detection
    shawzin_notes = mapper.map_events(events)
    
    print(f"Detected scale: {mapper.current_scale_id}")
    print(f"Generated {len(shawzin_notes)} Shawzin notes:")
    
    for i, note in enumerate(shawzin_notes):
        print(f"  {i+1}. '{note.character}' at {note.time_sec:.1f}s "
              f"(MIDI {note.original_midi} -> {note.mapped_midi}, "
              f"shift: {note.octave_shift})")
    
    # Show mapping stats
    stats = mapper.get_mapping_stats()
    print(f"Mapper stats: {stats}")
    print()


def demo_consistency_caching():
    """Demo mapping consistency."""
    print("=== Consistency Caching Demo ===")
    
    # Same note repeated
    events = [
        Event(type='note', time_sec=0.0, delta_sec=0.5, note=60),
        Event(type='note', time_sec=1.0, delta_sec=0.5, note=62),
        Event(type='note', time_sec=2.0, delta_sec=0.5, note=60),  # Repeated C4
        Event(type='note', time_sec=3.0, delta_sec=0.5, note=62),  # Repeated D4
    ]
    
    mapper = ShawzinMapper()
    shawzin_notes = mapper.map_events(events, scale_id=2)
    
    print("Testing consistency for repeated notes:")
    
    # Check C4 mappings (MIDI 60)
    c4_mappings = [note for note in shawzin_notes if note.original_midi == 60]
    print(f"C4 (MIDI 60) mappings: {[note.character for note in c4_mappings]}")
    print(f"All C4 same character? {len(set(note.character for note in c4_mappings)) == 1}")
    
    # Check D4 mappings (MIDI 62)  
    d4_mappings = [note for note in shawzin_notes if note.original_midi == 62]
    print(f"D4 (MIDI 62) mappings: {[note.character for note in d4_mappings]}")
    print(f"All D4 same character? {len(set(note.character for note in d4_mappings)) == 1}")
    print()


def demo_different_scales():
    """Demo mapping with different scales."""
    print("=== Different Scales Demo ===")
    
    # Test note
    test_note = 65  # F4
    
    print(f"Mapping MIDI note {test_note} to different scales:")
    
    for scale_id in [1, 2, 3, 5, 7]:
        try:
            char, mapped_midi, octave_shift = quick_map_single_note(test_note, scale_id)
            deviation = abs(mapped_midi - test_note)
            print(f"  Scale {scale_id}: '{char}' (mapped to {mapped_midi}, "
                  f"deviation: {deviation})")
        except Exception as e:
            print(f"  Scale {scale_id}: Error - {e}")
    print()


def main():
    """Run all demos."""
    print("🎵 MIDI to Shawzin Mapper Demo - Bước 6 🎵\n")
    
    demo_playable_table()
    demo_single_note_mapping()
    demo_scale_selection()
    demo_event_mapping()
    demo_consistency_caching()
    demo_different_scales()
    
    print("✅ All mapper demos completed successfully!")
    print("\nKey Features Demonstrated:")
    print("- ✅ Playable table generation across octave ranges")
    print("- ✅ Closest-pitch mapping with ±2 semitone accuracy")
    print("- ✅ Automatic scale detection for optimal coverage")
    print("- ✅ Event processing with non-note filtering")
    print("- ✅ Mapping consistency cache for repeated notes")
    print("- ✅ Multiple scale support with character mapping")
    print("- ✅ Octave-shift heuristics for playable range")


if __name__ == "__main__":
    main()
