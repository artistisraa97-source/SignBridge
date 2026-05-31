from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from . import schemas, models, database, auth
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post('/signup')
def signup(payload: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # validate uniqueness
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = auth.get_password_hash(payload.password)
    user = models.User(name=payload.name.strip(), email=payload.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return JSONResponse({"success": True, "message": "Account created successfully"})


@router.post('/login')
def login(payload: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # create token with subject as user id
    token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = auth.create_access_token({"sub": str(user.id), "email": user.email}, expires_delta=token_expires)

    user_out = schemas.UserOut.from_orm(user)
    return {"success": True, "token": token, "user": user_out}


@router.get('/me')
def me(current_user: models.User = Depends(auth.get_current_user)):
    user_out = schemas.UserOut.from_orm(current_user)
    return {"success": True, "user": user_out}
