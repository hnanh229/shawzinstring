#!/usr/bin/env python3
"""Fix the format to match original Warframe spec - no newlines."""

def fix_warframe_format():
    """Create correct single-line format."""
    
    # Current format (with newline)
    current = """1
aAPaACaAaaAPaAPaAjaAyaAPxAOaABaAcaACaA3xAAxA5xA5aACaAdaAEaACaAJaAHxAEaAAxABaADaAZaADaADaACxAVxAcaADaAEaACaAUxAAaACaAaxAAaAHaAVxABxACaAbxABaAPaANxAAaACaAEaAKaALxADaAGaACaABxAEaAOxACaAEaABaACxAFxABaAB"""
    
    # Correct format (single line)
    correct = "1aAPaACaAaaAPaAPaAjaAyaAPxAOaABaAcaACaA3xAAxA5xA5aACaAdaAEaACaAJaAHxAEaAAxABaADaAZaADaADaACxAVxAcaADaAEaACaAUxAAaACaAaxAAaAHaAVxABxACaAbxABaAPaANxAAaACaAEaAKaALxADaAGaACaABxAEaAOxACaAEaABaACxAFxABaAB"
    
    print("=== FORMAT CORRECTION ===")
    print("❌ Current format (with newline):")
    print(repr(current))
    print()
    print("✅ Correct format (single line):")
    print(repr(correct))
    print()
    print("=== COPY THIS TO WARFRAME ===")
    print("─" * 50)
    print(correct)
    print("─" * 50)
    print()
    
    # Also create shorter version for testing
    short_correct = "1aAPaACaAaaAPaAPaAjaAyaAPxAOaABaAcaACaA3xAAxA5xA5aACaAdaAEaAC"
    print("=== SHORT TEST VERSION ===")
    print("─" * 50)
    print(short_correct)
    print("─" * 50)
    
    # Analyze lengths
    print(f"\nFull length: {len(correct)} characters")
    print(f"Short length: {len(short_correct)} characters")
    print(f"Note count (full): {(len(correct)-1)//3}")
    print(f"Note count (short): {(len(short_correct)-1)//3}")

if __name__ == '__main__':
    fix_warframe_format()
