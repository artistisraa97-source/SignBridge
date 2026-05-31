"""
translator_router.py - Clean FastAPI Translator Router

ARCHITECTURE: Backend API only (NO webcam, NO threads, NO realtime.py import)
- Receives frames from browser via /translator/predict
- Maintains per-session state (30-frame buffer, sentence, timing)
- Runs model ONLY when: len(sequence)==30 AND time>1.5s
- Returns predictions with majority vote smoothing

✓ ISOLATED: Does NOT import realtime.py (fully independent)
✓ STATEFUL: Session-based state machine per user
✓ SAFE: No camera, no threads, no import side effects
"""

from fastapi import APIRouter, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
import asyncio
import collections
import hashlib
from collections import OrderedDict
import time
import numpy as np
import cv2
import json
from translator_model_loader import (
    SEQUENCE_LENGTH,
    extract_keypoints,
    predict_realtime_sequence,
)
from grammar_corrector import correct_sentence
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter()

# =========================
# PERFORMANCE TUNING
# =========================
MIN_PREDICTION_INTERVAL = 0.18  # 180ms minimum between predictions (prevent spam)
MAX_PREDICTION_INTERVAL = 0.6   # 600ms max (allow natural speech pace)

# Lightweight LRU cache for recent frame predictions
LRU_CACHE_SIZE = 256
prediction_lru = OrderedDict()

# =========================
# SESSIONS
# =========================
sessions = collections.defaultdict(lambda: {
    "sequence": collections.deque(maxlen=SEQUENCE_LENGTH),
    "sentence": [],
    # dynamic small window for majority vote
    "pred_buffer": collections.deque(maxlen=3),
    "last_prediction_time": 0.0,  # for throttling (not cumulative like last_time)
    "current_label": "",
    "current_confidence": 0.0,
    "running": False,
    "message": "Ready"
})

session_locks = collections.defaultdict(asyncio.Lock)

# =========================
# HELPER: Format sentence with grammar correction
# =========================
def _format_sentence(session: dict) -> str:
    """Format and correct the sentence before returning to client.
    
    Args:
        session: Current session state dict
        
    Returns:
        Grammar-corrected sentence string
    """
    raw_sentence = " ".join(session["sentence"])
    if raw_sentence.strip():
        return correct_sentence(raw_sentence)
    return raw_sentence

# =========================
# RESET SESSION (Full reset - only on initial start)
# =========================
def _reset_translator_session(session_id: str):
    """Full reset: clears everything and starts fresh."""
    session = sessions[session_id]
    session["sequence"].clear()
    session["sentence"] = []
    session["pred_buffer"].clear()
    session["last_prediction_time"] = 0.0
    session["current_label"] = ""
    session["current_confidence"] = 0.0
    session["running"] = True
    session["message"] = "Translator ready"

# =========================
# CLEAR SESSION (Partial clear - for mid-session clearing)
# =========================
def _clear_translator_session(session_id: str):
    """Partial clear: only clears sentence and sequence, preserves running state."""
    session = sessions[session_id]
    session["sequence"].clear()
    session["sentence"] = []
    session["pred_buffer"].clear()
    session["current_label"] = ""
    session["current_confidence"] = 0.0
    session["message"] = "Cleared"
    # CLEAR does not modify running or last_time

# =========================
# START (Idempotent - safe to call multiple times)
# =========================
@router.post("/translator/start")
async def translator_start(payload: dict = Body(default={})):
    """Start translator session.
    
    IDEMPOTENT:
    - If session already running: ignore, just return success (prevents accidental reset)
    - If session not running: reset and start
    """
    session_id = str(payload.get("session_id", "default"))
    session = sessions[session_id]
    
    # ✓ IDEMPOTENT FIX: Only reset if NOT already running
    if session["running"]:
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "running": True,
            "message": "Already running (idempotent)",
            "sentence": _format_sentence(session)
        })
    
    # Fresh start
    _reset_translator_session(session_id)

    return JSONResponse({
        "success": True,
        "session_id": session_id,
        "running": True,
        "message": "Translator started",
        "sentence": ""
    })

