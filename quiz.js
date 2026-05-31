const STORAGE_KEY = 'signbridge_quiz_stats';
const URL_PARAMS = new URLSearchParams(window.location.search);
const SELECTED_MODE = URL_PARAMS.get('mode');
const SELECTED_GROUP = (URL_PARAMS.get('group') || 'AF').toUpperCase();
const SELECTED_TOPIC = (URL_PARAMS.get('topic') || 'greetings').toLowerCase();
const ALPHABET_GROUPS = {
  AF: ['A', 'B', 'C', 'D', 'E', 'F'],
  GL: ['G', 'H', 'I', 'J', 'K', 'L'],
  MR: ['M', 'N', 'O', 'P', 'Q', 'R'],
  SZ: ['S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
};
const WORD_TOPICS = {
  greetings: {
    title: 'Greetings Quiz',
    description: 'Practice polite greetings used in everyday conversation.',
    items: [
      { word: 'Hello', hint: 'A friendly greeting used to start a conversation.' },
      { word: 'Goodbye', hint: 'A sign used when leaving or ending a chat.' },
      { word: 'Please', hint: 'A polite request for help or permission.' },
      { word: 'Thanks', hint: 'Gratitude offered after support or a favor.' },
      { word: 'Sorry', hint: 'An apology for a mistake or misunderstanding.' }
    ]
  },
  daily: {
    title: 'Daily Words Quiz',
    description: 'Build vocabulary for common daily activities and items.',
    items: [
      { word: 'Water', hint: 'A drink you use when you are thirsty.' },
      { word: 'Food', hint: 'A basic need for energy and growth.' },
      { word: 'Yes', hint: 'A positive response to a question.' },
      { word: 'No', hint: 'A negative response or refusal.' },
      { word: 'Help', hint: 'A request for assistance in a situation.' }
    ]
  },
  beginner: {
    title: 'Beginner Words',
    description: 'Start with essential words useful for new sign learners.',
    items: [
      { word: 'Friend', hint: 'Someone you know and trust.' },
      { word: 'Family', hint: 'A group of relatives or loved ones.' },
      { word: 'Happy', hint: 'A feeling of joy and contentment.' },
      { word: 'Learn', hint: 'To gain new knowledge or skill.' },
      { word: 'Study', hint: 'Practice or review material on purpose.' }
    ]
  },
  phrases: {
    title: 'Common Phrases',
    description: 'Practice everyday phrases that appear in real interactions.',
    items: [
      { word: 'How are you?', hint: 'A polite way to ask about someone’s condition.' },
      { word: 'Nice to meet you', hint: 'A phrase used after being introduced.' },
      { word: 'See you soon', hint: 'A friendly farewell with plans to meet again.' },
      { word: 'Take care', hint: 'A phrase expressing concern and well-wishes.' },
      { word: 'I understand', hint: 'A confirmation that you follow what was said.' }
    ]
  }
};
const MIXED_WORD_ITEMS = Object.values(WORD_TOPICS).flatMap((topic) => topic.items);
const QUIZ_CONFIG = {
  video_words: {
  title: 'Video Words Quiz',
  description: 'Watch the sign and choose the correct word.',
  difficulty: 'Medium',
  reward: '120 XP',
  timer: 20,
  totalQuestions: 5,
  createQuestions: (topic) => createVideoWordQuestions(topic || 'greetings')
  },
  alphabet: {
    title: 'Alphabet Quiz',
    description: 'Build alphabet fluency with letter recognition and sign interpretation.',
    difficulty: 'Medium',
    reward: '90 XP',
    timer: 18,
    totalQuestions: 6,
    createQuestions: (group) => createAlphabetQuestions(group || 'AF')
  },
  full_alphabet: {
    title: 'Full Alphabet Challenge',
    description: 'Complete a full-letter quiz with mixed question types and timed scoring.',
    difficulty: 'Hard',
    reward: '150 XP',
    timer: 16,
    totalQuestions: 12,
    createQuestions: () => createAlphabetQuestions('FULL', 12)
  },
  words: {
    title: 'Word Quiz',
    description: 'Practice core vocabulary using meaning-based multiple choice questions.',
    difficulty: 'Medium',
    reward: '100 XP',
    timer: 18,
    totalQuestions: 8,
    createQuestions: (topic) => createWordQuestions(topic || 'greetings')
  },
  mixed: {
    title: 'Mixed Challenge',
    description: 'Combine alphabet and word training in one balanced quiz.',
    difficulty: 'Hard',
    reward: '130 XP',
    timer: 16,
    totalQuestions: 12,
    createQuestions: () => createMixedQuestions(12, 18)
  },
  mixed_speed: {
    title: 'Speed Challenge',
    description: 'Answer quickly in a rapid mixed quiz that rewards fast recall.',
    difficulty: 'Hard',
    reward: '160 XP',
    timer: 12,
    totalQuestions: 12,
    createQuestions: () => createMixedQuestions(12, 12)
  },
  realtime_letter: {
    redirect: 'realtime_alphabet.html'
  },
  realtime_word: {
    redirect: 'realtime_words.html'
  }
};
let quizState = {
  questions: [],
  mode: null,
  title: '',
  description: '',
  difficulty: '',
  reward: '',
  timerSeconds: 18,
  currentIndex: 0,
  correct: 0,
  wrong: 0,
  streak: 0,
  maxStreak: 0,
  active: false,
  answered: false,
  timerId: null,
  elapsedSeconds: 0
};
const elements = {
  hubAttempts: document.getElementById('hub-attempts'),
  hubBestScore: document.getElementById('hub-best-score'),
  hubStreak: document.getElementById('hub-streak'),
  hubLastQuiz: document.getElementById('hub-last-quiz'),
  quizRunner: document.getElementById('quiz-runner'),
  quizLibrary: document.getElementById('quiz-library'),
  quizModeTitle: document.getElementById('quiz-mode-title'),
  quizModeCopy: document.getElementById('quiz-mode-copy'),
  quizDifficulty: document.getElementById('quiz-difficulty'),
  quizTimeEstimate: document.getElementById('quiz-time-estimate'),
  quizReward: document.getElementById('quiz-reward'),
  quizStep: document.getElementById('quiz-step'),
  quizTotal: document.getElementById('quiz-total'),
  quizProgressBar: document.getElementById('quiz-progress-bar'),
  quizTimer: document.getElementById('quiz-timer'),
  questionTypeLabel: document.getElementById('question-type-label'),
  questionPrompt: document.getElementById('question-prompt'),
  questionMeta: document.getElementById('question-meta'),
  questionMedia: document.getElementById('question-media'),
  answerOptions: document.getElementById('answer-options'),
  feedbackMessage: document.getElementById('feedback-message'),
  btnStart: document.getElementById('btn-start'),
  btnNext: document.getElementById('btn-next'),
  btnFinish: document.getElementById('btn-finish'),
  btnRetry: document.getElementById('btn-retry'),
  btnSuggest: document.getElementById('btn-suggest'),
  statCorrect: document.getElementById('stat-correct'),
  statWrong: document.getElementById('stat-wrong'),
  statStreak: document.getElementById('stat-streak'),
  statAccuracy: document.getElementById('stat-accuracy'),
  resultPanel: document.getElementById('result-panel'),
  resultScore: document.getElementById('result-score'),
  resultMessage: document.getElementById('result-message'),
  resultBadge: document.getElementById('result-badge')
};
function shuffle(array) {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
function uniqueChoices(correct, pool, count = 4) {
  const choices = new Set([correct]);
  const candidates = pool.filter((item) => item !== correct);
  while (choices.size < count && candidates.length > 0) {
    const next = candidates.splice(Math.floor(Math.random() * candidates.length), 1)[0];
    choices.add(next);
  }
  return shuffle(Array.from(choices));
}
function createAlphabetQuestions(group, max = 6) {
  const letters = group === 'FULL' ? 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('') : ALPHABET_GROUPS[group] || ALPHABET_GROUPS.AF;
  const allLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  const selected = shuffle(letters).slice(0, Math.min(max, letters.length));
  return selected.map((letter, index) => {
    const choices = uniqueChoices(letter, allLetters, 4);
    const isVideo = index % 2 === 0;
    return {
      id: `alphabet-${letter}`,
      type: isVideo ? 'video' : 'multiple_choice',
      prompt: isVideo ? 'Watch the sign and choose the correct letter.' : `Select the correct letter for this sign gesture.`,
      meta: isVideo ? 'Video question' : 'Letter selection',
      media: `assets/videos/alphabet_quiz/${letter}.mp4`,
      choices,
      answer: letter,
      time: 18
    };
  });
}
function createWordQuestions(topic) {
  const topicData = WORD_TOPICS[topic] || WORD_TOPICS.greetings;
  const pool = shuffle(MIXED_WORD_ITEMS.map((item) => item.word));
  return shuffle(topicData.items).slice(0, Math.min(8, topicData.items.length)).map((item) => ({
    id: `word-${item.word.replace(/\s+/g, '-')}`,
    type: 'multiple_choice',
    prompt: `Which sign matches this meaning? ${item.hint}`,
    meta: 'Word meaning',
    choices: uniqueChoices(item.word, pool, 4),
    answer: item.word,
    time: 20
  }));
}
function createMixedQuestions(count, timer) {
  const questionSet = [];
  const letterPool = createAlphabetQuestions('FULL', 12);
  const wordPool = shuffle(MIXED_WORD_ITEMS).slice(0, 12).map((item) => ({
    id: `word-${item.word.replace(/\s+/g, '-')}`,
    type: 'multiple_choice',
    prompt: `Which sign matches this meaning? ${item.hint}`,
    meta: 'Word meaning',
    choices: uniqueChoices(item.word, MIXED_WORD_ITEMS.map((entry) => entry.word), 4),
    answer: item.word,
    time: timer
  }));
  const mixed = shuffle([...letterPool, ...wordPool]).slice(0, count);
  return mixed.map((question) => ({ ...question, time: timer }));
}
function safeParseJson(raw, fallback) {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}
function loadStats() {
  return safeParseJson(localStorage.getItem(STORAGE_KEY), {
    attempts: 0,
    bestScore: 0,
    bestStreak: 0,
    currentStreak: 0,
    totalCorrect: 0,
    totalQuestions: 0,
    lastQuiz: null,
    history: []
  });
}
function saveStats(stats) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
}
function updateHubStats() {
  const stats = loadStats();
  elements.hubAttempts.textContent = stats.attempts || 0;
  elements.hubBestScore.textContent = `${stats.bestScore || 0}%`;
  elements.hubStreak.textContent = stats.currentStreak || 0;
  elements.hubLastQuiz.textContent = stats.lastQuiz ? `${stats.lastQuiz.title} • ${stats.lastQuiz.score}%` : 'No quiz played yet';
}
function showSection(section, show) {
  if (!section) return;
  section.classList.toggle('d-none', !show);
}
function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0');
  const remainder = (seconds % 60).toString().padStart(2, '0');
  return `${minutes}:${remainder}`;
}
function setFeedback(message, variant = 'info') {
  if (!elements.feedbackMessage) return;
  const classes = ['feedback-banner', 'success', 'danger', 'info'];
  elements.feedbackMessage.className = 'feedback-banner';
  if (variant === 'success') elements.feedbackMessage.classList.add('success');
  if (variant === 'danger') elements.feedbackMessage.classList.add('danger');
  elements.feedbackMessage.textContent = message;
}
function resetTimer() {
  clearInterval(quizState.timerId);
  quizState.timerId = null;
}
function updateTimerDisplay() {
  elements.quizTimer.textContent = formatTime(quizState.elapsedSeconds);
}
function startQuestionTimer() {
  quizState.elapsedSeconds = quizState.timerSeconds;
  updateTimerDisplay();
  resetTimer();
  quizState.timerId = setInterval(() => {
    quizState.elapsedSeconds -= 1;
    updateTimerDisplay();
    if (quizState.elapsedSeconds <= 0) {
      clearInterval(quizState.timerId);
      handleAnswer(null);
    }
  }, 1000);
}
function renderQuestion() {
  const question = quizState.questions[quizState.currentIndex];
  if (!question) return;
  quizState.answered = false;
  elements.quizStep.textContent = quizState.currentIndex + 1;
  elements.quizTotal.textContent = quizState.questions.length;
  const progressPercent = Math.round(((quizState.currentIndex) / quizState.questions.length) * 100);
  elements.quizProgressBar.style.width = `${progressPercent}%`;
  elements.questionTypeLabel.textContent = question.type === 'video' ? 'Video Question' : 'Question';
  elements.questionPrompt.textContent = question.prompt;
  elements.questionMeta.textContent = question.meta || (question.type === 'video' ? 'Video question' : 'Multiple choice');
  elements.answerOptions.innerHTML = '';
  elements.btnNext.classList.add('d-none');
  elements.btnFinish.classList.add('d-none');
  setFeedback('Choose the best answer before the timer runs out.', 'info');
  if (question.type === 'video' && question.media) {
    elements.questionMedia.classList.remove('d-none');
    elements.questionMedia.innerHTML = `<video controls muted playsinline src="${question.media}"></video>`;
  } else {
    elements.questionMedia.classList.add('d-none');
    elements.questionMedia.innerHTML = '';
  }
  const options = shuffle(question.choices || []);
  options.forEach((option) => {
    const col = document.createElement('div');
    col.className = 'col-12';
    const optionButton = document.createElement('div');
    optionButton.className = 'answer-option';
    optionButton.textContent = option;
    optionButton.addEventListener('click', () => handleAnswer(option, optionButton));
    col.appendChild(optionButton);
    elements.answerOptions.appendChild(col);
  });
  startQuestionTimer();
}
function recordStats() {
  const percent = Math.round((quizState.correct / quizState.questions.length) * 100);
  const stats = loadStats();
  stats.attempts += 1;
  stats.totalCorrect += quizState.correct;
  stats.totalQuestions += quizState.questions.length;
  stats.lastQuiz = {
    title: quizState.title,
    score: percent,
    date: new Date().toISOString()
  };
  stats.bestScore = Math.max(stats.bestScore || 0, percent);
  stats.currentStreak = percent >= 75 ? (stats.currentStreak || 0) + 1 : 0;
  stats.bestStreak = Math.max(stats.bestStreak || 0, stats.currentStreak);
  const session = {
    mode: quizState.mode,
    title: quizState.title,
    score: percent,
    correct: quizState.correct,
    wrong: quizState.wrong,
    streak: quizState.maxStreak,
    date: new Date().toISOString()
  };
  stats.history = [session, ...(stats.history || [])].slice(0, 12);
  saveStats(stats);
}
function getResultBadge(score) {
  if (score >= 90) return 'SignBridge Expert';
  if (score >= 75) return 'Strong Performer';
  if (score >= 50) return 'Practice Starter';
  return 'Keep Training';
}
function getResultMessage(score) {
  if (score >= 90) return 'Outstanding performance — you mastered this challenge.';
  if (score >= 75) return 'Great job! A strong result that shows growing confidence.';
  if (score >= 50) return 'Good effort. Keep practicing to improve your speed and accuracy.';
  return 'Nice start. Review the quiz and try again to build momentum.';
}
function updateLiveStats() {
  elements.statCorrect.textContent = quizState.correct;
  elements.statWrong.textContent = quizState.wrong;
  elements.statStreak.textContent = quizState.maxStreak;
  const percent = quizState.questions.length ? Math.round((quizState.correct / quizState.questions.length) * 100) : 0;
  elements.statAccuracy.textContent = `${percent}%`;
}
function finishQuiz() {
  resetTimer();
  quizState.active = false;
  recordStats();
  updateHubStats();
  const percent = Math.round((quizState.correct / quizState.questions.length) * 100);
  elements.resultScore.textContent = `${percent}%`;
  elements.resultBadge.textContent = getResultBadge(percent);
  elements.resultMessage.textContent = getResultMessage(percent);
  elements.resultPanel.classList.remove('d-none');
  elements.btnNext.classList.add('d-none');
  elements.btnFinish.classList.add('d-none');
  elements.btnStart.textContent = 'Restart Quiz';
}
function handleAnswer(selected, buttonElement) {
  if (!quizState.active || quizState.answered) return;
  quizState.answered = true;
  resetTimer();
  const currentQuestion = quizState.questions[quizState.currentIndex];
  const isCorrect = selected === currentQuestion.answer;
  if (isCorrect) {
    quizState.correct += 1;
    quizState.streak += 1;
    quizState.maxStreak = Math.max(quizState.maxStreak, quizState.streak);
    setFeedback('Correct! Keep your focus for the next question.', 'success');
    if (buttonElement) buttonElement.classList.add('correct');
  } else {
    quizState.wrong += 1;
    quizState.streak = 0;
    setFeedback(`Incorrect. The right answer was ${currentQuestion.answer}.`, 'danger');
    if (buttonElement) buttonElement.classList.add('incorrect');
    const correctOption = Array.from(document.querySelectorAll('.answer-option')).find((item) => item.textContent === currentQuestion.answer);
    if (correctOption) correctOption.classList.add('correct');
  }
  quizState.active = false;
  elements.btnNext.classList.toggle('d-none', quizState.currentIndex + 1 >= quizState.questions.length);
  elements.btnFinish.classList.toggle('d-none', quizState.currentIndex + 1 < quizState.questions.length);
  updateLiveStats();
}
function advanceQuestion() {
  quizState.currentIndex += 1;
  if (quizState.currentIndex >= quizState.questions.length) {
    finishQuiz();
    return;
  }
  renderQuestion();
  elements.resultPanel.classList.add('d-none');
  elements.btnStart.textContent = 'Restart Quiz';
}
function startQuiz() {
  quizState.active = true;
  quizState.correct = 0;
  quizState.wrong = 0;
  quizState.streak = 0;
  quizState.maxStreak = 0;
  quizState.currentIndex = 0;
  elements.resultPanel.classList.add('d-none');
  elements.btnStart.textContent = 'Restart Quiz';
  elements.btnNext.classList.add('d-none');
  elements.btnFinish.classList.add('d-none');
  updateLiveStats();
  renderQuestion();
}
function setupQuizRunner() {
  const config = QUIZ_CONFIG[SELECTED_MODE];
  if (!config) return;
  if (config.redirect) {
    window.location.href = config.redirect;
    return;
  }
  quizState.mode = SELECTED_MODE;
  quizState.title = config.title;
  quizState.description = config.description;
  quizState.difficulty = config.difficulty;
  quizState.reward = config.reward;
  quizState.timerSeconds = config.timer;
  quizState.questions = config.createQuestions(SELECTED_MODE === 'alphabet' ? SELECTED_GROUP : SELECTED_MODE === 'words' ? SELECTED_TOPIC : undefined);
  elements.quizModeTitle.textContent = quizState.title;
  elements.quizModeCopy.textContent = quizState.description;
  elements.quizDifficulty.textContent = quizState.difficulty;
  elements.quizTimeEstimate.textContent = `${quizState.timerSeconds}s each`;
  elements.quizReward.textContent = quizState.reward;
  elements.quizTotal.textContent = quizState.questions.length;
  elements.quizStep.textContent = 1;
  elements.quizProgressBar.style.width = '0%';
  setFeedback('Press Start to launch the quiz session.', 'info');
  showSection(elements.quizRunner, true);
  showSection(elements.quizLibrary, false);
  updateLiveStats();
  if (location.search && !elements.btnStart) {
    startQuiz();
  }
}
function getQuizSuggestion() {
  if (SELECTED_MODE === 'alphabet' || SELECTED_MODE === 'full_alphabet') {
    return 'quiz.html?mode=words&topic=greetings';
  }
  if (SELECTED_MODE === 'words') {
    return 'quiz.html?mode=alphabet&group=AF';
  }
  if (SELECTED_MODE === 'mixed' || SELECTED_MODE === 'mixed_speed') {
    return 'quiz.html?mode=full_alphabet';
  }
  return 'quiz.html?mode=alphabet&group=AF';
}
function initPage() {
  updateHubStats();
  if (SELECTED_MODE) {
    setupQuizRunner();
  }
  elements.btnStart.addEventListener('click', () => {
    if (quizState.active && quizState.answered) {
      startQuiz();
      return;
    }
    startQuiz();
  });
  elements.btnNext.addEventListener('click', advanceQuestion);
  elements.btnFinish.addEventListener('click', finishQuiz);
  elements.btnRetry.addEventListener('click', startQuiz);
  elements.btnSuggest.addEventListener('click', () => {
    window.location.href = getQuizSuggestion();
  });
  AOS.init({ duration: 700, once: true, easing: 'ease-out-cubic' });
}
window.addEventListener('DOMContentLoaded', initPage);
window.addEventListener('storage', updateHubStats);

function createVideoWordQuestions(topic) {
  const topicData = WORD_TOPICS[topic] || WORD_TOPICS.greetings;
  const pool = MIXED_WORD_ITEMS.map((item) => item.word);

  return shuffle(topicData.items).map((item) => ({
    id: `video-word-${item.word.replace(/\s+/g, '-')}`,
    type: 'video',
    prompt: 'Watch the sign and choose the correct word.',
    meta: 'Video Question',
    media: `assets/videos/words_quiz/${item.word}.mp4`,
    choices: uniqueChoices(item.word, pool, 4),
    answer: item.word,
    time: 20
  }));
}