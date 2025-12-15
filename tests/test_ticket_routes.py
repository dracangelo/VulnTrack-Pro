"""
Comprehensive tests for ticket routes API endpoints.
"""
import pytest
from api.models.ticket import Ticket
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.models.target import Target
from api.models.scan import Scan
from api.extensions import db


def test_get_tickets_empty(client):
    """Test getting tickets when none exist."""
    response = client.get('/api/tickets/')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_create_ticket_basic(client):
    """Test creating a basic ticket."""
    ticket_data = {
        'title': 'Fix Critical Vulnerability',
        'description': 'SQL Injection found in login form',
        'priority': 'high'
    }
    response = client.post('/api/tickets/', json=ticket_data)
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['message'] == 'Ticket created'
    
    # Verify ticket was created
    ticket = Ticket.query.get(data['id'])
    assert ticket is not None
    assert ticket.title == 'Fix Critical Vulnerability'
    assert ticket.priority == 'high'


def test_create_ticket_missing_title(client):
    """Test creating ticket without title fails."""
    ticket_data = {'description': 'No title'}
    response = client.post('/api/tickets/', json=ticket_data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_create_ticket_with_assignee(client, test_user):
    """Test creating ticket with assignee."""
    ticket_data = {
        'title': 'Assigned Ticket',
        'description': 'Test ticket',
        'priority': 'medium',
        'assignee_id': test_user.id
    }
    response = client.post('/api/tickets/', json=ticket_data)
    assert response.status_code == 201
    data = response.get_json()
    
    ticket = Ticket.query.get(data['id'])
    assert ticket.assignee_id == test_user.id


def test_get_ticket_details(client):
    """Test getting ticket details."""
    ticket = Ticket(
        title='Test Ticket',
        description='Test description',
        priority='high',
        status='open'
    )
    db.session.add(ticket)
    db.session.commit()
    
    response = client.get(f'/api/tickets/{ticket.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == ticket.id
    assert data['title'] == 'Test Ticket'
    assert data['description'] == 'Test description'
    assert data['priority'] == 'high'
    assert data['status'] == 'open'
    assert 'created_at' in data
    assert 'updated_at' in data
    assert 'vulnerabilities' in data


def test_get_ticket_not_found(client):
    """Test getting non-existent ticket."""
    response = client.get('/api/tickets/99999')
    assert response.status_code == 404


def test_update_ticket_title(client):
    """Test updating ticket title."""
    ticket = Ticket(title='Old Title', priority='low')
    db.session.add(ticket)
    db.session.commit()
    
    update_data = {'title': 'New Title'}
    response = client.put(f'/api/tickets/{ticket.id}', json=update_data)
    assert response.status_code == 200
    
    ticket = Ticket.query.get(ticket.id)
    assert ticket.title == 'New Title'


def test_update_ticket_status(client):
    """Test updating ticket status."""
    ticket = Ticket(title='Status Test', status='open', priority='medium')
    db.session.add(ticket)
    db.session.commit()
    
    update_data = {'status': 'in_progress'}
    response = client.put(f'/api/tickets/{ticket.id}', json=update_data)
    assert response.status_code == 200
    
    ticket = Ticket.query.get(ticket.id)
    assert ticket.status == 'in_progress'


def test_update_ticket_priority(client):
    """Test updating ticket priority."""
    ticket = Ticket(title='Priority Test', priority='low')
    db.session.add(ticket)
    db.session.commit()
    
    update_data = {'priority': 'critical'}
    response = client.put(f'/api/tickets/{ticket.id}', json=update_data)
    assert response.status_code == 200
    
    ticket = Ticket.query.get(ticket.id)
    assert ticket.priority == 'critical'


def test_update_ticket_assignee(client, test_user):
    """Test updating ticket assignee."""
    ticket = Ticket(title='Assignee Test', priority='medium')
    db.session.add(ticket)
    db.session.commit()
    
    update_data = {'assignee_id': test_user.id}
    response = client.put(f'/api/tickets/{ticket.id}', json=update_data)
    assert response.status_code == 200
    
    ticket = Ticket.query.get(ticket.id)
    assert ticket.assignee_id == test_user.id


def test_update_ticket_multiple_fields(client, test_user):
    """Test updating multiple ticket fields at once."""
    ticket = Ticket(
        title='Multi Update',
        description='Old description',
        status='open',
        priority='low'
    )
    db.session.add(ticket)
    db.session.commit()
    
    update_data = {
        'title': 'Updated Title',
        'description': 'New description',
        'status': 'resolved',
        'priority': 'high',
        'assignee_id': test_user.id
    }
    response = client.put(f'/api/tickets/{ticket.id}', json=update_data)
    assert response.status_code == 200
    
    ticket = Ticket.query.get(ticket.id)
    assert ticket.title == 'Updated Title'
    assert ticket.description == 'New description'
    assert ticket.status == 'resolved'
    assert ticket.priority == 'high'
    assert ticket.assignee_id == test_user.id


def test_update_ticket_not_found(client):
    """Test updating non-existent ticket."""
    update_data = {'title': 'New Title'}
    response = client.put('/api/tickets/99999', json=update_data)
    assert response.status_code == 404


def test_delete_ticket(client):
    """Test deleting a ticket."""
    ticket = Ticket(title='Delete Me', priority='low')
    db.session.add(ticket)
    db.session.commit()
    ticket_id = ticket.id
    
    response = client.delete(f'/api/tickets/{ticket_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'deleted' in data['message'].lower()
    
    # Verify ticket was deleted
    ticket = Ticket.query.get(ticket_id)
    assert ticket is None


def test_delete_ticket_not_found(client):
    """Test deleting non-existent ticket."""
    response = client.delete('/api/tickets/99999')
    assert response.status_code == 404


def test_bind_vulnerabilities(client, test_user):
    """Test binding vulnerabilities to ticket."""
    # Create ticket
    ticket = Ticket(title='Bind Test', priority='high')
    db.session.add(ticket)
    
    # Create target and scan
    target = Target(ip_address='192.168.1.100', name='Target 100', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    # Create vulnerability and instance
    vuln = Vulnerability(
        name='SQL Injection',
        severity='critical',
        cve_id='CVE-2023-1234'
    )
    db.session.add(vuln)
    db.session.flush()
    
    vuln_instance = VulnerabilityInstance(
        vulnerability_id=vuln.id,
        target_id=target.id,
        scan_id=scan.id,
        status='open'
    )
    db.session.add(vuln_instance)
    db.session.commit()
    
    # Bind vulnerability to ticket
    bind_data = {'vuln_ids': [vuln_instance.id]}
    response = client.post(f'/api/tickets/{ticket.id}/bind', json=bind_data)
    assert response.status_code == 200
    
    # Verify binding
    ticket = Ticket.query.get(ticket.id)
    assert len(ticket.vulnerabilities) == 1
    assert ticket.vulnerabilities[0].id == vuln_instance.id


def test_bind_vulnerabilities_missing_vuln_ids(client):
    """Test binding without vuln_ids fails."""
    ticket = Ticket(title='Bind Fail', priority='medium')
    db.session.add(ticket)
    db.session.commit()
    
    response = client.post(f'/api/tickets/{ticket.id}/bind', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_bind_multiple_vulnerabilities(client, test_user):
    """Test binding multiple vulnerabilities to ticket."""
    # Create ticket
    ticket = Ticket(title='Multi Bind', priority='high')
    db.session.add(ticket)
    
    # Create target and scan
    target = Target(ip_address='192.168.1.101', name='Target 101', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_full', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    # Create multiple vulnerabilities
    vuln_instances = []
    for i in range(3):
        vuln = Vulnerability(
            name=f'Vulnerability {i}',
            severity='high',
            cve_id=f'CVE-2023-{1000+i}'
        )
        db.session.add(vuln)
        db.session.flush()
        
        vuln_instance = VulnerabilityInstance(
            vulnerability_id=vuln.id,
            target_id=target.id,
            scan_id=scan.id,
            status='open'
        )
        db.session.add(vuln_instance)
        db.session.flush()
        vuln_instances.append(vuln_instance.id)
    
    db.session.commit()
    
    # Bind all vulnerabilities
    bind_data = {'vuln_ids': vuln_instances}
    response = client.post(f'/api/tickets/{ticket.id}/bind', json=bind_data)
    assert response.status_code == 200
    
    # Verify all were bound
    ticket = Ticket.query.get(ticket.id)
    assert len(ticket.vulnerabilities) == 3


def test_create_ticket_from_vuln(client, test_user):
    """Test creating ticket from vulnerability (one-click)."""
    # Create target and scan
    target = Target(ip_address='192.168.1.102', name='Target 102', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    # Create vulnerability
    vuln = Vulnerability(
        name='XSS Vulnerability',
        severity='high',
        cve_id='CVE-2023-5678'
    )
    db.session.add(vuln)
    db.session.flush()
    
    vuln_instance = VulnerabilityInstance(
        vulnerability_id=vuln.id,
        target_id=target.id,
        scan_id=scan.id,
        status='open'
    )
    db.session.add(vuln_instance)
    db.session.commit()
    
    # Create ticket from vulnerability
    ticket_data = {
        'title': 'Fix XSS Vulnerability',
        'description': 'XSS found in search form',
        'priority': 'high',
        'vuln_instance_id': vuln_instance.id
    }
    response = client.post('/api/tickets/create-from-vuln', json=ticket_data)
    assert response.status_code == 201
    data = response.get_json()
    assert 'ticket_id' in data
    assert 'ticket' in data
    assert data['ticket']['vuln_count'] == 1
    
    # Verify ticket and binding
    ticket = Ticket.query.get(data['ticket_id'])
    assert ticket is not None
    assert ticket.title == 'Fix XSS Vulnerability'
    assert len(ticket.vulnerabilities) == 1
    assert ticket.vulnerabilities[0].id == vuln_instance.id


def test_create_ticket_from_vuln_missing_fields(client):
    """Test creating ticket from vuln without required fields fails."""
    ticket_data = {'title': 'Missing vuln_instance_id'}
    response = client.post('/api/tickets/create-from-vuln', json=ticket_data)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_create_ticket_from_vuln_not_found(client):
    """Test creating ticket from non-existent vulnerability fails."""
    ticket_data = {
        'title': 'Test Ticket',
        'vuln_instance_id': 99999
    }
    response = client.post('/api/tickets/create-from-vuln', json=ticket_data)
    assert response.status_code == 404
    data = response.get_json()
    assert 'not found' in data['error'].lower()


def test_get_tickets_with_vuln_count(client, test_user):
    """Test that ticket list includes vulnerability count."""
    # Create ticket with vulnerabilities
    ticket = Ticket(title='Count Test', priority='medium')
    db.session.add(ticket)
    
    target = Target(ip_address='192.168.1.103', name='Target 103', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    # Add 2 vulnerabilities
    for i in range(2):
        vuln = Vulnerability(name=f'Vuln {i}', severity='medium')
        db.session.add(vuln)
        db.session.flush()
        
        vuln_instance = VulnerabilityInstance(
            vulnerability_id=vuln.id,
            target_id=target.id,
            scan_id=scan.id,
            status='open'
        )
        db.session.add(vuln_instance)
        db.session.flush()
        ticket.vulnerabilities.append(vuln_instance)
    
    db.session.commit()
    
    response = client.get('/api/tickets/')
    assert response.status_code == 200
    data = response.get_json()
    
    # Find our ticket
    our_ticket = next((t for t in data if t['id'] == ticket.id), None)
    assert our_ticket is not None
    assert our_ticket['vuln_count'] == 2
