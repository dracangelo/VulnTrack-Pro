# api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from core.database import get_db
from core import models
from api.utils import verify_password, create_access_token, hash_password, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

@router.post("/register")
def register_user(user: dict, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user["email"]).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = models.User(
        username=user["username"],
        email=user.get("email"),
        password_hash=hash_password(user["password"])
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
