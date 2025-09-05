"""
Conversion Quality Metrics

Provides functions to measure the quality of MIDI to Shawzin conversion
compared to original input, enabling comparison with other tools like Empyrrhus.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from .midi_io import Event
from .mapper import ShawzinNote


@dataclass
class ConversionMetrics:
    """Container for conversion quality metrics."""
    mapped_ratio: float              # Percentage of notes successfully mapped (0.0-1.0)
    avg_abs_semitone_error: float    # Average absolute pitch deviation in semitones
    timing_rms: float                # RMS timing error in beats
    total_notes: int                 # Total number of input notes
    mapped_notes: int                # Number of successfully mapped notes
    ignored_notes: int               # Number of notes that couldn't be mapped
    max_pitch_error: float           # Maximum pitch deviation in semitones
    timing_errors: List[float]       # Individual timing errors for analysis


def compute_mapping_metrics(original_events: List[Event], 
                          mapped_events: List[ShawzinNote],
                          ticks_per_beat: int = 480,
                          tempo_us_per_beat: int = 500000) -> ConversionMetrics:
    """
    Compute conversion quality metrics comparing original MIDI to mapped Shawzin notes.
    
    Args:
        original_events: Original MIDI note events
        mapped_events: Resulting Shawzin note events
        ticks_per_beat: MIDI ticks per beat for timing calculations
        tempo_us_per_beat: Tempo in microseconds per beat
        
    Returns:
        ConversionMetrics object with quality measurements
    """
    # Filter to note events only
    note_events = [e for e in original_events if e.type in ['note', 'note_on'] and e.note is not None]
    
    total_notes = len(note_events)
    mapped_notes = len(mapped_events)
    ignored_notes = total_notes - mapped_notes
    
    if total_notes == 0:
        return ConversionMetrics(
            mapped_ratio=0.0,
            avg_abs_semitone_error=0.0,
            timing_rms=0.0,
            total_notes=0,
            mapped_notes=0,
            ignored_notes=0,
            max_pitch_error=0.0,
            timing_errors=[]
        )
    
    # Calculate mapping ratio
    mapped_ratio = mapped_notes / total_notes if total_notes > 0 else 0.0
    
    # Calculate pitch deviations
    pitch_errors = []
    timing_errors = []
    
    # Match original events to mapped events by time proximity
    matched_pairs = _match_events_by_time(note_events, mapped_events)
    
    for original, mapped in matched_pairs:
        if original is not None and mapped is not None:
            # Pitch deviation in semitones
            original_pitch = original.note
            mapped_pitch = mapped.mapped_midi
            pitch_error = abs(mapped_pitch - original_pitch)
            pitch_errors.append(pitch_error)
            
            # Timing deviation in beats
            original_beats = _seconds_to_beats(original.time_sec, tempo_us_per_beat)
            mapped_beats = _seconds_to_beats(mapped.time_sec, tempo_us_per_beat)
            timing_error = abs(mapped_beats - original_beats)
            timing_errors.append(timing_error)
    
    # Calculate statistics
    avg_abs_semitone_error = sum(pitch_errors) / len(pitch_errors) if pitch_errors else 0.0
    max_pitch_error = max(pitch_errors) if pitch_errors else 0.0
    
    # RMS timing error
    timing_rms = math.sqrt(sum(e**2 for e in timing_errors) / len(timing_errors)) if timing_errors else 0.0
    
    return ConversionMetrics(
        mapped_ratio=mapped_ratio,
        avg_abs_semitone_error=avg_abs_semitone_error,
        timing_rms=timing_rms,
        total_notes=total_notes,
        mapped_notes=mapped_notes,
        ignored_notes=ignored_notes,
        max_pitch_error=max_pitch_error,
        timing_errors=timing_errors
    )


def _match_events_by_time(original_events: List[Event], 
                         mapped_events: List[ShawzinNote],
                         time_tolerance: float = 0.1) -> List[Tuple[Optional[Event], Optional[ShawzinNote]]]:
    """
    Match original events to mapped events by time proximity.
    
    Args:
        original_events: Original MIDI events
        mapped_events: Mapped Shawzin events
        time_tolerance: Maximum time difference for matching (seconds)
        
    Returns:
        List of (original, mapped) pairs, None for unmatched events
    """
    matched_pairs = []
    used_mapped = set()
    
    for orig in original_events:
        best_match = None
        best_distance = float('inf')
        best_idx = -1
        
        for idx, mapped in enumerate(mapped_events):
            if idx in used_mapped:
                continue
                
            time_distance = abs(orig.time_sec - mapped.time_sec)
            if time_distance < time_tolerance and time_distance < best_distance:
                best_match = mapped
                best_distance = time_distance
                best_idx = idx
        
        if best_match is not None:
            matched_pairs.append((orig, best_match))
            used_mapped.add(best_idx)
        else:
            matched_pairs.append((orig, None))  # Original note with no match
    
    # Add unmatched mapped events
    for idx, mapped in enumerate(mapped_events):
        if idx not in used_mapped:
            matched_pairs.append((None, mapped))  # Mapped note with no original
    
    return matched_pairs


def _seconds_to_beats(seconds: float, tempo_us_per_beat: int) -> float:
    """Convert seconds to beats based on tempo."""
    beat_duration = tempo_us_per_beat / 1_000_000  # Convert to seconds
    return seconds / beat_duration


def format_metrics_report(metrics: ConversionMetrics, 
                         mode: str = "melody-only",
                         include_recommendations: bool = True) -> str:
    """
    Format metrics into a readable report with quality assessment.
    
    Args:
        metrics: Computed conversion metrics
        mode: Conversion mode for context
        include_recommendations: Whether to include quality recommendations
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("CONVERSION QUALITY METRICS")
    report.append("=" * 50)
    
    # Basic statistics
    report.append(f"Total Input Notes:     {metrics.total_notes}")
    report.append(f"Successfully Mapped:   {metrics.mapped_notes}")
    report.append(f"Ignored Notes:         {metrics.ignored_notes}")
    report.append("")
    
    # Quality metrics
    report.append(f"Mapping Ratio:         {metrics.mapped_ratio:.3f} ({metrics.mapped_ratio*100:.1f}%)")
    report.append(f"Avg Pitch Error:       {metrics.avg_abs_semitone_error:.2f} semitones")
    report.append(f"Max Pitch Error:       {metrics.max_pitch_error:.2f} semitones")
    report.append(f"Timing RMS Error:      {metrics.timing_rms:.3f} beats")
    
    if include_recommendations:
        report.append("")
        report.append("QUALITY ASSESSMENT")
        report.append("-" * 30)
        
        # Mapping ratio assessment
        if mode == "melody-only":
            target_ratio = 0.95
        else:
            target_ratio = 0.90
            
        if metrics.mapped_ratio >= target_ratio:
            report.append(f"✓ Mapping Ratio: EXCELLENT (≥{target_ratio:.2f})")
        elif metrics.mapped_ratio >= target_ratio - 0.1:
            report.append(f"⚠ Mapping Ratio: GOOD (≥{target_ratio-0.1:.2f})")
        else:
            report.append(f"✗ Mapping Ratio: POOR (<{target_ratio-0.1:.2f})")
            report.append("  → Try chromatic scale (--scale-override 3)")
        
        # Pitch accuracy assessment
        if metrics.avg_abs_semitone_error <= 1.0:
            report.append("✓ Pitch Accuracy: EXCELLENT (≤1.0 semitone)")
        elif metrics.avg_abs_semitone_error <= 2.0:
            report.append("⚠ Pitch Accuracy: GOOD (≤2.0 semitones)")
        else:
            report.append("✗ Pitch Accuracy: POOR (>2.0 semitones)")
            report.append("  → Check scale selection or use chromatic scale")
        
        # Timing accuracy assessment
        if metrics.timing_rms <= 0.1:
            report.append("✓ Timing Accuracy: EXCELLENT (≤0.1 beats)")
        elif metrics.timing_rms <= 0.25:
            report.append("⚠ Timing Accuracy: GOOD (≤0.25 beats)")
        else:
            report.append("✗ Timing Accuracy: POOR (>0.25 beats)")
            report.append("  → Adjust quantization (--quantize-subdivision)")
        
        # Overall quality score
        quality_score = _compute_overall_quality(metrics, mode)
        report.append("")
        report.append(f"Overall Quality Score: {quality_score:.1f}/10")
        
        if quality_score >= 8.0:
            report.append("🎵 Excellent conversion! Ready for Warframe.")
        elif quality_score >= 6.0:
            report.append("🎼 Good conversion. Minor adjustments may improve quality.")
        else:
            report.append("🔧 Poor conversion. Consider different settings.")
    
    return "\n".join(report)