# =========================
# CLEAR (New endpoint - safe sentence clearing)
# =========================
@router.post("/translator/clear")
async def translator_clear(payload: dict = Body(default={})):
    """Clear sentence and sequence WITHOUT stopping the session.
    
    Used by frontend when user wants to clear the output mid-stream.
    Does NOT affect running flag or session lifecycle.
    """
    session_id = str(payload.get("session_id", "default"))
    session = sessions[session_id]
    
    # perform clear regardless of running state; do NOT touch running
    _clear_translator_session(session_id)
    
    return JSONResponse({
        "success": True,
        "message": "Cleared",
        "sentence": ""
    })

# =========================
# STOP
# =========================
@router.post("/translator/stop")
async def translator_stop(payload: dict = Body(default={})):
    session_id = str(payload.get("session_id", "default"))
    session = sessions[session_id]
    
    session["running"] = False
    sentence = _format_sentence(session)

    return JSONResponse({
        "success": True,
        "running": False,
        "sentence": sentence
    })

# =========================
# STATUS
# =========================
@router.get("/translator/status")
async def translator_status(session_id: str = "default"):
    session = sessions[session_id]

    return JSONResponse({
        "success": True,
        "running": session["running"],
        "label": session["current_label"],
        "confidence": session["current_confidence"],
        "sentence": _format_sentence(session),
        "frames_collected": len(session["sequence"]),
        "message": session["message"]
    })

