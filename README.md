# 🤟 SignBridge

## AI-Powered Sign Language Learning & Realtime Translation Platform

SignBridge is a comprehensive, intelligent platform designed to make sign language learning accessible, interactive, and engaging. Built with cutting-edge AI and machine learning technologies, SignBridge enables users to learn sign language through gamified quizzes, alphabet training, and real-time translation powered by computer vision.

---

## ✨ Features

- 🎯 **Realtime Sign Language Translation** - Live webcam-based sign recognition and translation
- 🔤 **Alphabet Learning System** - Interactive lessons for learning the sign language alphabet
- 📚 **Word & Phrase Learning** - Comprehensive vocabulary building modules
- 🎮 **Interactive Quiz Platform** - Gamified assessments for vocabulary and sentence comprehension
- 📊 **Progress Dashboard** - Track learning progress and achievements
- ⚡ **Realtime Sentence Prediction** - Advanced AI model predicting full sentences from sign sequences
- 🎨 **Responsive Bootstrap UI** - Beautiful, mobile-friendly interface
- 🔗 **RESTful API** - Complete FastAPI backend for extensibility
- 🧠 **MediaPipe Landmarks** - Advanced hand and pose detection
- 🤖 **TensorFlow/Keras Models** - State-of-the-art deep learning models for sign recognition
- 📱 **Multi-page Application** - Dedicated pages for learning, translation, and analytics

---

## 🛠️ Technologies Used

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Advanced styling and animations
- **Bootstrap 5** - Responsive design framework
- **JavaScript** - Interactive functionality and real-time processing

### Backend
- **FastAPI** - High-performance web framework
- **Python 3** - Core backend logic
- **Uvicorn** - ASGI web server

### AI/ML & Computer Vision
- **TensorFlow** - Deep learning framework
- **Keras** - Neural network API
- **MediaPipe** - Hand and pose landmark detection
- **OpenCV** - Image processing and video handling
- **NumPy** - Numerical computations
- **scikit-learn** - Machine learning utilities

---

## 🧠 AI/ML Pipeline

SignBridge utilizes a sophisticated multi-stage AI pipeline for accurate sign language recognition:

1. **MediaPipe Landmark Extraction**
   - Extracts 21-point hand landmarks from video frames
   - Captures hand position, orientation, and gesture details

2. **OpenCV Video Processing**
   - Real-time frame capture from webcam
   - Video stream preprocessing and normalization
   - Frame buffering for sequence processing

3. **CNN + LSTM Architecture**
   - Convolutional Neural Network (CNN) for spatial feature extraction
   - Long Short-Term Memory (LSTM) for temporal sequence modeling
   - Captures temporal dynamics of sign language gestures

4. **TensorFlow/Keras Inference**
   - Real-time sequence prediction
   - Confidence scoring for predictions
   - Multi-class classification for signs and letters

5. **Realtime Frame Buffering**
   - Sliding window approach for sequence management
   - Temporal smoothing for improved accuracy
   - Reduces noise and fluctuations in predictions

---

## 📁 Project Structure

```
SignBridge/
│
├── main.py                          # FastAPI application entry point
├── server.py                        # Alternative server configuration
├── requirements.txt                 # Python dependencies
│
├── routers/                         # API route handlers
│   ├── auth_router.py
│   ├── translator_router.py
│   ├── words_api.py
│   ├── spell_api.py
│   └── ...
│
├── services/                        # Business logic layer
│   ├── predictor_service.py
│   ├── translator_service.py
│   └── ...
│
├── auth/                            # Authentication module
│   ├── auth.py
│   ├── auth_router.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── email_utils.py
│
├── backend/                         # Backend utilities and helpers
│
├── utils/                           # Utility functions
│
├── assets/                          # Static assets
│   ├── css/
│   ├── js/
│   ├── img/
│   ├── music/
│   └── videos/
│
├── asl_alphabet_train/              # Training dataset (organized by label)
│   ├── 0-9/
│   ├── A-Z/
│   ├── space/
│   └── ...
│
├── asl_landmarks.csv                # Pre-computed landmark features
├── asl_cnn_model.keras              # CNN model for alphabet recognition
├── asl_landmarks_model.h5           # Landmark detection model
│
├── index.html                       # Home page
├── learn.html                       # Learning interface
├── alphabet.html                    # Alphabet trainer
├── translate.html                   # Real-time translation tool
├── quiz.html                        # Quiz platform
├── progress.html                    # Progress dashboard
├── realtime.html                    # Real-time recognition interface
├── signup.html                      # User registration
│
└── README.md                        # Project documentation
```

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/SignBridge.git
cd SignBridge
```

### Step 2: Create Virtual Environment
```bash
python -m venv signai_env_v2
```

### Step 3: Activate Virtual Environment

**On Windows:**
```bash
signai_env_v2\Scripts\activate
```

**On macOS/Linux:**
```bash
source signai_env_v2/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Project

