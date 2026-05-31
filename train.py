import os
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    LSTM, Dense, Conv1D, MaxPooling1D,
    Flatten, Dropout, TimeDistributed
)

# ==============================
# PATHS
# ==============================
DATA_PATH = r"C:\Users\Lenovo\Desktop\personalDataset\data\npy"
OUTPUT_PATH = r"C:\Users\Lenovo\Desktop\personalDataset\cnn_lstm_output"

os.makedirs(OUTPUT_PATH, exist_ok=True)

# ==============================
# CONSTANTS
# ==============================
SEQUENCE_LENGTH = 30
STEP = 5   # 🔥 sliding window قوي
FEATURES = None  # رح نحددها لاحقاً

# ==============================
# LOAD DATA (Sliding Window)
# ==============================
X, y = [], []

labels = sorted(os.listdir(DATA_PATH))

print("Loading data...")

for label in labels:
    folder = os.path.join(DATA_PATH, label)

    if not os.path.isdir(folder):
        continue

    print(f"Loading {label}")

    for file in os.listdir(folder):
        if not file.endswith(".npy"):
            continue

        data = np.load(os.path.join(folder, file)).astype(np.float32)

        # 🔥 Sliding window
        for i in range(0, len(data) - SEQUENCE_LENGTH + 1, STEP):
            seq = data[i:i+SEQUENCE_LENGTH]
            X.append(seq)
            y.append(label)

print("Total sequences:", len(X))

# ==============================
# AUGMENTATION 🔥🔥🔥
# ==============================
def augment(seq):
    noise = np.random.normal(0, 0.01, seq.shape)
    scale = seq * np.random.uniform(0.9, 1.1)
    shift = np.roll(seq, np.random.randint(1,3), axis=0)

    return [
        seq,
        seq + noise,
        scale,
        shift
    ]

X_aug, y_aug = [], []

for seq, label in zip(X, y):
    for aug_seq in augment(seq):
        X_aug.append(aug_seq)
        y_aug.append(label)

X = np.array(X_aug, dtype=np.float32)
y = np.array(y_aug)

print("After augmentation:", X.shape)

# ==============================
# LABEL ENCODING
# ==============================
le = LabelEncoder()
y_encoded = le.fit_transform(y)

with open(os.path.join(OUTPUT_PATH, "labels.pkl"), "wb") as f:
    pickle.dump(le, f)

# ==============================
# SPLIT
# ==============================
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, shuffle=True
)

FEATURES = X.shape[2]

# ==============================
# 🔥 RESHAPE FOR CNN
# ==============================
X_train = X_train.reshape(-1, SEQUENCE_LENGTH, FEATURES, 1)
X_test = X_test.reshape(-1, SEQUENCE_LENGTH, FEATURES, 1)

# ==============================
# MODEL 🔥 CNN + LSTM
# ==============================
model = Sequential([

    # CNN Feature Extraction
    TimeDistributed(Conv1D(64, 3, activation='relu'),
                    input_shape=(SEQUENCE_LENGTH, FEATURES, 1)),
    TimeDistributed(MaxPooling1D(2)),

    TimeDistributed(Conv1D(128, 3, activation='relu')),
    TimeDistributed(MaxPooling1D(2)),

    TimeDistributed(Flatten()),

    # LSTM
    LSTM(128, return_sequences=False),
    Dropout(0.5),

    # Dense
    Dense(64, activation='relu'),
    Dropout(0.3),

    Dense(len(le.classes_), activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# ==============================
# TRAIN 🔥
# ==============================
history = model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=40,
    batch_size=16,
    shuffle=True
)

# ==============================
# EVALUATE
# ==============================
loss, acc = model.evaluate(X_test, y_test)
print(f"\n🔥 FINAL ACCURACY: {acc * 100:.2f}%")

# ==============================
# SAVE MODEL
# ==============================
model.save(os.path.join(OUTPUT_PATH, "cnn_lstm_model.keras"))

print("✅ TRAINING DONE")