const STORAGE_KEYS = {
  letters: 'signbridge_alphabet_progress',
  words: 'signbridge_words_progress',
  quiz: 'quizScores',
  accuracy: 'practiceAccuracy',
  translator: 'translatorUsage',
  recent: 'recentActivities',
  sessions: 'practiceSessions',
  weekly: 'weeklyPractice',
  accuracyTrend: 'accuracyTrend'
};

const FALLBACK_DATA = {
  completedAlphabetLetters: [],
  completedWords: [],
  quizScores: [],
  practiceAccuracy: [],
  translatorUsage: 0,
  practiceSessions: 0,
  weeklyPractice: [0, 0, 0, 0, 0, 0, 0],
  accuracyTrend: [0, 0, 0, 0, 0, 0, 0],
  recentActivities: []
};



function toNumber(value) {
  if (Array.isArray(value)) return value.length;
  if (typeof value === 'string' && value.trim() !== '') {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : 0;
  }
  return typeof value === 'number' ? value : 0;
}

function average(numbers) {
  if (!Array.isArray(numbers) || numbers.length === 0) return 0;
  const total = numbers.reduce((sum, item) => sum + toNumber(item), 0);
  return Math.round(total / numbers.length);
}

function buildActivityFeed(activities) {
  const feed = document.getElementById('activity-feed');
  feed.innerHTML = '';

  if (!Array.isArray(activities) || activities.length === 0) {
    const placeholder = document.createElement('li');
    placeholder.className = 'list-group-item px-0 border-0 mb-3 text-muted';
    placeholder.textContent = 'No recent activity recorded yet. Progress will appear as you practice.';
    feed.appendChild(placeholder);
    return;
  }

  activities.forEach((item) => {
    const li = document.createElement('li');
    li.className = 'list-group-item px-0 border-0 mb-3';
    li.innerHTML = `
      <div class="row g-3 align-items-start">
        <div class="col-auto">
          <span class="badge rounded-circle bg-${item.icon || 'primary'}" style="width:14px;height:14px;"></span>
        </div>
        <div class="col">
          <h6 class="mb-1">${item.title}</h6>
          <p class="text-muted mb-0">${item.description}</p>
        </div>
        <div class="col-auto text-nowrap">
          <small class="text-muted">${item.time}</small>
        </div>
      </div>
    `;
    feed.appendChild(li);
  });
}

function normalizeSeries(value, length) {
  if (!Array.isArray(value)) return Array(length).fill(0);
  const series = value.slice(0, length).map((item) => Number(item) || 0);
  while (series.length < length) series.push(0);
  return series;
}

function updateProgressBar(id, labelId, value) {
  const bar = document.getElementById(id);
  const label = document.getElementById(labelId);
  const safeValue = Math.max(0, Math.min(100, Math.round(value)));
  bar.style.width = `${safeValue}%`;
  label.textContent = `${safeValue}%`;
}

function updateStats(data) {
  const letters = toNumber(data.completedAlphabetLetters);
  const words = toNumber(data.completedWords);
  const quizScores = Array.isArray(data.quizScores) ? data.quizScores : [];
  const translatorSessions = toNumber(data.translatorUsage);
  const practiceSessions = toNumber(data.practiceSessions);
  const averageAccuracy = average(data.practiceAccuracy);

  document.getElementById('stat-letters').textContent = letters;
  document.getElementById('stat-words').textContent = words;
  document.getElementById('stat-accuracy').textContent = `${averageAccuracy}%`;
  document.getElementById('stat-practice').textContent = practiceSessions;
  document.getElementById('stat-translator').textContent = translatorSessions;

  const alphabetPercent = (letters / 26) * 100;
  const wordsPercent = (words / 40) * 100;
  const quizPercent = (quizScores.length / 12) * 100;
  const translatorPercent = (translatorSessions / 15) * 100;

  updateProgressBar('progress-alphabet', 'progress-alphabet-label', alphabetPercent);
  updateProgressBar('progress-words', 'progress-words-label', wordsPercent);
  updateProgressBar('progress-quiz', 'progress-quiz-label', quizPercent);
  updateProgressBar('progress-translator', 'progress-translator-label', translatorPercent);

  setAchievement('beginner', letters >= 5);
  setAchievement('fastlearner', words >= 10 && averageAccuracy >= 80);
  setAchievement('quizmaster', quizScores.length >= 3 && average(quizScores) >= 80);
  setAchievement('translator', translatorSessions >= 5);
}

