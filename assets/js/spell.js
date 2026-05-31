/**
 * Spell Your Name - Client-side logic for letter-by-letter spelling
 * Communicates with spell_api.py backend
 */

const SPELL_API_URL = 'http://localhost:5003';
const FRAME_INTERVAL = 100; // ms between frames

let spellSession = {
  isActive: false,
  stream: null,
  videoElement: null,
  canvasElement: null,
  frameIntervalId: null,
  spelledText: '',
  lastConfidence: 0.0
};

/**
 * Initialize spell section event listeners
 */
function initSpellSection() {
  const startBtn = document.getElementById('spell-start-camera');
  const stopBtn = document.getElementById('spell-stop-camera');
  const copyBtn = document.getElementById('spell-copy-output');
  const clearBtn = document.getElementById('spell-clear-output');
  const undoBtn = document.getElementById('spell-undo-letter');

  if (startBtn) startBtn.addEventListener('click', startSpellCamera);
  if (stopBtn) stopBtn.addEventListener('click', stopSpellCamera);
  if (copyBtn) copyBtn.addEventListener('click', copySpelledText);
  if (clearBtn) clearBtn.addEventListener('click', clearSpelledText);
  if (undoBtn) undoBtn.addEventListener('click', undoSpelledLetter);
}

/**
 * Start camera and spell session
 */
async function startSpellCamera() {
  try {
    const video = document.getElementById('spell-camera-video');
    const startBtn = document.getElementById('spell-start-camera');
    const stopBtn = document.getElementById('spell-stop-camera');

    if (!video) {
      console.error('Video element not found');
      return;
    }

    // Request camera access
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    });

    spellSession.stream = stream;
    video.srcObject = stream;
    spellSession.videoElement = video;

    // Create canvas for frame capture
    if (!spellSession.canvasElement) {
      spellSession.canvasElement = document.createElement('canvas');
    }

    // Start backend session
    const sessionResponse = await fetch(`${SPELL_API_URL}/spell/start`, {
      method: 'POST'
    });
    const sessionData = await sessionResponse.json();

    if (sessionData.status === 'started') {
      spellSession.isActive = true;
      updateSpellUI();

      // Disable start, enable stop
      startBtn.disabled = true;
      stopBtn.disabled = false;

      // Update status
      updateSpellStatus('Active');

      // Start frame processing
      startFrameProcessing();
    }
  } catch (error) {
    console.error('Error starting spell camera:', error);
    updateSpellStatus('Camera Error');
    alert('Could not access camera: ' + error.message);
  }
}

/**
 * Stop camera and spell session
 */
async function stopSpellCamera() {
  try {
    const startBtn = document.getElementById('spell-start-camera');
    const stopBtn = document.getElementById('spell-stop-camera');

    // Stop frame processing
    if (spellSession.frameIntervalId) {
      clearInterval(spellSession.frameIntervalId);
      spellSession.frameIntervalId = null;
    }

    // Stop backend session
    const stopResponse = await fetch(`${SPELL_API_URL}/spell/stop`, {
      method: 'POST'
    });
    const stopData = await stopResponse.json();

    // Stop camera stream
    if (spellSession.stream) {
      spellSession.stream.getTracks().forEach(track => track.stop());
      spellSession.stream = null;
    }

    spellSession.isActive = false;
    updateSpellUI();

    // Enable start, disable stop
    startBtn.disabled = false;
    stopBtn.disabled = true;

    updateSpellStatus('Ready');
  } catch (error) {
    console.error('Error stopping spell camera:', error);
  }
}

/**
 * Process frames from video stream
 */
function startFrameProcessing() {
  spellSession.frameIntervalId = setInterval(async () => {
    if (!spellSession.isActive || !spellSession.videoElement) {
      return;
    }

    try {
      const canvas = spellSession.canvasElement;
      const ctx = canvas.getContext('2d');

      canvas.width = spellSession.videoElement.videoWidth || 640;
      canvas.height = spellSession.videoElement.videoHeight || 480;

      // Draw video frame to canvas
      ctx.drawImage(spellSession.videoElement, 0, 0, canvas.width, canvas.height);

      // Convert to blob
      canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('frame', blob, 'frame.jpg');

        try {
          const response = await fetch(`${SPELL_API_URL}/spell/process`, {
            method: 'POST',
            body: formData
          });

          if (response.ok) {
            const data = await response.json();
            updateSpellDisplay(data);
          }
        } catch (error) {
          console.error('Error processing frame:', error);
        }
      }, 'image/jpeg', 0.8);
    } catch (error) {
      console.error('Frame processing error:', error);
    }
  }, FRAME_INTERVAL);
}

/**
 * Update spell display with detection results
 */
