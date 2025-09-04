#!/usr/bin/env python3
"""
Chord Handling Demo

Demonstrates chord processing capabilities including reduction and arpeggiation.
"""

from midi2shawzin.midi_io import Event
from midi2shawzin.chord_handling import (
    ChordPolicy,
    ChordProcessor,
    group_simultaneous,
    analyze_chord_structure,
    reduce_chord,
    create_arpeggio_events,
    process_all_chords,
    reduce_chords_to_melody_bass,
    arpeggiate_all_chords,
    conservative_chord_reduction
)

def print_events_summary(events, title="Events"):
    """Print a summary of events."""
    print(f"\n{title}:")
    print("-" * 50)
    if not events:
        print("  (No events)")
        return
    
    for i, event in enumerate(events):
        note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][event.note % 12]
        octave = event.note // 12 - 1
        print(f"  {i+1}. {note_name}{octave} (MIDI {event.note}) at {event.time_sec:.3f}s")

def print_chord_groups(groups, title="Chord Groups"):
    """Print chord groups analysis."""
    print(f"\n{title}:")
    print("-" * 50)
    for i, group in enumerate(groups):
        if len(group) > 1:
            notes = [e.note for e in group if e.type == 'note']
            note_names = []
            for note in sorted(notes):
                note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][note % 12]
                octave = note // 12 - 1
                note_names.append(f"{note_name}{octave}")
            print(f"  Group {i+1}: {len(group)} notes - {', '.join(note_names)} at {group[0].time_sec:.3f}s")
        else:
            note = group[0].note
            note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][note % 12]
            octave = note // 12 - 1
            print(f"  Group {i+1}: Single note - {note_name}{octave} at {group[0].time_sec:.3f}s")

def demo_simultaneous_grouping():
    """Demonstrate simultaneous event grouping."""
    print("=" * 60)
    print("CHORD HANDLING DEMO")
    print("=" * 60)
    
    print("\nTest 1: Simultaneous Event Grouping")
    print("Creating polyphonic events...")
    
    # Create events with multiple chords and single notes
    events = [
        # C major chord at t=0
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),   # C4
        Event(type='note', note=64, time_sec=0.0, delta_sec=0.0, velocity=80),   # E4
        Event(type='note', note=67, time_sec=0.0, delta_sec=0.0, velocity=80),   # G4
        
        # Single note at t=0.5
        Event(type='note', note=72, time_sec=0.5, delta_sec=0.5, velocity=80),   # C5
        
        # F major 7th chord at t=1.0 (4 notes)
        Event(type='note', note=53, time_sec=1.0, delta_sec=0.5, velocity=80),   # F3
        Event(type='note', note=57, time_sec=1.0, delta_sec=0.0, velocity=80),   # A3  
        Event(type='note', note=60, time_sec=1.0, delta_sec=0.0, velocity=80),   # C4
        Event(type='note', note=64, time_sec=1.0, delta_sec=0.0, velocity=80),   # E4
    ]
    
    print_events_summary(events, "Original Events")
    
    # Group simultaneous events
    groups = group_simultaneous(events, eps=1e-3)
    print_chord_groups(groups, "Grouped Events")

def demo_chord_analysis():
    """Demonstrate chord structure analysis."""
    print("\n\nTest 2: Chord Structure Analysis")
    print("Analyzing chord structures...")
    
    test_chords = [
        ([60, 64, 67], "C Major Triad"),
        ([60, 63, 67], "C Minor Triad"), 
        ([60, 64, 67, 71], "C Major 7th"),
        ([53, 57, 60, 64, 67], "F Major with extensions"),
        ([69, 72, 76], "A Major (different octave)"),
    ]
    
    for notes, chord_name in test_chords:
        analysis = analyze_chord_structure(notes)
        print(f"\n{chord_name}: {notes}")
        print(f"  Bass: {analysis.get('bass', 'N/A')} | Melody: {analysis.get('melody', 'N/A')}")
        print(f"  Root: {analysis.get('root', 'N/A')} | Third: {analysis.get('third', 'N/A')} | Fifth: {analysis.get('fifth', 'N/A')}")

def demo_chord_reduction():
    """Demonstrate chord reduction policies."""
    print("\n\nTest 3: Chord Reduction")
    print("Reducing complex chords to simpler forms...")
    
    # Create a complex 5-note chord
    complex_chord_notes = [48, 52, 55, 59, 62, 67]  # C3, E3, G3, B3, D4, G4
    
    print(f"\nOriginal chord: {complex_chord_notes} ({len(complex_chord_notes)} notes)")
    
    # Test different reduction approaches
    reduced_3 = reduce_chord(complex_chord_notes, 'reduce', max_notes=3)
    reduced_2 = reduce_chord(complex_chord_notes, 'reduce', max_notes=2)
    arpeggio = reduce_chord(complex_chord_notes, 'arpeggiate')
    
    print(f"Reduced to 3 notes: {reduced_3}")
    print(f"Reduced to 2 notes: {reduced_2}")
    print(f"Arpeggio mode: {arpeggio} (all notes, timing handled separately)")

def demo_arpeggiation():
    """Demonstrate chord arpeggiation."""
    print("\n\nTest 4: Chord Arpeggiation")
    print("Converting chords to arpeggiated sequences...")
    
    # Create simultaneous chord events
    chord_events = [
        Event(type='note', note=60, time_sec=1.0, delta_sec=1.0, velocity=80),   # C4
        Event(type='note', note=64, time_sec=1.0, delta_sec=0.0, velocity=80),   # E4
        Event(type='note', note=67, time_sec=1.0, delta_sec=0.0, velocity=80),   # G4
        Event(type='note', note=72, time_sec=1.0, delta_sec=0.0, velocity=80),   # C5
    ]
    
    print_events_summary(chord_events, "Original Simultaneous Chord")
    
    # Create arpeggio with 25ms spread
    arpeggiated = create_arpeggio_events(chord_events, spread_ms=25.0)
    print_events_summary(arpeggiated, "Arpeggiated Sequence (25ms spread)")

