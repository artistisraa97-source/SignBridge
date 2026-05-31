"""
words_router.py - FastAPI router for real-time sign language word recognition.
Uses the EXACT SAME feature extraction pipeline as realtime.py (via translator_model_loader).
"""

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import asyncio
import collections
import os
import time
import numpy as np
import cv2

router = APIRouter()

# Use canonical SEQUENCE_LENGTH from translator_model_loader
SEQUENCE_LENGTH = 30
try:
    from translator_model_loader import SEQUENCE_LENGTH as _TL_SEQLEN
    SEQUENCE_LENGTH = int(_TL_SEQLEN)
except Exception:
    pass

# Import the EXACT extractor used during training and in realtime.py
from translator_model_loader import load_model_and_labels, extract_keypoints

# Per-process session store
sessions = collections.defaultdict(lambda: {
    'sequence': collections.deque(maxlen=SEQUENCE_LENGTH),
    'sentence': [],
    'last_accepted_word': '',
    'last_accepted_time': 0.0,
    'current_label': '',
    'current_confidence': 0.0,
    'last_prediction_time': 0.0,
    'last_frame_time': 0.0,
    'running': True,
    'message': 'Ready'
})

# Per-session async locks to prevent concurrent deque mutation
session_locks = collections.defaultdict(asyncio.Lock)

_model_labels = None

def get_model_and_labels():
    global _model_labels
    if _model_labels is None:
        _model_labels = load_model_and_labels()
    return _model_labels

CONFIDENCE_THRESHOLD = 0.80
DUPLICATE_SILENCE_SECONDS = 2.5
PREDICTION_INTERVAL = 1.5

# Debug flag
DEBUG_VERBOSE = False
DEBUG_SAVE_INPUTS = True
DEBUG_SAVE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'debug', 'words'))

def save_debug_input(session_id, frame, features):
    if not DEBUG_SAVE_INPUTS:
        return
    try:
        os.makedirs(DEBUG_SAVE_DIR, exist_ok=True)
        ts = int(time.time() * 1000)
        image_file = os.path.join(DEBUG_SAVE_DIR, f'frame_{session_id}_{ts}.jpg')
        cv2.imwrite(image_file, frame)
        if isinstance(features, np.ndarray):
            feature_file = os.path.join(DEBUG_SAVE_DIR, f'features_{session_id}_{ts}.npy')
            np.save(feature_file, features)
    except Exception as e:
        print(f"[words_router] DEBUG save failed: {e}")


def predict_word_sequence(session_id: str):
    session = sessions[session_id]
    buffer_len_after = len(session['sequence'])

    if buffer_len_after < SEQUENCE_LENGTH:
        session['message'] = f'Collecting frames: {buffer_len_after}/{SEQUENCE_LENGTH}'
        return {
            'success': True,
            'running': session['running'],
            'ready': False,
            'label': '',
            'confidence': 0.0,
            'accepted': False,
            'sentence': ' '.join(session['sentence']),
            'message': session['message'],
            'frames_collected': buffer_len_after
        }

    now = time.time()
    time_since_last_prediction = now - session['last_prediction_time'] if session['last_prediction_time'] > 0.0 else None
    if session['last_prediction_time'] > 0.0 and time_since_last_prediction < PREDICTION_INTERVAL:
        return {
            'success': True,
            'running': session['running'],
            'ready': True,
            'label': session['current_label'] if session['current_confidence'] >= 0.01 else '',
            'confidence': session['current_confidence'],
            'accepted': False,
            'sentence': ' '.join(session['sentence']),
            'message': 'Waiting for next prediction',
            'frames_collected': buffer_len_after
        }

    sequence_array = np.array(list(session['sequence']), dtype=np.float32)
    if sequence_array.shape != (SEQUENCE_LENGTH, 332):
        print(f"[words_router] WARNING: sequence.shape={sequence_array.shape}, expected ({SEQUENCE_LENGTH}, 332)")

    sequence_input = sequence_array.reshape(1, SEQUENCE_LENGTH, sequence_array.shape[1], 1)

    try:
        prediction = get_model_and_labels()[0].predict(sequence_input, verbose=0)[0]
    except Exception as e:
        print(f"[words_router] ERROR in model.predict: {e}")
        raise

    class_id = int(np.argmax(prediction))
    label = str(get_model_and_labels()[1][class_id])
    confidence = float(prediction[class_id])
    session['last_prediction_time'] = now
    session['current_label'] = label
    session['current_confidence'] = confidence

    accepted = False
    if confidence >= CONFIDENCE_THRESHOLD:
        if label != session['last_accepted_word']:
            accepted = True
        else:
            time_since_last = now - session['last_accepted_time']
            if time_since_last >= DUPLICATE_SILENCE_SECONDS:
                accepted = True

    if accepted:
        if not session['sentence'] or session['sentence'][-1] != label:
            session['sentence'].append(label)
        session['last_accepted_word'] = label
        session['last_accepted_time'] = now
        session['message'] = 'Word accepted'
    else:
        session['message'] = f'Below threshold ({confidence:.2f} < {CONFIDENCE_THRESHOLD})'

    return {
        'success': True,
        'running': session['running'],
        'ready': True,
        'label': label if confidence >= 0.01 else '',
        'confidence': confidence,
        'accepted': accepted,
        'sentence': ' '.join(session['sentence']),
        'message': session['message'],
        'frames_collected': buffer_len_after
    }