function updateSpellDisplay(data) {
  // Update spelled text
  if (data.spelled_text !== undefined) {
    spellSession.spelledText = data.spelled_text;
    const outputEl = document.getElementById('spell-output');
    if (outputEl) {
      outputEl.textContent = data.spelled_text || '_';
    }
  }

  // Update current letter detection
  if (data.current_letter) {
    const letterEl = document.getElementById('spell-current-letter');
    const confidenceEl = document.getElementById('spell-confidence');
    const displayEl = document.getElementById('spell-confidence-display');

    if (letterEl) letterEl.textContent = data.current_letter;
    if (confidenceEl) {
      const conf = Math.round(data.confidence * 100);
      confidenceEl.textContent = conf + '%';

      // Color code confidence
      if (conf >= 80) {
        confidenceEl.style.color = '#16a34a';
      } else if (conf >= 60) {
        confidenceEl.style.color = '#eab308';
      } else {
        confidenceEl.style.color = '#ef6603';
      }
    }

    if (displayEl && data.current_letter !== '-') {
      displayEl.style.display = 'block';
    }
  }

  // Update status badge when new letter detected
  if (data.detected_new) {
    const statusEl = document.getElementById('spell-status');
    if (statusEl) {
      statusEl.textContent = `Detected: ${data.spelled_letters[data.spelled_letters.length - 1]}`;
      // Reset after 1 second
      setTimeout(() => {
        statusEl.textContent = 'Active';
      }, 1000);
    }

    // Glow effect on output
    const outputEl = document.getElementById('spell-output');
    if (outputEl) {
      outputEl.style.animation = 'none';
      setTimeout(() => {
        outputEl.style.animation = 'pulse-glow 0.6s ease-out';
      }, 10);
    }
  }

  // Update last confidence
  if (data.last_confidence) {
    spellSession.lastConfidence = data.last_confidence;
    const confEl = document.getElementById('spell-last-confidence');
    if (confEl) {
      confEl.textContent = (Math.round(data.last_confidence * 100)) + '%';
    }
  }

  // Update camera status
  const statusEl = document.getElementById('spell-camera-status');
  if (statusEl) {
    statusEl.textContent = `Frame ${data.frame_count} • Stable: ${data.stable_frames}/10`;
  }
}

/**
 * Update spell UI state
 */
function updateSpellUI() {
  const outputEl = document.getElementById('spell-output');
  if (outputEl) {
    outputEl.textContent = spellSession.spelledText || '_';
  }
}

/**
 * Update spell status badge
 */
function updateSpellStatus(status) {
  const statusEl = document.getElementById('spell-status');
  if (statusEl) {
    statusEl.textContent = status;
  }
}

/**
 * Copy spelled text to clipboard
 */
async function copySpelledText() {
  try {
    if (spellSession.spelledText) {
      await navigator.clipboard.writeText(spellSession.spelledText);

      const copyBtn = document.getElementById('spell-copy-output');
      const originalText = copyBtn.innerHTML;

      // Show feedback
      copyBtn.innerHTML = '<i class="bi bi-check"></i> Copied!';
      setTimeout(() => {
        copyBtn.innerHTML = originalText;
      }, 2000);
    }
  } catch (error) {
    console.error('Error copying text:', error);
    alert('Could not copy text');
  }
}

/**
 * Clear all spelled letters
 */
async function clearSpelledText() {
  try {
    const response = await fetch(`${SPELL_API_URL}/spell/clear`, {
      method: 'POST'
    });
    const data = await response.json();

    spellSession.spelledText = '';
    const outputEl = document.getElementById('spell-output');
    if (outputEl) {
      outputEl.textContent = '_';
    }

    // Show feedback
    const clearBtn = document.getElementById('spell-clear-output');
    const originalText = clearBtn.innerHTML;
    clearBtn.innerHTML = '<i class="bi bi-check"></i> Cleared!';
    setTimeout(() => {
      clearBtn.innerHTML = originalText;
    }, 1500);
  } catch (error) {
    console.error('Error clearing text:', error);
  }
}

/**
 * Remove last spelled letter
 */
async function undoSpelledLetter() {
  try {
    const response = await fetch(`${SPELL_API_URL}/spell/undo`, {
      method: 'POST'
    });
    const data = await response.json();

    spellSession.spelledText = data.spelled_text;
    const outputEl = document.getElementById('spell-output');
    if (outputEl) {
      outputEl.textContent = data.spelled_text || '_';
    }
  } catch (error) {
    console.error('Error undoing letter:', error);
  }
}

/**
 * Add CSS animations for spell effects
 */
function addSpellStyles() {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes pulse-glow {
      0% {
        text-shadow: 0 0 20px var(--accent-color);
        transform: scale(1);
      }
      50% {
        transform: scale(1.05);
      }
      100% {
        text-shadow: 0 0 0 var(--accent-color);
        transform: scale(1);
      }
    }

    .spelled-text {
      transition: color 0.3s ease;
    }

    .spelled-text.glow {
      animation: pulse-glow 0.6s ease-out;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(16, 185, 129, 0.15);
      color: #059669;
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 1rem;
    }

    .status-badge i {
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `;
  document.head.appendChild(style);
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
  addSpellStyles();
  initSpellSection();

  // Set initial output
  const outputEl = document.getElementById('spell-output');
  if (outputEl) {
    outputEl.textContent = '_';
  }
});

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
  if (spellSession.isActive) {
    stopSpellCamera();
  }
});
