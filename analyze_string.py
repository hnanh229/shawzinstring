#!/usr/bin/env python3
"""Detailed analysis of the Shawzin string that failed in Warframe."""

def analyze_warframe_string_detailed():
    """Analyze the exact string that failed in Warframe."""
    
    # The exact string from user (without scale header)
    note_string = "aAPaACaAaaAPaAPaAjaAyaAPxAOaABaAcaACaA3xAAxA5xA5aACaAdaAEaACaAJaAHxAEaAAxABaADaAZaADaADaACxAVxAcaADaAEaACaAUxAAaACaAaxAAaAHaAVxABxACaAbxABaAPaANxAAaACaAEaAKaALxADaAGaACaABxAEaAOxACaAEaABaACxAFxABaAB"
    
    print("=== DETAILED WARFRAME STRING ANALYSIS ===")
    print(f"String: {note_string}")
    print(f"Length: {len(note_string)} characters")
    print()
    
    # Check if divisible by 3
    remainder = len(note_string) % 3
    print(f"Length ÷ 3 = {len(note_string) // 3} với dư {remainder}")
    
    if remainder == 0:
        print("✅ Độ dài chia hết cho 3 - OK")
        num_tokens = len(note_string) // 3
        print(f"Số token: {num_tokens}")
        
        # Parse into 3-character tokens
        print("\n=== PHÂN TÍCH TOKENS ===")
        for i in range(0, min(len(note_string), 30), 3):  # Show first 10 tokens
            if i + 2 < len(note_string):
                token = note_string[i:i+3]
                note_char = token[0]
                time_char1 = token[1]
                time_char2 = token[2]
                print(f"Token {i//3 + 1:2d}: '{token}' -> Note='{note_char}' Time='{time_char1}{time_char2}'")
        
        if len(note_string) > 30:
            print(f"... và {len(note_string)//3 - 10} tokens nữa")
            
    else:
        print(f"❌ Độ dài KHÔNG chia hết cho 3 - INVALID!")
        print(f"Thiếu {3 - remainder} ký tự để tròn")
        print("Warframe sẽ reject chuỗi này!")
    
    # Check valid characters
    print(f"\n=== KIỂM TRA KÝ TỰ ===")
    valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    invalid_chars = []
    
    for i, char in enumerate(note_string):
        if char not in valid_chars:
            invalid_chars.append((i, char))
    
    if invalid_chars:
        print(f"❌ Tìm thấy {len(invalid_chars)} ký tự không hợp lệ:")
        for pos, char in invalid_chars[:5]:  # Show first 5
            print(f"  Vị trí {pos}: '{char}'")
    else:
        print("✅ Tất cả ký tự đều hợp lệ (base64)")
    
    # Check with the complete string including scale header
    complete_string = f"1\n{note_string}"
    print(f"\n=== CHUỖI HOÀN CHỈNH ===")
    print(f"Với scale header: {repr(complete_string)}")
    print(f"Tổng độ dài: {len(complete_string)} ký tự")
    
    # Try to validate with our parser
    print(f"\n=== TEST VỚI PARSER CỦA CHÚNG TA ===")
    try:
        from midi2shawzin.encoder import read_shawzin_file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(complete_string)
            temp_path = f.name
        
        try:
            scale_id, notes = read_shawzin_file(temp_path)
            print(f"✅ Parser thành công!")
            print(f"   Scale ID: {scale_id}")
            print(f"   Số notes: {len(notes)}")
        except Exception as e:
            print(f"❌ Parser lỗi: {e}")
        finally:
            os.unlink(temp_path)
            
    except ImportError:
        print("❌ Không thể import parser")
    
    # Final assessment
    print(f"\n=== KẾT LUẬN ===")
    if remainder == 0 and not invalid_chars:
        print("🤔 Chuỗi đúng format theo lý thuyết...")
        print("❓ Có thể vấn đề khác:")
        print("   - Timing values ngoài phạm vi Warframe")
        print("   - Note characters không hợp lệ cho scale")
        print("   - Chuỗi quá dài cho Warframe")
        print("   - Version Warframe khác nhau")
    else:
        print("❌ Chuỗi có lỗi format!")
        if remainder != 0:
            print(f"   → Độ dài không chia hết cho 3")
        if invalid_chars:
            print(f"   → Có ký tự không hợp lệ")

if __name__ == '__main__':
    analyze_warframe_string_detailed()