@router.post('/predict')
async def predict(image: UploadFile = File(...), session_id: str = Form("default")):
    """
    Predict sign language word from image frame.
    
    HEAVILY INSTRUMENTED FOR DEBUGGING:
    - Prints feature shape/size at every step
    - Tracks session persistence
    - Shows top predictions
    - Validates sequence reshaping
    - Does NOT aggressively reject all-zero frames
    """
    session = sessions[session_id]
    buffer_len_before = len(session['sequence'])

    # ============================================================
    # 1. DECODE IMAGE
    # ============================================================
    image_data = await image.read()
    if not image_data:
        print(f"[words_router] ERROR: No image data for session={session_id}")
        return JSONResponse(
            content={'success': False, 'message': 'No image data'}, 
            status_code=400
        )

    np_img = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if frame is None:
        print(f"[words_router] ERROR: Unable to decode frame for session={session_id}")
        return JSONResponse(
            content={'success': False, 'message': 'Unable to decode image'}, 
            status_code=400
        )
    
    if DEBUG_VERBOSE:
        print(f"\n[words_router] ========== PREDICTION START ==========")
        print(f"[words_router] session_id={session_id}")
        print(f"[words_router] buffer_len_before={buffer_len_before}")

    # ============================================================
    # 2. EXTRACT FEATURES
    # ============================================================
    try:
        features = extract_keypoints(frame)
    except Exception as e:
        print(f"[words_router] ERROR in extract_keypoints: {e}")
        import traceback
        traceback.print_exc()
        features = None

    save_debug_input(session_id, frame, features)

    if features is None:
        print(f"[words_router] ERROR: extract_keypoints returned None")
        return JSONResponse(
            content={
                'success': True,
                'running': session['running'],
                'ready': False,
                'label': '',
                'confidence': 0.0,
                'accepted': False,
                'sentence': ' '.join(session['sentence']),
                'message': 'Waiting for clear sign...',
                'frames_collected': buffer_len_before
            }
        )

    # ============================================================
    # 3. VALIDATE FEATURE VECTOR
    # ============================================================
    if DEBUG_VERBOSE:
        print(f"[words_router] features.shape={features.shape}")
        print(f"[words_router] features.dtype={features.dtype}")
        print(f"[words_router] features.size={features.size}")
        print(f"[words_router] features[0:5]={features[0:5]}")
        print(f"[words_router] features[-5:]={features[-5:]}")
        print(f"[words_router] non_zero_count={np.count_nonzero(features)}")
        print(f"[words_router] all_zeros={np.all(features == 0)}")

    if features.shape != (332,):
        print(f"[words_router] WARNING: Feature shape is {features.shape}, expected (332,)")

    if features.size == 0:
        print(f"[words_router] ERROR: features.size == 0")
        return JSONResponse(
            content={
                'success': True,
                'running': session['running'],
                'ready': False,
                'label': '',
                'confidence': 0.0,
                'accepted': False,
                'sentence': ' '.join(session['sentence']),
                'message': 'Waiting for clear sign...',
                'frames_collected': buffer_len_before
            }
        )

    # ============================================================
    # 4. APPEND TO SESSION (NO AGGRESSIVE REJECTION)
    # ============================================================
    current_frame_time = time.time()
    session_lock = session_locks[session_id]
    async with session_lock:
        interval = current_frame_time - session['last_frame_time'] if session['last_frame_time'] else 0.0
        session['last_frame_time'] = current_frame_time
        if DEBUG_VERBOSE and session['last_frame_time'] > 0.0:
            print(f"[words_router] frame_interval={interval:.3f}s")

        session['sequence'].append(features)
        buffer_len_after = len(session['sequence'])
        
        if DEBUG_VERBOSE:
            print(f"[words_router] buffer_len_after={buffer_len_after}")

        # Not enough frames yet
        if buffer_len_after < SEQUENCE_LENGTH:
            msg = f'Collecting frames: {buffer_len_after}/{SEQUENCE_LENGTH}'
            if DEBUG_VERBOSE:
                print(f"[words_router] {msg}")
            
            return JSONResponse(
                content={
                    'success': True,
                    'running': session['running'],
                    'ready': False,
                    'label': '',
                    'confidence': 0.0,
                    'accepted': False,
                    'sentence': ' '.join(session['sentence']),
                    'message': msg,
                    'frames_collected': buffer_len_after
                }
            )

        # ============================================================
        # 5. ENFORCE REALTIME.PY PREDICTION TIMING
        # ============================================================
        now = time.time()
        time_since_last_prediction = now - session['last_prediction_time']
        if session['last_prediction_time'] > 0.0 and time_since_last_prediction < PREDICTION_INTERVAL:
            if DEBUG_VERBOSE:
                print(f"[words_router] Skipping prediction for {PREDICTION_INTERVAL - time_since_last_prediction:.3f}s; returning last stable result")

            return JSONResponse(
                content={
                    'success': True,
                    'running': session['running'],
                    'ready': True,
                    'label': session['current_label'] if session['current_confidence'] >= 0.01 else '',
                    'confidence': session['current_confidence'],
                    'accepted': False,
                    'sentence': ' '.join(session['sentence']),
                    'message': 'Waiting for next prediction',
                    'frames_collected': buffer_len_after
                }
            )

    # ============================================================
    # 6. LOAD MODEL
    # ============================================================
    try:
        model, labels = get_model_and_labels()
    except Exception as e:
        print(f"[words_router] ERROR loading model: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={'success': False, 'message': 'Model load error'},
            status_code=500
        )

    # ============================================================
    # 6. RESHAPE SEQUENCE
    # ============================================================
    sequence_array = np.array(list(session['sequence']), dtype=np.float32)
    
    if DEBUG_VERBOSE:
        print(f"\n[words_router] RESHAPE VALIDATION:")
        print(f"[words_router] sequence_array.shape (30 frames, 332)={sequence_array.shape}")
        print(f"[words_router] sequence_array.dtype={sequence_array.dtype}")

    # Should be (30, 332)
    if sequence_array.shape != (SEQUENCE_LENGTH, 332):
        print(f"[words_router] WARNING: sequence.shape={sequence_array.shape}, expected ({SEQUENCE_LENGTH}, 332)")

    # Reshape to (1, 30, 332, 1)
    try:
        sequence_input = sequence_array.reshape(1, SEQUENCE_LENGTH, sequence_array.shape[1], 1)
        if DEBUG_VERBOSE:
            print(f"[words_router] After reshape: {sequence_input.shape}")
            print(f"[words_router] Expected: (1, {SEQUENCE_LENGTH}, 332, 1)")
    except Exception as e:
        print(f"[words_router] ERROR reshaping: {e}")
        return JSONResponse(
            content={'success': False, 'message': 'Reshape error'},
            status_code=500
        )

    # ============================================================
    # 7. RUN PREDICTION
    # ============================================================
    try:
        prediction = model.predict(sequence_input, verbose=0)[0]
    except Exception as e:
        print(f"[words_router] ERROR in model.predict: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={'success': False, 'message': 'Prediction error'},
            status_code=500
        )

    if DEBUG_VERBOSE:
        print(f"\n[words_router] PREDICTION OUTPUT:")
        print(f"[words_router] prediction.shape={prediction.shape}")
        print(f"[words_router] prediction.dtype={prediction.dtype}")

    # ============================================================
    # 8. TOP PREDICTIONS (DEBUGGING)
    # ============================================================
    top_indices = np.argsort(prediction)[-5:][::-1]
    if DEBUG_VERBOSE:
        print(f"[words_router] Top 5 predictions:")
        for rank, idx in enumerate(top_indices, 1):
            conf = float(prediction[idx])
            lbl = str(labels[idx])
            print(f"[words_router]   {rank}. {lbl:<20} conf={conf:.6f}")

    # ============================================================
    # 9. GET BEST PREDICTION
    # ============================================================
    class_id = int(np.argmax(prediction))
    label = str(labels[class_id])
    confidence = float(prediction[class_id])
    session['last_prediction_time'] = now

    if DEBUG_VERBOSE:
        print(f"\n[words_router] BEST PREDICTION:")
        print(f"[words_router] class_id={class_id}")
        print(f"[words_router] label={label}")
        print(f"[words_router] confidence={confidence:.6f}")
        print(f"[words_router] CONFIDENCE_THRESHOLD={CONFIDENCE_THRESHOLD}")

    session['current_label'] = label
    session['current_confidence'] = confidence

    # ============================================================
    # 10. APPLY THRESHOLD & DUPLICATE FILTER
    # ============================================================
    accepted = False
    now = time.time()
    
    if confidence >= CONFIDENCE_THRESHOLD:
        if DEBUG_VERBOSE:
            print(f"[words_router] Confidence {confidence:.6f} >= threshold {CONFIDENCE_THRESHOLD}")
        
        if label != session['last_accepted_word']:
            accepted = True
            if DEBUG_VERBOSE:
                print(f"[words_router] Label '{label}' != last '{session['last_accepted_word']}' -> ACCEPT")
        else:
            time_since_last = now - session['last_accepted_time']
            if time_since_last >= DUPLICATE_SILENCE_SECONDS:
                accepted = True
                if DEBUG_VERBOSE:
                    print(f"[words_router] Same label but {time_since_last:.2f}s since last -> ACCEPT (repeat)")
            else:
                if DEBUG_VERBOSE:
                    print(f"[words_router] Same label and only {time_since_last:.2f}s since last -> REJECT (duplicate)")
    else:
        if DEBUG_VERBOSE:
            print(f"[words_router] Confidence {confidence:.6f} < threshold {CONFIDENCE_THRESHOLD} -> REJECT")

    # ============================================================
    # 11. UPDATE SENTENCE
    # ============================================================
    if accepted:
        if not session['sentence'] or session['sentence'][-1] != label:
            session['sentence'].append(label)
            if DEBUG_VERBOSE:
                print(f"[words_router] Added '{label}' to sentence: {session['sentence']}")
        
        session['last_accepted_word'] = label
        session['last_accepted_time'] = now
        message = 'Word accepted'
    else:
        message = f'Below threshold ({confidence:.2f} < {CONFIDENCE_THRESHOLD})'

    if DEBUG_VERBOSE:
        print(f"[words_router] Final sentence: {' '.join(session['sentence'])}")
        print(f"[words_router] Message: {message}")
        print(f"[words_router] ========== PREDICTION END ==========\n")

    # ============================================================
    # 12. RETURN RESPONSE
    # ============================================================
    return JSONResponse(
        content={
            'success': True,
            'running': session['running'],
            'ready': True,
            'label': label if confidence >= 0.01 else '',
            'confidence': confidence,
            'accepted': accepted,
            'sentence': ' '.join(session['sentence']),
            'message': message,
            'frames_collected': buffer_len_after
        }
    )


@router.post('/reset_session')
async def reset_session(session_id: str = Form("default")):
    """Reset the frame buffer for a session."""
    if session_id in sessions:
        sessions[session_id]['sequence'].clear()
        sessions[session_id]['sentence'] = []
        sessions[session_id]['last_accepted_word'] = ''
        sessions[session_id]['last_accepted_time'] = 0.0
        sessions[session_id]['current_label'] = ''
        sessions[session_id]['current_confidence'] = 0.0
        sessions[session_id]['message'] = 'Reset'

    return JSONResponse(content={'success': True, 'session_id': session_id})


@router.get('/status')
async def status(session_id: str = "default"):
    """Get the current status of a session."""
    session = sessions[session_id]
    return JSONResponse(content={
        'success': True,
        'session_id': session_id,
        'frames_collected': len(session['sequence']),
        'running': session['running'],
        'message': session['message'],
        'current_label': session['current_label'],
        'current_confidence': session['current_confidence']
    })
