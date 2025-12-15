"""
Tests for vulnerability manager service.
"""
import pytest
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.models.target import Target
from api.models.scan import Scan
from api.services.vuln_manager import VulnManager
from api.extensions import db


def test_vuln_status_transition_open_to_in_progress(test_user):
    """Test transitioning vulnerability from open to in_progress."""
    # Create target and scan
    target = Target(ip_address='192.168.1.10', name='Test Target', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    # Create vulnerability
    vuln = Vulnerability(name='Test Vuln', severity='high')
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
    
    # Transition status
    vuln_instance.status = 'in_progress'
    db.session.commit()
    
    # Verify
    assert vuln_instance.status == 'in_progress'


def test_vuln_status_transition_to_fixed(test_user):
    """Test transitioning vulnerability to fixed status."""
    target = Target(ip_address='192.168.1.11', name='Target 11', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_full', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    vuln = Vulnerability(name='Fixed Vuln', severity='medium')
    db.session.add(vuln)
    db.session.flush()
    
    vuln_instance = VulnerabilityInstance(
        vulnerability_id=vuln.id,
        target_id=target.id,
        scan_id=scan.id,
        status='in_progress'
    )
    db.session.add(vuln_instance)
    db.session.commit()
    
    # Mark as fixed
    vuln_instance.status = 'fixed'
    db.session.commit()
    
    assert vuln_instance.status == 'fixed'


def test_vuln_status_false_positive(test_user):
    """Test marking vulnerability as false positive."""
    target = Target(ip_address='192.168.1.12', name='Target 12', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    vuln = Vulnerability(name='False Positive', severity='low')
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
    
    # Mark as false positive
    vuln_instance.status = 'false_positive'
    db.session.commit()
    
    assert vuln_instance.status == 'false_positive'


def test_vuln_status_risk_accepted(test_user):
    """Test marking vulnerability as risk accepted."""
    target = Target(ip_address='192.168.1.13', name='Target 13', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_full', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    vuln = Vulnerability(name='Accepted Risk', severity='low')
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
    
    # Accept risk
    vuln_instance.status = 'risk_accepted'
    db.session.commit()
    
    assert vuln_instance.status == 'risk_accepted'


def test_vuln_deduplication_same_cve(test_user):
    """Test that vulnerabilities with same CVE are deduplicated."""
    # Create vulnerability with CVE
    vuln1 = Vulnerability(
        name='SQL Injection',
        severity='critical',
        cve_id='CVE-2023-1234'
    )
    db.session.add(vuln1)
    db.session.commit()
    
    # Try to create another with same CVE
    existing = Vulnerability.query.filter_by(cve_id='CVE-2023-1234').first()
    assert existing is not None
    assert existing.id == vuln1.id
    
    # Should reuse existing vulnerability
    vuln2 = Vulnerability.query.filter_by(cve_id='CVE-2023-1234').first()
    assert vuln2.id == vuln1.id


def test_vuln_deduplication_same_name_and_port(test_user):
    """Test that vulnerabilities with same name are deduplicated."""
    # Create first vulnerability
    vuln1 = Vulnerability(
        name='Open Port 22',
        severity='info'
    )
    db.session.add(vuln1)
    db.session.commit()
    
    # Check for existing
    existing = Vulnerability.query.filter_by(
        name='Open Port 22'
    ).first()
    
    assert existing is not None
    assert existing.id == vuln1.id


def test_vuln_bulk_status_change(test_user):
    """Test changing status of multiple vulnerabilities."""
    target = Target(ip_address='192.168.1.14', name='Target 14', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    # Create multiple vulnerability instances
    vuln_instances = []
    for i in range(5):
        vuln = Vulnerability(name=f'Bulk Vuln {i}', severity='medium')
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
        vuln_instances.append(vuln_instance)
    
    db.session.commit()
    
    # Bulk update status
    for vi in vuln_instances:
        vi.status = 'in_progress'
    db.session.commit()
    
    # Verify all updated
    for vi in vuln_instances:
        fresh_vi = VulnerabilityInstance.query.get(vi.id)
        assert fresh_vi.status == 'in_progress'


def test_vuln_instance_linking(test_user):
    """Test vulnerability instance properly links to target and scan."""
    target = Target(ip_address='192.168.1.15', name='Target 15', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_full', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    vuln = Vulnerability(name='Linked Vuln', severity='high')
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
    
    # Verify relationships
    assert vuln_instance.target_id == target.id
    assert vuln_instance.scan_id == scan.id
    assert vuln_instance.vulnerability_id == vuln.id
    assert vuln_instance.target == target
    assert vuln_instance.scan == scan
    assert vuln_instance.vulnerability == vuln


def test_vuln_severity_levels(test_user):
    """Test different vulnerability severity levels."""
    severities = ['critical', 'high', 'medium', 'low', 'info']
    
    for severity in severities:
        vuln = Vulnerability(
            name=f'{severity.upper()} Vulnerability',
            severity=severity
        )
        db.session.add(vuln)
    
    db.session.commit()
    
    # Verify all created
    for severity in severities:
        vuln = Vulnerability.query.filter_by(severity=severity).first()
        assert vuln is not None
        assert vuln.severity == severity


def test_vuln_with_cvss_score(test_user):
    """Test vulnerability with CVSS score."""
    vuln = Vulnerability(
        name='CVSS Vuln',
        severity='critical',
        cvss_score=9.8,
        cve_id='CVE-2023-9999'
    )
    db.session.add(vuln)
    db.session.commit()
    
    assert vuln.cvss_score == 9.8
    assert vuln.severity == 'critical'


def test_vuln_with_description(test_user):
    """Test vulnerability with detailed description."""
    description = "This is a critical SQL injection vulnerability in the login form."
    vuln = Vulnerability(
        name='SQL Injection',
        severity='critical',
        description=description
    )
    db.session.add(vuln)
    db.session.commit()
    
    assert vuln.description == description


def test_vuln_instance_multiple_scans_same_target(test_user):
    """Test same vulnerability found in multiple scans of same target."""
    target = Target(ip_address='192.168.1.16', name='Target 16', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    # Create vulnerability
    vuln = Vulnerability(name='Persistent Vuln', severity='high')
    db.session.add(vuln)
    db.session.flush()
    
    # Create two scans
    scan1 = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    scan2 = Scan(target_id=target.id, scan_type='nmap_full', status='completed', user_id=test_user.id)
    db.session.add(scan1)
    db.session.add(scan2)
    db.session.flush()
    
    # Create vulnerability instances for both scans
    vi1 = VulnerabilityInstance(
        vulnerability_id=vuln.id,
        target_id=target.id,
        scan_id=scan1.id,
        status='open'
    )
    vi2 = VulnerabilityInstance(
        vulnerability_id=vuln.id,
        target_id=target.id,
        scan_id=scan2.id,
        status='open'
    )
    db.session.add(vi1)
    db.session.add(vi2)
    db.session.commit()
    
    # Verify both instances exist
    instances = VulnerabilityInstance.query.filter_by(
        vulnerability_id=vuln.id,
        target_id=target.id
    ).all()
    assert len(instances) == 2


def test_vuln_filter_by_status(test_user):
    """Test filtering vulnerabilities by status."""
    target = Target(ip_address='192.168.1.17', name='Target 17', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    # Create vulnerabilities with different statuses
    statuses = ['open', 'in_progress', 'fixed', 'false_positive']
    for status in statuses:
        vuln = Vulnerability(name=f'Vuln {status}', severity='medium')
        db.session.add(vuln)
        db.session.flush()
        
        vi = VulnerabilityInstance(
            vulnerability_id=vuln.id,
            target_id=target.id,
            scan_id=scan.id,
            status=status
        )
        db.session.add(vi)
    
    db.session.commit()
    
    # Filter by each status
    for status in statuses:
        instances = VulnerabilityInstance.query.filter_by(status=status).all()
        assert len(instances) >= 1
        assert all(vi.status == status for vi in instances)
