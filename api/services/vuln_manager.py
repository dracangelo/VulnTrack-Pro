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
        elif scan.scan_type == 'openvas':
            # OpenVAS results are already parsed
            vulnerabilities = scan_data.get('vulnerabilities', [])
        # Add other types here
        
        # Track vulnerability counts
        vuln_breakdown = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0,
            'Info': 0
        }
        
        for vuln_dict in vulnerabilities:
            self._create_or_update_vuln(vuln_dict, scan)
            
            # Update breakdown
            severity = vuln_dict.get('severity', 'Info')
            if severity in vuln_breakdown:
                vuln_breakdown[severity] += 1
        
        # Update scan with vulnerability counts
        scan.vuln_count = len(vulnerabilities)
        scan.vuln_breakdown = vuln_breakdown
        db.session.commit()

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
        query = db.session.query(
            Vulnerability.severity,
            db.func.count(VulnerabilityInstance.id)
        ).join(VulnerabilityInstance)
        
        if target_id:
            query = query.filter(VulnerabilityInstance.target_id == target_id)
        
        query = query.filter(VulnerabilityInstance.status == 'open')
        query = query.group_by(Vulnerability.severity)
        
        results = query.all()
        
        severity_counts = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0,
            'Info': 0
        }
        
        for severity, count in results:
            if severity in severity_counts:
                severity_counts[severity] = count
        
        return severity_counts
    
    def get_top_vulnerable_hosts(self, limit=10):
        """
        Get the top N most vulnerable hosts.
        """
        results = db.session.query(
            VulnerabilityInstance.target_id,
            db.func.count(VulnerabilityInstance.id).label('vuln_count')
        ).filter(
            VulnerabilityInstance.status == 'open'
        ).group_by(
            VulnerabilityInstance.target_id
        ).order_by(
            db.desc('vuln_count')
        ).limit(limit).all()
        
        from api.models.target import Target
        hosts = []
        for target_id, count in results:
            target = Target.query.get(target_id)
            if target:
                hosts.append({
                    'id': target.id,
                    'name': target.name,
                    'ip_address': target.ip_address,
                    'count': count
                })
        
        return hosts

