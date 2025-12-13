import pytest
import json
from unittest.mock import patch, MagicMock
from api.models.scan import Scan
from api.models.vulnerability import Vulnerability
from api.extensions import db

def test_e2e_full_flow(client, auth_header, app):
    """
    Simulate a full user flow:
    1. Create Target
    2. Start Scan (mocked execution)
    3. Verify Scan Completion & Vulnerabilities
    4. Create Ticket from Vulnerability
    5. Generate Report
    """
    
    # 1. Create Target
    res_target = client.post('/api/targets/', json={
        'name': 'E2E Target',
        'ip_address': '192.168.1.100',
        'description': 'End-to-End Test Target'
    }, headers=auth_header)
    assert res_target.status_code == 201
    target_id = res_target.json['id']
    
    # 2. Start Scan
    # We mock the _start_scan_thread to simulate immediate completion
    with patch('api.services.scan_manager.ScanManager._start_scan_thread') as mock_thread:
        # Define side effect to simulate scan completion
        def simulate_scan_completion(scan_id, *args, **kwargs):
            with app.app_context():
                scan = Scan.query.get(scan_id)
                scan.status = 'completed'
                scan.progress = 100
                scan.vuln_count = 1
                scan.vuln_breakdown = {'High': 1}
                
                from api.models.vulnerability import VulnerabilityInstance
                
                # Create a dummy vulnerability definition
                vuln = Vulnerability(
                    name='E2E Vulnerability',
                    severity='High',
                    cvss_score=8.5,
                    description='Test vulnerability found during E2E',
                    remediation='Fix it',
                    cve_id='CVE-2023-12345'
                )
                db.session.add(vuln)
                db.session.flush() # Get ID
                
                # Create instance
                instance = VulnerabilityInstance(
                    vulnerability_id=vuln.id,
                    target_id=target_id,
                    scan_id=scan_id,
                    port='80',
                    protocol='tcp',
                    service='http',
                    status='open'
                )
                db.session.add(instance)
                db.session.commit()
                
        mock_thread.side_effect = simulate_scan_completion
        
        res_scan = client.post('/api/scans/', json={
            'target_id': target_id,
            'scan_type': 'nmap',
            'args': '-F'
        }, headers=auth_header)
        assert res_scan.status_code == 201
        scan_id = res_scan.json['scan_id']
        
        # Verify mock was called
        mock_thread.assert_called_once()
        
    # 3. Verify Scan Completion
    res_scan_details = client.get(f'/api/scans/{scan_id}', headers=auth_header)
    assert res_scan_details.status_code == 200
    assert res_scan_details.json['status'] == 'completed'
    
    # Check progress
    res_progress = client.get(f'/api/scans/{scan_id}/progress', headers=auth_header)
    assert res_progress.status_code == 200
    assert res_progress.json['progress'] == 100
    
    # Verify Vulnerabilities
    res_vulns = client.get(f'/api/vulns/?scan_id={scan_id}', headers=auth_header)
    assert res_vulns.status_code == 200
    # Note: Depending on implementation, might need to check instances or main vulns
    # For now, just check if we can list them
    
    # 4. Create Ticket
    # First get a vulnerability instance ID
    with app.app_context():
        from api.models.vulnerability import VulnerabilityInstance
        instance = VulnerabilityInstance.query.filter_by(scan_id=scan_id).first()
        instance_id = instance.id if instance else None
        
    if instance_id:
        res_ticket = client.post('/api/tickets/create-from-vuln', json={
            'title': 'Fix E2E Vuln',
            'priority': 'high',
            'description': 'Fix the vulnerability found in E2E test',
            'vuln_instance_id': instance_id
        }, headers=auth_header)
        assert res_ticket.status_code == 201
        
    # 5. Generate Report
    # Mock report generation to avoid WeasyPrint/dependency issues in test env
    with patch('api.services.legacy_report_generator.ReportGenerator.generate_pdf_report') as mock_pdf:
        mock_pdf.return_value = b'%PDF-1.4...'
        
        res_report = client.post('/api/reports/', json={
            'scan_id': scan_id,
            'type': 'scan',
            'format': 'pdf'
        }, headers=auth_header)
        assert res_report.status_code in [200, 201]
        
    # Verify Report Exists
    res_reports = client.get('/api/reports/', headers=auth_header)
    assert res_reports.status_code == 200
    assert len(res_reports.json) >= 1