# =========================
# PREDICT
# =========================
@router.post("/translator/predict")
async def translator_predict(
    image: UploadFile = File(...),
    session_id: str = Form("default")
):
    session = sessions[session_id]
    lock = session_locks[session_id]

    if not session["running"]:
        return JSONResponse({"success": False, "message": "Not running"}, status_code=400)

    if lock.locked():
        return JSONResponse({"success": False, "message": "Busy"}, status_code=429)

    async with lock:

        # =========================
        # READ IMAGE + QUICK HASH
        # =========================
        image_bytes = await image.read()
        try:
            frame_hash = hashlib.sha1(image_bytes).hexdigest()
        except Exception:
            frame_hash = None
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = await asyncio.to_thread(cv2.imdecode, np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return JSONResponse({"success": False, "message": "Bad frame"}, status_code=400)

        # Server-side dedup: if same frame recently seen for this session, return cached
        if frame_hash:
            last_hash = session.get("last_frame_hash")
            if last_hash == frame_hash:
                # Return current state quickly (no model call)
                return JSONResponse({
                    "success": True,
                    "label": session["current_label"],
                    "confidence": float(session["current_confidence"]),
                    "accepted": False,
                    "sentence": _format_sentence(session),
                    "frames_collected": len(session["sequence"]),
                    "message": "Duplicate frame (skipped)"
                })

        # Check LRU cache for recent identical frames
        if frame_hash and frame_hash in prediction_lru:
            # Move to end as recently used
            pred_label, pred_conf, pred_time = prediction_lru.pop(frame_hash)
            prediction_lru[frame_hash] = (pred_label, pred_conf, time.time())
            # If cached prediction fresh (<1.0s), return it
            if time.time() - pred_time < 1.0:
                session["last_frame_hash"] = frame_hash
                session["current_label"] = pred_label
                session["current_confidence"] = pred_conf
                return JSONResponse({
                    "success": True,
                    "label": pred_label,
                    "confidence": float(pred_conf),
                    "accepted": False,
                    "sentence": _format_sentence(session),
                    "frames_collected": len(session["sequence"]),
                    "message": "Cached prediction"
                })

        # =========================
        # EXTRACT FEATURES
        # =========================
        try:
            features = await asyncio.to_thread(extract_keypoints, frame)
        except Exception as e:
            return JSONResponse({"success": False, "message": str(e)}, status_code=500)

        if features is None or len(features) == 0:
            return JSONResponse({
                "success": True,
                "label": "",
                "confidence": 0.0,
                "sentence": _format_sentence(session),
                "message": "No features"
            })

        # =========================
        # UPDATE BUFFER
        # =========================
        session["sequence"].append(features)
        seq_len = len(session["sequence"])

        # WAIT UNTIL 30 FRAMES
        if seq_len < SEQUENCE_LENGTH:
            return JSONResponse({
                "success": True,
                "label": "",
                "confidence": 0.0,
                "sentence": _format_sentence(session),
                "message": f"Collecting {seq_len}/{SEQUENCE_LENGTH}"
            })

        # =========================
        # ADAPTIVE THROTTLING
        # =========================
        now = time.time()
        time_since_prediction = now - session["last_prediction_time"]

        # per-session adaptive interval
        throttle_interval = session.get("throttle_interval", MIN_PREDICTION_INTERVAL)

        # motion detection (frame change)
        last_hash = session.get("last_frame_hash")
        motion = (frame_hash is not None and last_hash is not None and frame_hash != last_hash)

        # dynamic adjustment: if motion detected -> speed up; if stable -> slow down
        if motion:
            throttle_interval = max(MIN_PREDICTION_INTERVAL * 0.6, throttle_interval * 0.7)
        else:
            throttle_interval = min(MAX_PREDICTION_INTERVAL, throttle_interval * 1.15)

        # store back
        session["throttle_interval"] = throttle_interval

        if time_since_prediction < throttle_interval:
            # update last_frame_hash to avoid repeated decode spam
            if frame_hash:
                session["last_frame_hash"] = frame_hash
            return JSONResponse({
                "success": True,
                "label": session["current_label"],
                "confidence": session["current_confidence"],
                "sentence": _format_sentence(session),
                "message": "Throttled (adaptive)"
            })

        # =========================
        # PREDICT
        # =========================
        try:
            word, conf, _ = predict_realtime_sequence(session["sequence"])
        except Exception as e:
            logger.exception(f"[PREDICT ERROR] session_id={session_id} error during model predict: {e}")
            return JSONResponse({"success": False, "message": str(e)}, status_code=500)

        # update state and throttle timestamp
        session["last_prediction_time"] = now
        session["current_label"] = word
        session["current_confidence"] = conf

        # Store frame hash / cache result
        if frame_hash:
            try:
                # insert/update LRU cache
                if frame_hash in prediction_lru:
                    prediction_lru.pop(frame_hash)
                prediction_lru[frame_hash] = (word, float(conf), time.time())
                # trim LRU
                while len(prediction_lru) > LRU_CACHE_SIZE:
                    prediction_lru.popitem(last=False)
            except Exception:
                pass

        # =========================
        # ADD TO BUFFER (improved majority vote)
        # - drop very low confidence
        # - early accept on very high confidence
        # =========================
        accepted = False
        if conf >= 0.95:
            # immediate accept
            stable_word = word
            if len(session["sentence"]) == 0 or stable_word != session["sentence"][-1]:
                session["sentence"].append(stable_word)
                accepted = True
                session["message"] = f"Accepted: {stable_word} (high confidence)"
                logger.info(f"[PREDICT] session_id={session_id} label={word} conf={conf:.3f} [EARLY ACCEPT]")
        elif conf < 0.5:
            # low confidence: ignore for smoothing
            session["message"] = f"Low confidence {conf:.2f}"
            logger.info(f"[PREDICT] session_id={session_id} label={word} conf={conf:.3f} [IGNORED]")
        else:
            # append to small sliding window
            session["pred_buffer"].append(word)
            buf = list(session["pred_buffer"])
            session["message"] = f"Building consensus... {len(buf)}/{session['pred_buffer'].maxlen}"

            # check consensus early: majority in buffer
            if len(buf) >= 2:
                counts = {}
                for w in buf:
                    counts[w] = counts.get(w, 0) + 1
                best = max(counts, key=counts.get)
                if counts[best] >= 2:
                    if len(session["sentence"]) == 0 or best != session["sentence"][-1]:
                        session["sentence"].append(best)
                        accepted = True
                        session["message"] = f"Accepted: {best}"
                        logger.info(f"[PREDICT] session_id={session_id} label={best} conf={conf:.3f} [ACCEPTED]")
                    else:
                        session["message"] = "Duplicate skipped"

        # =========================
        # RESPONSE
        # =========================
        return JSONResponse({
            "success": True,
            "label": word,
            "confidence": float(conf),
            "accepted": accepted,
            "sentence": _format_sentence(session),
            "frames_collected": seq_len,
            "message": session["message"]
        })


# WebSocket support removed — system is HTTP-only using `/translator/predict`.
# The HTTP pipeline retains caching, adaptive throttling, majority voting,
# and frame-deduplication implemented earlier. Removing WebSocket avoids
# runtime `NameError` issues and unstable persistent-connection logic.