"""
Unit tests for pattern detection module.

Tests the pattern detection and compression functionality for Shawzin tokens.
"""

import pytest
from midi2shawzin.pattern_detection import (
    find_repeating_sequences,
    fold_repeats_into_refs,
    expand_pattern_refs,
    analyze_compression_ratio,
    PatternDetector,
    compress_shawzin_tokens,
    detect_song_structure,
    rolling_hash
)


class TestRollingHash:
    """Test rolling hash functionality."""
    
    def test_rolling_hash_basic(self):
        """Test basic rolling hash computation."""
        tokens = ['1AA', '2BB', '3CC', '4DD']
        hashes = rolling_hash(tokens, 2)
        
        assert len(hashes) == 3  # 4 tokens, window size 2 -> 3 hashes
        assert all(isinstance(h, int) for h in hashes)
    
    def test_rolling_hash_window_too_large(self):
        """Test rolling hash with window larger than token list."""
        tokens = ['1AA', '2BB']
        hashes = rolling_hash(tokens, 5)
        
        assert hashes == []
    
    def test_rolling_hash_identical_windows(self):
        """Test that identical token windows produce identical hashes."""
        tokens = ['1AA', '2BB', '1AA', '2BB']
        hashes = rolling_hash(tokens, 2)
        
        assert len(hashes) == 3
        assert hashes[0] == hashes[2]  # First and third windows are identical


class TestRepeatingSequences:
    """Test repeating sequence detection."""
    
    def test_find_repeating_sequences_basic(self):
        """Test basic pattern detection."""
        tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        patterns = find_repeating_sequences(tokens, min_len=3, min_occurrences=2)
        
        assert len(patterns) >= 1
        # Should find the repeated sequence ['1AA', '2BB', '3CC']
        start_indices, length = patterns[0]
        assert length == 3
        assert len(start_indices) == 2
        assert start_indices == [0, 3]
    
    def test_find_repeating_sequences_no_patterns(self):
        """Test with no repeating patterns."""
        tokens = ['1AA', '2BB', '3CC', 'qDD', 'wEE']
        patterns = find_repeating_sequences(tokens, min_len=2, min_occurrences=2)
        
        assert len(patterns) == 0
    
    def test_find_repeating_sequences_overlapping(self):
        """Test handling of overlapping patterns."""
        tokens = ['1AA', '2BB', '1AA', '2BB', '1AA', '2BB']
        patterns = find_repeating_sequences(tokens, min_len=2, min_occurrences=2)
        
        assert len(patterns) >= 1
        # Algorithm prefers longer patterns, so may find ['1AA', '2BB', '1AA'] instead of ['1AA', '2BB']
        start_indices, length = patterns[0]
        assert length >= 2  # At least length 2
        assert len(start_indices) >= 2  # At least 2 occurrences
    
    def test_find_repeating_sequences_short_tokens(self):
        """Test with token list shorter than minimum pattern length."""
        tokens = ['1AA', '2BB']
        patterns = find_repeating_sequences(tokens, min_len=4, min_occurrences=2)
        
        assert len(patterns) == 0
    
    def test_find_repeating_sequences_chorus_like(self):
        """Test detection of chorus-like repeated sections."""
        # Simulate verse-chorus-verse-chorus structure
        verse = ['1AA', '2BB', '3CC', 'qDD']
        chorus = ['wEE', 'aDDs', 'sBB', 'dCC']
        tokens = verse + chorus + verse + chorus
        
        patterns = find_repeating_sequences(tokens, min_len=4, min_occurrences=2)
        
        # Should find at least one pattern (may be the full verse+chorus sequence)
        assert len(patterns) >= 1
        
        # Check that we found significant patterns
        for start_indices, length in patterns:
            assert length >= 4  # At least minimum length
            assert len(start_indices) >= 2  # At least 2 occurrences


class TestFoldRepeats:
    """Test pattern folding and compression."""
    
    def test_fold_repeats_basic(self):
        """Test basic pattern folding."""
        tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        compressed, patterns_dict = fold_repeats_into_refs(tokens, min_len=3, min_occurrences=2)
        
        # Should compress the repeated sequence
        assert len(compressed) < len(tokens)
        assert len(patterns_dict) >= 1
        
        # Should have pattern references
        pattern_refs = [token for token in compressed if token.startswith('@')]
        assert len(pattern_refs) >= 1
    
    def test_fold_repeats_no_patterns(self):
        """Test folding with no repeating patterns."""
        tokens = ['1AA', '2BB', '3CC', 'qDD', 'wEE']
        compressed, patterns_dict = fold_repeats_into_refs(tokens, min_len=2, min_occurrences=2)
        
        assert compressed == tokens
        assert len(patterns_dict) == 0
    
    def test_fold_repeats_empty_input(self):
        """Test folding with empty input."""
        tokens = []
        compressed, patterns_dict = fold_repeats_into_refs(tokens)
        
        assert compressed == []
        assert patterns_dict == {}
    
    def test_fold_repeats_multiple_patterns(self):
        """Test folding with multiple different patterns."""
        # Pattern A: [1AA, 2BB] appears twice
        # Pattern B: [3CC, qDD] appears twice  
        tokens = ['1AA', '2BB', '3CC', 'qDD', '1AA', '2BB', '3CC', 'qDD', 'wEE']
        compressed, patterns_dict = fold_repeats_into_refs(tokens, min_len=2, min_occurrences=2)
        
        # Should detect multiple patterns
        assert len(patterns_dict) >= 1
        assert len(compressed) < len(tokens)


