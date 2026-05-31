# SignBridge

## AI-Powered Sign Language Learning and Real-Time Translation Platform

SignBridge is an AI-powered platform built to help users learn sign language, track progress, and translate signs in real time. It combines browser-based learning pages, user authentication, and machine learning pipelines for alphabet and word recognition.

---

# Project Overview

SignBridge is designed to bridge the gap between sign language learners and real-time communication. The platform supports alphabet and word learning, interactive quizzes, progress tracking, and live sign translation using webcam capture, MediaPipe landmark extraction, and TensorFlow inference.

The primary goal of SignBridge is to provide an accessible learning environment where users can practice sign language, validate their progress, and experience AI-powered gesture recognition in a modern web interface.

---

# Features

- Alphabet Learning
- Word Learning
- Quiz System
- Progress Tracking
- Real-Time Sign Recognition
- Authentication System
- AI-powered Translation

---

# Technology Stack

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- JavaScript

### Backend
- FastAPI
- Python 3.10
- Uvicorn
- SQLAlchemy

### AI/ML
- TensorFlow
- Keras
- scikit-learn
- NumPy

### Computer Vision
- OpenCV
- MediaPipe

---

# Project Structure

```
SignBridge/
├── .gitignore
├── README.md
├── app.db
├── users.db
├── main.py
├── server.py
├── requirements.txt
├── index.html
├── learn.html
├── alphabet.html
├── translate.html
├── quiz.html
├── progress.html
├── signup.html
├── words.html
├── realtime_alphabet.html
├── realtime_words.html
├── create_landmark_dataset.py
├── train_landmarks.py
├── realtime_landmarks.py
├── keypoints.py
├── train.py
├── realtime.py
├── predict_words.py
├── grammar_corrector.py
├── alphabet_quiz.js
├── progress.js
├── quiz.js
├── script.js
├── style.css
├── quiz.css
├── progress.css
├── assets/
│   ├── css/
│   ├── img/
│   ├── js/
│   ├── scss/
│   ├── vendor/
│   └── videos/
├── auth/
│   ├── auth.py
│   ├── auth_router.py
│   ├── database.py
│   ├── email_utils.py
│   ├── models.py
│   ├── schemas.py
│   └── __init__.py
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── auth_router.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── requirements.txt
│   └── users.db
├── routers/
│   ├── alphabet_router.py
│   ├── words_router.py
│   ├── translator_router.py
│   ├── spell_router.py
│   ├── quiz_router.py
│   ├── progress_router.py
│   └── __init__.py
├── services/
│   ├── prediction_service.py
│   ├── progress_service.py
│   ├── realtime_service.py
│   ├── translator_realtime_engine.py
│   ├── video_service.py
│   └── __init__.py
├── asl_alphabet_train/
├── dataset/
├── data/
├── cnn_lstm_output/
└── utils/
```

---

# Installation

## Prerequisites
- Python 3.10
- Git

## Clone Repository

```bash
git clone https://github.com/smnsdra/SignBridge.git
cd SignBridge
```

## Create Virtual Environment

Windows:

```
python -m venv signai_env_v2
signai_env_v2\Scripts\activate
```

Linux/macOS:

```
python -m venv signai_env_v2
source signai_env_v2/bin/activate
```

## Install Dependencies

```
pip install -r requirements.txt
```

---

# Running the Website

The application is started using:

```
python main.py
```

After startup, open:

```
http://localhost:8000/progress.html
```

The Progress page acts as the entry point to the learning platform.

---

# Main Website Pages

| Page | Purpose |
| --- | --- |
| `index.html` | Home landing page with overview of SignBridge and quick navigation. |
| `learn.html` | Learning hub that introduces alphabet practice, word learning, quizzes, and translation. |
| `alphabet.html` | Alphabet training page for practicing individual letters and launching realtime recognition. |
| `translate.html` | Real-time translator page for sign-to-text and text-to-sign features. |
| `quiz.html` | Quiz system home page with interactive challenges, scoring, and progress tracking. |
| `progress.html` | Progress dashboard that displays learning stats, achievements, and usage metrics. |
| `signup.html` | User registration, login, email verification, and authentication interface. |

