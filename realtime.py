import cv2
import numpy as np
import mediapipe as mp
import time
import pickle
from collections import deque
from tensorflow.keras.models import load_model


# ==============================
# PATHS 🔥 (عدليهم إذا لزم)
# ==============================
MODEL_PATH = r"C:\Users\Lenovo\Desktop\personalDataset\cnn_lstm_output\cnn_lstm_model.keras"
LABELS_PATH = r"C:\Users\Lenovo\Desktop\personalDataset\cnn_lstm_output\labels.pkl"

# ==============================
# LOAD MODEL
# ==============================
model = load_model(MODEL_PATH)

with open(LABELS_PATH, "rb") as f:
    le = pickle.load(f)

labels = le.classes_

# ==============================
# MEDIAPIPE (Holistic 🔥)
# ==============================
mp_holistic = mp.solutions.holistic

holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=2,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ==============================
# CONSTANTS (نفس التدريب)
# ==============================
SEQUENCE_LENGTH = 30

IMPORTANT_FACE_POINTS = [
    13, 14,      # mouth
    78, 308,     # mouth corners
    234, 454,    # ears
    33, 263      # eyes
]

sequence = []
sentence = []
pred_buffer = deque(maxlen=5)

last_time = time.time()

# ==============================
# HELPERS
# ==============================
def landmarks_to_array(landmarks, num_points):
    if landmarks:
        return np.array([[lm.x, lm.y] for lm in landmarks.landmark]).flatten()
    else:
        return np.zeros(num_points)

def extract_face(face_landmarks):
    if face_landmarks:
        points = []
        for idx in IMPORTANT_FACE_POINTS:
            lm = face_landmarks.landmark[idx]
            points.extend([lm.x, lm.y])
        return np.array(points)
    else:
        return np.zeros(len(IMPORTANT_FACE_POINTS) * 2)

# ==============================
# EXTRACT KEYPOINTS 🔥 (مطابق للتدريب)
# ==============================
def extract_keypoints(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = holistic.process(image)

    pose = landmarks_to_array(results.pose_landmarks, 33 * 2)
    left_hand = landmarks_to_array(results.left_hand_landmarks, 21 * 2)
    right_hand = landmarks_to_array(results.right_hand_landmarks, 21 * 2)
    face = extract_face(results.face_landmarks)

    keypoints = np.concatenate([pose, face, left_hand, right_hand])
    keypoints = keypoints.reshape(-1, 2)

    # 🔥 center = shoulders
    if len(pose) >= 33 * 2:
        lx = pose[11 * 2]
        ly = pose[11 * 2 + 1]

        rx = pose[12 * 2]
        ry = pose[12 * 2 + 1]

        center_x = (lx + rx) / 2
        center_y = (ly + ry) / 2
    else:
        center_x, center_y = 0, 0

    relative = keypoints - np.array([center_x, center_y])

    combined = np.concatenate([keypoints, relative], axis=1)

    return combined.flatten().astype(np.float32)

# ==============================
# PREDICT WRAPPER (for translator)
# ==============================
def predict_realtime_sequence(sequence):
    """Predict a single sequence (for translator API use)"""
    if not sequence or len(sequence) < SEQUENCE_LENGTH:
        return "", 0.0, None
    
    seq = np.array(sequence)
    FEATURES = seq.shape[1]
    seq = seq.reshape(1, SEQUENCE_LENGTH, FEATURES, 1)
    
    res = model.predict(seq, verbose=0)[0]
    pred_index = np.argmax(res)
    confidence = float(res[pred_index])
    word = labels[pred_index]
    
    return word, confidence, res

# ==============================
# CAMERA (ONLY RUN IF EXECUTED DIRECTLY)
# ==============================
def run_realtime():
    """Main realtime loop - ONLY run when executed directly"""
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        keypoints = extract_keypoints(frame)
        sequence.append(keypoints)

        # نخلي بس آخر 30
        sequence = sequence[-SEQUENCE_LENGTH:]

        # ==============================
        # 🔥 prediction
        # ==============================
        if len(sequence) == SEQUENCE_LENGTH and (time.time() - last_time) > 1.5:

            seq = np.array(sequence)

            FEATURES = seq.shape[1]

            seq = seq.reshape(1, SEQUENCE_LENGTH, FEATURES, 1)

            res = model.predict(seq, verbose=0)[0]

            pred_index = np.argmax(res)
            confidence = res[pred_index]
            word = labels[pred_index]

            print(f"{word} ({confidence:.2f})")

            pred_buffer.append(word)

            # فلترة ذكية 🔥
            if confidence > 0.80:
                # majority vote from last 5 predictions
                if len(pred_buffer) == 5:
                    stable_word = max(set(pred_buffer), key=list(pred_buffer).count)

                    if pred_buffer.count(stable_word) >= 3:
                        if len(sentence) == 0 or stable_word != sentence[-1]:
                            sentence.append(stable_word)

            last_time = time.time()

        # ==============================
        # DISPLAY
        # ==============================
        cv2.rectangle(frame, (0, 0), (640, 60), (0, 0, 0), -1)

        cv2.putText(
            frame,
            " ".join(sentence[-5:]),
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        cv2.imshow("Sign Language AI 🔥", frame)

        key = cv2.waitKey(10) & 0xFF

        if key == ord('q'):
            break

        if key == ord('r'):
            sentence = []

    cap.release()
    cv2.destroyAllWindows()


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    run_realtime()