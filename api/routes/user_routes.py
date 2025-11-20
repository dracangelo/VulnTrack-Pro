# api/routes/user_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from api.utils import require_auth

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
def list_users(db: Session = Depends(get_db), user=Depends(require_auth)):
    users = db.query(models.User).all()
    return {"users": users}

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), user=Depends(require_auth)):
    user_obj = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return user_obj
