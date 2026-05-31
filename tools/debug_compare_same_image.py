import cv2
import numpy as np
from pathlib import Path
import os
import sys

sys.path.insert(0, os.getcwd())

from realtime import extract_keypoints as rt_extract
from translator_model_loader import extract_keypoints as tr_extract

path = Path('debug/realtime/frame_11c4bbcf-d4ed-4d83-a176-c08576c336e4_1779220494560.jpg')
frame = cv2.imread(str(path))
if frame is None:
    raise SystemExit(f'failed to load {path}')
print('frame shape', frame.shape)
ret, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
if not ret:
    raise SystemExit('encode failed')
decoded = cv2.imdecode(np.frombuffer(buf.tobytes(), np.uint8), cv2.IMREAD_COLOR)
print('decoded shape', decoded.shape)
print('mse_plain', float(np.mean((frame.astype(np.float32) - decoded.astype(np.float32)) ** 2)))
print('mse_flip', float(np.mean((frame.astype(np.float32) - cv2.flip(decoded, 1).astype(np.float32)) ** 2)))
print('mse_swap', float(np.mean((frame.astype(np.float32) - decoded[..., ::-1].astype(np.float32)) ** 2)))
rt = rt_extract(frame)
tr = tr_extract(frame)
print('rt shape', rt.shape, 'tr shape', tr.shape)
print('rt all_zero', bool(np.all(rt == 0)), 'tr all_zero', bool(np.all(tr == 0)))
d = np.abs(rt - tr)
print('feat diff mean', float(np.mean(d)))
print('feat diff median', float(np.median(d)))
print('feat diff max', float(np.max(d)))
print('feat mean rt', float(np.mean(rt)), 'feat mean tr', float(np.mean(tr)))
print('first 10 rt', rt[:10])
print('first 10 tr', tr[:10])
