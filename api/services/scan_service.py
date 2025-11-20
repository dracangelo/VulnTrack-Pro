from sqlalchemy.orm import Session
from models.scan import Scan
from datetime import datetime

# -------------------------------------------------
# Start a new scan
# -------------------------------------------------
def start_scan_service(db: Session, target_id: int) -> Scan:
    scan = Scan(target_id=target_id, status="queued")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # In the future: trigger Celery / task queue here
    # For now: simulate the scan task
    return run_scan(db, scan.id)


# -------------------------------------------------
# Simulated scan execution
# -------------------------------------------------
def run_scan(db: Session, scan_id: int) -> Scan:
    scan = db.query(Scan).filter(Scan.id == scan_id).first()

    if not scan:
        return None

    scan.status = "running"
    db.commit()

    # Simulate scan result
    scan.result = f"Scan for target {scan.target_id} completed successfully."
    scan.status = "completed"
    scan.finished_at = datetime.utcnow()

    db.commit()
    db.refresh(scan)
    
    return scan


# -------------------------------------------------
# Get scan by ID
# -------------------------------------------------
def get_scan_by_id(db: Session, scan_id: int) -> Scan:
    return db.query(Scan).filter(Scan.id == scan_id).first()


# -------------------------------------------------
# Get all scans for a target
# -------------------------------------------------
def get_scans_by_target(db: Session, target_id: int):
    return (
        db.query(Scan)
        .filter(Scan.target_id == target_id)
        .order_by(Scan.created_at.desc())
        .all()
    )
