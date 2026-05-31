from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import tensorflow as tf
import mediapipe as mp

router = APIRouter()

# Global state for spell mode
class SpellSession:
    def __init__(self):
        self.is_active = False
        self.model = None
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

# Load the model lazily
def get_spell_model():
    if spell_session.model is None:
        try:
            import tensorflow as tf
            spell_session.model = tf.keras.models.load_model('asl_cnn_model.keras')
        except AttributeError:
            try:
                import keras
                spell_session.model = keras.models.load_model('asl_cnn_model.keras')
            except:
                print("✗ Error loading model: Could not load TensorFlow or Keras models")
        
        if spell_session.mp_holistic is None:
            spell_session.mp_holistic = mp.solutions.holistic.Holistic(
                static_image_mode=False,
                model_complexity=1
            )
        
        if spell_session.model is not None:
            print("✓ Spell API: Model loaded successfully")
    return spell_session.model is not None

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

@router.post('/spell/start')
async def spell_start():
    """Start a new spell session"""
    spell_session.is_active = True
    spell_session.reset()
    return JSONResponse(content={
        'status': 'started',
        'message': 'Spell session started',
        'spelled_letters': spell_session.spelled_letters
    })

@router.post('/spell/stop')
async def spell_stop():
    """Stop the current spell session"""
    spell_session.is_active = False
    spelled_text = ''.join(spell_session.spelled_letters)
    return JSONResponse(content={
        'status': 'stopped',
        'spelled_text': spelled_text,
        'letter_count': len(spell_session.spelled_letters)
    })

@router.post('/spell/process')
async def spell_process(frame: UploadFile = File(...)):
    """Process a single frame for letter detection"""
    if not spell_session.is_active:
        raise HTTPException(status_code=400, detail="Session not active")
    
    if not get_spell_model():
        raise HTTPException(status_code=500, detail="Model not available")

    try:
        if not frame:
            raise HTTPException(status_code=400, detail="No frame provided")

        # Read image
        file_bytes = np.frombuffer(await frame.read(), np.uint8)
        frame_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if frame_img is None:
            raise HTTPException(status_code=400, detail="Invalid frame")

        # Detect letter
        letter, confidence = detect_letter(frame_img)

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

        return JSONResponse(content={
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/spell/status')
async def spell_status():
    """Get current session status"""
    spelled_text = ''.join(spell_session.spelled_letters)
    return JSONResponse(content={
        'is_active': spell_session.is_active,
        'spelled_letters': spell_session.spelled_letters,
        'spelled_text': spelled_text,
        'frame_count': spell_session.frame_count,
        'last_confidence': round(spell_session.last_confidence, 4)
    })

@router.post('/spell/clear')
async def spell_clear():
    """Clear the spelled text"""
    spell_session.reset()
    return JSONResponse(content={
        'status': 'cleared',
        'spelled_letters': spell_session.spelled_letters
    })

@router.post('/spell/undo')
async def spell_undo():
    """Remove the last letter"""
    if spell_session.spelled_letters:
        spell_session.spelled_letters.pop()
    spelled_text = ''.join(spell_session.spelled_letters)
    return JSONResponse(content={
        'status': 'undone',
        'spelled_letters': spell_session.spelled_letters,
        'spelled_text': spelled_text
    })