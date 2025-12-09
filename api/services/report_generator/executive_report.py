"""
Executive Summary Report Generator.
Creates high-level reports for management with charts and key metrics.
"""
from typing import Dict, Any, Optional
from api.services.report_generator.base_report import BaseReport


class ExecutiveReport(BaseReport):
    """Generate executive summary reports."""
    
    def gather_data(self) -> Dict[str, Any]:
        """
        Gather data for executive summary report.
        
        Returns:
            Dictionary with report data
        """
        vulnerabilities = self.get_vulnerabilities()
        summary_stats = self.get_summary_stats(vulnerabilities)
        top_vulns = self.get_top_vulnerabilities(vulnerabilities, limit=5)
        
        # Prepare vulnerability data for export
        vuln_list = []
        for vuln_group in top_vulns:
            vuln = vuln_group['vulnerability']
            vuln_list.append({
                'id': vuln.id,
                'name': vuln.name,
                'severity': vuln.severity,
                'cvss_score': vuln.cvss_score,
                'cve_id': vuln.cve_id,
                'count': vuln_group['count'],
                'target': f"{vuln_group['count']} target(s)",
                'status': 'Open',
                'discovered_at': self.format_date(self.generated_at)
            })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(top_vulns)
        
        return {
            'title': 'Executive Summary - Vulnerability Report',
            'generated_at': self.format_date(self.generated_at),
            'summary_stats': summary_stats,
            'vulnerabilities': vuln_list,
            'recommendations': recommendations,
            'report_type': 'executive'
        }
    
    def _generate_recommendations(self, top_vulns) -> list:
        """Generate priority recommendations."""
        recommendations = []
        
        for vuln_group in top_vulns[:5]:
            vuln = vuln_group['vulnerability']
            priority = vuln.severity.capitalize()
            
            # Generic recommendations based on severity
            if vuln.severity.lower() == 'critical':
                rec = f"Immediate action required. Patch or mitigate within 24 hours."
            elif vuln.severity.lower() == 'high':
                rec = f"High priority. Address within 7 days."
            else:
                rec = f"Schedule remediation in next maintenance window."
            
            recommendations.append({
                'priority': priority,
                'vulnerability': vuln.name,
                'recommendation': rec
            })
        
        return recommendations
