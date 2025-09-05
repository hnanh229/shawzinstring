#!/usr/bin/env python3
"""Check our note mapping vs Emphyrrus standard."""

def check_note_mapping():
    """Compare our note mapping with Emphyrrus/Warframe standard."""
    
    print("=== SO SÁNH NOTE MAPPING ===")
    print()
    
    # Emphyrrus note mapping from the documentation
    emphyrrus_mapping = {
        # String 1 (Sky)
        'B': (1, 'no_fret'),
        'J': (1, 'sky'), 
        'R': (1, 'earth'),
        'Z': (1, 'sky+earth'),
        'h': (1, 'water'),
        'p': (1, 'sky+water'),
        'x': (1, 'earth+water'),
        '5': (1, 'sky+earth+water'),
        
        # String 2 (Earth)  
        'C': (2, 'no_fret'),
        'K': (2, 'sky'),
        'S': (2, 'earth'),
        'a': (2, 'sky+earth'),
        'i': (2, 'water'),
        'q': (2, 'sky+water'),
        'y': (2, 'earth+water'),
        '6': (2, 'sky+earth+water'),
        
        # String 3 (Water)
        'E': (3, 'no_fret'),
        'M': (3, 'sky'),
        'U': (3, 'earth'),
        'c': (3, 'sky+earth'),
        'k': (3, 'water'),
        's': (3, 'sky+water'),
        '0': (3, 'earth+water'),
        '8': (3, 'sky+earth+water'),
    }
    
    print("📋 EMPHYRRUS NOTE MAPPING (theo tài liệu):")
    print("String 1: B(no) J(sky) R(earth) Z(sky+earth) h(water) p(sky+water) x(earth+water) 5(all)")
    print("String 2: C(no) K(sky) S(earth) a(sky+earth) i(water) q(sky+water) y(earth+water) 6(all)")  
    print("String 3: E(no) M(sky) U(earth) c(sky+earth) k(water) s(sky+water) 0(earth+water) 8(all)")
    print()
    
    # Check what our converter is using
    print("🔍 KIỂM TRA CONVERTER CHÚNG TA:")
    print("Chuỗi output: 11AA1Ag1Ag")
    print("Note character được dùng: '1'")
    print()
    
    if '1' not in emphyrrus_mapping:
        print("❌ PHÁT HIỆN VẤN ĐỀ!")
        print("Note character '1' KHÔNG CÓ trong bảng mapping Emphyrrus!")
        print("Đây có thể là nguyên nhân Warframe reject chuỗi.")
        print()
        
        print("✅ GIẢI PHÁP:")
        print("Cần fix note mapping để dùng characters từ bảng Emphyrrus:")
        print("Thay vì '1' → dùng 'B' (string 1, no fret)")
        print("Thay vì '1' → dùng 'C' (string 2, no fret)")
        print("Thay vì '1' → dùng 'E' (string 3, no fret)")
    else:
        print("✅ Note character '1' có trong mapping")
    
    print()
    print("🔧 KIỂM TRA TIMING:")
    print("Timing codes: 'AA', 'Ag'")
    
    # Test timing decode
    try:
        from midi2shawzin.encoder import shawzin_time_to_seconds
        
        aa_time = shawzin_time_to_seconds('AA')
        ag_time = shawzin_time_to_seconds('Ag')
        
        print(f"'AA' → {aa_time}s")
        print(f"'Ag' → {ag_time}s")
        
        if aa_time == 0.0:
            print("✅ 'AA' = 0s (đúng cho note đầu)")
        else:
            print("❌ 'AA' không phải 0s")
            
    except Exception as e:
        print(f"❌ Lỗi decode timing: {e}")
    
    print()
    print("🎯 HÀNH ĐỘNG TIẾP THEO:")
    print("1. Kiểm tra module mapper.py - xem note mapping table")
    print("2. Fix để dùng đúng characters: B, C, E, etc.")
    print("3. Test lại với chuỗi corrected")

def check_our_mapping():
    """Check what note mapping our converter is actually using."""
    
    print("\n=== KIỂM TRA MAPPING CHÚNG TA ===")
    try:
        from midi2shawzin.mapper import build_playable_table
        
        # Check Scale 1 mapping
        table_scale1 = build_playable_table(1)
        print("Scale 1 mapping:")
        for midi_note, char in table_scale1[:10]:  # First 10
            print(f"  MIDI {midi_note} → '{char}'")
        
        print()
        
        # Check Scale 3 mapping  
        table_scale3 = build_playable_table(3)
        print("Scale 3 mapping:")
        for midi_note, char in table_scale3[:10]:  # First 10
            print(f"  MIDI {midi_note} → '{char}'")
            
    except Exception as e:
        print(f"❌ Lỗi check mapping: {e}")

if __name__ == '__main__':
    check_note_mapping()
    check_our_mapping()
