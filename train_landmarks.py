import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import pickle

# =========================
# تحميل الموديل + LabelEncoder
# =========================
model = tf.keras.models.load_model("asl_landmarks_model.h5")
with open("label_encoder.pkl", "rb") as f:
    le = pickle.load(f)

class_names = le.classes_

# =========================
# MediaPipe Hands Setup
# =========================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# =========================
# Finger state function
# =========================
def is_finger_extended(tip, pip):
    return 1 if tip < pip else 0

def thumb_distances(lm_array):
    def dist(a, b):
        return np.linalg.norm(lm_array[a] - lm_array[b])
    return [
        dist(4, 8),
        dist(4, 12),
        dist(4, 16),
        dist(4, 20)
    ]

# =========================
# تشغيل الكاميرا
# =========================
cap = cv2.VideoCapture(0)



while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    label = ""

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            lm_list = []
            for lm in hand_landmarks.landmark:
                lm_list.append([lm.x, lm.y, lm.z])

            lm_array = np.array(lm_list)

            # =========================
            # relative to wrist
            # =========================
            base = lm_array[0]
            lm_array = lm_array - base

            # =========================
            # normalize
            # =========================
            norm = np.linalg.norm(lm_array)
            if norm != 0:
                lm_array = lm_array / norm

            row = lm_array.flatten().tolist()

            # =========================
            # finger states
            # =========================
            index_ext = is_finger_extended(lm_array[8][1], lm_array[6][1])
            middle_ext = is_finger_extended(lm_array[12][1], lm_array[10][1])
            ring_ext = is_finger_extended(lm_array[16][1], lm_array[14][1])
            pinky_ext = is_finger_extended(lm_array[20][1], lm_array[18][1])
            row.extend([index_ext, middle_ext, ring_ext, pinky_ext])

            # =========================
            # thumb distances
            # =========================
            row.extend(thumb_distances(lm_array))

            # =========================
            # prediction
            # =========================
            X = np.array(row).reshape(1, -1)  # الشكل = 71 features
            prediction = model.predict(X, verbose=0)
            class_id = np.argmax(prediction)
            label = class_names[class_id]

            # رسم النقاط
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # عرض الحرف على الشاشة
    cv2.putText(frame, label, (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                2, (0, 255, 0), 3)

    cv2.imshow("ASL Live Translator", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()