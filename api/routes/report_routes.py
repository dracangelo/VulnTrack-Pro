# api/routes/report_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core import models
from api.utils import require_auth

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{scan_id}")
def generate_report(scan_id: int, db: Session = Depends(get_db), user=Depends(require_auth)):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    vulnerabilities = db.query(models.VulnerabilityInstance).filter(
        models.VulnerabilityInstance.scan_id == scan.id
    ).all()

    return {"scan": scan, "vulnerabilities": vulnerabilities}
