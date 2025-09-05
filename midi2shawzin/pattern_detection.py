"""
Pattern Detection and Reuse Module

Detects repeated sequences of Shawzin tokens and replaces them with references
to shorten output. This is especially useful for songs with repeating sections
like choruses, verses, or rhythmic patterns.

Key Features:
- Rolling hash-based pattern detection for token sequences
- Greedy replacement with references
- Configurable minimum pattern length and occurrence count
- Optional pattern compression (can be disabled)

Example:
    >>> tokens = ['1AA', '2BB', '3CC', '1AA', '2BB', '3CC', 'qDD']
    >>> patterns = find_repeating_sequences(tokens, min_len=3, min_occurrences=2)
    >>> compressed, refs = fold_repeats_into_refs(tokens)
"""

from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class PatternMatch:
    """Represents a detected pattern match."""
    start_index: int
    length: int
    pattern_id: str
    occurrences: List[int]  # List of start indices where pattern occurs


@dataclass
class PatternReference:
    """Represents a reference to a pattern."""
    pattern_id: str
    original_tokens: List[str]


def rolling_hash(tokens: List[str], window_size: int) -> List[int]:
    """
    Compute rolling hash for token sequences.
    
    Args:
        tokens: List of token strings
        window_size: Size of sliding window
        
    Returns:
        List of hash values for each window position
    """
    if window_size > len(tokens):
        return []
    
    hashes = []
    for i in range(len(tokens) - window_size + 1):
        window = tokens[i:i + window_size]
        # Create hash from concatenated tokens
        content = ''.join(window)
        hash_value = hash(content)
        hashes.append(hash_value)
    
    return hashes


def find_repeating_sequences(tokens: List[str], 
                           min_len: int = 4, 
                           min_occurrences: int = 2) -> List[Tuple[List[int], int]]:
    """
    Find repeated sequences of tokens using rolling hash approach.
    
    Args:
        tokens: List of token strings to analyze
        min_len: Minimum length of patterns to detect
        min_occurrences: Minimum number of times pattern must occur
        
    Returns:
        List of (start_indices, length) tuples for detected patterns
    """
    if len(tokens) < min_len:
        return []
    
    patterns = []
    
    # Try different pattern lengths, starting from longest
    max_len = min(len(tokens) // min_occurrences, 50)
    
    for pattern_len in range(max_len, min_len - 1, -1):
        # Get rolling hashes for this pattern length
        hashes = rolling_hash(tokens, pattern_len)
        
        # Group by hash value to find potential matches
        hash_groups = defaultdict(list)
        for i, hash_val in enumerate(hashes):
            hash_groups[hash_val].append(i)
        
        # Check each group for actual pattern matches
        for hash_val, indices in hash_groups.items():
            if len(indices) >= min_occurrences:
                # Verify that sequences are actually identical (not just hash collision)
                base_pattern = tokens[indices[0]:indices[0] + pattern_len]
                confirmed_indices = [indices[0]]
                
                for idx in indices[1:]:
                    candidate = tokens[idx:idx + pattern_len]
                    if candidate == base_pattern:
                        # Check for overlap with already found patterns
                        overlaps = False
                        for existing_start_indices, existing_len in patterns:
                            for existing_idx in existing_start_indices:
                                if (idx < existing_idx + existing_len and 
                                    idx + pattern_len > existing_idx):
                                    overlaps = True
                                    break
                            if overlaps:
                                break
                        
                        if not overlaps:
                            confirmed_indices.append(idx)
                
                if len(confirmed_indices) >= min_occurrences:
                    patterns.append((confirmed_indices, pattern_len))
    
    # Sort by potential savings (length * occurrences)
    patterns.sort(key=lambda p: p[1] * len(p[0]), reverse=True)
    
    return patterns


def fold_repeats_into_refs(tokens: List[str], 
                          min_len: int = 4, 
                          min_occurrences: int = 2) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Replace repeated token sequences with references using greedy algorithm.
    
    Args:
        tokens: Original list of tokens
        min_len: Minimum pattern length to detect
        min_occurrences: Minimum occurrences for replacement
        
    Returns:
        Tuple of (tokens_with_refs, patterns_dict) where patterns_dict
        maps pattern IDs to their original token sequences
    """
    if not tokens:
        return [], {}
    
    # Find all repeating patterns
    patterns = find_repeating_sequences(tokens, min_len, min_occurrences)
    
    if not patterns:
        return tokens.copy(), {}
    
    # Create pattern references
    patterns_dict = {}
    compressed = tokens.copy()
    
    # Apply replacements greedily (largest savings first)
    pattern_id = 1
    
    for start_indices, length in patterns:
        # Get the pattern tokens
        pattern_tokens = tokens[start_indices[0]:start_indices[0] + length]
        current_pattern_id = f"P{pattern_id}"
        
        # Check if this pattern is still beneficial after previous replacements
        current_occurrences = []
        
        # Find current occurrences in compressed tokens
        for i in range(len(compressed) - length + 1):
            if compressed[i:i + length] == pattern_tokens:
                current_occurrences.append(i)
        
        # Apply replacement if still beneficial
        if len(current_occurrences) >= min_occurrences:
            # Replace from right to left to maintain indices
            current_occurrences.sort(reverse=True)
            
            for idx in current_occurrences:
                # Replace pattern with reference token
                ref_token = f"@{current_pattern_id}"
                compressed[idx:idx + length] = [ref_token]
            
            # Store pattern in dictionary
            patterns_dict[current_pattern_id] = pattern_tokens
            pattern_id += 1
    
    return compressed, patterns_dict


def expand_pattern_refs(compressed_tokens: List[str], 
                       patterns_dict: Dict[str, List[str]]) -> List[str]:
    """
    Expand pattern references back to original tokens.
    
    Args:
        compressed_tokens: Tokens with pattern references
        patterns_dict: Dictionary mapping pattern IDs to token sequences
        
    Returns:
        Expanded token list
    """
    expanded = []
    
    for token in compressed_tokens:
        if token.startswith('@') and token[1:] in patterns_dict:
            # Expand pattern reference
            pattern_id = token[1:]
            expanded.extend(patterns_dict[pattern_id])
        else:
            # Regular token
            expanded.append(token)
    
    return expanded


def analyze_compression_ratio(original_tokens: List[str], 
                             compressed_tokens: List[str], 
                             patterns_dict: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Analyze compression effectiveness.
    
    Args:
        original_tokens: Original token list
        compressed_tokens: Compressed token list
        patterns_dict: Pattern references dictionary
        
    Returns:
        Dictionary with compression statistics
    """
    original_size = len(original_tokens)
    compressed_size = len(compressed_tokens)
    
    # Calculate space saved by patterns
    total_pattern_size = sum(len(tokens) for tokens in patterns_dict.values())
    
    compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
    space_saved = original_size - compressed_size
    
    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'compression_ratio': compression_ratio,
        'space_saved': space_saved,
        'space_saved_percent': (space_saved / original_size * 100) if original_size > 0 else 0.0,
        'patterns_detected': len(patterns_dict),
        'total_pattern_size': total_pattern_size
    }


