#!/usr/bin/env python3
"""Verify a Shawzin string for Warframe compatibility."""

def verify_warframe_string(shawzin_string):
    """Check if a Shawzin string meets Warframe requirements."""
    
    print("=== WARFRAME COMPATIBILITY CHECK ===")
    print(f"Input string: {shawzin_string}")
    print(f"Length: {len(shawzin_string)} characters")
    print()
    
    # Check all requirements
    checks = []
    
    # 1. No # prefix
    no_hash = not shawzin_string.startswith('#')
    checks.append(("No # prefix", no_hash, "✓" if no_hash else "✗"))
    
    # 2. Starts with digit (scale header)
    starts_digit = shawzin_string[0].isdigit() if shawzin_string else False
    checks.append(("Starts with scale digit", starts_digit, "✓" if starts_digit else "✗"))
    
    # 3. Within 256 character limit
    within_limit = len(shawzin_string) <= 256
    checks.append(("Within 256 char limit", within_limit, "✓" if within_limit else "✗"))
    
    # 4. Valid characters (alphanumeric for base64-like encoding)
    valid_chars = all(c.isalnum() or c in '\n\r' for c in shawzin_string)
    checks.append(("Valid characters only", valid_chars, "✓" if valid_chars else "✗"))
    
    # 5. Proper token structure (3-character tokens after scale header)
    lines = shawzin_string.strip().split('\n')
    if len(lines) >= 2:
        note_content = ''.join(lines[1:]).replace('\n', '').replace('\r', '')
        proper_tokens = len(note_content) % 3 == 0
        checks.append(("Proper 3-char token structure", proper_tokens, "✓" if proper_tokens else "✗"))
    else:
        checks.append(("Proper 3-char token structure", False, "✗ (No note content)"))
    
    # Print results
    print("REQUIREMENT CHECKS:")
    print("-" * 40)
    all_passed = True
    for desc, passed, symbol in checks:
        print(f"{symbol} {desc}: {'PASS' if passed else 'FAIL'}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 40)
    if all_passed:
        print("🎉 STRING IS WARFRAME COMPATIBLE!")
        print("✅ This string should work in Warframe Shawzin.")
    else:
        print("⚠️  STRING MAY HAVE ISSUES")
        print("❌ Check the failed requirements above.")
    
    print("=" * 40)
    
    # Test parsing with our decoder
    try:
        from midi2shawzin.encoder import read_shawzin_file
        import tempfile
        import os
        
        # Write to temp file and try to parse
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(shawzin_string)
            temp_path = f.name
        
        try:
            scale_id, notes = read_shawzin_file(temp_path)
            print(f"\n📖 PARSING TEST:")
            print(f"✓ Successfully parsed!")
            print(f"  Scale ID: {scale_id}")
            print(f"  Notes found: {len(notes)}")
            if notes:
                print(f"  First few notes: {notes[:5]}")
        except Exception as e:
            print(f"\n📖 PARSING TEST:")
            print(f"✗ Parse error: {e}")
        finally:
            os.unlink(temp_path)
            
    except ImportError:
        print(f"\n📖 PARSING TEST: Skipped (encoder not available)")
    
    return all_passed

if __name__ == '__main__':
    # Test the user's string
    test_string = "1\naAPaACaAaaAPaAPaAjaAyaAPxAOaABaAcaACaA3xAAxA5xA5aACaAdaAEaACaAJaAHxAEaAAxABaADaAZaADaADaACxAVxAcaADaAEaACaAUxAAaACaAaxAAaAHaAVxABxACaAbxABaAPaANxAAaACaAEaAKaALxADaAGaACaABxAEaAOxACaAEaABaACxAFxABaAB"
    
    verify_warframe_string(test_string)
