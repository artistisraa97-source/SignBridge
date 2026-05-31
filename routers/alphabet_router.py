from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import pickle
import os
import mediapipe as mp
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

MODEL_PATH = 'asl_landmarks_model.h5'
LABEL_ENCODER_PATH = 'label_encoder.pkl'

# Lazy load model
_model = None
_label_encoder = None

def get_model():
    global _model, _label_encoder
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f'Model not found: {MODEL_PATH}')
        if not os.path.exists(LABEL_ENCODER_PATH):
            raise FileNotFoundError(f'Label encoder not found: {LABEL_ENCODER_PATH}')
        
        try:
            import tensorflow as tf
            _model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        except AttributeError:
            # Fallback if tf.keras is not available
            try:
                import keras
                _model = keras.models.load_model(MODEL_PATH, compile=False)
            except:
                raise RuntimeError("Could not load TensorFlow or Keras models")
        
        with open(LABEL_ENCODER_PATH, 'rb') as f:
            _label_encoder = pickle.load(f)
    
    return _model, _label_encoder

_mp_hands = None
_hands = None

def get_hands():
    """Lazy load MediaPipe Hands on first use"""
    global _mp_hands, _hands
    if _hands is None:
        try:
            print("[alphabet_router] Initializing MediaPipe Hands...")
            _mp_hands = mp.solutions.hands
            _hands = _mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.6
            )
            print("[alphabet_router] MediaPipe Hands initialized successfully")
        except Exception as e:
            print(f"[alphabet_router] ERROR initializing MediaPipe Hands: {e}")
            import traceback
            traceback.print_exc()
            raise
    return _hands

def is_finger_extended(tip: int, pip: int) -> int:
    """Check if finger is extended based on tip and pip positions."""
    return 1 if tip < pip else 0

def build_feature_vector(hand_landmarks) -> np.ndarray:
    """Extract feature vector from hand landmarks."""
    lm_list = []
    for lm in hand_landmarks.landmark:
        lm_list.append([lm.x, lm.y, lm.z])

    lm_array = np.array(lm_list, dtype=np.float32)
    if lm_array.shape[0] != 21:
        padded = np.zeros((21, 3), dtype=np.float32)
        padded[: lm_array.shape[0]] = lm_array[:21]
        lm_array = padded

    base = lm_array[0]
    lm_array = lm_array - base

    norm = np.linalg.norm(lm_array)
    if norm != 0:
        lm_array = lm_array / norm

    row = lm_array.flatten().tolist()
    row.extend([
        is_finger_extended(lm_array[8][1], lm_array[6][1]),
        is_finger_extended(lm_array[12][1], lm_array[10][1]),
        is_finger_extended(lm_array[16][1], lm_array[14][1]),
        is_finger_extended(lm_array[20][1], lm_array[18][1])
    ])

    def dist(a, b):
        return float(np.linalg.norm(lm_array[a] - lm_array[b]))

    row.extend([
        dist(4, 8),
        dist(4, 12),
        dist(4, 16),
        dist(4, 20)
    ])

    return np.array(row, dtype=np.float32).reshape(1, -1)

@router.post('/predict')
async def predict(image: UploadFile = File(...)):
    """Process uploaded image and return ASL letter prediction."""
    if not image:
        raise HTTPException(status_code=400, detail="Image file required.")

    model, label_encoder = get_model()
    
    image_data = await image.read()
    np_img = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Unable to decode image.")

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hands = get_hands()
    result = hands.process(rgb)

    if not result.multi_hand_landmarks:
        return JSONResponse(content={'success': True, 'label': '', 'confidence': 0.0})

    hand_landmarks = result.multi_hand_landmarks[0]
    features = build_feature_vector(hand_landmarks)
    print("Feature length:", len(features.flatten()))
    print("Feature shape:", features.shape)
    print("Expected model shape:", model.input_shape)
    if features.shape != (1, 71):
        raise HTTPException(status_code=500, detail=f"Invalid feature shape {features.shape}, expected (1, 71)")

    prediction = model.predict(features, verbose=0)[0]
    class_id = int(np.argmax(prediction))
    label = label_encoder.inverse_transform([class_id])[0]
    confidence = float(prediction[class_id])
    print("Features shape:", features.shape)
    print("Min:", np.min(features))
    print("Max:", np.max(features))
    print("Mean:", np.mean(features))
    print("Prediction:", prediction)
    print("Confidence:", confidence)
    return JSONResponse(content={'success': True, 'label': label, 'confidence': confidence})