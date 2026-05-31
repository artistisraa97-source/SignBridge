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
  const FPS_INTERVAL = 300; // send every 300ms (matches backend 300-400ms throttling)
  const REQUEST_TIMEOUT = 5000; // timeout if request takes > 5 seconds

  let cameraStream = null;
  let sessionRunning = false;
  let sessionStarted = false;
  let isProcessing = false; // prevent duplicate requests in flight
  let lastRequestTime = 0;

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

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

  async function sendFrame() {
    // ✓ GUARD: Prevent duplicate requests
    if (!sessionRunning || isProcessing) return;
    
    // ✓ GUARD: Throttle requests (don't send faster than FPS_INTERVAL)
    const now = Date.now();
    if (now - lastRequestTime < FPS_INTERVAL) return;

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
    // ✓ GUARD: Clear any existing interval before starting new one
    if (window._translatorInterval) {
      clearInterval(window._translatorInterval);
      window._translatorInterval = null;
    }

    // Start new interval
    window._translatorInterval = setInterval(() => {
      sendFrame();
    }, FPS_INTERVAL);
  }

  function stopLoop() {
    if (window._translatorInterval) {
      clearInterval(window._translatorInterval);
      window._translatorInterval = null;
    }
  }

  async function startSession() {
    // ✓ GUARD: Prevent duplicate /start calls
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
