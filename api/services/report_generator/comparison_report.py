"""
Comparison Report Generator.
Compares two scans side-by-side to show changes.
"""
from typing import Dict, Any, List
from api.services.report_generator.base_report import BaseReport
from api.models.vulnerability import VulnerabilityInstance
from api.models.scan import Scan


class ComparisonReport(BaseReport):
    """Generate comparison reports between two scans."""
    
    def __init__(self, scan_a_id: int, scan_b_id: int):
        """
        Initialize comparison report.
        
        Args:
            scan_a_id: First scan ID (baseline)
            scan_b_id: Second scan ID (comparison)
        """
        super().__init__()
        self.scan_a_id = scan_a_id
        self.scan_b_id = scan_b_id
    
    def gather_data(self) -> Dict[str, Any]:
        """
        Gather data for comparison report.
        
        Returns:
            Dictionary with report data
        """
        # Get scans
        scan_a = Scan.query.get(self.scan_a_id)
        scan_b = Scan.query.get(self.scan_b_id)
        
        if not scan_a or not scan_b:
            raise ValueError("One or both scans not found")
        
        # Get vulnerabilities for each scan
        vulns_a = VulnerabilityInstance.query.filter_by(scan_id=self.scan_a_id).all()
        vulns_b = VulnerabilityInstance.query.filter_by(scan_id=self.scan_b_id).all()
        
        # Calculate comparison
        comparison = self._compare_scans(vulns_a, vulns_b)
        
        # Prepare vulnerability lists
        new_vulns = self._prepare_vuln_list(comparison['new'])
        fixed_vulns = self._prepare_vuln_list(comparison['fixed'])
        persistent_vulns = self._prepare_vuln_list(comparison['persistent'])
        
        # Generate recommendations
        recommendations = self._generate_comparison_recommendations(comparison)
        
        # Summary stats
        summary_stats = {
            'scan_a': {
                'id': scan_a.id,
                'date': self.format_date(scan_a.created_at),
                'total': len(vulns_a),
                'severity_counts': self.get_severity_counts(vulns_a)
            },
            'scan_b': {
                'id': scan_b.id,
                'date': self.format_date(scan_b.created_at),
                'total': len(vulns_b),
                'severity_counts': self.get_severity_counts(vulns_b)
            },
            'comparison': {
                'new': len(comparison['new']),
                'fixed': len(comparison['fixed']),
                'persistent': len(comparison['persistent']),
                'net_change': len(vulns_b) - len(vulns_a)
            }
        }
        
        return {
            'title': f'Scan Comparison Report: Scan #{scan_a.id} vs #{scan_b.id}',
            'generated_at': self.format_date(self.generated_at),
            'summary_stats': summary_stats,
            'new_vulnerabilities': new_vulns,
            'fixed_vulnerabilities': fixed_vulns,
            'persistent_vulnerabilities': persistent_vulns,
            'recommendations': recommendations,
            'report_type': 'comparison'
        }
    
    def _compare_scans(self, vulns_a: List, vulns_b: List) -> Dict:
        """Compare two sets of vulnerabilities."""
        # Create sets of vulnerability signatures (name + port)
        set_a = {(v.vulnerability.name, v.port or 'N/A'): v for v in vulns_a}
        set_b = {(v.vulnerability.name, v.port or 'N/A'): v for v in vulns_b}
        
        keys_a = set(set_a.keys())
        keys_b = set(set_b.keys())
        
        return {
            'new': [set_b[k] for k in (keys_b - keys_a)],  # In B but not in A
            'fixed': [set_a[k] for k in (keys_a - keys_b)],  # In A but not in B
            'persistent': [set_b[k] for k in (keys_a & keys_b)]  # In both
        }
    
    def _prepare_vuln_list(self, vuln_instances: List) -> List[Dict]:
        """Prepare vulnerability list for export."""
        vuln_list = []
        
        for vuln_instance in vuln_instances[:50]:  # Limit to 50
            vuln = vuln_instance.vulnerability
            scan = vuln_instance.scan
            target = scan.target if scan else None
            
            vuln_list.append({
                'id': vuln_instance.id,
                'name': vuln.name,
                'severity': vuln.severity,
                'cvss_score': vuln.cvss_score,
                'cve_id': vuln.cve_id,
                'target': target.ip_address if target else 'N/A',
                'port': vuln_instance.port or 'N/A',
                'status': vuln_instance.status or 'Open',
                'discovered_at': self.format_date(vuln_instance.discovered_at)
            })
        
        return vuln_list
    
    def _generate_comparison_recommendations(self, comparison: Dict) -> List[Dict]:
        """Generate recommendations based on comparison."""
        recommendations = []
        
        new_count = len(comparison['new'])
        fixed_count = len(comparison['fixed'])
        persistent_count = len(comparison['persistent'])
        
        if new_count > 0:
            recommendations.append({
                'priority': 'High',
                'vulnerability': f'{new_count} New Vulnerabilities Detected',
                'recommendation': 'Investigate and remediate newly discovered vulnerabilities immediately.'
            })
        
        if fixed_count > 0:
            recommendations.append({
                'priority': 'Low',
                'vulnerability': f'{fixed_count} Vulnerabilities Fixed',
                'recommendation': 'Good progress! Continue remediation efforts.'
            })
        
        if persistent_count > 0:
            recommendations.append({
                'priority': 'Medium',
                'vulnerability': f'{persistent_count} Persistent Vulnerabilities',
                'recommendation': 'These vulnerabilities remain unresolved. Prioritize remediation.'
            })
        
        # Overall assessment
        net_change = new_count - fixed_count
        if net_change > 0:
            recommendations.append({
                'priority': 'Critical',
                'vulnerability': 'Security Posture Declining',
                'recommendation': f'Net increase of {net_change} vulnerabilities. Increase remediation efforts.'
            })
        elif net_change < 0:
            recommendations.append({
                'priority': 'Info',
                'vulnerability': 'Security Posture Improving',
                'recommendation': f'Net decrease of {abs(net_change)} vulnerabilities. Maintain current efforts.'
            })
        
        return recommendations
