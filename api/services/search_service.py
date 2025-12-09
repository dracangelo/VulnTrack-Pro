"""
Search Service.
Handles global search across multiple entities and advanced filtering.
"""
from api.models.target import Target
from api.models.scan import Scan
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.models.ticket import Ticket
from api.extensions import db
from sqlalchemy import or_

class SearchService:
    """
    Service for performing global searches and advanced filtering.
    """

    @staticmethod
    def global_search(query_text, limit=10):
        """
        Perform a global search across Targets, Scans, Vulnerabilities, and Tickets.
        
        Args:
            query_text: The search string.
            limit: Max results per category.
            
        Returns:
            Dictionary with results grouped by category.
        """
        if not query_text:
            return {}

        search_term = f"%{query_text}%"
        results = {
            'targets': [],
            'scans': [],
            'vulnerabilities': [],
            'tickets': []
        }

        # Search Targets
        targets = Target.query.filter(
            or_(
                Target.name.ilike(search_term),
                Target.ip_address.ilike(search_term),
                Target.description.ilike(search_term)
            )
        ).limit(limit).all()
        
        results['targets'] = [{
            'id': t.id,
            'name': t.name,
            'ip_address': t.ip_address,
            'type': 'target'
        } for t in targets]

        # Search Scans (by ID or Target Name)
        # Note: Searching by ID if query is numeric
        scan_query = Scan.query.join(Target).filter(
            or_(
                Target.name.ilike(search_term),
                Target.ip_address.ilike(search_term)
            )
        )
        
        if query_text.isdigit():
            scan_query = Scan.query.filter(Scan.id == int(query_text))
            
        scans = scan_query.limit(limit).all()
        results['scans'] = [{
            'id': s.id,
            'target_name': s.target.name,
            'status': s.status,
            'created_at': s.created_at.isoformat(),
            'type': 'scan'
        } for s in scans]

        # Search Vulnerabilities (Definitions)
        vulns = Vulnerability.query.filter(
            or_(
                Vulnerability.name.ilike(search_term),
                Vulnerability.cve_id.ilike(search_term),
                Vulnerability.description.ilike(search_term)
            )
        ).limit(limit).all()
        
        results['vulnerabilities'] = [{
            'id': v.id,
            'name': v.name,
            'severity': v.severity,
            'cve_id': v.cve_id,
            'type': 'vulnerability'
        } for v in vulns]

        # Search Tickets
        tickets = Ticket.query.filter(
            or_(
                Ticket.title.ilike(search_term),
                Ticket.description.ilike(search_term)
            )
        ).limit(limit).all()
        
        results['tickets'] = [{
            'id': t.id,
            'title': t.title,
            'status': t.status,
            'priority': t.priority,
            'type': 'ticket'
        } for t in tickets]

        return results