class PatternDetector:
    """
    Advanced pattern detection with configurable settings.
    """
    
    def __init__(self, 
                 min_pattern_length: int = 4,
                 min_occurrences: int = 2,
                 max_pattern_length: int = 50,
                 enable_compression: bool = True):
        """
        Initialize pattern detector.
        
        Args:
            min_pattern_length: Minimum length of patterns to detect
            min_occurrences: Minimum occurrences for pattern to be useful
            max_pattern_length: Maximum pattern length to consider
            enable_compression: Whether to enable pattern compression
        """
        self.min_pattern_length = min_pattern_length
        self.min_occurrences = min_occurrences
        self.max_pattern_length = max_pattern_length
        self.enable_compression = enable_compression
        self.stats = {
            'patterns_found': 0,
            'patterns_applied': 0,
            'tokens_processed': 0,
            'compression_ratio': 1.0
        }
    
    def detect_patterns(self, tokens: List[str]) -> List[Tuple[List[int], int]]:
        """
        Detect patterns in token sequence.
        
        Args:
            tokens: List of tokens to analyze
            
        Returns:
            List of (start_indices, length) tuples for detected patterns
        """
        self.stats['tokens_processed'] = len(tokens)
        
        if not self.enable_compression:
            return []
        
        patterns = find_repeating_sequences(
            tokens, 
            self.min_pattern_length, 
            self.min_occurrences
        )
        
        # Filter by max length
        patterns = [(indices, length) for indices, length in patterns 
                   if length <= self.max_pattern_length]
        
        self.stats['patterns_found'] = len(patterns)
        return patterns
    
    def compress_tokens(self, tokens: List[str]) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Compress tokens using pattern detection.
        
        Args:
            tokens: Original tokens
            
        Returns:
            Tuple of (compressed_tokens, patterns_dict)
        """
        if not self.enable_compression:
            return tokens.copy(), {}
        
        compressed, patterns_dict = fold_repeats_into_refs(
            tokens,
            self.min_pattern_length,
            self.min_occurrences
        )
        
        self.stats['patterns_applied'] = len(patterns_dict)
        if len(tokens) > 0:
            self.stats['compression_ratio'] = len(compressed) / len(tokens)
        
        return compressed, patterns_dict
    
    def get_stats(self) -> Dict[str, any]:
        """Get compression statistics."""
        return self.stats.copy()


# Convenience functions
def compress_shawzin_tokens(tokens: List[str], 
                           enable_patterns: bool = True,
                           min_pattern_length: int = 4,
                           min_occurrences: int = 2) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Compress Shawzin tokens with pattern detection.
    
    Args:
        tokens: List of Shawzin tokens
        enable_patterns: Whether to enable pattern compression
        min_pattern_length: Minimum pattern length
        min_occurrences: Minimum pattern occurrences
        
    Returns:
        Tuple of (compressed_tokens, patterns_dict)
    """
    if not enable_patterns:
        return tokens.copy(), {}
    
    return fold_repeats_into_refs(tokens, min_pattern_length, min_occurrences)


def detect_song_structure(tokens: List[str], 
                         min_section_length: int = 8) -> Dict[str, List[Tuple[int, int]]]:
    """
    Detect song structure patterns (verse, chorus, etc.).
    
    Args:
        tokens: List of Shawzin tokens
        min_section_length: Minimum length for section detection
        
    Returns:
        Dictionary mapping section types to (start, end) indices
    """
    patterns = find_repeating_sequences(tokens, min_section_length, 2)
    
    structure = {
        'verses': [],
        'choruses': [],
        'bridges': [],
        'outros': []
    }
    
    # Classify patterns by characteristics
    for start_indices, length in patterns:
        positions = [(idx, idx + length) for idx in start_indices]
        
        # Simple heuristic: longer patterns are more likely to be choruses
        if length >= min_section_length * 2:
            structure['choruses'].extend(positions)
        else:
            structure['verses'].extend(positions)
    
    return structure