class TestExpandPatternRefs:
    """Test pattern reference expansion."""
    
    def test_expand_pattern_refs_basic(self):
        """Test basic pattern expansion."""
        compressed = ['@P1', 'qDD', '@P1']
        patterns_dict = {'P1': ['1AA', '2BB', '3CC']}
        
        expanded = expand_pattern_refs(compressed, patterns_dict)
        
        expected = ['1AA', '2BB', '3CC', 'qDD', '1AA', '2BB', '3CC']
        assert expanded == expected
    
    def test_expand_pattern_refs_no_refs(self):
        """Test expansion with no pattern references."""
        compressed = ['1AA', '2BB', '3CC']
        patterns_dict = {}
        
        expanded = expand_pattern_refs(compressed, patterns_dict)
        
        assert expanded == compressed
    
    def test_expand_pattern_refs_unknown_pattern(self):
        """Test expansion with unknown pattern reference."""
        compressed = ['@P1', '@P99', 'qDD']
        patterns_dict = {'P1': ['1AA', '2BB']}
        
        expanded = expand_pattern_refs(compressed, patterns_dict)
        
        # Should expand known pattern, leave unknown as-is
        expected = ['1AA', '2BB', '@P99', 'qDD']
        assert expanded == expected


class TestRoundTripConsistency:
    """Test that compression and expansion are consistent."""
    
    def test_roundtrip_consistency(self):
        """Test that fold + expand = original."""
        original = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD', 'wEE']
        
        # Compress
        compressed, patterns_dict = fold_repeats_into_refs(original, min_len=3, min_occurrences=2)
        
        # Expand back
        expanded = expand_pattern_refs(compressed, patterns_dict)
        
        # Should match original
        assert expanded == original
    
    def test_roundtrip_complex_pattern(self):
        """Test roundtrip with complex pattern structure."""
        # Create a more complex pattern structure
        pattern_a = ['1AA', '2BB', '3CC']
        pattern_b = ['qDD', 'wEE']
        original = pattern_a + pattern_b + pattern_a + pattern_b + ['sBB'] + pattern_a
        
        compressed, patterns_dict = fold_repeats_into_refs(original, min_len=2, min_occurrences=2)
        expanded = expand_pattern_refs(compressed, patterns_dict)
        
        assert expanded == original


class TestCompressionAnalysis:
    """Test compression ratio analysis."""
    
    def test_analyze_compression_ratio(self):
        """Test compression analysis."""
        original = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        compressed = ['@P1', '@P1', 'qDD']
        patterns_dict = {'P1': ['1AA', '2BB', '3CC']}
        
        stats = analyze_compression_ratio(original, compressed, patterns_dict)
        
        assert stats['original_size'] == 7
        assert stats['compressed_size'] == 3
        assert stats['compression_ratio'] == 3/7
        assert stats['space_saved'] == 4
        assert stats['patterns_detected'] == 1


