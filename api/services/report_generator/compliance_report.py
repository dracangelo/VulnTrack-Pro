"""
Compliance Report Generator.
Creates compliance-focused reports for PCI-DSS, HIPAA, and SOC 2.
"""
from typing import Dict, Any
from api.services.report_generator.base_report import BaseReport


class ComplianceReport(BaseReport):
    """Generate compliance reports for various standards."""
    
    COMPLIANCE_STANDARDS = {
        'pci-dss': 'PCI-DSS v4.0',
        'hipaa': 'HIPAA Security Rule',
        'soc2': 'SOC 2 Type II'
    }
    
    # PCI-DSS Requirements mapping
    PCI_DSS_REQUIREMENTS = {
        'critical': 'Requirement 6.2 - Critical Security Patches',
        'high': 'Requirement 6.1 - Security Vulnerabilities',
        'medium': 'Requirement 11.2 - Vulnerability Scans',
        'network': 'Requirement 1 - Firewall Configuration',
        'access': 'Requirement 7 - Access Control',
        'encryption': 'Requirement 4 - Encryption'
    }
    
    # HIPAA Security Rule mapping
    HIPAA_REQUIREMENTS = {
        'critical': '§164.308(a)(1)(ii)(A) - Risk Analysis',
        'high': '§164.308(a)(5)(ii)(B) - Protection from Malicious Software',
        'medium': '§164.312(a)(1) - Access Control',
        'encryption': '§164.312(a)(2)(iv) - Encryption',
        'audit': '§164.312(b) - Audit Controls'
    }
    
    # SOC 2 Trust Service Criteria
    SOC2_CRITERIA = {
        'critical': 'CC7.1 - System Monitoring',
        'high': 'CC7.2 - Threat Detection',
        'medium': 'CC6.1 - Logical Access Controls',
        'availability': 'A1.2 - System Availability',
        'confidentiality': 'C1.1 - Confidential Information'
    }
    
    def __init__(self, filters: Dict[str, Any] = None, compliance_standard: str = 'pci-dss'):
        """
        Initialize compliance report.
        
        Args:
            filters: Standard filters
            compliance_standard: 'pci-dss', 'hipaa', or 'soc2'
        """
        super().__init__(filters)
        self.compliance_standard = compliance_standard.lower()
        
        if self.compliance_standard not in self.COMPLIANCE_STANDARDS:
            raise ValueError(f"Invalid compliance standard: {compliance_standard}")
    
    def gather_data(self) -> Dict[str, Any]:
        """
        Gather data for compliance report.
        
        Returns:
            Dictionary with report data
        """
        vulnerabilities = self.get_vulnerabilities()
        summary_stats = self.get_summary_stats(vulnerabilities)
        
        # Map vulnerabilities to compliance requirements
        compliance_mapping = self._map_to_compliance(vulnerabilities)
        
        # Prepare vulnerability data
        vuln_list = []
        for vuln_instance in vulnerabilities:
            vuln = vuln_instance.vulnerability
            scan = vuln_instance.scan
            target = scan.target if scan else None
            
            # Get compliance requirement
            requirement = self._get_compliance_requirement(vuln.severity.lower())
            
            vuln_list.append({
                'id': vuln_instance.id,
                'name': vuln.name,
                'severity': vuln.severity,
                'cvss_score': vuln.cvss_score,
                'cve_id': vuln.cve_id,
                'target': target.ip_address if target else 'N/A',
                'port': vuln_instance.port or 'N/A',
                'status': vuln_instance.status or 'Open',
                'discovered_at': self.format_date(vuln_instance.detected_at),
                'compliance_requirement': requirement
            })
        
        # Generate compliance-specific recommendations
        recommendations = self._generate_compliance_recommendations(compliance_mapping)
        
        standard_name = self.COMPLIANCE_STANDARDS[self.compliance_standard]
        
        return {
            'title': f'{standard_name} Compliance Report',
            'generated_at': self.format_date(self.generated_at),
            'summary_stats': summary_stats,
            'vulnerabilities': vuln_list,
            'recommendations': recommendations,
            'compliance_standard': standard_name,
            'compliance_mapping': compliance_mapping,
            'report_type': 'compliance'
        }
    
    def _map_to_compliance(self, vulnerabilities) -> Dict[str, int]:
        """Map vulnerabilities to compliance requirements."""
        mapping = {}
        
        if self.compliance_standard == 'pci-dss':
            requirements = self.PCI_DSS_REQUIREMENTS
        elif self.compliance_standard == 'hipaa':
            requirements = self.HIPAA_REQUIREMENTS
        else:  # soc2
            requirements = self.SOC2_CRITERIA
        
        for vuln_instance in vulnerabilities:
            severity = vuln_instance.vulnerability.severity.lower()
            req = requirements.get(severity, requirements.get('medium'))
            mapping[req] = mapping.get(req, 0) + 1
        
        return mapping
    
    def _get_compliance_requirement(self, severity: str) -> str:
        """Get compliance requirement for a severity level."""
        if self.compliance_standard == 'pci-dss':
            requirements = self.PCI_DSS_REQUIREMENTS
        elif self.compliance_standard == 'hipaa':
            requirements = self.HIPAA_REQUIREMENTS
        else:  # soc2
            requirements = self.SOC2_CRITERIA
        
        return requirements.get(severity, requirements.get('medium', 'General Security'))
    
    def _generate_compliance_recommendations(self, compliance_mapping) -> list:
        """Generate compliance-specific recommendations."""
        recommendations = []
        
        for requirement, count in sorted(compliance_mapping.items(), key=lambda x: -x[1])[:10]:
            if self.compliance_standard == 'pci-dss':
                action = f"Address {count} finding(s) to maintain PCI-DSS compliance."
            elif self.compliance_standard == 'hipaa':
                action = f"Remediate {count} issue(s) to meet HIPAA Security Rule requirements."
            else:  # soc2
                action = f"Resolve {count} control gap(s) for SOC 2 certification."
            
            recommendations.append({
                'priority': 'High' if count > 5 else 'Medium',
                'vulnerability': requirement,
                'recommendation': action
            })
        
        return recommendations