function setAchievement(idSuffix, unlocked) {
  const badge = document.getElementById(`achievement-${idSuffix}`);
  if (!badge) return;
  badge.className = unlocked ? 'badge bg-success' : 'badge bg-secondary';
  badge.textContent = unlocked ? 'Unlocked' : 'Locked';
}

function buildChart(weekly, accuracyTrend) {
  const ctx = document.getElementById('performanceChart').getContext('2d');
  const existing = Chart.getChart(ctx);
  if (existing) existing.destroy();

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [
        {
          label: 'Practice Sessions',
          data: normalizeSeries(weekly, 7),
          tension: 0.35,
          borderWidth: 3,
          borderColor: '#3f6efc',
          backgroundColor: 'rgba(63,110,252,0.18)',
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: '#3f6efc'
        },
        {
          label: 'Accuracy (%)',
          data: normalizeSeries(accuracyTrend, 7),
          tension: 0.35,
          borderWidth: 3,
          borderColor: '#0d9488',
          backgroundColor: 'rgba(13,148,136,0.16)',
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: '#0d9488',
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: '#334155' },
          grid: { color: 'rgba(15,23,42,0.08)' }
        },
        y1: {
          position: 'right',
          beginAtZero: true,
          max: 100,
          ticks: { color: '#0f766e' },
          grid: { drawOnChartArea: false }
        },
        x: {
          ticks: { color: '#334155' },
          grid: { color: 'rgba(15,23,42,0.08)' }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#334155' }
        },
        tooltip: {
          backgroundColor: '#111827',
          titleColor: '#fff',
          bodyColor: '#fff'
        }
      }
    }
  });
}

async function loadDashboard() {
  // Initialize session once and preserve in-memory progress for authenticated users
  if (window.SB && typeof window.SB.init === 'function') {
    try { await window.SB.init(); } catch (e) {}
  }
  const token = window.SB && window.SB.authToken ? window.SB.authToken : null;
  // For guests, ensure in-memory progress is empty
  if (!token) {
    try { window.completedLetters = []; } catch (e) {}
    try { window.completedWords = []; } catch (e) {}
  }
  const data = {
    completedAlphabetLetters: FALLBACK_DATA.completedAlphabetLetters.slice(),
    completedWords: FALLBACK_DATA.completedWords.slice(),
    quizScores: FALLBACK_DATA.quizScores.slice(),
    practiceAccuracy: FALLBACK_DATA.practiceAccuracy.slice(),
    translatorUsage: FALLBACK_DATA.translatorUsage,
    practiceSessions: FALLBACK_DATA.practiceSessions,
    weeklyPractice: FALLBACK_DATA.weeklyPractice.slice(),
    accuracyTrend: FALLBACK_DATA.accuracyTrend.slice(),
    recentActivities: FALLBACK_DATA.recentActivities.slice()
  };

  if (token) {
    // Authenticated users: use cached SB.progress (only fetched once per session)
    const backend = window.SB ? window.SB.progress : null;
    if (backend) {
      data.completedAlphabetLetters = Array.isArray(backend.mastered_letters) ? backend.mastered_letters : [];
      data.completedWords = Array.isArray(backend.completed_words) ? backend.completed_words : [];
      try { window.completedLetters = data.completedAlphabetLetters.slice(); } catch (e) {}
      try { window.completedWords = data.completedWords.slice(); } catch (e) {}
    }
    // If backend.progress is null (fetch failed), keep empty state per spec
  }

  updateStats(data);
  buildActivityFeed(data.recentActivities);
  buildChart(data.weeklyPractice, data.accuracyTrend);
}

window.addEventListener('DOMContentLoaded', async () => {
  await loadDashboard();
  AOS.init({ duration: 800, once: true, easing: 'ease-out-cubic' });
});

window.addEventListener('storage', async () => {
  await loadDashboard();
});