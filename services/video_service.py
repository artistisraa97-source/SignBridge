# Video processing services

import os
import subprocess
from werkzeug.utils import secure_filename

VIDEOS_DIR = os.path.join('assets', 'videos')
WORDS_COMBINE_DIR = os.path.join(VIDEOS_DIR, 'words_combinations')
COMBINE_OUTPUT_FILE = os.path.join(VIDEOS_DIR, 'final_translation.mp4')

def combine_videos(sentence: str) -> dict:
    """Combine video clips for the given sentence."""
    words = [word.strip().lower() for word in sentence.split() if word.strip()]
    if not words:
        return {'success': False, 'message': 'Empty sentence', 'error': 'Empty sentence'}

    video_files = []
    missing_words = []
    matched_videos = []
    for word in words:
        clean_word = ''.join(c for c in word if c.isalnum())
        if not clean_word:
            continue

        video_filename = f'{secure_filename(clean_word)}.mp4'
        video_path = os.path.join(WORDS_COMBINE_DIR, video_filename)
        if os.path.exists(video_path):
            video_files.append(video_path)
            matched_videos.append(video_filename)
        else:
            missing_words.append(clean_word)

    print('Requested words:', words)
    print('Matched videos:', matched_videos)
    print('Missing words:', missing_words)

    if not video_files:
        error_msg = f'No videos found for: {", ".join(missing_words)}' if missing_words else 'No matching videos'
        return {
            'success': False,
            'message': error_msg,
            'error': error_msg,
            'matched_videos': matched_videos,
            'missing_words': missing_words
        }

    concat_file = 'temp_concat.txt'
    with open(concat_file, 'w', encoding='utf-8') as f:
        for video in video_files:
            absolute_path = os.path.abspath(video)
            f.write(f"file '{absolute_path}'\n")

    result = subprocess.run([
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c', 'copy',
        '-y', COMBINE_OUTPUT_FILE
    ], capture_output=True, text=True, timeout=60)

    if os.path.exists(concat_file):
        os.remove(concat_file)

    if result.returncode != 0 or not os.path.exists(COMBINE_OUTPUT_FILE):
        error_msg = f'Video generation failed: {result.stderr[:200]}' if result.stderr else 'FFmpeg error'
        return {
            'success': False,
            'message': error_msg,
            'error': error_msg,
            'matched_videos': matched_videos,
            'missing_words': missing_words
        }

    return {
        'success': True,
        'message': 'Video generated successfully',
        'video_url': '/assets/videos/final_translation.mp4',
        'sentence': ' '.join(words),
        'missing_words': missing_words,
        'matched_videos': matched_videos
    }