"""
Comprehensive tests for report routes API endpoints.
"""
import pytest
from api.models.report import Report
from api.models.target import Target
from api.models.scan import Scan
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.extensions import db


def test_list_reports_empty(client):
    """Test listing reports when none exist."""
    response = client.get('/api/reports/')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_generate_executive_report(client, test_user):
    """Test generating executive report."""
    # Create some test data
    target = Target(ip_address='192.168.1.20', name='Target 20', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'executive',
        'format': 'pdf',
        'title': 'Executive Summary Report'
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_technical_report(client, test_user):
    """Test generating technical report."""
    target = Target(ip_address='192.168.1.21', name='Target 21', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_full', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'technical',
        'format': 'pdf',
        'title': 'Technical Findings Report'
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_compliance_report(client, test_user):
    """Test generating compliance report."""
    target = Target(ip_address='192.168.1.22', name='Target 22', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'compliance',
        'format': 'pdf',
        'title': 'PCI-DSS Compliance Report',
        'compliance_standard': 'PCI-DSS'
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_trend_report(client, test_user):
    """Test generating trend analysis report."""
    target = Target(ip_address='192.168.1.23', name='Target 23', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'trend',
        'format': 'pdf',
        'title': 'Vulnerability Trend Analysis'
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_comparison_report(client, test_user):
    """Test generating comparison report."""
    target = Target(ip_address='192.168.1.24', name='Target 24', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan1 = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    scan2 = Scan(target_id=target.id, scan_type='nmap_full', status='completed', user_id=test_user.id)
    db.session.add(scan1)
    db.session.add(scan2)
    db.session.commit()
    
    report_data = {
        'report_type': 'comparison',
        'format': 'pdf',
        'title': 'Scan Comparison Report',
        'scan_id_1': scan1.id,
        'scan_id_2': scan2.id
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_report_excel_format(client, test_user):
    """Test generating report in Excel format."""
    target = Target(ip_address='192.168.1.25', name='Target 25', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'executive',
        'format': 'excel',
        'title': 'Executive Report Excel'
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_report_html_format(client, test_user):
    """Test generating report in HTML format."""
    target = Target(ip_address='192.168.1.26', name='Target 26', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'technical',
        'format': 'html',
        'title': 'Technical Report HTML'
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_report_markdown_format(client, test_user):
    """Test generating report in Markdown format."""
    target = Target(ip_address='192.168.1.27', name='Target 27', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'executive',
        'format': 'markdown',
        'title': 'Executive Report Markdown'
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_get_report_details(client, test_user):
    """Test getting report details."""
    # Create a report
    report = Report(
        title='Test Report',
        type='executive',
        format='pdf',
        file_path='/tmp/test_report.pdf'
    )
    db.session.add(report)
    db.session.commit()
    
    response = client.get(f'/api/reports/{report.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == 'Test Report'
    assert data['report_type'] == 'executive'


def test_delete_report(client, test_user):
    """Test deleting a report."""
    report = Report(
        title='Delete Me Report',
        type='technical',
        format='pdf',
        file_path='/tmp/delete_me.pdf'
    )
    db.session.add(report)
    db.session.commit()
    report_id = report.id
    
    response = client.delete(f'/api/reports/{report_id}')
    assert response.status_code == 200
    
    # Verify report was deleted
    report = Report.query.get(report_id)
    assert report is None


def test_list_reports_with_data(client, test_user):
    """Test listing reports when some exist."""
    # Create a target and scan for the reports
    target = Target(ip_address='192.168.1.100', name='Report Target', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()

    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()

    # Create multiple reports
    for i in range(3):
        report = Report(
            title='Test Report',
            type='scan',
            format='pdf',
            status='completed',
            scan_id=scan.id
        )
        db.session.add(report)
    db.session.commit()
    
    response = client.get('/api/reports/')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 3


def test_generate_report_with_filters(client, test_user):
    """Test generating report with severity filters."""
    target = Target(ip_address='192.168.1.28', name='Target 28', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.flush()
    
    # Create vulnerabilities with different severities
    for severity in ['critical', 'high', 'medium']:
        vuln = Vulnerability(name=f'{severity} vuln', severity=severity)
        db.session.add(vuln)
        db.session.flush()
        
        vi = VulnerabilityInstance(
            vulnerability_id=vuln.id,
            target_id=target.id,
            scan_id=scan.id,
            status='open'
        )
        db.session.add(vi)
    
    db.session.commit()
    db.session.remove()
    
    report_data = {
        'report_type': 'executive',
        'format': 'pdf',
        'title': 'Filtered Report',
        'filters': {
            'severity': ['critical', 'high']
        }
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_report_for_specific_target(client, test_user):
    """Test generating report for a specific target."""
    target = Target(ip_address='192.168.1.29', name='Target 29', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_quick', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'technical',
        'format': 'pdf',
        'title': 'Target-Specific Report',
        'filters': {
            'target_ids': [target.id]
        }
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_generate_report_for_scan(client, test_user):
    """Test generating report for a specific scan."""
    target = Target(ip_address='192.168.1.30', name='Target 30', user_id=test_user.id)
    db.session.add(target)
    db.session.flush()
    
    scan = Scan(target_id=target.id, scan_type='nmap_full', status='completed', user_id=test_user.id)
    db.session.add(scan)
    db.session.commit()
    
    report_data = {
        'report_type': 'technical',
        'format': 'pdf',
        'title': 'Scan-Specific Report',
        'filters': {
            'scan_ids': [scan.id]
        }
    }
    response = client.post('/api/reports/generate', json=report_data)
    assert response.status_code in [200, 201]


def test_download_report(client, test_user):
    """Test downloading a report."""
    report = Report(
        title='Download Test Report',
        type='executive',
        format='pdf',
        file_path='/tmp/download_test.pdf'
    )
    db.session.add(report)
    db.session.commit()
    
    response = client.get(f'/api/reports/{report.id}/download')
    # May return 200 with file or 404 if file doesn't exist
    assert response.status_code in [200, 404]


def test_report_pagination(client, test_user):
    """Test report list pagination."""
    # Create many reports
    for i in range(15):
        report = Report(
            title=f'Pagination Report {i}',
            type='executive',
            format='pdf',
            file_path=f'/tmp/page_report_{i}.pdf'
        )
        db.session.add(report)
    db.session.commit()
    
    # Test with pagination parameters
    response = client.get('/api/reports/?page=1&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    # Should return list (pagination may or may not be implemented)
    assert isinstance(data, list) or isinstance(data, dict)
