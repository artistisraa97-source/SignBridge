import os
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np

DATASET_PATH = "asl_alphabet_train"
OUTPUT_FILE = "asl_landmarks.csv"

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5
)

data = []

def is_finger_extended(tip, pip):
    return 1 if tip < pip else 0

for label in os.listdir(DATASET_PATH):
    label_path = os.path.join(DATASET_PATH, label)

    if not os.path.isdir(label_path):
        continue

    print(f"Processing class: {label}")

    for img_name in os.listdir(label_path):
        img_path = os.path.join(label_path, img_name)

        image = cv2.imread(img_path)
        if image is None:
            continue

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]

            lm_list = []
            for lm in hand_landmarks.landmark:
                lm_list.append([lm.x, lm.y, lm.z])

            lm_array = np.array(lm_list)

            # =========================
            # 1. Relative to wrist
            # =========================
            base = lm_array[0]  # wrist
            lm_array = lm_array - base

            # =========================
            # 2. Normalize scale
            # =========================
            norm = np.linalg.norm(lm_array)
            if norm != 0:
                lm_array = lm_array / norm

            row = lm_array.flatten().tolist()

            # =========================
            # 3. Finger states
            # =========================
            index_ext = is_finger_extended(lm_array[8][1], lm_array[6][1])
            middle_ext = is_finger_extended(lm_array[12][1], lm_array[10][1])
            ring_ext = is_finger_extended(lm_array[16][1], lm_array[14][1])
            pinky_ext = is_finger_extended(lm_array[20][1], lm_array[18][1])

            row.extend([index_ext, middle_ext, ring_ext, pinky_ext])

            # =========================
            # 4. Thumb distance features
            # =========================
            def dist(a, b):
                return np.linalg.norm(lm_array[a] - lm_array[b])

            thumb_index = dist(4, 8)
            thumb_middle = dist(4, 12)
            thumb_ring = dist(4, 16)
            thumb_pinky = dist(4, 20)

            row.extend([thumb_index, thumb_middle, thumb_ring, thumb_pinky])

            # =========================
            # 5. Label
            # =========================
            row.append(label)
            data.append(row)

# =========================
# Columns
# =========================
columns = []

for i in range(21):
    columns += [f"x{i}", f"y{i}", f"z{i}"]

columns += [
    "index_ext", "middle_ext", "ring_ext", "pinky_ext",
    "thumb_index_dist", "thumb_middle_dist",
    "thumb_ring_dist", "thumb_pinky_dist"
]

columns.append("label")

df = pd.DataFrame(data, columns=columns)
df.to_csv(OUTPUT_FILE, index=False)

print("Dataset created successfully ✅")
print(f"Total samples: {len(df)}")