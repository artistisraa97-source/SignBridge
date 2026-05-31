"""
Spell Your Name API - Letter-by-letter recognition for sign language spelling
Uses the trained alphabet model to detect individual letters
"""

import cv2
import numpy as np
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import mediapipe as mp
import json

app = Flask(__name__)

# Global state for spell mode
class SpellSession:
    def __init__(self):
        self.is_active = False
        self.model = None
        self.mp_hands = None
        self.mp_pose = None
        self.mp_holistic = None
        self.spelled_letters = []
        self.last_detected = None
        self.frame_count = 0
        self.stable_frames = 0
        self.confidence_threshold = 0.80
        self.stability_frames = 10  # frames needed to confirm letter
        self.last_confidence = 0.0
        self.alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 
                        'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 
                        'U', 'V', 'W', 'X', 'Y', 'Z', 'del', 'nothing', 'space']
    
    def reset(self):
        self.spelled_letters = []
        self.last_detected = None
        self.frame_count = 0
        self.stable_frames = 0
        self.last_confidence = 0.0

spell_session = SpellSession()

# Load the model
try:
    spell_session.model = load_model('asl_cnn_model.keras')
    spell_session.mp_holistic = mp.solutions.holistic.Holistic(
        static_image_mode=False,
        model_complexity=1
    )
    print("✓ Spell API: Model loaded successfully")
except Exception as e:
    print(f"✗ Error loading model: {e}")

def extract_keypoints(results):
    """Extract hand landmarks from MediaPipe results"""
    if results is None:
        return None
    
    try:
        # Right hand landmarks (21 points)
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(63)
        
        # Left hand landmarks (21 points)
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(63)
        
        # Pose landmarks (33 points)
        pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(132)
        
        return np.concatenate([rh, lh, pose])
    except:
        return None

def detect_letter(frame):
    """Detect letter from frame using the trained model"""
    try:
        if spell_session.model is None or spell_session.mp_holistic is None:
            return None, 0.0
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = spell_session.mp_holistic.process(rgb_frame)
        
        # Extract keypoints
        keypoints = extract_keypoints(results)
        if keypoints is None:
            return None, 0.0
        
        # Reshape for model
        keypoints = keypoints.reshape(1, -1)
        
        # Predict
        prediction = spell_session.model.predict(keypoints, verbose=0)
        confidence = np.max(prediction)
        letter_idx = np.argmax(prediction)
        letter = spell_session.alphabet[letter_idx]
        
        return letter, float(confidence)
    except Exception as e:
        print(f"Error detecting letter: {e}")
        return None, 0.0

@app.route('/spell/start', methods=['POST'])
def spell_start():
    """Start a new spell session"""
    spell_session.is_active = True
    spell_session.reset()
    return jsonify({
        'status': 'started',
        'message': 'Spell session started',
        'spelled_letters': spell_session.spelled_letters
    })

@app.route('/spell/stop', methods=['POST'])
def spell_stop():
    """Stop the current spell session"""
    spell_session.is_active = False
    spelled_text = ''.join(spell_session.spelled_letters)
    return jsonify({
        'status': 'stopped',
        'spelled_text': spelled_text,
        'letter_count': len(spell_session.spelled_letters)
    })

@app.route('/spell/process', methods=['POST'])
def spell_process():
    """Process a single frame for letter detection"""
    if not spell_session.is_active:
        return jsonify({'error': 'Session not active'}), 400
    
    try:
        # Get image from request
        file = request.files.get('frame')
        if not file:
            return jsonify({'error': 'No frame provided'}), 400
        
        # Read image
        file_bytes = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid frame'}), 400
        
        # Detect letter
        letter, confidence = detect_letter(frame)
        
        spell_session.frame_count += 1
        detected_new = False
        
        # Stabilization logic
        if letter and confidence >= spell_session.confidence_threshold and letter not in ['nothing', 'del']:
            if letter == spell_session.last_detected:
                spell_session.stable_frames += 1
                
                # Add letter once when threshold is reached
                if spell_session.stable_frames == spell_session.stability_frames:
                    spell_session.spelled_letters.append(letter)
                    detected_new = True
                    spell_session.last_confidence = confidence
            else:
                spell_session.last_detected = letter
                spell_session.stable_frames = 1
        else:
            spell_session.last_detected = None
            spell_session.stable_frames = 0
        
        spelled_text = ''.join(spell_session.spelled_letters)
        
        return jsonify({
            'frame_count': spell_session.frame_count,
            'current_letter': letter if letter and letter not in ['nothing', 'del'] else '-',
            'confidence': round(float(confidence), 4),
            'stable_frames': spell_session.stable_frames,
            'detected_new': detected_new,
            'spelled_letters': spell_session.spelled_letters,
            'spelled_text': spelled_text,
            'last_confidence': round(spell_session.last_confidence, 4)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/spell/status', methods=['GET'])
def spell_status():
    """Get current session status"""
    spelled_text = ''.join(spell_session.spelled_letters)
    return jsonify({
        'is_active': spell_session.is_active,
        'spelled_letters': spell_session.spelled_letters,
        'spelled_text': spelled_text,
        'frame_count': spell_session.frame_count,
        'last_confidence': round(spell_session.last_confidence, 4)
    })

@app.route('/spell/clear', methods=['POST'])
def spell_clear():
    """Clear the spelled text"""
    spell_session.reset()
    return jsonify({
        'status': 'cleared',
        'spelled_letters': spell_session.spelled_letters
    })

@app.route('/spell/undo', methods=['POST'])
def spell_undo():
    """Remove the last letter"""
    if spell_session.spelled_letters:
        spell_session.spelled_letters.pop()
    spelled_text = ''.join(spell_session.spelled_letters)
    return jsonify({
        'status': 'undone',
        'spelled_letters': spell_session.spelled_letters,
        'spelled_text': spelled_text
    })

if __name__ == '__main__':
    app.run(debug=True, port=5003, threaded=True)
