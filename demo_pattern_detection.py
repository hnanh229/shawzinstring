"""
Pattern Detection Demo

Demonstrates the pattern detection and compression capabilities
for Shawzin token sequences.
"""

from midi2shawzin.pattern_detection import (
    find_repeating_sequences,
    fold_repeats_into_refs,
    expand_pattern_refs,
    analyze_compression_ratio,
    PatternDetector,
    compress_shawzin_tokens
)


def demo_basic_pattern_detection():
    """Demo basic pattern detection with simple repeated chorus."""
    print("=== Basic Pattern Detection Demo ===")
    
    # Create a simple song with repeated chorus
    verse1 = ['1AA', '2BB', '3CC', 'qDD']
    chorus = ['wEE', 'aFF', 'sGG', 'dHH'] 
    verse2 = ['1II', '2JJ', '3KK', 'qLL']
    bridge = ['zMM', 'xNN']
    
    # Song structure: verse1 - chorus - verse2 - chorus - bridge - chorus
    tokens = verse1 + chorus + verse2 + chorus + bridge + chorus
    
    print(f"Original tokens ({len(tokens)}): {tokens}")
    print()
    
    # Find patterns
    patterns = find_repeating_sequences(tokens, min_len=3, min_occurrences=2)
    print(f"Found {len(patterns)} patterns:")
    
    for i, (start_indices, length) in enumerate(patterns):
        pattern_tokens = tokens[start_indices[0]:start_indices[0] + length]
        print(f"  Pattern {i+1}: {pattern_tokens}")
        print(f"    Length: {length}, Occurrences: {len(start_indices)} at indices {start_indices}")
    print()
    
    # Compress with patterns
    compressed, patterns_dict = fold_repeats_into_refs(tokens, min_len=3, min_occurrences=2)
    print(f"Compressed tokens ({len(compressed)}): {compressed}")
    print(f"Pattern dictionary: {patterns_dict}")
    print()
    
    # Analyze compression
    stats = analyze_compression_ratio(tokens, compressed, patterns_dict)
    print("Compression Analysis:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Verify round-trip
    expanded = expand_pattern_refs(compressed, patterns_dict)
    print(f"Round-trip successful: {expanded == tokens}")
    print()


def demo_musical_structure():
    """Demo pattern detection with realistic musical structure."""
    print("=== Musical Structure Demo ===")
    
    # Create a more realistic song structure
    # Intro (4 tokens)
    intro = ['1AA', '1AI', '1AQ', '1AI']
    
    # Verse (8 tokens) - appears twice
    verse = ['1AA', '2BB', '3CC', 'qDD', 'wEE', 'aFF', 'sGG', 'dHH']
    
    # Chorus (6 tokens) - appears three times  
    chorus = ['zII', 'xJJ', 'cKK', 'vLL', 'bMM', 'nNN']
    
    # Bridge (4 tokens)
    bridge = ['1OO', 'qPP', 'aQQ', 'zRR']
    
    # Song: Intro - Verse1 - Chorus - Verse2 - Chorus - Bridge - Chorus
    song_tokens = intro + verse + chorus + verse + chorus + bridge + chorus
    
    print(f"Song structure ({len(song_tokens)} tokens):")
    print(f"  Intro (4): {intro}")
    print(f"  Verse (8): {verse}")  
    print(f"  Chorus (6): {chorus}")
    print(f"  Bridge (4): {bridge}")
    print()
    
    # Use PatternDetector for analysis
    detector = PatternDetector(min_pattern_length=4, min_occurrences=2)
    
    # Detect patterns
    patterns = detector.detect_patterns(song_tokens)
    print(f"Detected {len(patterns)} patterns:")
    
    for i, (start_indices, length) in enumerate(patterns):
        pattern_tokens = song_tokens[start_indices[0]:start_indices[0] + length]
        print(f"  Pattern {i+1}: {pattern_tokens[:3]}... (length {length})")
        print(f"    Occurrences: {len(start_indices)} at {start_indices}")
    print()
    
    # Compress song
    compressed, patterns_dict = detector.compress_tokens(song_tokens)
    
    print(f"Original song: {len(song_tokens)} tokens")
    print(f"Compressed: {len(compressed)} tokens")
    print(f"Compression ratio: {len(compressed)/len(song_tokens):.2%}")
    print()
    
    print("Compressed representation:")
    print(f"  {compressed}")
    print()
    
    print("Pattern definitions:")
    for pattern_id, tokens in patterns_dict.items():
        print(f"  {pattern_id}: {tokens}")
    print()
    
    # Show statistics
    stats = detector.get_stats()
    print("Detector Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()


def demo_compression_comparison():
    """Demo compression effectiveness with different pattern sizes."""
    print("=== Compression Comparison Demo ===")
    
    # Create token sequence with patterns of different sizes
    small_pattern = ['1AA', '2BB']  # 2 tokens
    medium_pattern = ['qCC', 'wDD', 'eEE', 'aFF']  # 4 tokens  
    large_pattern = ['sGG', 'dHH', 'zII', 'xJJ', 'cKK', 'vLL']  # 6 tokens
    
    # Repeat patterns different numbers of times
    tokens = (small_pattern * 5 +     # 5 occurrences
             medium_pattern * 3 +     # 3 occurrences  
             large_pattern * 2 +      # 2 occurrences
             ['noise1', 'noise2'])    # Non-repeating
    
    print(f"Test sequence ({len(tokens)} tokens):")
    print(f"  Small pattern (2 tokens): {small_pattern} × 5")
    print(f"  Medium pattern (4 tokens): {medium_pattern} × 3") 
    print(f"  Large pattern (6 tokens): {large_pattern} × 2")
    print(f"  Plus 2 non-repeating tokens")
    print()
    
    # Test different minimum pattern lengths
    for min_len in [2, 3, 4, 6]:
        compressed, patterns_dict = compress_shawzin_tokens(
            tokens, 
            min_pattern_length=min_len,
            min_occurrences=2
        )
        
        compression_ratio = len(compressed) / len(tokens)
        space_saved = len(tokens) - len(compressed)
        
        print(f"Min pattern length {min_len}:")
        print(f"  Patterns found: {len(patterns_dict)}")
        print(f"  Compressed size: {len(compressed)} tokens")
        print(f"  Space saved: {space_saved} tokens ({space_saved/len(tokens):.1%})")
        print(f"  Compression ratio: {compression_ratio:.2%}")
        print()


def demo_pattern_folding_details():
    """Demo detailed pattern folding process."""
    print("=== Pattern Folding Details Demo ===")
    
    # Simple sequence with clear repetition
    tokens = ['A', 'B', 'C', 'D', 'A', 'B', 'C', 'E', 'A', 'B', 'C', 'F']
    
    print(f"Original: {tokens}")
    print()
    
    # Show step-by-step pattern detection
    patterns = find_repeating_sequences(tokens, min_len=3, min_occurrences=2)
    
    print("Pattern Detection Results:")
    for i, (start_indices, length) in enumerate(patterns):
        pattern_tokens = tokens[start_indices[0]:start_indices[0] + length]
        print(f"  Pattern {i+1}: {pattern_tokens}")
        print(f"    Found at indices: {start_indices}")
        
        # Show where each occurrence appears in original
        for idx in start_indices:
            occurrence = tokens[idx:idx + length]
            print(f"      Index {idx}: {occurrence}")
        print()
    
    # Apply folding
    compressed, patterns_dict = fold_repeats_into_refs(tokens, min_len=3, min_occurrences=2)
    
    print("After Folding:")
    print(f"  Compressed: {compressed}")
    print(f"  Patterns: {patterns_dict}")
    print()
    
    # Show expansion
    expanded = expand_pattern_refs(compressed, patterns_dict)
    print(f"Expanded back: {expanded}")
    print(f"Matches original: {expanded == tokens}")


if __name__ == "__main__":
    demo_basic_pattern_detection()
    print("\n" + "="*60 + "\n")
    
    demo_musical_structure()
    print("\n" + "="*60 + "\n")
    
    demo_compression_comparison()
    print("\n" + "="*60 + "\n")
    
    demo_pattern_folding_details()
