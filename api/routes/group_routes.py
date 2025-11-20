# api/routes/group_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from api.utils import require_auth

router = APIRouter(prefix="/groups", tags=["Target Groups"])

@router.post("/")
def create_group(group: dict, db: Session = Depends(get_db), user=Depends(require_auth)):
    new_group = models.TargetGroup(
        name=group["name"],
        description=group.get("description")
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return {"message": "Group created", "group_id": new_group.id}

@router.get("/")
def list_groups(db: Session = Depends(get_db), user=Depends(require_auth)):
    groups = db.query(models.TargetGroup).all()
    return {"groups": groups}