def demo_policy_comparison():
    """Compare different chord processing policies."""
    print("\n\nTest 5: Policy Comparison")
    print("Comparing different chord processing policies...")
    
    # Create polyphonic music with various chord types
    polyphonic_events = [
        # 4-note chord at t=0
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),   # C4
        Event(type='note', note=64, time_sec=0.0, delta_sec=0.0, velocity=80),   # E4
        Event(type='note', note=67, time_sec=0.0, delta_sec=0.0, velocity=80),   # G4
        Event(type='note', note=71, time_sec=0.0, delta_sec=0.0, velocity=80),   # B4
        
        # Single note at t=0.5
        Event(type='note', note=72, time_sec=0.5, delta_sec=0.5, velocity=80),   # C5
        
        # 5-note chord at t=1.0
        Event(type='note', note=53, time_sec=1.0, delta_sec=0.5, velocity=80),   # F3
        Event(type='note', note=57, time_sec=1.0, delta_sec=0.0, velocity=80),   # A3
        Event(type='note', note=60, time_sec=1.0, delta_sec=0.0, velocity=80),   # C4
        Event(type='note', note=64, time_sec=1.0, delta_sec=0.0, velocity=80),   # E4
        Event(type='note', note=69, time_sec=1.0, delta_sec=0.0, velocity=80),   # A4
    ]
    
    print_events_summary(polyphonic_events, "Original Polyphonic Music")
    
    # Apply different policies
    policies = [
        ("Conservative (max 3 notes)", conservative_chord_reduction),
        ("Melody + Bass only", reduce_chords_to_melody_bass),
        ("Arpeggiate all chords", lambda events: arpeggiate_all_chords(events, spread_ms=20.0)),
    ]
    
    for policy_name, policy_func in policies:
        processed = policy_func(polyphonic_events)
        print_events_summary(processed, f"Policy: {policy_name}")

def demo_chord_processor_class():
    """Demonstrate ChordProcessor class with statistics."""
    print("\n\nTest 6: Chord Processor with Statistics")
    print("Using ChordProcessor class with different policies...")
    
    # Create test events with multiple chords
    test_events = [
        # Chord 1: C major (3 notes)
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=64, time_sec=0.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=67, time_sec=0.0, delta_sec=0.0, velocity=80),
        
        # Chord 2: F major 7th (4 notes) 
        Event(type='note', note=53, time_sec=1.0, delta_sec=1.0, velocity=80),
        Event(type='note', note=57, time_sec=1.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=60, time_sec=1.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=64, time_sec=1.0, delta_sec=0.0, velocity=80),
        
        # Chord 3: G major (3 notes)
        Event(type='note', note=67, time_sec=2.0, delta_sec=1.0, velocity=80),
        Event(type='note', note=71, time_sec=2.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=74, time_sec=2.0, delta_sec=0.0, velocity=80),
    ]
    
    # Test reduction policy
    reduction_policy = ChordPolicy(max_chord_notes=2, reduction_mode='reduce')
    reduction_processor = ChordProcessor(reduction_policy)
    reduced_result = reduction_processor.process(test_events)
    
    print(f"Reduction Policy Results:")
    print(f"  Original events: {len(test_events)}")
    print(f"  Processed events: {len(reduced_result)}")
    print(f"  Statistics: {reduction_processor.get_stats()}")
    
    # Test arpeggiation policy
    arpeggio_policy = ChordPolicy(max_chord_notes=1, reduction_mode='arpeggiate', arpeggio_spread_ms=30.0)
    arpeggio_processor = ChordProcessor(arpeggio_policy)
    arpeggio_result = arpeggio_processor.process(test_events)
    
    print(f"\nArpeggiation Policy Results:")
    print(f"  Original events: {len(test_events)}")
    print(f"  Processed events: {len(arpeggio_result)}")
    print(f"  Statistics: {arpeggio_processor.get_stats()}")

def demo_edge_cases():
    """Test edge cases and error conditions."""
    print("\n\nTest 7: Edge Cases")
    print("Testing boundary conditions...")
    
    # Empty events
    processor = ChordProcessor()
    result = processor.process([])
    print(f"Empty events: {len(result)} events returned")
    
    # Single event
    single_event = [Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80)]
    result = processor.process(single_event)
    print(f"Single event: {len(result)} events returned")
    
    # Very close timing (within epsilon)
    close_events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=64, time_sec=0.0005, delta_sec=0.0005, velocity=80),  # 0.5ms later
    ]
    groups = group_simultaneous(close_events, eps=1e-3)
    print(f"Close timing (0.5ms apart): {len(groups)} groups")
    
    # Very far timing
    far_events = [
        Event(type='note', note=60, time_sec=0.0, delta_sec=0.0, velocity=80),
        Event(type='note', note=64, time_sec=0.002, delta_sec=0.002, velocity=80),  # 2ms later
    ]
    groups = group_simultaneous(far_events, eps=1e-3)
    print(f"Far timing (2ms apart): {len(groups)} groups")

if __name__ == "__main__":
    demo_simultaneous_grouping()
    demo_chord_analysis()
    demo_chord_reduction()
    demo_arpeggiation()
    demo_policy_comparison() 
    demo_chord_processor_class()
    demo_edge_cases()
    
    print("\n" + "=" * 60)
    print("CHORD HANDLING DEMO COMPLETED")
    print("=" * 60)
