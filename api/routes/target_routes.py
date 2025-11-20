# api/routes/target_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from api.utils import require_auth

router = APIRouter(prefix="/targets", tags=["Targets"])

@router.post("/")
def create_target(target: dict, db: Session = Depends(get_db), user=Depends(require_auth)):
    new_target = models.Target(
        name=target.get("name"),
        address=target.get("address"),
        group_id=target.get("group_id"),
        tags=target.get("tags"),
        os_detected=target.get("os_detected")
    )
    db.add(new_target)
    db.commit()
    db.refresh(new_target)
    return {"message": "Target created", "target_id": new_target.id}

@router.get("/")
def list_targets(db: Session = Depends(get_db), user=Depends(require_auth)):
    targets = db.query(models.Target).all()
    return {"targets": targets}

@router.get("/{target_id}")
def get_target(target_id: int, db: Session = Depends(get_db), user=Depends(require_auth)):
    target = db.query(models.Target).filter(models.Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target

@router.put("/{target_id}")
def update_target(target_id: int, payload: dict, db: Session = Depends(get_db), user=Depends(require_auth)):
    target = db.query(models.Target).filter(models.Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    for key, value in payload.items():
        setattr(target, key, value)
    db.commit()
    db.refresh(target)
    return {"message": "Updated", "target": target}

@router.delete("/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db), user=Depends(require_auth)):
    target = db.query(models.Target).filter(models.Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
    return {"message": "Deleted"}
