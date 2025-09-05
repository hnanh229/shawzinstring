#!/usr/bin/env python3
"""Analyze differences between our approach and Emphyrrus converter."""

def analyze_emphyrrus_differences():
    """Compare our approach with Emphyrrus to find issues."""
    
    print("=== PHÂN TÍCH VẤN ĐỀ ===")
    print()
    
    print("🔍 Vấn đề 1: Chuỗi không hoạt động")
    print("- Format đã đúng single-line")
    print("- Có thể vấn đề khác:")
    print("  → Note mapping không đúng")
    print("  → Timing encoding sai")
    print("  → Scale selection không phù hợp")
    print()
    
    print("🔍 Vấn đề 2: Tạp âm được convert")
    print("- Converter hiện tại map TẤT CẢ notes")
    print("- Không filter percussion/drums")
    print("- Không phân biệt melody vs accompaniment")
    print()
    
    print("=== SO SÁNH VỚI EMPHYRRUS ===")
    print()
    
    print("📋 Emphyrrus features chúng ta chưa có:")
    print("1. MELODY EXTRACTION:")
    print("   - Chỉ convert track chính (melody)")
    print("   - Bỏ qua percussion và bass")
    print("   - Filter theo channel và instrument")
    print()
    
    print("2. NOTE FILTERING:")
    print("   - Bỏ qua notes ngoài scale")
    print("   - Chỉ giữ notes trong range của Shawzin")
    print("   - Filter velocity thấp (ghost notes)")
    print()
    
    print("3. TIMING PRECISION:")
    print("   - Quantize đúng với Warframe timing")
    print("   - Handle playback speed")
    print("   - Correct time limits (256s)")
    print()
    
    print("4. TRACK SELECTION:")
    print("   - Cho phép chọn track manually")
    print("   - Auto-detect melody track")
    print("   - Skip drum tracks (channel 9)")
    print()
    
    print("=== CẢI THIỆN CẦN THIẾT ===")
    print()
    
    print("🎯 Ưu tiên cao:")
    print("1. Fix note mapping - check với bảng note Emphyrrus")
    print("2. Add melody extraction - chỉ convert track chính")
    print("3. Filter percussion (channel 9)")
    print("4. Improve scale detection")
    print()
    
    print("🎯 Ưu tiên trung bình:")
    print("5. Add track selection UI")
    print("6. Better timing quantization")
    print("7. Note range filtering")
    print()
    
    print("=== TEST SUGGESTIONS ===")
    print()
    
    print("🧪 Immediate tests:")
    print("1. Tạo MIDI file đơn giản (chỉ 1 track, vài notes)")
    print("2. Test với same MIDI file qua Emphyrrus")
    print("3. So sánh output format chi tiết")
    print("4. Check note mapping table")
    print()
    
    # Create a simple test MIDI
    print("💡 Tạo MIDI test đơn giản:")
    create_simple_midi_test()

def create_simple_midi_test():
    """Create a very simple MIDI for testing."""
    try:
        import mido
        
        # Create simple C major scale
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Add simple notes: C D E F G (5 notes only)
        notes = [60, 62, 64, 65, 67]  # C4 to G4
        
        for i, note in enumerate(notes):
            # Note on
            track.append(mido.Message('note_on', 
                                    channel=0, 
                                    note=note, 
                                    velocity=64, 
                                    time=0 if i == 0 else 480))
            # Note off
            track.append(mido.Message('note_off', 
                                    channel=0, 
                                    note=note, 
                                    velocity=64, 
                                    time=480))
        
        # Save test file
        test_file = "simple_test.mid"
        mid.save(test_file)
        print(f"✅ Tạo file test: {test_file}")
        print("   - 5 notes: C D E F G")
        print("   - 1 track, channel 0")
        print("   - No percussion")
        print()
        print("👉 Hãy test file này với:")
        print("   1. Converter của chúng ta")
        print("   2. Emphyrrus converter")
        print("   3. So sánh outputs")
        
    except ImportError:
        print("❌ Cần mido để tạo test MIDI")
        print("Run: pip install mido")

if __name__ == '__main__':
    analyze_emphyrrus_differences()
