from api.extensions import db
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.models.scan import Scan
from api.services.vuln_parser import VulnParser
import json

class VulnManager:
    def __init__(self):
        self.parser = VulnParser()

    def process_scan_results(self, scan_id):
        """
        Processes a completed scan, parses results, and updates the vulnerability database.
        """
        scan = Scan.query.get(scan_id)
        if not scan or scan.status != 'completed' or not scan.raw_output:
            return

        try:
            scan_data = json.loads(scan.raw_output)
        except json.JSONDecodeError:
            print(f"Failed to decode scan output for scan {scan_id}")
            return

        vulnerabilities = []
        if scan.scan_type == 'nmap':
            vulnerabilities = self.parser.parse_nmap_results(scan_data)
        # Add other types here
        
        for vuln_dict in vulnerabilities:
            self._create_or_update_vuln(vuln_dict, scan)

    def _create_or_update_vuln(self, vuln_dict, scan):
        # 1. Find or Create Vulnerability Definition
        # Deduplicate by name for now (or cve_id if available)
        vuln_def = Vulnerability.query.filter_by(name=vuln_dict['name']).first()
        
        if not vuln_def:
            vuln_def = Vulnerability(
                name=vuln_dict['name'],
                description=vuln_dict['description'],
                severity=vuln_dict['severity'],
                cve_id=vuln_dict['cve_id'],
                remediation=vuln_dict['remediation']
            )
            db.session.add(vuln_def)
            db.session.commit() # Commit to get ID
        
        # 2. Create Vulnerability Instance
        # Check if instance already exists for this target and vuln (maybe from previous scan?)
        # Actually, we want to track instances per scan, OR track current state of target.
        # The prompt says "VulnerabilityInstance mapping: target_id, vuln_id, scan_id, status".
        # So we create a new instance for this scan.
        
        instance = VulnerabilityInstance(
            vulnerability_id=vuln_def.id,
            scan_id=scan.id,
            target_id=scan.target_id,
            status='open'
        )
        db.session.add(instance)
        db.session.commit()
