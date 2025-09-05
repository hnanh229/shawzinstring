#!/usr/bin/env python3
"""Deep analysis of timing and note values in the Shawzin string."""

def analyze_timing_and_notes():
    """Analyze if timing values and note characters are valid for Warframe."""
    
    note_string = "aAPaACaAaaAPaAPaAjaAyaAPxAOaABaAcaACaA3xAAxA5xA5aACaAdaAEaACaAJaAHxAEaAAxABaADaAZaADaADaACxAVxAcaADaAEaACaAUxAAaACaAaxAAaAHaAVxABxACaAbxABaAPaANxAAaACaAEaAKaALxADaAGaACaABxAEaAOxACaAEaABaACxAFxABaAB"
    
    print("=== PHÂN TÍCH CHI TIẾT TIMING VÀ NOTES ===")
    
    # Parse tokens
    tokens = []
    for i in range(0, len(note_string), 3):
        if i + 2 < len(note_string):
            token = note_string[i:i+3]
            tokens.append(token)
    
    print(f"Tổng số tokens: {len(tokens)}")
    
    # Analyze note characters
    note_chars = [token[0] for token in tokens]
    unique_notes = sorted(set(note_chars))
    print(f"\nNote characters được sử dụng: {unique_notes}")
    
    # Valid note characters for Warframe (based on layout)
    # Scale 1 typically uses: 1, q, a, z, 2, w, s, x, 3, e, d, c
    warframe_valid_notes = set('1qa z2wsx3edc45rft67ygh98uij0opl')  # All possible notes
    
    invalid_notes = set(note_chars) - warframe_valid_notes
    if invalid_notes:
        print(f"❌ Invalid note chars: {sorted(invalid_notes)}")
    else:
        print(f"✅ Tất cả note chars hợp lệ")
    
    # Analyze timing characters  
    timing_chars = []
    for token in tokens:
        timing_chars.append(token[1:3])
    
    unique_timings = sorted(set(timing_chars))
    print(f"\nTiming codes được sử dụng ({len(unique_timings)} unique):")
    for i, timing in enumerate(unique_timings):
        if i < 20:  # Show first 20
            print(f"  '{timing}'", end="")
            if (i + 1) % 8 == 0:
                print()
        elif i == 20:
            print(f"\n  ... và {len(unique_timings) - 20} timing codes khác")
            break
    
    # Try to decode timing values using our encoder
    print(f"\n=== DECODE TIMING VALUES ===")
    try:
        from midi2shawzin.encoder import shawzin_time_to_seconds
        
        timing_issues = []
        for i, timing in enumerate(unique_timings[:10]):  # Check first 10
            try:
                seconds = shawzin_time_to_seconds(timing)
                print(f"  '{timing}' -> {seconds:.4f}s")
                if seconds < 0 or seconds > 10:  # Reasonable bounds
                    timing_issues.append((timing, seconds))
            except Exception as e:
                print(f"  '{timing}' -> ERROR: {e}")
                timing_issues.append((timing, "decode_error"))
        
        if timing_issues:
            print(f"\n❌ Phát hiện {len(timing_issues)} timing values có vấn đề:")
            for timing, issue in timing_issues:
                print(f"   '{timing}': {issue}")
        else:
            print(f"\n✅ Timing values có vẻ OK")
            
    except ImportError:
        print("❌ Không thể import timing decoder")
    
    # Check for common Warframe issues
    print(f"\n=== KIỂM TRA CÁC VẤN ĐỀ THƯỜNG GẶP ===")
    
    # 1. Check if string is too long
    if len(note_string) > 200:
        print(f"⚠️  Chuỗi dài ({len(note_string)} chars) - có thể quá dài cho Warframe")
    else:
        print(f"✅ Độ dài OK ({len(note_string)} chars)")
    
    # 2. Check for timing consistency
    timing_lengths = [len(timing) for timing in unique_timings]
    if all(length == 2 for length in timing_lengths):
        print(f"✅ Tất cả timing codes đều 2 ký tự")
    else:
        print(f"❌ Có timing codes không đúng độ dài 2")
    
    # 3. Suggest fixes
    print(f"\n=== GỢI Ý KHẮC PHỤC ===")
    print("1. Thử với scale khác:")
    print("   - Scale 2 (Chromatic): 2")
    print("   - Scale 3 (Hirajoshi): 3") 
    print("2. Rút ngắn chuỗi (chỉ lấy 50-100 chars đầu)")
    print("3. Kiểm tra version Warframe (có thể đã thay đổi format)")
    print("4. Thử copy-paste cẩn thận (đừng có ký tự ẩn)")

if __name__ == '__main__':
    analyze_timing_and_notes()
