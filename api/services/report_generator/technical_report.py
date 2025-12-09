"""
Technical Report Generator.
Creates detailed technical reports for security teams.
"""
from typing import Dict, Any
from api.services.report_generator.base_report import BaseReport


class TechnicalReport(BaseReport):
    """Generate detailed technical reports."""
    
    def gather_data(self) -> Dict[str, Any]:
        """
        Gather data for technical report.
        
        Returns:
            Dictionary with report data
        """
        vulnerabilities = self.get_vulnerabilities()
        summary_stats = self.get_summary_stats(vulnerabilities)
        
        # Prepare detailed vulnerability data
        vuln_list = []
        for vuln_instance in vulnerabilities:
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
                'discovered_at': self.format_date(vuln_instance.discovered_at),
                'description': vuln.description,
                'solution': vuln.solution
            })
        
        # Generate detailed recommendations
        recommendations = self._generate_technical_recommendations(vulnerabilities)
        
        return {
            'title': 'Technical Vulnerability Report',
            'generated_at': self.format_date(self.generated_at),
            'summary_stats': summary_stats,
            'vulnerabilities': vuln_list,
            'recommendations': recommendations,
            'report_type': 'technical'
        }
    
    def _generate_technical_recommendations(self, vulnerabilities) -> list:
        """Generate detailed technical recommendations."""
        recommendations = []
        top_vulns = self.get_top_vulnerabilities(vulnerabilities, limit=10)
        
        for vuln_group in top_vulns:
            vuln = vuln_group['vulnerability']
            count = vuln_group['count']
            
            # Use solution from vulnerability if available
            recommendation = vuln.solution or "Apply security patches and follow vendor guidelines."
            
            recommendations.append({
                'priority': vuln.severity.capitalize(),
                'vulnerability': f"{vuln.name} ({count} instance(s))",
                'recommendation': recommendation
            })
        
        return recommendations
