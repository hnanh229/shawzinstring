#!/usr/bin/env python3
"""Create a shorter test string for Warframe."""

def create_short_test():
    original = "aAPaACaAaaAPaAPaAjaAyaAPxAOaABaAcaACaA3xAAxA5xA5aACaAdaAEaACaAJaAHxAEaAAxABaADaAZaADaADaACxAVxAcaADaAEaACaAUxAAaACaAaxAAaAHaAVxABxACaAbxABaAPaANxAAaACaAEaAKaALxADaAGaACaABxAEaAOxACaAEaABaACxAFxABaAB"
    
    # Take first 60 characters (20 notes)
    short = original[:60]
    complete = f"1\n{short}"
    
    print("=== SHORT TEST STRING ===")
    print(f"Original length: {len(original)} chars")
    print(f"Short version: {len(short)} chars ({len(short)//3} notes)")
    print(f"Short string: {short}")
    print()
    print("=== COMPLETE FORMAT FOR WARFRAME ===")
    print(complete)
    print()
    print("=== COPY THIS TO WARFRAME ===")
    print("Copy từ đây:")
    print("─" * 40)
    print(complete)
    print("─" * 40)
    print("Đến đây ↑")

if __name__ == '__main__':
    create_short_test()
