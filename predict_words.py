import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'

import cv2
import json
import time
import pickle
import numpy as np
import random
import glob

from tensorflow.keras.models import load_model

# =====================================
# PATHS
# =====================================

MODEL_PATH = r"cnn_lstm_output\cnn_lstm_model.h5"

LABELS_PATH = r"cnn_lstm_output\labels.pkl"

DATA_DIR = r"data\npy"

PREDICTION_FILE = "prediction.json"

# =====================================
# LOAD MODEL
# =====================================

print("Loading model...", flush=True)

model = load_model(MODEL_PATH)

with open(LABELS_PATH, "rb") as f:
    le = pickle.load(f)

labels = le.classes_

print("Model loaded", flush=True)

# =====================================
# LOAD DATA FILES
# =====================================

def get_data_files():
    """Get all .npy files from data directory"""
    pattern = os.path.join(DATA_DIR, "**", "*.npy")
    return glob.glob(pattern, recursive=True)

def load_random_sequence():
    """Load a random sequence from the data files"""
    files = get_data_files()
    if not files:
        print("No data files found", flush=True)
        return None, None

    file_path = random.choice(files)
    sequence = np.load(file_path)

    # Extract word from filename (folder name)
    word = os.path.basename(os.path.dirname(file_path))

    return sequence, word

# =====================================
# PREDICTION FUNCTION
# =====================================

def predict_sequence(sequence):
    """Predict word from sequence"""
    try:
        FEATURES = sequence.shape[1]

        seq = sequence.reshape(1, 30, FEATURES, 1)

        prediction = model.predict(seq, verbose=0)[0]

        pred_index = np.argmax(prediction)
        confidence = float(prediction[pred_index])
        word = labels[pred_index]

        return word, confidence

    except Exception as e:
        print(f"PREDICTION ERROR: {e}", flush=True)
        return None, 0.0

# =====================================
# SAVE PREDICTION
# =====================================

def save_prediction(word, confidence, expected_word):

    try:
        data = {
            "predicted_word": word,
            "confidence": float(confidence),
            "expected_word": expected_word,
            "timestamp": time.time()
        }

        with open(PREDICTION_FILE, "w") as f:
            json.dump(data, f)

    except Exception as e:
        print(f"SAVE ERROR: {e}", flush=True)

# =====================================
# MAIN LOOP
# =====================================

print("Starting word prediction from data files...", flush=True)

predictions = []
total_predictions = 10  # Test with 10 random samples

for i in range(total_predictions):
    print(f"\nPrediction {i+1}/{total_predictions}", flush=True)

    # Load random sequence
    sequence, expected_word = load_random_sequence()

    if sequence is None:
        continue

    print(f"Expected word: {expected_word}", flush=True)

    # Predict
    predicted_word, confidence = predict_sequence(sequence)

    if predicted_word:
        print(f"Predicted: {predicted_word} ({confidence:.2f})", flush=True)

        predictions.append({
            "expected": expected_word,
            "predicted": predicted_word,
            "confidence": confidence,
            "correct": expected_word.lower() == predicted_word.lower()
        })

        # Save last prediction
        save_prediction(predicted_word, confidence, expected_word)

    time.sleep(0.5)  # Small delay between predictions

# =====================================
# SUMMARY
# =====================================

if predictions:
    correct = sum(1 for p in predictions if p["correct"])
    accuracy = correct / len(predictions)

    print("\n=== PREDICTION SUMMARY ===", flush=True)
    print(f"Total predictions: {len(predictions)}", flush=True)
    print(f"Correct predictions: {correct}", flush=True)
    print(f"Accuracy: {accuracy:.2%}", flush=True)

    print("\nDetailed results:", flush=True)
    for p in predictions:
        status = "✓" if p["correct"] else "✗"
        print(f"{status} Expected: {p['expected']} | Predicted: {p['predicted']} ({p['confidence']:.2f})", flush=True)

else:
    print("No predictions made", flush=True)

print("Word prediction completed", flush=True)