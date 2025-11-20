from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.scan import Scan
from models.target import Target
from schemas.scan import ScanCreate, ScanResponse
from services.scan_service import start_scan_service, get_scan_by_id, get_scans_by_target

router = APIRouter(prefix="/scans", tags=["Scans"])

# -------------------------------------------------
# Start a new scan
# -------------------------------------------------
@router.post("/start", response_model=ScanResponse)
def start_scan(scan_data: ScanCreate, db: Session = Depends(get_db)):
    # Validate target exists
    target = db.query(Target).filter(Target.id == scan_data.target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Start the scan using the service layer
    scan = start_scan_service(db, scan_data.target_id)
    return scan


# -------------------------------------------------
# Get scan details by scan ID
# -------------------------------------------------
@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = get_scan_by_id(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


# -------------------------------------------------
# Get all scans for a specific target
# -------------------------------------------------
@router.get("/target/{target_id}", response_model=List[ScanResponse])
def scans_for_target(target_id: int, db: Session = Depends(get_db)):
    # Validate target exists
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    return get_scans_by_target(db, target_id)