def _compute_overall_quality(metrics: ConversionMetrics, mode: str) -> float:
    """
    Compute overall quality score from 0-10 based on metrics.
    
    Args:
        metrics: Conversion metrics
        mode: Conversion mode for scoring context
        
    Returns:
        Quality score from 0.0 to 10.0
    """
    # Mapping ratio score (40% weight)
    target_ratio = 0.95 if mode == "melody-only" else 0.90
    ratio_score = min(10.0, (metrics.mapped_ratio / target_ratio) * 10.0)
    
    # Pitch accuracy score (40% weight)
    pitch_score = max(0.0, 10.0 - (metrics.avg_abs_semitone_error * 5.0))
    
    # Timing accuracy score (20% weight)
    timing_score = max(0.0, 10.0 - (metrics.timing_rms * 20.0))
    
    # Weighted average
    overall_score = (ratio_score * 0.4) + (pitch_score * 0.4) + (timing_score * 0.2)
    
    return min(10.0, max(0.0, overall_score))


def analyze_conversion_bottlenecks(metrics: ConversionMetrics) -> List[str]:
    """
    Analyze metrics to identify conversion bottlenecks and suggest improvements.
    
    Args:
        metrics: Conversion metrics to analyze
        
    Returns:
        List of improvement suggestions
    """
    suggestions = []
    
    if metrics.mapped_ratio < 0.8:
        suggestions.append("Low mapping ratio - try chromatic scale (--scale-override 3)")
        suggestions.append("Check octave range - some notes may be out of Shawzin range")
    
    if metrics.avg_abs_semitone_error > 2.0:
        suggestions.append("High pitch errors - consider different scale or chromatic mode")
        
    if metrics.timing_rms > 0.5:
        suggestions.append("Poor timing accuracy - try different quantization settings")
        suggestions.append("Consider using --keep-offsets for complex timing")
    
    if metrics.ignored_notes > metrics.mapped_notes * 0.5:
        suggestions.append("Many ignored notes - input may be too complex for current settings")
        suggestions.append("Try --chord-policy reduce for polyphonic input")
    
    return suggestions


