import os
import cv2
import numpy as np
import mediapipe as mp
import csv

# ==============================
# MediaPipe
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
# PATHS
# ==============================
DATASET_PATH = r"C:\Users\Lenovo\Desktop\personalDataset\dataset"

OUTPUT_PATH_NPY = r"C:\Users\Lenovo\Desktop\personalDataset\data\npy"
OUTPUT_PATH_CSV = r"C:\Users\Lenovo\Desktop\personalDataset\data\csv"

SEQUENCE_LENGTH = 30

os.makedirs(OUTPUT_PATH_NPY, exist_ok=True)
os.makedirs(OUTPUT_PATH_CSV, exist_ok=True)

# ==============================
# IMPORTANT FACE POINTS 🔥
# ==============================
IMPORTANT_FACE_POINTS = [
    13, 14,      # mouth center
    78, 308,     # mouth corners
    234, 454,    # ears
    33, 263      # eyes
]

# ==============================
# HELPERS
# ==============================
def landmarks_to_array(landmarks, num_points):
    if landmarks:
        return np.array([[lm.x, lm.y] for lm in landmarks.landmark]).flatten()
    else:
        return np.zeros(num_points)

def extract_face_keypoints(face_landmarks):
    if face_landmarks:
        points = []
        for idx in IMPORTANT_FACE_POINTS:
            lm = face_landmarks.landmark[idx]
            points.extend([lm.x, lm.y])
        return np.array(points)
    else:
        return np.zeros(len(IMPORTANT_FACE_POINTS) * 2)

# ==============================
# EXTRACT KEYPOINTS 🔥
# ==============================
def extract_keypoints(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = holistic.process(image)

    pose = landmarks_to_array(results.pose_landmarks, 33 * 2)
    left_hand = landmarks_to_array(results.left_hand_landmarks, 21 * 2)
    right_hand = landmarks_to_array(results.right_hand_landmarks, 21 * 2)
    face = extract_face_keypoints(results.face_landmarks)

    keypoints = np.concatenate([pose, face, left_hand, right_hand])
    keypoints = keypoints.reshape(-1, 2)

    # ==============================
    # 🔥 CENTER = SHOULDERS
    # ==============================
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
# PROCESS DATASET
# ==============================
for label in os.listdir(DATASET_PATH):
    label_path = os.path.join(DATASET_PATH, label)

    if not os.path.isdir(label_path):
        continue

    save_npy_label = os.path.join(OUTPUT_PATH_NPY, label)
    save_csv_label = os.path.join(OUTPUT_PATH_CSV, label)

    os.makedirs(save_npy_label, exist_ok=True)
    os.makedirs(save_csv_label, exist_ok=True)

    for video in os.listdir(label_path):
        if not video.endswith(".mp4"):
            continue

        video_name = video.replace(".mp4", "")

        npy_path = os.path.join(save_npy_label, video_name + ".npy")
        csv_path = os.path.join(save_csv_label, video_name + ".csv")

        # ==============================
        # 🚫 SKIP IF ALREADY EXISTS
        # ==============================
        if os.path.exists(npy_path) and os.path.exists(csv_path):
            print(f"⏩ Skipping (already processed): {label} - {video}")
            continue

        video_path = os.path.join(label_path, video)
        cap = cv2.VideoCapture(video_path)

        sequence = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            keypoints = extract_keypoints(frame)
            sequence.append(keypoints)

        cap.release()

        # ==============================
        # FIX SEQUENCE LENGTH
        # ==============================
        if len(sequence) >= SEQUENCE_LENGTH:
            sequence = sequence[:SEQUENCE_LENGTH]
        else:
            while len(sequence) < SEQUENCE_LENGTH:
                sequence.append(np.zeros_like(sequence[0]))

        sequence = np.stack(sequence)

        # ==============================
        # SAVE NPY
        # ==============================
        np.save(npy_path, sequence)

        # ==============================
        # SAVE CSV
        # ==============================
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(sequence)

        print(f"✅ Saved: {label} - {video}")

print("🎉 DONE - SMART KEYPOINTS (POSE + HANDS + IMPORTANT FACE + RELATIVE)")