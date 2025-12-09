"""
Base report generator class.
Provides common functionality for all report types.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from api.extensions import db
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.models.scan import Scan
from api.models.target import Target


class BaseReport:
    """
    Base class for all report generators.
    """
    
    def __init__(self, filters: Optional[Dict[str, Any]] = None):
        """
        Initialize report generator.
        
        Args:
            filters: Dictionary of filters to apply
                - scan_ids: List of scan IDs
                - severity: List of severities
                - status: List of statuses
                - date_range: Dict with 'start' and 'end' dates
                - target_ids: List of target IDs
        """
        self.filters = filters or {}
        self.data = {}
        self.generated_at = datetime.utcnow()
    
    def gather_data(self):
        """Gather data for the report. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement gather_data()")
    
    def get_vulnerabilities(self) -> List[VulnerabilityInstance]:
        """
        Get vulnerabilities based on filters.
        
        Returns:
            List of vulnerability instances
        """
        query = VulnerabilityInstance.query
        
        # Apply filters
        if 'scan_ids' in self.filters:
            query = query.filter(VulnerabilityInstance.scan_id.in_(self.filters['scan_ids']))
        
        if 'severity' in self.filters:
            query = query.join(Vulnerability).filter(
                Vulnerability.severity.in_(self.filters['severity'])
            )
        
        if 'status' in self.filters:
            query = query.filter(VulnerabilityInstance.status.in_(self.filters['status']))
        
        if 'target_ids' in self.filters:
            query = query.join(Scan).filter(Scan.target_id.in_(self.filters['target_ids']))
        
        if 'date_range' in self.filters:
            date_range = self.filters['date_range']
            if 'start' in date_range:
                query = query.filter(VulnerabilityInstance.discovered_at >= date_range['start'])
            if 'end' in date_range:
                query = query.filter(VulnerabilityInstance.discovered_at <= date_range['end'])
        
        return query.all()
    
    def get_severity_counts(self, vulnerabilities: List[VulnerabilityInstance]) -> Dict[str, int]:
        """
        Count vulnerabilities by severity.
        
        Args:
            vulnerabilities: List of vulnerability instances
            
        Returns:
            Dictionary with severity counts
        """
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        
        for vuln_instance in vulnerabilities:
            severity = vuln_instance.vulnerability.severity.lower()
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    def get_status_counts(self, vulnerabilities: List[VulnerabilityInstance]) -> Dict[str, int]:
        """
        Count vulnerabilities by status.
        
        Args:
            vulnerabilities: List of vulnerability instances
            
        Returns:
            Dictionary with status counts
        """
        counts = {}
        
        for vuln_instance in vulnerabilities:
            status = vuln_instance.status or 'open'
            counts[status] = counts.get(status, 0) + 1
        
        return counts
    
    def get_top_vulnerabilities(self, vulnerabilities: List[VulnerabilityInstance], limit: int = 10) -> List[Dict]:
        """
        Get top vulnerabilities by severity and count.
        
        Args:
            vulnerabilities: List of vulnerability instances
            limit: Maximum number to return
            
        Returns:
            List of vulnerability summaries
        """
        # Group by vulnerability
        vuln_groups = {}
        for vuln_instance in vulnerabilities:
            vuln_id = vuln_instance.vulnerability_id
            if vuln_id not in vuln_groups:
                vuln_groups[vuln_id] = {
                    'vulnerability': vuln_instance.vulnerability,
                    'count': 0,
                    'instances': []
                }
            vuln_groups[vuln_id]['count'] += 1
            vuln_groups[vuln_id]['instances'].append(vuln_instance)
        
        # Sort by severity and count
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        sorted_vulns = sorted(
            vuln_groups.values(),
            key=lambda x: (
                severity_order.get(x['vulnerability'].severity.lower(), 5),
                -x['count']
            )
        )
        
        return sorted_vulns[:limit]
    
    def format_date(self, date: datetime) -> str:
        """Format datetime for display."""
        if not date:
            return 'N/A'
        return date.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def get_summary_stats(self, vulnerabilities: List[VulnerabilityInstance]) -> Dict[str, Any]:
        """
        Get summary statistics.
        
        Args:
            vulnerabilities: List of vulnerability instances
            
        Returns:
            Dictionary with summary statistics
        """
        severity_counts = self.get_severity_counts(vulnerabilities)
        status_counts = self.get_status_counts(vulnerabilities)
        
        return {
            'total_vulnerabilities': len(vulnerabilities),
            'severity_counts': severity_counts,
            'status_counts': status_counts,
            'critical_high_count': severity_counts['critical'] + severity_counts['high'],
            'generated_at': self.format_date(self.generated_at)
        }
