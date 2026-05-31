import traceback
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from . import schemas, models, database, auth
from . import email_utils
from datetime import timedelta, datetime
import hashlib
import random

router = APIRouter(tags=["auth"])


@router.post('/signup', status_code=201)
def signup(payload: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        active_user = db.query(models.User).filter(models.User.email == payload.email).first()
        if active_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # generate 6-digit code
        code = f"{random.randint(0, 999999):06d}"
        # store hashed code
        hashed_code = hashlib.sha256(code.encode('utf-8')).hexdigest()
        expires = datetime.utcnow() + timedelta(minutes=10)

        hashed = auth.get_password_hash(payload.password)
        pending = db.query(models.PendingUser).filter(models.PendingUser.email == payload.email).first()
        if pending:
            pending.first_name = payload.first_name.strip()
            pending.last_name = payload.last_name.strip()
            pending.hashed_password = hashed
            pending.verification_code = hashed_code
            pending.verification_expires = expires
            db.add(pending)
        else:
            pending = models.PendingUser(
                first_name=payload.first_name.strip(),
                last_name=payload.last_name.strip(),
                email=payload.email,
                hashed_password=hashed,
                verification_code=hashed_code,
                verification_expires=expires,
            )
            db.add(pending)

        db.flush()
        sent = email_utils.send_verification_email(pending.email, code)
        if not sent:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to send verification email')

        db.commit()
        return JSONResponse({"success": True, "message": "Signup pending verification. Check your email for the code."})
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)},
        )


@router.post('/login')
def login(payload: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not getattr(user, 'is_verified', False):
        raise HTTPException(status_code=403, detail="Please verify your email first.")

    token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = auth.create_access_token({"sub": str(user.id), "email": user.email}, expires_delta=token_expires)
    user_out = schemas.UserOut.from_orm(user)
    return {"success": True, "token": token, "user": user_out}


@router.get('/me')
def me(current_user: models.User = Depends(auth.get_current_user)):
    user_out = schemas.UserOut.from_orm(current_user)
    return {"success": True, "user": user_out}


@router.delete('/delete-me')
def delete_me(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db.delete(current_user)
    db.commit()
    return {"success": True, "message": "User account deleted successfully."}


@router.post('/verify')
def verify(payload: schemas.VerifyRequest, db: Session = Depends(database.get_db)):
    pending = db.query(models.PendingUser).filter(models.PendingUser.email == payload.email).first()
    if not pending:
        raise HTTPException(status_code=404, detail='No pending signup found for this email')
    if datetime.utcnow() > pending.verification_expires:
        raise HTTPException(status_code=400, detail='Verification code expired')

    provided_hash = hashlib.sha256(payload.code.encode('utf-8')).hexdigest()
    if provided_hash != pending.verification_code:
        raise HTTPException(status_code=400, detail='Invalid verification code')

    active_user = db.query(models.User).filter(models.User.email == pending.email).first()
    if active_user:
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail='An active account already exists for this email')

    user = models.User(
        first_name=pending.first_name,
        last_name=pending.last_name,
        email=pending.email,
        hashed_password=pending.hashed_password,
        is_verified=True,
        verification_code=None,
        verification_expires=None,
    )
    db.add(user)
    db.delete(pending)
    db.commit()
    return {"success": True, "message": "Email verified successfully"}


@router.post('/resend-code')
def resend_code(payload: schemas.ResendRequest, db: Session = Depends(database.get_db)):
    pending = db.query(models.PendingUser).filter(models.PendingUser.email == payload.email).first()
    if not pending:
        active_user = db.query(models.User).filter(models.User.email == payload.email).first()
        if active_user:
            return {"success": True, "message": "User already verified"}
        raise HTTPException(status_code=404, detail='No pending signup found; please sign up first')

    code = f"{random.randint(0, 999999):06d}"
    hashed_code = hashlib.sha256(code.encode('utf-8')).hexdigest()
    expires = datetime.utcnow() + timedelta(minutes=10)
    pending.verification_code = hashed_code
    pending.verification_expires = expires
    db.add(pending)
    db.flush()

    sent = email_utils.send_verification_email(pending.email, code)
    if not sent:
        db.rollback()
        raise HTTPException(status_code=500, detail='Failed to send verification email')

    db.commit()
    return {"success": True, "message": "Verification code resent"}
