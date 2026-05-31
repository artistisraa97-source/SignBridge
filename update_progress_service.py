from pathlib import Path

content = '''# Progress tracking services - per user

import json
import os

PROGRESS_FILE = 'progress.json'

def load_all_progress() -> dict:
    """Load all progress data."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_all_progress(data: dict):
    """Save all progress data."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_user_progress(user_email: str) -> dict:
    """Get progress data for a specific user."""
    all_progress = load_all_progress()
    if user_email not in all_progress:
        # Initialize default progress for new user
        all_progress[user_email] = {
            'total_lessons': 10,
            'completed_lessons': 0,
            'accuracy': 0.0,
            'streak': 0,
            'completed_words': [],
            'mastered_letters': [],
            'quiz_scores': [],
            'challenge_progress': {}
        }
        save_all_progress(all_progress)
    return all_progress[user_email]

def save_user_progress(user_email: str, progress: dict):
    """Save progress data for a specific user."""
    all_progress = load_all_progress()
    all_progress[user_email] = progress
    save_all_progress(all_progress)

def update_progress(user_email: str, lesson_id: int, completed: bool, accuracy: float):
    """Update progress for a lesson for a specific user."""
    progress = get_user_progress(user_email)
    if completed:
        progress['completed_lessons'] = min(progress['completed_lessons'] + 1, progress['total_lessons'])
    progress['accuracy'] = (progress['accuracy'] + accuracy) / 2  # Simple average
    if completed:
        progress['streak'] += 1
    else:
        progress['streak'] = 0
    save_user_progress(user_email, progress)
    return progress

def add_completed_word(user_email: str, word: str):
    """Mark a word as completed for a user."""
    progress = get_user_progress(user_email)
    if word not in progress['completed_words']:
        progress['completed_words'].append(word)
    save_user_progress(user_email, progress)
    return progress

def add_mastered_letter(user_email: str, letter: str):
    """Mark a letter as mastered for a user."""
    progress = get_user_progress(user_email)
    if letter not in progress['mastered_letters']:
        progress['mastered_letters'].append(letter)
    save_user_progress(user_email, progress)
    return progress

def add_quiz_score(user_email: str, score: float, total: int):
    """Add a quiz score for a user."""
    progress = get_user_progress(user_email)
    progress['quiz_scores'].append({'score': score, 'total': total, 'percentage': (score / total) * 100})
    save_user_progress(user_email, progress)
    return progress

def update_challenge_progress(user_email: str, challenge_id: str, progress_data: dict):
    """Update challenge progress for a user."""
    progress = get_user_progress(user_email)
    progress['challenge_progress'][challenge_id] = progress_data
    save_user_progress(user_email, progress)
    return progress
'''

Path('services/progress_service.py').write_text(content, encoding='utf-8')
print('✓ progress_service.py updated with user-based tracking')
