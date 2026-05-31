const LETTER_GROUPS = {
  af: ['A', 'B', 'C', 'D', 'E', 'F'],
  gl: ['G', 'H', 'I', 'J', 'K', 'L'],
  mr: ['M', 'N', 'O', 'P', 'Q', 'R'],
  sz: ['S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
};

const PROGRESS_KEY = 'signbridge_alphabet_progress';
const API_URL = window.location.protocol === 'file:' ? 'http://127.0.0.1:5000/predict' : '/predict';
const body = document.body;
const group = body.dataset.group || 'af';
const groupLabel = body.dataset.groupLabel || 'A–F';
const letters = LETTER_GROUPS[group] || LETTER_GROUPS.af;
const totalQuestions = Math.min(6, letters.length);

const groupLabelEl = document.getElementById('group-label');
const targetLetterEl = document.getElementById('question-letter');
const questionProgressEl = document.getElementById('question-progress');
const questionScoreEl = document.getElementById('question-score');
const overallScoreEl = document.getElementById('overall-score');
const feedbackPill = document.getElementById('feedback-pill');
const sessionStateEl = document.getElementById('session-state');
const startButton = document.getElementById('start-quiz');
const nextButton = document.getElementById('next-question');
const stopButton = document.getElementById('stop-quiz');
const cameraPreview = document.getElementById('camera-preview');
const questionStatusEl = document.getElementById('question-status');
const summaryPanel = document.getElementById('summary-panel');
const summaryTextEl = document.getElementById('summary-text');

let stream = null;
let quizActive = false;
let currentQuestionIndex = 0;
let questionOrder = [];
let questionScore = 0;
let totalScore = 0;
let consecutiveCorrect = 0;
let timer = 15;
let timerInterval = null;
let predictInterval = null;

let completedLettersCache = [];
// Initialize per-page in-memory cache; authenticated users load backend, guests stay empty
(function initCompletedLettersCache() {
  completedLettersCache = completedLettersCache || [];
  if (window.SB && typeof window.SB.init === 'function') {
    window.SB.init().then(() => {
      if (window.SB && window.SB.authToken && window.SB.progress && Array.isArray(window.SB.progress.mastered_letters)) {
        completedLettersCache = window.SB.progress.mastered_letters.map(l => (typeof l === 'string' ? l.toUpperCase() : l));
      } else if (!window.SB.authToken) {
        completedLettersCache = [];
      }
    }).catch(() => {});
  } else {
    completedLettersCache = [];
  }
})();

function loadCompletedLetters() {
  return completedLettersCache.slice();
}

function saveCompletedLetter(letter) {
  const token = localStorage.getItem('auth_token');
  if (token && window.masterletter) {
    window.masterletter(letter).then(p => {
      if (p && Array.isArray(p.mastered_letters)) {
        completedLettersCache = p.mastered_letters.map(l => (typeof l === 'string' ? l.toUpperCase() : l));
      }
    }).catch(() => {});
  }
  // guests: do not persist or write to localStorage
}

function shuffle(array) {
  const copy = [...array];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function setFeedback(message, type) {
  feedbackPill.textContent = message;
  feedbackPill.className = `feedback-pill ${type}`;
}

function updateQuestionDisplay() {
  questionProgressEl.textContent = `Question ${currentQuestionIndex + 1} of ${totalQuestions}`;
  questionScoreEl.textContent = `${questionScore} / 100`;
  overallScoreEl.textContent = `${totalScore} / ${totalQuestions * 100}`;
}

function showSummary() {
  quizActive = false;
  stopCamera();
  stopTimers();
  questionStatusEl.textContent = 'Completed';
  sessionStateEl.textContent = 'Finished';
  summaryPanel.classList.remove('d-none');
  summaryTextEl.textContent = `You completed the ${groupLabel} quiz. Final score: ${Math.round(totalScore / totalQuestions)} / 100.`;
  setFeedback('Great work! Review your progress or try another quiz.', 'success');
}

function nextQuestion() {
  stopTimers();
  if (currentQuestionIndex + 1 >= questionOrder.length) {
    showSummary();
    return;
  }
  currentQuestionIndex += 1;
  questionScore = 0;
  consecutiveCorrect = 0;
  timer = 15;
  questionStatusEl.textContent = 'Ready';
  targetLetterEl.textContent = questionOrder[currentQuestionIndex];
  updateQuestionDisplay();
  setFeedback('Perform the letter shown above', 'warning');
  timerInterval = setInterval(() => {
    timer -= 1;
    document.getElementById('timer-value').textContent = `${timer}s`;
    if (timer <= 0) {
      stopTimers();
      setFeedback('Time is up for this letter. Use Next to continue.', 'warning');
      nextButton.disabled = false;
    }
  }, 1000);
  predictInterval = setInterval(requestPrediction, 900);
}

function stopTimers() {
  clearInterval(timerInterval);
  clearInterval(predictInterval);
  timerInterval = null;
  predictInterval = null;
}

function stopCamera() {
  if (!stream) return;
  stream.getTracks().forEach(track => track.stop());
  cameraPreview.srcObject = null;
  stream = null;
}

async function initCamera() {
  if (stream) {
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    cameraPreview.srcObject = stream;
    await cameraPreview.play();
  } catch (error) {
    setFeedback('Camera access is required for quiz mode.', 'danger');
  }
}

async function captureFrame() {
  if (!stream || cameraPreview.readyState < 2) {
    return null;
  }
  const canvas = document.createElement('canvas');
  canvas.width = cameraPreview.videoWidth || 640;
  canvas.height = cameraPreview.videoHeight || 480;
  const ctx = canvas.getContext('2d');
  ctx.translate(canvas.width, 0);
  ctx.scale(-1, 1);
  ctx.drawImage(cameraPreview, 0, 0, canvas.width, canvas.height);
  return new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
}

async function requestPrediction() {
  if (!quizActive) return;
  const blob = await captureFrame();
  if (!blob) return;
  const formData = new FormData();
  formData.append('image', blob, 'frame.jpg');

  try {
    const response = await fetch(API_URL, { method: 'POST', body: formData });
    if (!response.ok) throw new Error('Prediction failed');
    const data = await response.json();
    processPrediction(data.label, Number(data.confidence) || 0);
  } catch (error) {
    console.error(error);
    setFeedback('Unable to reach the practice server.', 'danger');
  }
}

function processPrediction(label, confidence) {
  const normalized = label?.toUpperCase() || '-';
  const performance = Math.round(confidence * 100);
  const target = questionOrder[currentQuestionIndex];
  const correct = normalized === target && confidence >= 0.6;

  if (correct) {
    consecutiveCorrect += 1;
    questionScore = clamp(Math.round((questionScore * 0.4) + (performance * 0.6) + 2), 0, 100);
  } else {
    consecutiveCorrect = 0;
    questionScore = clamp(questionScore - 2, 0, 100);
  }

  if (correct && consecutiveCorrect >= 4) {
    totalScore += questionScore;
    saveCompletedLetter(target);
    setFeedback('Great job! Letter completed for this quiz.', 'success');
    questionStatusEl.textContent = 'Question complete';
    updateQuestionDisplay();
    nextButton.disabled = false;
    nextButton.textContent = currentQuestionIndex + 1 >= questionOrder.length ? 'Finish quiz' : 'Next letter';
    stopTimers();
    return;
  }

  if (performance >= 60) {
    setFeedback('Good attempt. Keep the pose steady.', 'success');
  } else if (performance >= 35) {
    setFeedback('Try again with a clearer hand pose.', 'warning');
  } else {
    setFeedback('Move your hand closer and hold steady.', 'danger');
  }

  questionStatusEl.textContent = normalized === '-' ? 'No hand detected' : `Detected ${normalized}`;
  updateQuestionDisplay();
}

function startQuiz() {
  quizActive = true;
  questionOrder = shuffle(letters).slice(0, totalQuestions);
  currentQuestionIndex = 0;
  questionScore = 0;
  totalScore = 0;
  consecutiveCorrect = 0;
  timer = 15;
  summaryPanel.classList.add('d-none');
  questionStatusEl.textContent = 'Ready';
  groupLabelEl.textContent = groupLabel;
  questionProgressEl.textContent = `Question 1 of ${totalQuestions}`;
  targetLetterEl.textContent = questionOrder[0];
  nextButton.disabled = true;
  nextButton.textContent = 'Next letter';
  sessionStateEl.textContent = 'Running';
  setFeedback('Quiz started! Perform the letter shown above.', 'success');
  updateQuestionDisplay();

  initCamera().then(() => {
    if (!stream) return;
    predictInterval = setInterval(requestPrediction, 900);
    timerInterval = setInterval(() => {
      timer -= 1;
      document.getElementById('timer-value').textContent = `${timer}s`;
      if (timer <= 0) {
        stopTimers();
        setFeedback('Time is up for this letter. Use Next to continue.', 'warning');
        nextButton.disabled = false;
      }
    }, 1000);
  });
}

function stopQuiz() {
  quizActive = false;
  stopTimers();
  stopCamera();
  sessionStateEl.textContent = 'Stopped';
  setFeedback('Quiz stopped. You can restart or finish the current letter.', 'warning');
}

startButton.addEventListener('click', startQuiz);
stopButton.addEventListener('click', stopQuiz);
nextButton.addEventListener('click', () => {
  if (!quizActive && summaryPanel.classList.contains('d-none')) {
    startQuiz();
    return;
  }
  nextQuestion();
});

window.addEventListener('beforeunload', () => {
  stopQuiz();
});

window.addEventListener('load', () => {
  groupLabelEl.textContent = groupLabel;
  questionProgressEl.textContent = `Question 1 of ${totalQuestions}`;
  questionScoreEl.textContent = '0 / 100';
  overallScoreEl.textContent = `0 / ${totalQuestions * 100}`;
  setFeedback('Press Start to begin the quiz.', 'warning');
});