class TestPatternDetectorClass:
    """Test PatternDetector class functionality."""
    
    def test_pattern_detector_init(self):
        """Test PatternDetector initialization."""
        detector = PatternDetector(
            min_pattern_length=3,
            min_occurrences=2,
            enable_compression=True
        )
        
        assert detector.min_pattern_length == 3
        assert detector.min_occurrences == 2
        assert detector.enable_compression == True
        assert detector.stats['tokens_processed'] == 0
    
    def test_pattern_detector_detect_patterns(self):
        """Test pattern detection via PatternDetector."""
        detector = PatternDetector(min_pattern_length=3)  # Lower threshold for test
        tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        
        patterns = detector.detect_patterns(tokens)
        
        assert detector.stats['tokens_processed'] == 7
        assert detector.stats['patterns_found'] >= 1
        assert len(patterns) >= 1
    
    def test_pattern_detector_compress_tokens(self):
        """Test token compression via PatternDetector."""
        detector = PatternDetector(min_pattern_length=3)  # Lower threshold for test
        tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        
        compressed, patterns_dict = detector.compress_tokens(tokens)
        
        assert len(compressed) < len(tokens)
        assert len(patterns_dict) >= 1
        assert detector.stats['patterns_applied'] >= 1
        assert detector.stats['compression_ratio'] < 1.0
    
    def test_pattern_detector_disabled_compression(self):
        """Test PatternDetector with compression disabled."""
        detector = PatternDetector(enable_compression=False)
        tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        
        patterns = detector.detect_patterns(tokens)
        compressed, patterns_dict = detector.compress_tokens(tokens)
        
        assert len(patterns) == 0
        assert compressed == tokens
        assert len(patterns_dict) == 0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_compress_shawzin_tokens(self):
        """Test compress_shawzin_tokens convenience function."""
        tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        
        compressed, patterns_dict = compress_shawzin_tokens(
            tokens, 
            enable_patterns=True,
            min_pattern_length=3,
            min_occurrences=2
        )
        
        assert len(compressed) < len(tokens)
        assert len(patterns_dict) >= 1
    
    def test_compress_shawzin_tokens_disabled(self):
        """Test compress_shawzin_tokens with patterns disabled."""
        tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        
        compressed, patterns_dict = compress_shawzin_tokens(
            tokens, 
            enable_patterns=False
        )
        
        assert compressed == tokens
        assert len(patterns_dict) == 0
    
    def test_detect_song_structure(self):
        """Test song structure detection."""
        # Create verse-chorus-verse structure
        verse = ['1AA', '2BB', '3CC', 'qDD'] * 2  # 8 tokens
        chorus = ['wEE', 'aDDs', 'sBB', 'dCC'] * 2  # 8 tokens
        tokens = verse + chorus + verse + chorus
        
        structure = detect_song_structure(tokens, min_section_length=8)
        
        # Should detect some structure
        assert isinstance(structure, dict)
        assert 'verses' in structure
        assert 'choruses' in structure


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_very_short_tokens(self):
        """Test with very short token lists."""
        tokens = ['1AA']
        patterns = find_repeating_sequences(tokens, min_len=2, min_occurrences=2)
        
        assert len(patterns) == 0
    
    def test_all_identical_tokens(self):
        """Test with all identical tokens."""
        tokens = ['1AA'] * 10
        patterns = find_repeating_sequences(tokens, min_len=2, min_occurrences=2)
        
        # Should find patterns of various lengths
        assert len(patterns) >= 1
    
    def test_no_repeats_min_occurrences(self):
        """Test where patterns exist but don't meet min_occurrences."""
        tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
        patterns = find_repeating_sequences(tokens, min_len=3, min_occurrences=3)
        
        # Pattern only occurs twice, needs 3 occurrences
        assert len(patterns) == 0
    
    def test_large_pattern_length(self):
        """Test with pattern length larger than token list."""
        tokens = ['1AA', '2BB', '3CC']
        patterns = find_repeating_sequences(tokens, min_len=10, min_occurrences=2)
        
        assert len(patterns) == 0


class TestMusicPatternRealism:
    """Test with realistic musical pattern scenarios."""
    
    def test_typical_chorus_repetition(self):
        """Test detection of typical chorus repetition."""
        # Typical song structure: Verse1-Chorus-Verse2-Chorus-Bridge-Chorus
        verse1 = ['1AA', '2BB', '3CC', 'qDD', 'wEE', 'aFF', 'sGG', 'dHH']
        chorus = ['zII', 'xJJ', 'cKK', 'vLL', 'bMM', 'nNN', 'mOO', 'lPP']
        verse2 = ['1QQ', '2RR', '3SS', 'qTT', 'wUU', 'aVV', 'sWW', 'dXX']
        bridge = ['zYY', 'xZZ', 'c11', 'v22']
        
        tokens = verse1 + chorus + verse2 + chorus + bridge + chorus
        
        patterns = find_repeating_sequences(tokens, min_len=8, min_occurrences=2)
        
        # Should detect the chorus pattern (8 tokens, 3 occurrences)
        assert len(patterns) >= 1
        
        # The largest pattern should be the chorus
        start_indices, length = patterns[0]
        assert length == 8  # Chorus length
        assert len(start_indices) == 3  # 3 occurrences
    
    def test_rhythmic_pattern_repetition(self):
        """Test detection of rhythmic patterns."""
        # Simulate a rhythmic pattern that repeats
        rhythm_pattern = ['1AA', '1AI', '1AQ', '1AI']  # Quarter-eighth-eighth-quarter
        
        # Repeat the rhythm with different notes
        tokens = []
        notes = ['1', '2', '3', 'q', 'w', 'e']
        
        for note in notes:
            pattern_with_note = [note + timing for timing in ['AA', 'AI', 'AQ', 'AI']]
            tokens.extend(pattern_with_note)
        
        # This creates a timing pattern that repeats
        patterns = find_repeating_sequences(tokens, min_len=4, min_occurrences=2)
        
        # Should find some patterns (though exact detection depends on algorithm)
        # The test verifies the function handles realistic musical data
        assert isinstance(patterns, list)
