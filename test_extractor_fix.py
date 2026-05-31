"""
test_extractor_fix.py - Verify the extractor produces exactly 332 features per frame
"""

import cv2
import numpy as np
from translator_model_loader import extract_keypoints

# Load a test image (you can modify this to use any image)
try:
    # Try to load a test image from webcam or use a dummy image
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("⚠️  Cannot access webcam. Creating dummy frame...")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
except Exception as e:
    print(f"⚠️  Error accessing webcam: {e}. Creating dummy frame...")
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

print("\n" + "="*60)
print("TESTING EXTRACTOR FIX")
print("="*60)

# Extract features
try:
    features = extract_keypoints(frame)
    
    if features is not None:
        print(f"\n✅ features.shape = {features.shape}")
        print(f"   Expected: (332,)")
        
        if features.shape[0] == 332:
            print(f"   ✅ PASS: Feature vector size is exactly 332!")
        else:
            print(f"   ❌ FAIL: Expected 332, got {features.shape[0]}")
    else:
        print("\n⚠️  extract_keypoints returned None (no detection)")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("EXPECTED BREAKDOWN:")
print("="*60)
print("pose (33 landmarks * 2 coords)           = 66")
print("face (8 important points * 2 coords)     = 16")
print("left_hand (21 landmarks * 2 coords)      = 42")
print("right_hand (21 landmarks * 2 coords)     = 42")
print("-" * 60)
print("Total landmarks (x,y)                    = 166")
print("After reshape to (-1, 2)                 = (83, 2)")
print("After combined with relative (x,y,rx,ry)= (83, 4)")
print("After flatten                            = 332")
print("="*60)

# Test sequence building
print("\n" + "="*60)
print("TESTING SEQUENCE BUILDING (30 frames)")
print("="*60)

sequence = []
for i in range(30):
    # Use the same frame or generate dummy ones
    features = extract_keypoints(frame)
    if features is not None:
        sequence.append(features)
    else:
        print(f"Frame {i}: No detection, skipping...")

if len(sequence) == 30:
    seq_array = np.array(sequence, dtype=np.float32)
    print(f"\n✅ sequence before reshape = {seq_array.shape}")
    print(f"   Expected: (30, 332)")
    
    if seq_array.shape == (30, 332):
        print(f"   ✅ PASS: Sequence shape is correct!")
        
        # Reshape for model
        reshaped = seq_array.reshape(1, 30, 332, 1)
        print(f"\n✅ sequence after reshape = {reshaped.shape}")
        print(f"   Expected: (1, 30, 332, 1)")
        
        if reshaped.shape == (1, 30, 332, 1):
            print(f"   ✅ PASS: Model input shape is correct!")
        else:
            print(f"   ❌ FAIL: Expected (1, 30, 332, 1), got {reshaped.shape}")
    else:
        print(f"   ❌ FAIL: Expected (30, 332), got {seq_array.shape}")
else:
    print(f"❌ Could only collect {len(sequence)} frames (expected 30)")

print("\n" + "="*60)
print("ALL TESTS COMPLETE")
print("="*60 + "\n")