def compare_with_benchmark(metrics: ConversionMetrics, 
                          benchmark_name: str = "Empyrrhus") -> Dict[str, Any]:
    """
    Compare metrics against benchmark tools like Empyrrhus.
    
    Args:
        metrics: Current conversion metrics
        benchmark_name: Name of benchmark tool
        
    Returns:
        Comparison results dictionary
    """
    # Estimated Empyrrhus benchmarks (would need real data for accuracy)
    empyrrhus_benchmarks = {
        "mapped_ratio": 0.92,
        "avg_abs_semitone_error": 1.2,
        "timing_rms": 0.15
    }
    
    comparison = {
        "benchmark": benchmark_name,
        "mapped_ratio_diff": metrics.mapped_ratio - empyrrhus_benchmarks["mapped_ratio"],
        "pitch_error_diff": metrics.avg_abs_semitone_error - empyrrhus_benchmarks["avg_abs_semitone_error"],
        "timing_diff": metrics.timing_rms - empyrrhus_benchmarks["timing_rms"],
        "overall_better": 0,
        "overall_worse": 0,
        "summary": ""
    }
    
    # Count improvements vs regressions
    if comparison["mapped_ratio_diff"] > 0:
        comparison["overall_better"] += 1
    elif comparison["mapped_ratio_diff"] < -0.05:
        comparison["overall_worse"] += 1
        
    if comparison["pitch_error_diff"] < 0:
        comparison["overall_better"] += 1
    elif comparison["pitch_error_diff"] > 0.5:
        comparison["overall_worse"] += 1
        
    if comparison["timing_diff"] < 0:
        comparison["overall_better"] += 1
    elif comparison["timing_diff"] > 0.1:
        comparison["overall_worse"] += 1
    
    # Generate summary
    if comparison["overall_better"] > comparison["overall_worse"]:
        comparison["summary"] = f"Better than {benchmark_name} in {comparison['overall_better']}/3 metrics"
    elif comparison["overall_worse"] > comparison["overall_better"]:
        comparison["summary"] = f"Worse than {benchmark_name} in {comparison['overall_worse']}/3 metrics"
    else:
        comparison["summary"] = f"Comparable to {benchmark_name}"
    
    return comparison
