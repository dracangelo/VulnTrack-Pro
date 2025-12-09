"""
Markdown exporter for reports.
Creates GitHub-flavored markdown reports.
"""
from typing import Dict, List, Any


class MarkdownExporter:
    """Export reports to Markdown format."""
    
    def export(self, data: Dict[str, Any]) -> str:
        """
        Export data to Markdown format.
        
        Args:
            data: Complete report data
            
        Returns:
            Markdown string
        """
        md = []
        
        # Title
        md.append(f"# {data.get('title', 'Vulnerability Report')}\n")
        md.append(f"**Generated:** {data.get('generated_at', 'N/A')}\n")
        md.append("---\n")
        
        # Executive Summary
        md.append("## Executive Summary\n")
        stats = data.get('summary_stats', {})
        md.append(f"- **Total Vulnerabilities:** {stats.get('total_vulnerabilities', 0)}")
        md.append(f"- **Critical & High:** {stats.get('critical_high_count', 0)}\n")
        
        # Severity Breakdown
        md.append("### Severity Breakdown\n")
        severity_counts = stats.get('severity_counts', {})
        severity_emojis = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'info': '🔵'
        }
        
        for severity, emoji in severity_emojis.items():
            count = severity_counts.get(severity, 0)
            md.append(f"- {emoji} **{severity.capitalize()}:** {count}")
        md.append("")
        
        # Vulnerabilities Table
        if 'vulnerabilities' in data and data['vulnerabilities']:
            md.append("## Vulnerability Details\n")
            md.append("| Name | Severity | CVSS | CVE | Target | Status |")
            md.append("|------|----------|------|-----|--------|--------|")
            
            for vuln in data['vulnerabilities']:
                severity_badge = self._get_severity_badge(vuln.get('severity', ''))
                md.append(
                    f"| {vuln.get('name', 'N/A')} | "
                    f"{severity_badge} | "
                    f"{vuln.get('cvss_score', 'N/A')} | "
                    f"{vuln.get('cve_id', 'N/A')} | "
                    f"{vuln.get('target', 'N/A')} | "
                    f"{vuln.get('status', 'Open')} |"
                )
            md.append("")
        
        # Recommendations
        if 'recommendations' in data and data['recommendations']:
            md.append("## Recommendations\n")
            md.append("| Priority | Vulnerability | Recommendation |")
            md.append("|----------|---------------|----------------|")
            
            for rec in data['recommendations']:
                md.append(
                    f"| {rec.get('priority', 'Medium')} | "
                    f"{rec.get('vulnerability', 'N/A')} | "
                    f"{rec.get('recommendation', 'N/A')} |"
                )
            md.append("")
        
        return "\n".join(md)
    
    def _get_severity_badge(self, severity: str) -> str:
        """Get GitHub-style badge for severity."""
        severity = severity.lower()
        badges = {
            'critical': '![Critical](https://img.shields.io/badge/Critical-red)',
            'high': '![High](https://img.shields.io/badge/High-orange)',
            'medium': '![Medium](https://img.shields.io/badge/Medium-yellow)',
            'low': '![Low](https://img.shields.io/badge/Low-green)',
            'info': '![Info](https://img.shields.io/badge/Info-blue)'
        }
        return badges.get(severity, severity.capitalize())
