from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from services.progress_service import (
    get_user_progress,
    update_progress,
    add_completed_word,
    add_mastered_letter,
    add_quiz_score,
    update_challenge_progress
)
from auth.auth import get_current_user
from auth.models import User

router = APIRouter()

@router.get('/api/progress/me')
async def get_progress_me(current_user: User = Depends(get_current_user)):
    """Get current user progress."""
    progress = get_user_progress(current_user.email)
    return JSONResponse(content={"success": True, "progress": progress})

@router.post('/api/progress/update')
async def update_progress_endpoint(
    lesson_id: int,
    completed: bool,
    accuracy: float,
    current_user: User = Depends(get_current_user)
):
    """Update progress for current user."""
    progress = update_progress(current_user.email, lesson_id, completed, accuracy)
    return JSONResponse(content={"success": True, "progress": progress})

@router.post('/api/progress/word')
async def add_word_completion(
    word: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a word as completed for current user."""
    progress = add_completed_word(current_user.email, word)
    return JSONResponse(content={"success": True, "progress": progress})

@router.post('/api/progress/letter')
async def add_letter_mastery(
    letter: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a letter as mastered for current user."""
    progress = add_mastered_letter(current_user.email, letter)
    return JSONResponse(content={"success": True, "progress": progress})

@router.post('/api/progress/quiz')
async def add_quiz_result(
    score: float,
    total: int,
    current_user: User = Depends(get_current_user)
):
    """Add quiz result for current user."""
    progress = add_quiz_score(current_user.email, score, total)
    return JSONResponse(content={"success": True, "progress": progress})

@router.post('/api/progress/challenge')
async def update_challenge(
    challenge_id: str,
    progress_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Update challenge progress for current user."""
    progress = update_challenge_progress(current_user.email, challenge_id, progress_data)
    return JSONResponse(content={"success": True, "progress": progress})
