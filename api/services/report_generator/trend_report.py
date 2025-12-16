"""
Trend Analysis Report Generator.
Analyzes vulnerability trends over time.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from api.services.report_generator.base_report import BaseReport
from api.models.vulnerability import VulnerabilityInstance
from sqlalchemy import func


class TrendReport(BaseReport):
    """Generate trend analysis reports."""
    
    def __init__(self, filters: Dict[str, Any] = None, period_days: int = 30):
        """
        Initialize trend report.
        
        Args:
            filters: Standard filters
            period_days: Number of days to analyze (default: 30)
        """
        super().__init__(filters)
        self.period_days = period_days
    
    def gather_data(self) -> Dict[str, Any]:
        """
        Gather data for trend analysis report.
        
        Returns:
            Dictionary with report data
        """
        # Get vulnerabilities for the period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.period_days)
        
        # Update filters to include date range
        if 'date_range' not in self.filters:
            self.filters['date_range'] = {}
        self.filters['date_range']['start'] = start_date
        self.filters['date_range']['end'] = end_date
        
        vulnerabilities = self.get_vulnerabilities()
        summary_stats = self.get_summary_stats(vulnerabilities)
        
        # Calculate trends
        trend_data = self._calculate_trends(vulnerabilities, start_date, end_date)
        
        # Prepare vulnerability data (top 20 recent)
        vuln_list = []
        for vuln_instance in vulnerabilities[:20]:
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
                'discovered_at': self.format_date(vuln_instance.detected_at)
            })
        
        # Generate trend-based recommendations
        recommendations = self._generate_trend_recommendations(trend_data)
        
        return {
            'title': f'Vulnerability Trend Analysis ({self.period_days} days)',
            'generated_at': self.format_date(self.generated_at),
            'summary_stats': summary_stats,
            'vulnerabilities': vuln_list,
            'recommendations': recommendations,
            'trend_data': trend_data,
            'period_days': self.period_days,
            'report_type': 'trend'
        }
    
    def _calculate_trends(self, vulnerabilities: List, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate vulnerability trends over time."""
        # Group by week
        weeks = defaultdict(lambda: {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0, 'total': 0})
        
        for vuln_instance in vulnerabilities:
            discovered = vuln_instance.detected_at
            if not discovered:
                continue
            
            # Calculate week number
            week_start = discovered - timedelta(days=discovered.weekday())
            week_key = week_start.strftime('%Y-W%U')
            
            severity = vuln_instance.vulnerability.severity.lower()
            weeks[week_key][severity] += 1
            weeks[week_key]['total'] += 1
        
        # Convert to sorted list
        trend_timeline = []
        for week_key in sorted(weeks.keys()):
            trend_timeline.append({
                'week': week_key,
                **weeks[week_key]
            })
        
        # Calculate overall trend (increasing/decreasing/stable)
        if len(trend_timeline) >= 2:
            first_half = sum(w['total'] for w in trend_timeline[:len(trend_timeline)//2])
            second_half = sum(w['total'] for w in trend_timeline[len(trend_timeline)//2:])
            
            if second_half > first_half * 1.2:
                trend_direction = 'increasing'
            elif second_half < first_half * 0.8:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'timeline': trend_timeline,
            'trend_direction': trend_direction,
            'total_period': len(vulnerabilities),
            'avg_per_week': len(vulnerabilities) / max(len(trend_timeline), 1)
        }
    
    def _generate_trend_recommendations(self, trend_data: Dict) -> List[Dict]:
        """Generate recommendations based on trends."""
        recommendations = []
        
        direction = trend_data['trend_direction']
        avg_per_week = trend_data['avg_per_week']
        
        if direction == 'increasing':
            recommendations.append({
                'priority': 'Critical',
                'vulnerability': 'Increasing Vulnerability Trend',
                'recommendation': f'Vulnerabilities are increasing ({avg_per_week:.1f}/week average). Immediate action required to improve security posture.'
            })
        elif direction == 'decreasing':
            recommendations.append({
                'priority': 'Low',
                'vulnerability': 'Decreasing Vulnerability Trend',
                'recommendation': f'Positive trend: vulnerabilities decreasing ({avg_per_week:.1f}/week average). Continue current remediation efforts.'
            })
        else:
            recommendations.append({
                'priority': 'Medium',
                'vulnerability': 'Stable Vulnerability Trend',
                'recommendation': f'Vulnerabilities remain stable ({avg_per_week:.1f}/week average). Increase remediation efforts to reduce overall count.'
            })
        
        return recommendations