### Option 1: Direct Python Execution
```bash
python main.py
```

### Option 2: Uvicorn Server (Recommended)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Option 3: Uvicorn with Auto-Reload (Development)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at: **http://127.0.0.1:8000/**

---

## 🌐 Website Pages

### Home Page
- **URL:** http://127.0.0.1:8000/index.html
- Navigation hub connecting to all modules

### 🔤 Alphabet Learning
- **URL:** http://127.0.0.1:8000/alphabet.html
- Interactive alphabet trainer with sign recognition
- Learn individual letters with visual feedback

### 📚 Learn Module
- **URL:** http://127.0.0.1:8000/learn.html
- Structured learning content
- Vocabulary building exercises

### 🎮 Quiz System
- **URL:** http://127.0.0.1:8000/quiz.html
- Multiple quiz categories (alphabet, words, phrases)
- Score tracking and performance metrics

### 🔄 Real-time Translation
- **URL:** http://127.0.0.1:8000/translate.html
- Live webcam-based sign translation
- Real-time feedback and confidence scoring

### 📱 Progress Dashboard
- **URL:** http://127.0.0.1:8000/progress.html
- Visual learning statistics
- Achievement badges and milestones
- Performance analytics

### 🔐 Sign Up
- **URL:** http://127.0.0.1:8000/signup.html
- User registration and authentication

---

## 🔄 Realtime Translation System

The real-time translation system represents the core of SignBridge's functionality:

### Workflow
1. **Video Capture** - Webcam stream acquisition
2. **Landmark Detection** - MediaPipe extracts hand landmarks at 30 FPS
3. **Feature Extraction** - Landmarks normalized and formatted
4. **Model Inference** - TensorFlow/Keras model processes sequences
5. **Prediction** - CNN-LSTM predicts sign class and confidence
6. **Display** - Result rendered with confidence metrics

### Features
- Low-latency real-time processing
- Confidence scoring for each prediction
- Temporal smoothing to reduce flickering
- Support for single letters and complete words
- Real-time feedback loop

### Performance
- ~30 FPS processing speed
- <50ms latency for predictions
- Optimized for CPU and GPU execution

---

## 🎮 Quiz System

### Quiz Categories
- **Alphabet Quiz** - Letter recognition and production
- **Word Quiz** - Vocabulary comprehension
- **Phrase Quiz** - Sentence understanding
- **Sentence Construction** - Creating sentences from signs

### Features
- Timed challenges
- Multiple choice questions
- Immediate feedback
- Score calculation and tracking
- Difficulty levels
- Performance statistics

### Scoring
- Points awarded for correct answers
- Bonus points for speed
- Progressive difficulty scaling

---

## 📊 Progress Tracking

### Metrics Tracked
- Quiz completion count
- Average quiz scores
- Learning time spent
- Modules completed
- Vocabulary items learned
- Accuracy improvements over time

### Dashboard Features
- Visual progress charts
- Achievement milestones
- Performance trends
- Learning statistics
- Personalized recommendations

### Data Storage
- User progress stored in database
- Historical data maintained
- Export capabilities for analysis

---

## 🔮 Future Improvements

- 🌍 **Multilingual Support**
  - Arabic Sign Language (ArSL)
  - Chinese Sign Language (CSL)
  - British Sign Language (BSL)
  - Additional regional sign languages

- 📱 **Mobile Applications**
  - iOS native app
  - Android native app
  - Progressive Web App (PWA)
  - Cross-platform compatibility

- ☁️ **Cloud Deployment**
  - AWS Lambda integration
  - Docker containerization
  - Kubernetes orchestration
  - Scalable cloud infrastructure

- 🔐 **Enhanced Authentication**
  - OAuth2 integration
  - Multi-factor authentication
  - Social login support
  - Admin dashboard

- 🧠 **Advanced AI Capabilities**
  - Sentence-level recognition
  - Context-aware predictions
  - Emotion detection
  - Facial expression analysis

- 🔌 **WebSocket Streaming**
  - Real-time bidirectional communication
  - Multiplayer learning sessions
  - Live instructor feedback

- 📈 **Advanced Analytics**
  - Machine learning-based recommendations
  - Personalized learning paths
  - Spaced repetition optimization
  - Learning pattern analysis

- 🎓 **Gamification Enhancements**
  - Leaderboards
  - Achievements and badges
  - Multiplayer competitions
  - Social features

---

## 📝 Notes

- Ensure your webcam is accessible and has proper permissions
- The application requires an internet connection for initial setup
- GPU acceleration recommended for improved performance
- Models are pre-trained; no additional training required for basic usage
- Frame rate depends on system performance and video quality
- Lighting conditions affect recognition accuracy

---

## 👨‍💻 Author

**SignBridge Development Team**

A collaborative project dedicated to making sign language learning accessible through innovative AI technology.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 Support

For support, please open an issue on the GitHub repository or contact the development team.

---

**Made with ❤️ for the Sign Language Community**
