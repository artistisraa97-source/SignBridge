"""
test_words_api.py - Test the FastAPI words route with the fixed extractor
"""

import requests
import cv2
import numpy as np
import time
import sys

# Configuration
API_URL = "http://localhost:8000"
WORDS_ENDPOINT = f"{API_URL}/api/words/predict"
RESET_ENDPOINT = f"{API_URL}/api/words/reset_session"
STATUS_ENDPOINT = f"{API_URL}/api/words/status"
SEQUENCE_LENGTH = 30

def encode_image(frame):
    """Encode frame to JPEG bytes"""
    _, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes()

def test_words_route():
    """Test the words prediction route"""
    print("\n" + "="*70)
    print("TESTING FastAPI WORDS ROUTE (with fixed extractor)")
    print("="*70)
    
    session_id = "test_session"
    
    # First, reset the session
    print(f"\n1️⃣  Resetting session '{session_id}'...")
    try:
        response = requests.post(RESET_ENDPOINT, data={"session_id": session_id})
        if response.status_code == 200:
            print(f"   ✅ Session reset successfully")
        else:
            print(f"   ❌ Failed to reset: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Connection error: {e}")
        print(f"   💡 Make sure the FastAPI server is running on {API_URL}")
        return False
    
    # Collect frames
    print(f"\n2️⃣  Collecting {SEQUENCE_LENGTH} frames from webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("   ❌ Cannot open webcam. Using dummy frames...")
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(SEQUENCE_LENGTH)]
    else:
        frames = []
        for i in range(SEQUENCE_LENGTH):
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                print(f"   Frame {i+1}/{SEQUENCE_LENGTH}", end='\r')
            else:
                print(f"   ⚠️  Failed to read frame {i+1}")
        cap.release()
        print(f"   ✅ Collected {len(frames)} frames                  ")
    
    # Send frames to API
    print(f"\n3️⃣  Sending frames to API endpoint: {WORDS_ENDPOINT}")
    frames_sent = 0
    frames_collected = 0
    current_label = ""
    current_confidence = 0.0
    
    for idx, frame in enumerate(frames):
        if frame is None:
            continue
            
        try:
            # Encode frame
            image_bytes = encode_image(frame)
            files = {"image": ("frame.jpg", image_bytes, "image/jpeg")}
            data = {"session_id": session_id}
            
            # Send request
            response = requests.post(WORDS_ENDPOINT, files=files, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                frames_sent += 1
                frames_collected = result.get("frames_collected", 0)
                current_label = result.get("label", "")
                current_confidence = result.get("confidence", 0.0)
                
                status = f"[{idx+1}/{len(frames)}] Frames collected: {frames_collected}"
                if current_label:
                    status += f" | Prediction: {current_label} ({current_confidence:.2%})"
                print(f"   {status}", end='\r')
            else:
                print(f"   ❌ API error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"   ⚠️  Error sending frame {idx+1}: {e}")
    
    print(f"\n   ✅ Sent {frames_sent} frames to API")
    
    # Check final result
    print(f"\n4️⃣  Final Prediction Result:")
    print(f"   Frames collected: {frames_collected}")
    print(f"   Label: {current_label if current_label else '(no prediction)'}")
    print(f"   Confidence: {current_confidence:.2%}")
    
    if current_label and current_confidence > 0.1:
        print(f"\n   ✅ SUCCESS: Model returned a real prediction!")
        print(f"   Expected: Real word labels instead of 'Waiting for valid words...'")
        return True
    else:
        print(f"\n   ⚠️  No strong prediction yet (confidence too low)")
        print(f"   Try signing more clearly or with different lighting")
        return False

if __name__ == "__main__":
    success = test_words_route()
    
    print("\n" + "="*70)
    if success:
        print("✅ WORDS ROUTE TEST SUCCESSFUL")
    else:
        print("⚠️  TEST INCOMPLETE (check logs above)")
    print("="*70 + "\n")
    
    sys.exit(0 if success else 1)
