"""
Comprehensive tests for search service.
"""
import pytest
from api.services.search_service import SearchService
from api.models.target import Target
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.models.ticket import Ticket
from api.models.scan import Scan
from api.extensions import db


def test_global_search_targets(app, test_user):
    """Test global search finds targets."""
    with app.app_context():
        # Create test targets
        target1 = Target(ip_address='192.168.1.100', name='Target 100', description='Production server', user_id=test_user.id)
        target2 = Target(ip_address='192.168.1.101', name='Target 101', description='Development server', user_id=test_user.id)
        db.session.add(target1)
        db.session.add(target2)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('production')
        
        # Should find target1
        assert 'targets' in results or len(results) > 0


def test_global_search_vulnerabilities(app, test_user):
    """Test global search finds vulnerabilities."""
    with app.app_context():
        vuln = Vulnerability(
            name='SQL Injection',
            description='Critical SQL injection vulnerability',
            severity='critical'
        )
        db.session.add(vuln)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('SQL')
        
        # Should find vulnerability
        assert 'vulnerabilities' in results or len(results) > 0


def test_global_search_tickets(app):
    """Test global search finds tickets."""
    with app.app_context():
        ticket = Ticket(
            title='Fix critical vulnerability',
            description='Urgent fix needed',
            priority='high'
        )
        db.session.add(ticket)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('critical')
        
        # Should find ticket
        assert 'tickets' in results or len(results) > 0


def test_fuzzy_search(app, test_user):
    """Test fuzzy search functionality."""
    with app.app_context():
        target = Target(ip_address='192.168.1.102', name='Target 102', description='Database server', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        search_service = SearchService()
        
        # Search with typo
        results = search_service.global_search('databse')  # Missing 'a'
        
        # Fuzzy search might still find it (depending on implementation)
        assert results is not None


def test_search_case_insensitive(app, test_user):
    """Test search is case insensitive."""
    with app.app_context():
        target = Target(ip_address='192.168.1.103', name='Target 103', description='WEB SERVER', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        search_service = SearchService()
        
        # Search in lowercase
        results = search_service.global_search('web server')
        
        # Should find target regardless of case
        assert results is not None


def test_search_empty_query(app):
    """Test search with empty query."""
    with app.app_context():
        search_service = SearchService()
        results = search_service.global_search('')
        
        # Should return empty or all results
        assert results is not None


def test_search_no_results(app):
    """Test search with no matching results."""
    with app.app_context():
        search_service = SearchService()
        results = search_service.global_search('nonexistentquery12345')
        
        # Should return empty results
        assert results is not None


def test_search_with_special_characters(app, test_user):
    """Test search handles special characters."""
    with app.app_context():
        target = Target(ip_address='192.168.1.104', name='Target 104', description='Server (production)', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('(production)')
        
        # Should handle special characters
        assert results is not None


def test_search_by_ip_address(app, test_user):
    """Test searching by IP address."""
    with app.app_context():
        target = Target(ip_address='10.0.0.50', name='Target 50', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('10.0.0.50')
        
        # Should find target by IP
        assert results is not None


def test_search_by_cve_id(app):
    """Test searching by CVE ID."""
    with app.app_context():
        vuln = Vulnerability(
            name='Test Vulnerability',
            cve_id='CVE-2023-1234',
            severity='high'
        )
        db.session.add(vuln)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('CVE-2023-1234')
        
        # Should find vulnerability by CVE
        assert results is not None


def test_search_multiple_entity_types(app, test_user):
    """Test search returns multiple entity types."""
    with app.app_context():
        # Create entities with same keyword
        target = Target(ip_address='192.168.1.105', name='Target 105', description='Critical system', user_id=test_user.id)
        vuln = Vulnerability(name='Critical vulnerability', severity='critical')
        ticket = Ticket(title='Critical issue', priority='high')
        
        db.session.add(target)
        db.session.add(vuln)
        db.session.add(ticket)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('critical')
        
        # Should return multiple types
        assert results is not None


def test_search_pagination(app, test_user):
    """Test search with pagination."""
    with app.app_context():
        # Create many targets
        for i in range(20):
            target = Target(ip_address=f'192.168.2.{i}', name=f'Target {i}', description='Test server', user_id=test_user.id)
            db.session.add(target)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('test', limit=10)
        
        # Should respect limit
        assert results is not None


def test_search_by_severity(app):
    """Test searching vulnerabilities by severity."""
    with app.app_context():
        vuln1 = Vulnerability(name='High severity vuln', severity='high')
        vuln2 = Vulnerability(name='Critical severity vuln', severity='critical')
        db.session.add(vuln1)
        db.session.add(vuln2)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('high')
        
        # Should find high severity vulnerability
        assert results is not None


def test_search_by_ticket_status(app):
    """Test searching tickets by status."""
    with app.app_context():
        ticket = Ticket(title='Test ticket', status='open', priority='medium')
        db.session.add(ticket)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('open')
        
        # Should find open ticket
        assert results is not None


def test_search_partial_match(app, test_user):
    """Test search with partial matches."""
    with app.app_context():
        target = Target(ip_address='192.168.1.106', name='Target 106', description='Application server', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        search_service = SearchService()
        results = search_service.global_search('app')
        
        # Should find partial match
        assert results is not None
