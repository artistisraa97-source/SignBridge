"""compare_debug_features.py

Compare saved debug feature arrays and frames between two capture sources.
Usage:
  python tools/compare_debug_features.py --dirA debug/realtime --dirB debug/words

The script pairs files by session and nearest timestamp and reports mean absolute
and relative differences. It also tests whether images are mirrored (horizontal
flip) or channel-swapped (BGR<->RGB) between the two sources.
"""

import argparse
import glob
import os
import re
import numpy as np
import cv2
from math import inf

FEATURE_RE = re.compile(r'features_(?P<session>[^_]+)_(?P<ts>\d+)\.npy$')
FRAME_RE = re.compile(r'frame_(?P<session>[^_]+)_(?P<ts>\d+)\.jpg$')


def index_files(dir_path, pattern):
    files = glob.glob(os.path.join(dir_path, pattern))
    index = {}
    for f in files:
        name = os.path.basename(f)
        m = FEATURE_RE.match(name) if 'features_' in name else FRAME_RE.match(name)
        if not m:
            continue
        sess = m.group('session')
        ts = int(m.group('ts'))
        index.setdefault(sess, []).append((ts, f))
    # sort timestamp lists
    for sess in index:
        index[sess].sort()
    return index


def find_closest(ts_list, target_ts):
    # ts_list is list of (ts, path)
    best = None
    best_delta = inf
    for ts, path in ts_list:
        delta = abs(ts - target_ts)
        if delta < best_delta:
            best_delta = delta
            best = (ts, path)
    return best, best_delta


def compare_features(pathA, pathB):
    a = np.load(pathA)
    b = np.load(pathB)
    if a.shape != b.shape:
        return {'shapeA': a.shape, 'shapeB': b.shape}
    diff = np.abs(a - b)
    return {
        'shape': a.shape,
        'mean_abs': float(np.mean(diff)),
        'median_abs': float(np.median(diff)),
        'max_abs': float(np.max(diff)),
        'mean_rel': float(np.mean(diff) / (np.mean(np.abs(a)) + 1e-12))
    }


def mse_image(a, b):
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    return float(np.mean((a - b) ** 2))


def compare_images(pathA, pathB):
    a = cv2.imread(pathA)
    b = cv2.imread(pathB)
    if a is None or b is None:
        return {'error': 'unable to read images'}
    if a.shape != b.shape:
        # try resizing b to a
        b_resized = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_LINEAR)
    else:
        b_resized = b
    # plain mse
    mse_plain = mse_image(a, b_resized)
    # flipped mse
    mse_flip = mse_image(a, cv2.flip(b_resized, 1))
    # channel-swapped mse (BGR<->RGB)
    mse_swap = mse_image(a, b_resized[..., ::-1])
    return {
        'shapeA': a.shape,
        'shapeB': b.shape,
        'mse_plain': mse_plain,
        'mse_flip': mse_flip,
        'mse_swap': mse_swap,
        'flip_better': mse_flip < mse_plain,
        'swap_better': mse_swap < mse_plain
    }


def main(dirA, dirB, max_delta_ms=1000):
    featA = index_files(dirA, 'features_*.npy')
    featB = index_files(dirB, 'features_*.npy')
    frameA = index_files(dirA, 'frame_*.jpg')
    frameB = index_files(dirB, 'frame_*.jpg')

    sessions = set(list(featA.keys()) + list(featB.keys()))
    if not sessions:
        print('No feature files found in either directory. Check paths and debug saving.')
        return

    print(f'Comparing features between {dirA} and {dirB}')
    summary = []
    for sess in sessions:
        listA = featA.get(sess, [])
        listB = featB.get(sess, [])
        if not listA or not listB:
            print(f'  session {sess}: missing in one side (A:{len(listA)} B:{len(listB)})')
            continue
        for tsA, pathA in listA:
            (tsB, pathB), delta = find_closest(listB, tsA)
            if delta > max_delta_ms:
                print(f'  session {sess} ts {tsA} no close match in B (closest {tsB}, delta {delta}ms)')
                continue
            res = compare_features(pathA, pathB)
            print(f'  session {sess} tsA={tsA} tsB={tsB} delta={delta}ms -> {res}')
            summary.append((sess, tsA, tsB, delta, res))

    # Image comparisons
    print('\nImage comparisons (detect mirror/channel differences):')
    image_sessions = set(list(frameA.keys()) + list(frameB.keys()))
    for sess in image_sessions:
        listA = frameA.get(sess, [])
        listB = frameB.get(sess, [])
        if not listA or not listB:
            print(f'  session {sess}: missing frames on one side')
            continue
        for tsA, pA in listA:
            (tsB, pB), delta = find_closest(listB, tsA)
            if delta > max_delta_ms:
                continue
            r = compare_images(pA, pB)
            print(f'  image session {sess} tsA={tsA} tsB={tsB} delta={delta}ms -> mse_plain={r.get("mse_plain"):.1f} mse_flip={r.get("mse_flip"):.1f} mse_swap={r.get("mse_swap"):.1f} flip_better={r.get("flip_better")} swap_better={r.get("swap_better")}')

    print('\nDone.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--dirA', required=False, default='debug/realtime', help='First debug folder (realtime)')
    p.add_argument('--dirB', required=False, default='debug/words', help='Second debug folder (fastapi)')
    p.add_argument('--max-delta-ms', type=int, default=1000, help='Max timestamp delta to pair files (ms)')
    args = p.parse_args()
    main(args.dirA, args.dirB, max_delta_ms=args.max_delta_ms)
