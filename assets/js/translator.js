document.addEventListener('DOMContentLoaded', () => {
  const video = document.getElementById('camera-video');
  const startBtn = document.getElementById('start-camera');
  const stopBtn = document.getElementById('stop-camera');
  const statusText = document.getElementById('camera-status');
  const outputBox = document.getElementById('realtime-output');
  const currentPrediction = document.getElementById('current-prediction');
  const currentConfidence = document.getElementById('current-confidence');

  const API_BASE = 'http://127.0.0.1:8000';
  const SESSION_ID = crypto.randomUUID?.() || Math.random().toString(36).slice(2);

  const CONFIDENCE_THRESHOLD = 0.8;
  const ADAPTIVE_MIN = 120;   // ms
  const ADAPTIVE_MAX = 600;   // ms
  let adaptiveInterval = 300; // starting interval
  const REQUEST_TIMEOUT = 5000; // timeout if request takes > 5 seconds

  let cameraStream = null;
  let sessionRunning = false;
  let sessionStarted = false;
  let isProcessing = false; // prevent duplicate requests in flight
  let lastRequestTime = 0;

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  let lastFrameHash = null;
  let lastStableTime = 0;

  function api(path) {
    return `${API_BASE}${path}`;
  }

  function setStatus(msg, type = 'info') {
    if (!statusText) return;
    statusText.textContent = msg;
    statusText.style.color =
      type === 'danger' ? 'red' :
      type === 'success' ? 'green' : 'white';
  }

  function setPrediction(word, conf) {
    if (currentPrediction) currentPrediction.textContent = word || '...';
    if (currentConfidence) currentConfidence.textContent = `${Math.round(conf * 100)}%`;
  }

  function setSentence(text) {
    if (outputBox) outputBox.textContent = text || '';
  }

  async function setupCamera() {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 416, height: 416 },
      audio: false
    });
    video.srcObject = cameraStream;
    await video.play();
  }

  function stopCamera() {
    if (!cameraStream) return;
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
  }

  function captureFrame() {
    if (!video || video.readyState < 2) return null;
    const w = 416;
    const h = 416;
    canvas.width = w;
    canvas.height = h;
    ctx.drawImage(video, 0, 0, w, h);
    return new Promise(res => canvas.toBlob(res, 'image/jpeg', 0.7));
  }

  async function hashBlob(blob) {
    try {
      const buf = await blob.arrayBuffer();
      const hashBuf = await crypto.subtle.digest('SHA-1', buf);
      const hashArray = Array.from(new Uint8Array(hashBuf));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } catch (e) {
      return null;
    }
  }

  async function sendFrame() {
    // Guard: Prevent duplicate requests
    if (!sessionRunning || isProcessing) return;
    
    // Adaptive throttle: don't send faster than adaptiveInterval
    const now = Date.now();
    if (now - lastRequestTime < adaptiveInterval) return;

    isProcessing = true;
    lastRequestTime = now;
    
    // Timeout protection
    const timeoutId = setTimeout(() => {
      if (isProcessing) {
        console.warn('[TIMEOUT] Request took too long, resetting');
        isProcessing = false;
        setStatus('Request timeout', 'danger');
      }
    }, REQUEST_TIMEOUT);

    try {
      const blob = await captureFrame();
      if (!blob) {
        clearTimeout(timeoutId);
        isProcessing = false;
        return;
      }

      // Compute hash and skip if identical to last
      const frameHash = await hashBlob(blob);
      if (frameHash && frameHash === lastFrameHash) {
        // stable frame: increase adaptiveInterval slowly
        adaptiveInterval = Math.min(ADAPTIVE_MAX, adaptiveInterval * 1.08);
        lastStableTime = Date.now();
        clearTimeout(timeoutId);
        isProcessing = false;
        setStatus('Stable (skipped)', 'info');
        return;
      }

      // motion detected -> reduce interval for responsiveness
      if (lastFrameHash && frameHash && frameHash !== lastFrameHash) {
        adaptiveInterval = Math.max(ADAPTIVE_MIN, Math.floor(adaptiveInterval * 0.7));
      }

      lastFrameHash = frameHash;

      const fd = new FormData();
      fd.append('image', blob, 'frame.jpg');
      fd.append('session_id', SESSION_ID);

      const res = await fetch(api('/translator/predict'), {
        method: 'POST',
        body: fd
      });

      const data = await res.json();
      clearTimeout(timeoutId);

      if (!data.success) {
        setStatus(data.message || 'error', 'danger');
        isProcessing = false;
        return;
      }

      const label = data.label || '';
      const conf = Number(data.confidence || 0);
      const sentence = data.sentence || '';

      // Update UI
      if (label && conf >= CONFIDENCE_THRESHOLD) {
        setPrediction(label, conf);
        setStatus(data.message || (data.accepted ? 'Accepted' : 'Detecting...'), 'success');
      } else {
        setPrediction('...', 0);
      }

      setSentence(sentence);

      // Minimal logging: only accepted words
      if (data.accepted) {
        console.log('[ACCEPTED]', label);
      }

    } catch (err) {
      console.error('[ERROR]', err);
      clearTimeout(timeoutId);
      setStatus('Connection error', 'danger');
    } finally {
      isProcessing = false;
    }
  }

  async function startLoop() {
    // Guard: Clear any existing interval before starting new one
    if (window._translatorInterval) {
      clearInterval(window._translatorInterval);
      window._translatorInterval = null;
    }

    // Start new interval (fast tick, sendFrame will adaptively throttle)
    window._translatorInterval = setInterval(() => {
      sendFrame();
    }, 50);
  }

  function stopLoop() {
    if (window._translatorInterval) {
      clearInterval(window._translatorInterval);
      window._translatorInterval = null;
    }
  }

  async function startSession() {
    // Guard: Prevent duplicate /start calls
    if (sessionRunning || sessionStarted) {
      console.warn('[GUARD] Session already started, ignoring');
      setStatus('Session already running', 'success');
      return;
    }

    try {
      await setupCamera();
    } catch (err) {
      console.error('[CAMERA ERROR]', err);
      setStatus('Camera access denied', 'danger');
      return;
    }

    try {
      const res = await fetch(api('/translator/start'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID })
      });

      const data = await res.json();

      if (!data.success) {
        setStatus('Failed to start', 'danger');
        stopCamera();
        return;
      }

      sessionRunning = true;
      sessionStarted = true;
      setStatus('Running...', 'success');
      setSentence('Waiting...');
      isProcessing = false;
      lastRequestTime = 0;
      startLoop();
      
      // Send first frame immediately
      sendFrame();
    } catch (err) {
      console.error('[START ERROR]', err);
      setStatus('Failed to start session', 'danger');
      stopCamera();
      sessionStarted = false;
    }
  }

  async function stopSession() {
    sessionRunning = false;
    sessionStarted = false;
    isProcessing = false;
    stopLoop();
    stopCamera();

    try {
      const res = await fetch(api('/translator/stop'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID })
      });

      const data = await res.json();
      setStatus('Stopped', 'info');
    } catch (err) {
      console.error('[STOP ERROR]', err);
      setStatus('Stop error', 'danger');
    }
  }

  startBtn?.addEventListener('click', startSession);
  stopBtn?.addEventListener('click', stopSession);

  setStatus('Ready');
});