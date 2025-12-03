from api.extensions import db
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.models.scan import Scan
from api.services.vuln_parser import VulnParser
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

class VulnManager:
    def __init__(self):
        self.parser = VulnParser()

    def process_scan_results(self, scan_id):
        """
        Processes a completed scan, parses results, and updates the vulnerability database.
        """
        logger.info(f"Processing scan results for scan_id: {scan_id}")
        
        scan = Scan.query.get(scan_id)
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return
        
        if scan.status != 'completed':
            logger.warning(f"Scan {scan_id} status is '{scan.status}', expected 'completed'")
            return
        
        if not scan.raw_output:
            logger.warning(f"Scan {scan_id} has no raw_output")
            return

        try:
            scan_data = json.loads(scan.raw_output)
            logger.debug(f"Scan {scan_id} raw_output decoded successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode scan output for scan {scan_id}: {e}")
            return

        vulnerabilities = []
        if scan.scan_type == 'nmap':
            # Handle both old format (list) and new format (dict with 'results' key)
            if isinstance(scan_data, dict) and 'results' in scan_data:
                results = scan_data['results']
                logger.debug(f"Scan {scan_id} using new format with 'results' key: {len(results)} items")
            elif isinstance(scan_data, list):
                results = scan_data
                logger.debug(f"Scan {scan_id} using old list format: {len(results)} items")
            else:
                results = []
                logger.warning(f"Scan {scan_id} has unexpected data format: {type(scan_data)}")
            
            vulnerabilities = self.parser.parse_nmap_results(results)
            logger.info(f"Scan {scan_id} parsed {len(vulnerabilities)} vulnerabilities from Nmap results")
        elif scan.scan_type == 'openvas':
            # OpenVAS results are already parsed
            vulnerabilities = scan_data.get('vulnerabilities', [])
            logger.info(f"Scan {scan_id} extracted {len(vulnerabilities)} vulnerabilities from OpenVAS results")
        else:
            logger.warning(f"Scan {scan_id} has unknown scan_type: {scan.scan_type}")
        
        # Track vulnerability counts
        vuln_breakdown = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0,
            'Info': 0
        }
        
        created_count = 0
        for vuln_dict in vulnerabilities:
            try:
                self._create_or_update_vuln(vuln_dict, scan)
                created_count += 1
                
                # Update breakdown
                severity = vuln_dict.get('severity', 'Info')
                if severity in vuln_breakdown:
                    vuln_breakdown[severity] += 1
            except Exception as e:
                logger.error(f"Error creating vulnerability for scan {scan_id}: {e}", exc_info=True)
        
        # Update scan with vulnerability counts
        scan.vuln_count = len(vulnerabilities)
        scan.vuln_breakdown = vuln_breakdown
        db.session.commit()
        
        logger.info(f"Scan {scan_id} processing complete: {created_count}/{len(vulnerabilities)} vulnerabilities created. Breakdown: {vuln_breakdown}")


    def _create_or_update_vuln(self, vuln_dict, scan):
        """
        Create or update vulnerability definition and create instance.
        """
        # Extract CVSS score if available
        cvss_score = vuln_dict.get('cvss_score')
        
        # Calculate severity from CVSS if not provided
        severity = vuln_dict.get('severity')
        if not severity and cvss_score is not None:
            severity = Vulnerability.calculate_severity_from_cvss(cvss_score)
        elif not severity:
            severity = 'Info'
        
        # 1. Find or Create Vulnerability Definition
        # Try to find by CVE ID first, then by name
        vuln_def = None
        cve_id = vuln_dict.get('cve_id')
        
        if cve_id:
            vuln_def = Vulnerability.query.filter_by(cve_id=cve_id).first()
        
        if not vuln_def:
            vuln_def = Vulnerability.query.filter_by(name=vuln_dict['name']).first()
        
        if not vuln_def:
            vuln_def = Vulnerability(
                name=vuln_dict['name'],
                description=vuln_dict.get('description', ''),
                severity=severity,
                cve_id=cve_id,
                cvss_score=cvss_score,
                cvss_vector=vuln_dict.get('cvss_vector'),
                remediation=vuln_dict.get('remediation', ''),
                category=vuln_dict.get('category'),
                references=vuln_dict.get('references')
            )
            db.session.add(vuln_def)
            db.session.flush()  # Get ID without committing
        else:
            # Update existing vulnerability if we have better data
            if cvss_score and not vuln_def.cvss_score:
                vuln_def.cvss_score = cvss_score
                vuln_def.severity = severity
            if vuln_dict.get('cvss_vector') and not vuln_def.cvss_vector:
                vuln_def.cvss_vector = vuln_dict.get('cvss_vector')
        
        # 2. Create Vulnerability Instance
        # Check if this exact instance already exists for this scan
        existing_instance = VulnerabilityInstance.query.filter_by(
            vulnerability_id=vuln_def.id,
            scan_id=scan.id,
            target_id=scan.target_id,
            port=vuln_dict.get('port'),
            protocol=vuln_dict.get('protocol')
        ).first()
        
        if not existing_instance:
            instance = VulnerabilityInstance(
                vulnerability_id=vuln_def.id,
                scan_id=scan.id,
                target_id=scan.target_id,
                status='open',
                port=vuln_dict.get('port'),
                protocol=vuln_dict.get('protocol'),
                service=vuln_dict.get('service'),
                evidence=vuln_dict.get('evidence')
            )
            db.session.add(instance)
        
        db.session.commit()
    
    def get_vulnerabilities_by_severity(self, target_id=None):
        """
        Get vulnerability counts grouped by severity.
        Optionally filter by target.
        """
        # Use COALESCE to handle NULL severities (treat as 'Info')
        query = db.session.query(
            db.func.coalesce(Vulnerability.severity, 'Info').label('severity'),
            db.func.count(VulnerabilityInstance.id).label('count')
        ).join(
            VulnerabilityInstance, 
            VulnerabilityInstance.vulnerability_id == Vulnerability.id
        )
        
        if target_id:
            query = query.filter(VulnerabilityInstance.target_id == target_id)
        
        query = query.filter(VulnerabilityInstance.status == 'open')
        query = query.group_by(db.func.coalesce(Vulnerability.severity, 'Info'))
        
        results = query.all()
        
        severity_counts = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0,
            'Info': 0
        }
        
        for severity, count in results:
            # Normalize severity to match expected values
            if severity:
                severity = severity.strip()
                if severity in severity_counts:
                    severity_counts[severity] = count
                else:
                    # If severity doesn't match expected values, default to Info
                    severity_counts['Info'] += count
            else:
                severity_counts['Info'] += count
        
        return severity_counts
    
    def get_top_vulnerable_hosts(self, limit=10):
        """
        Get the top N most vulnerable hosts.
        Includes hosts with vulnerabilities and recently scanned hosts with 0 vulnerabilities.
        """
        from api.models.target import Target
        from api.models.scan import Scan
        
        # Get hosts with vulnerabilities
        results = db.session.query(
            VulnerabilityInstance.target_id,
            db.func.count(VulnerabilityInstance.id).label('vuln_count')
        ).filter(
            VulnerabilityInstance.status == 'open'
        ).group_by(
            VulnerabilityInstance.target_id
        ).order_by(
            db.desc('vuln_count')
        ).all()
        
        # Create a dict of target_id -> count
        vuln_counts = {target_id: count for target_id, count in results}
        
        # Get all targets that have been scanned (have at least one completed scan)
        scanned_targets = db.session.query(
            Scan.target_id
        ).filter(
            Scan.status == 'completed'
        ).distinct().all()
        
        scanned_target_ids = {target_id for (target_id,) in scanned_targets}
        
        # Combine: hosts with vulnerabilities + recently scanned hosts with 0 vulnerabilities
        all_target_ids = set(vuln_counts.keys()) | scanned_target_ids
        
        hosts = []
        for target_id in all_target_ids:
            target = Target.query.get(target_id)
            if target:
                count = vuln_counts.get(target_id, 0)
                hosts.append({
                    'id': target.id,
                    'name': target.name,
                    'ip_address': target.ip_address,
                    'count': count
                })
        
        # Sort by count (descending) and limit
        hosts.sort(key=lambda x: x['count'], reverse=True)
        return hosts[:limit]

