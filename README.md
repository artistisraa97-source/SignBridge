# 🤟 SignBridge

## AI-Powered Sign Language Learning & Real-Time Translation Platform

SignBridge is a web-based platform that combines sign language learning with AI-powered real-time recognition and translation. The project provides interactive lessons, quizzes, progress tracking, and computer-vision-based sign language interpretation using MediaPipe and TensorFlow.

---

## ✨ Features

### 🔤 Alphabet Learning
- Learn sign language alphabet letters interactively.
- Visual learning materials and practice exercises.
- Alphabet quiz system for self-assessment.

### 📚 Word Learning
- Learn common sign language words and expressions.
- Organized learning modules.
- Interactive word quizzes.

### 🎮 Quiz System
- Alphabet quizzes.
- Word quizzes.
- Multiple quiz categories.
- Instant scoring and feedback.

### 📊 Progress Tracking
- Track learning achievements.
- Monitor quiz performance.
- View learning statistics through a dedicated dashboard.

### 🤖 Real-Time Sign Recognition
- Webcam-based sign language recognition.
- MediaPipe landmark extraction.
- TensorFlow-powered prediction pipeline.
- Real-time feedback and translation output.

### 🔐 Authentication System
- User registration and login.
- Secure password handling.
- FastAPI-based authentication endpoints.

---

## 🛠️ Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap 5

### Backend
- Python 3.10
- FastAPI
- Uvicorn
- SQLAlchemy

### AI & Computer Vision
- TensorFlow
- MediaPipe
- OpenCV
- NumPy
- Scikit-learn

### Additional Libraries
- Pandas
- Pillow
- Matplotlib
- pyttsx3

---

## 🧠 AI Recognition Pipeline

The recognition system follows a multi-stage workflow:

1. Webcam frame capture using OpenCV.
2. Hand landmark extraction using MediaPipe.
3. Feature preprocessing and normalization.
4. Sequence-based prediction using TensorFlow models.
5. Real-time output generation and display.

This approach allows the platform to recognize sign gestures and provide live feedback to users.

---

## 📁 Project Structure

```text
SignBridge/
│
├── main.py
├── server.py
├── requirements.txt
│
├── auth/
│   ├── auth.py
│   ├── auth_router.py
│   ├── database.py
│   ├── email_utils.py
│   ├── models.py
│   └── schemas.py
│
├── routers/
│   ├── alphabet_router.py
│   ├── progress_router.py
│   ├── quiz_router.py
│   ├── spell_router.py
│   ├── translator_router.py
│   └── words_router.py
│
├── services/
│   ├── prediction_service.py
│   ├── progress_service.py
│   ├── realtime_service.py
│   ├── translator_realtime_engine.py
│   └── video_service.py
│
├── utils/
│
├── assets/
│   ├── css/
│   ├── js/
│   ├── img/
│   └── vendor/
│
├── index.html
├── learn.html
├── alphabet.html
├── translate.html
├── progress.html
├── quiz.html
├── signup.html
│
└── README.md
```

---

## 🚀 Installation

### Prerequisites

- Python 3.10
- Git

### Clone Repository

```bash
git clone https://github.com/smnsdra/SignBridge.git
cd SignBridge
```

### Create Virtual Environment

```bash
python -m venv signai_env_v2
```

### Activate Environment

Windows:

```bash
signai_env_v2\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Project

Start the application:

```bash
python main.py
```

After startup, open:

```text
http://localhost:8000/progress.html
```

From the dashboard, users can navigate to all learning, quiz, and translation modules.

---

## 🌐 Main Pages

| Page | Description |
|--------|-------------|
| index.html | Landing page |
| learn.html | Learning hub |
| alphabet.html | Alphabet learning |
| translate.html | Real-time translation |
| quiz.html | Quiz system |
| progress.html | Progress dashboard |
| signup.html | User registration |

---

## 📸 Screenshots

Add project screenshots inside:

```text
docs/screenshots/
```

Example:

```md
### Home Page

![Home](docs/screenshots/home.png)

### Learning Module

![Learn](docs/screenshots/learn.png)

### Real-Time Translation

![Translate](docs/screenshots/translate.png)

### Progress Dashboard

![Progress](docs/screenshots/progress.png)
```

---

## 🎥 Demo

You can add a GIF or video demonstration showing:

- Alphabet learning
- Quiz interaction
- Real-time translation
- Progress tracking

Example:

```md
![Demo](docs/screenshots/signbridge-demo.gif)
```

---

## 🔮 Future Improvements

- Additional sign language datasets.
- More vocabulary categories.
- Improved sentence-level recognition.
- Mobile application support.
- Cloud deployment.
- Enhanced analytics and personalization.
- Multi-language sign language support.

---

## 👨‍💻 Team

SignBridge Development Team

---

## 📄 License

This project is intended for educational and research purposes.