---

# Alphabet Recognition Pipeline

Dataset folder:

```
asl_alphabet_train/
```

Describe the complete workflow:

Step 1:

```
python create_landmark_dataset.py
```

Step 2:

```
python train_landmarks.py
```

Step 3:

```
python realtime_landmarks.py
```

Explain what each script does.

- `create_landmark_dataset.py` processes the alphabet dataset, extracts MediaPipe hand landmarks from images, normalizes positions, computes finger and thumb features, and exports a labeled landmark dataset.
- `train_landmarks.py` trains the alphabet recognition model using the generated dataset, building a CNN+LSTM network and saving the trained model artifacts.
- `realtime_landmarks.py` runs the realtime alphabet recognition demo using webcam capture, landmark extraction, and model inference.

---

# Word Recognition Pipeline

Dataset folder:

```
dataset/
```

Describe the workflow:

Step 1:

```
python keypoints.py
```

Step 2:

```
python train.py
```

Step 3:

```
python realtime.py
```

Explain what each script does.

- `keypoints.py` extracts pose, hand, and facial keypoints from word dataset videos, centers the data relative to the shoulders, and saves processed sequences as `.npy` and `.csv` files.
- `train.py` loads the keypoint sequences, augments data with sliding windows, trains a CNN+LSTM classifier, evaluates accuracy, and saves the resulting model.
- `realtime.py` performs realtime word recognition from webcam input, using the trained model to predict word gestures live.

---

# AI Recognition Workflow

SignBridge's recognition pipeline includes:

- **OpenCV webcam capture** for live video streaming and frame processing.
- **MediaPipe landmark extraction** to detect hand, pose, and face landmarks in real time.
- **Feature preprocessing** to normalize landmarks, compute relative coordinates, and assemble model-ready sequences.
- **TensorFlow inference** to run trained CNN+LSTM models on the preprocessed landmark sequences.
- **Real-time prediction** to produce sign labels and confidence values instantly in the browser.

---

# Download Required Resources

Large resources are intentionally excluded from public GitHub releases. Download the following assets from the shared link and place them into the repository as needed:

- Alphabet Dataset
- Word Dataset
- Trained Models
- Generated Keypoints

[ADD GOOGLE DRIVE LINK HERE]

---

# Excluded Files

The following generated or sensitive files should be excluded from a public release and managed separately:

- `asl_alphabet_train/`
- `dataset/`
- `*.npy`
- `*.keras`
- `*.h5`
- `users.db`
- `app.db`
- `**/__pycache__/`
- `*.log`

These files can be restored from the Google Drive link above.

---

# Screenshots

```
![Home](docs/images/home.png)
![Learning](docs/images/learn.png)
![Alphabet](docs/images/alphabet.png)
![Quiz](docs/images/quiz.png)
![Translation](docs/images/translation.png)
![Progress](docs/images/progress.png)
```

---

# Demo Video

```
![Demo](docs/images/signbridge-demo.gif)
```

```
[Watch Demo Video](ADD_VIDEO_LINK_HERE)
```

---

# Dependencies

SignBridge depends on the following Python libraries listed in `requirements.txt`:

- `numpy`
- `tensorflow` / `tensorflow-intel`
- `mediapipe`
- `opencv-contrib-python`
- `scikit-learn`
- `pandas`
- `matplotlib`
- `pillow`
- `fastapi`
- `uvicorn`
- `python-multipart`
- `SQLAlchemy`
- `passlib[bcrypt]`
- `python-jose[cryptography]`
- `email-validator`
- `pyttsx3`

---

# Future Improvements

- Add multilingual sign language support and regional datasets.
- Build native Android/iOS apps and a Progressive Web App (PWA).
- Add WebSocket-powered real-time streaming for lower latency.
- Improve the translation engine with sentence-level and context-aware prediction.
- Add gamification, leaderboards, and collaborative learning features.
- Containerize the app with Docker and add cloud deployment support.

---

# Authors

SignBridge Development Team

---

# License

Educational and research purposes.
