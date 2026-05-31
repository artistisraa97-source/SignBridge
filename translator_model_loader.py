import os
import pickle
import time
import cv2
import numpy as np
mp = None
tf = None
LAST_MEDIAPIPE_PROCESS_MS = 0.0

# ==============================
# Paths
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'cnn_lstm_output', 'cnn_lstm_model.keras')
MODEL_PATH_FALLBACK = os.path.join(BASE_DIR, 'cnn_lstm_output', 'cnn_lstm_model.keras')
LABELS_PATH = os.path.join(BASE_DIR, 'cnn_lstm_output', 'labels.pkl')

# ==============================
# MediaPipe Holistic (lazy load)
# ==============================
_mp_holistic = None
_holistic = None
MEDIA_PIPE_MODEL_COMPLEXITY = int(os.getenv('SIGNAI_MEDIAPIPE_COMPLEXITY', '1'))
MEDIA_PIPE_SMOOTH_LANDMARKS = False


def get_holistic():
    """Lazy load MediaPipe Holistic on first use"""
    global _mp_holistic, _holistic
    # import mediapipe only when we actually need it
    global mp
    if mp is None:
        try:
            import mediapipe as _mp
            mp = _mp
        except Exception:
            mp = None
    if _holistic is None:
        try:
            print(f"[translator_model_loader] Initializing MediaPipe Holistic... complexity={MEDIA_PIPE_MODEL_COMPLEXITY} smooth_landmarks={MEDIA_PIPE_SMOOTH_LANDMARKS}")
            _mp_holistic = mp.solutions.holistic
            _holistic = _mp_holistic.Holistic(
                static_image_mode=False,
                model_complexity=MEDIA_PIPE_MODEL_COMPLEXITY,
                smooth_landmarks=MEDIA_PIPE_SMOOTH_LANDMARKS,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            print(f"[translator_model_loader] MediaPipe Holistic initialized successfully (complexity={MEDIA_PIPE_MODEL_COMPLEXITY})")
        except Exception as e:
            print(f"[translator_model_loader] ERROR initializing MediaPipe Holistic: {e}")
            import traceback
            traceback.print_exc()
            raise
    return _holistic

# Provide a module-level function to get holistic for backward compatibility
def get_mp_holistic_model():
    return get_holistic()

# ==============================
# Sequence constants
# ==============================
SEQUENCE_LENGTH = 30
IMPORTANT_FACE_POINTS = [
    13, 14,
    78, 308,
    234, 454,
    33, 263
]


def load_model_and_labels():
    model_path = MODEL_PATH
    if not os.path.exists(model_path):
        if os.path.exists(MODEL_PATH_FALLBACK):
            model_path = MODEL_PATH_FALLBACK
        else:
            raise FileNotFoundError(f'Model not found: {MODEL_PATH} or {MODEL_PATH_FALLBACK}')

    if not os.path.exists(LABELS_PATH):
        raise FileNotFoundError(f'Labels not found: {LABELS_PATH}')

    # import tensorflow only when loading the model
    global tf
    if tf is None:
        try:
            import tensorflow as _tf
            tf = _tf
        except Exception:
            tf = None
    if tf is None:
        raise RuntimeError('TensorFlow not available')
    model = tf.keras.models.load_model(model_path, compile=False)
    with open(LABELS_PATH, 'rb') as f:
        label_encoder = pickle.load(f)

    labels = label_encoder.classes_
    return model, labels


def landmarks_to_array(landmarks, num_points):
    if landmarks:
        return np.array([[lm.x, lm.y] for lm in landmarks.landmark], dtype=np.float32).flatten()
    return np.zeros(num_points, dtype=np.float32)


def extract_face_landmarks(face_landmarks):
    if face_landmarks:
        points = []
        for idx in IMPORTANT_FACE_POINTS:
            lm = face_landmarks.landmark[idx]
            points.extend([lm.x, lm.y])
        return np.array(points, dtype=np.float32)
    return np.zeros(len(IMPORTANT_FACE_POINTS) * 2, dtype=np.float32)


def extract_keypoints(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    holistic = get_holistic()
    mediapipe_start = time.perf_counter()
    results = holistic.process(image)
    global LAST_MEDIAPIPE_PROCESS_MS
    LAST_MEDIAPIPE_PROCESS_MS = (time.perf_counter() - mediapipe_start) * 1000.0

    pose = landmarks_to_array(results.pose_landmarks, 33 * 2)
    left_hand = landmarks_to_array(results.left_hand_landmarks, 21 * 2)
    right_hand = landmarks_to_array(results.right_hand_landmarks, 21 * 2)
    face = extract_face_landmarks(results.face_landmarks)

    keypoints = np.concatenate([pose, face, left_hand, right_hand])
    keypoints = keypoints.reshape(-1, 2)

    if len(pose) >= 33 * 2:
        lx = pose[11 * 2]
        ly = pose[11 * 2 + 1]
        rx = pose[12 * 2]
        ry = pose[12 * 2 + 1]
        center_x = (lx + rx) / 2
        center_y = (ly + ry) / 2
    else:
        center_x, center_y = 0.0, 0.0

    relative = keypoints - np.array([center_x, center_y], dtype=np.float32)
    combined = np.concatenate([keypoints, relative], axis=1)
    return combined.flatten().astype(np.float32)


# ==============================
# PREDICT (for web API use)
# ==============================
# Cache model and labels to avoid reloading
_cached_model = None
_cached_labels = None


def get_model_and_labels():
    """Get cached model and labels"""
    global _cached_model, _cached_labels
    if _cached_model is None or _cached_labels is None:
        _cached_model, _cached_labels = load_model_and_labels()
    return _cached_model, _cached_labels


def predict_realtime_sequence(sequence):
    """Predict a single sequence for web API
    
    Args:
        sequence: deque or list of keypoint arrays (should have length >= SEQUENCE_LENGTH)
    
    Returns:
        (word, confidence, raw_predictions)
    """
    if not sequence or len(sequence) < SEQUENCE_LENGTH:
        return "", 0.0, None
    
    model, labels = get_model_and_labels()
    
    seq = np.array(sequence, dtype=np.float32)
    FEATURES = seq.shape[1]
    seq = seq.reshape(1, SEQUENCE_LENGTH, FEATURES, 1)
    
    res = model.predict(seq, verbose=0)[0]
    pred_index = int(np.argmax(res))
    confidence = float(res[pred_index])
    word = str(labels[pred_index])
    
    return word, confidence, res
