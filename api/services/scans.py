# api/services/scans.py

import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from scanners.nmap_scanner import NmapScanner
from core import models


class ScanService:

    @staticmethod
    def create_scan(db: Session, target_id: int, scan_type: str = "nmap") -> models.Scan:
        """
        Create a scan entry in the database.
        """
        scan = models.Scan(
            target_id=target_id,
            scan_type=scan_type,
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan

    @staticmethod
    async def run_scan(db: Session, scan: models.Scan):
        """
        Executes the scan asynchronously and stores results.
        """

        scan.status = "running"
        scan.started_at = datetime.utcnow()
        db.commit()

        target = db.query(models.Target).filter(models.Target.id == scan.target_id).first()
        if not target:
            scan.status = "error"
            db.commit()
            return

        # --- Run Nmap ---
        try:
            results = await NmapScanner.run_nmap(target.address)
        except Exception as exc:
            scan.status = "error"
            db.commit()
            print(f"[SCAN ERROR] {exc}")
            return

        # Update target basic info
        target.last_scanned = datetime.utcnow()
        target.os_detected = None  # Could integrate OS detection in future

        # Save vulnerabilities
        for vuln_dict in results.get("vulnerabilities", []):
            ScanService._store_vulnerability(db, scan, target, vuln_dict)

        scan.status = "finished"
        scan.finished_at = datetime.utcnow()
        db.commit()

    @staticmethod
    def _store_vulnerability(db: Session, scan: models.Scan, target: models.Target, vuln_dict: dict):
        """
        Stores a vulnerability + vulnerability instance into the DB.
        """

        unique_key = f"nmap_{target.id}_{vuln_dict['port']}_{vuln_dict['name']}"

        # Check if vulnerability profile exists
        vuln = db.query(models.Vulnerability).filter(
            models.Vulnerability.unique_key == unique_key
        ).first()

        if not vuln:
            vuln = models.Vulnerability(
                unique_key=unique_key,
                name=vuln_dict["name"],
                description=vuln_dict.get("description"),
                severity=vuln_dict.get("severity", "Low"),
                cvss_base=None,
                references=None,
            )
            db.add(vuln)
            db.commit()
            db.refresh(vuln)

        instance = models.VulnerabilityInstance(
            vulnerability_id=vuln.id,
            target_id=target.id,
            scan_id=scan.id,
            port=vuln_dict.get("port"),
            protocol=vuln_dict.get("protocol"),
            evidence=vuln_dict.get("evidence"),
            status="open",
            created_at=datetime.utcnow(),
        )

        db.add(instance)
        db.commit()

    @staticmethod
    def start_background_scan(db: Session, scan: models.Scan):
        """
        Spawns the async scan execution without blocking FastAPI.
        """
        asyncio.create_task(ScanService._background_task(db, scan.id))

    @staticmethod
    async def _background_task(db_session_factory, scan_id: int):
        """
        The real async task runner (fresh DB session for async context).
        """
        db: Session = db_session_factory()

        try:
            scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
            if scan:
                await ScanService.run_scan(db, scan)
        finally:
            db.close()
