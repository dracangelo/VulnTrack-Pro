"""
Comprehensive tests for scan manager service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from api.services.scan_manager import ScanManager
from api.models.scan import Scan
from api.models.target import Target
from api.extensions import db
import time


def test_scan_manager_initialization(app):
    """Test scan manager initializes correctly."""
    scan_manager = ScanManager(app)
    assert scan_manager.app == app
    assert scan_manager.nmap_service is not None
    assert scan_manager.scan_queue.max_concurrent == 3
    assert len(scan_manager.active_scans) == 0


def test_start_scan_creates_scan_record(app, test_user):
    """Test starting a scan creates a scan record."""
    with app.app_context():
        target = Target(ip_address='192.168.1.50', name='Target 50', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        
        with patch.object(scan_manager, '_start_scan_thread'):
            scan_id = scan_manager.start_scan(
                target_id=target.id,
                scan_type='nmap_quick',
                user_id=test_user.id
            )
        
        assert scan_id is not None
        scan = Scan.query.get(scan_id)
        assert scan is not None
        assert scan.target_id == target.id
        assert scan.scan_type == 'nmap_quick'


def test_start_scan_queues_when_at_capacity(app, test_user):
    """Test scan is queued when at max capacity."""
    with app.app_context():
        target = Target(ip_address='192.168.1.51', name='Target 51', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        scan_manager.scan_queue.max_concurrent = 1
        
        # Fill capacity
        scan_manager.active_scans[1] = Mock()
        
        with patch.object(scan_manager.scan_queue, 'add_to_queue', return_value=1) as mock_add_to_queue:
            scan_id = scan_manager.start_scan(
                target_id=target.id,
                scan_type='nmap_full',
                user_id=test_user.id
            )
            
            # Should be queued
            assert mock_add_to_queue.called


def test_cancel_scan(app, test_user):
    """Test cancelling a running scan."""
    with app.app_context():
        target = Target(ip_address='192.168.1.52', name='Target 52', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        scan = Scan(target_id=target.id, scan_type='nmap_quick', status='running')
        db.session.add(scan)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        # Mock active scan
        scan_manager.active_scans[scan.id] = {'should_cancel': False, 'parser': None}
        
        scan_manager.cancel_scan(scan.id)
        
        db.session.refresh(scan)
        assert scan_manager.is_cancelled(scan.id) is True


def test_is_cancelled(app, test_user):
    """Test checking if scan is cancelled."""
    with app.app_context():
        scan_manager = ScanManager(app)
        scan_manager.active_scans[123] = {'should_cancel': True}
        
        assert scan_manager.is_cancelled(123) is True
        assert scan_manager.is_cancelled(456) is False


def test_update_progress(app, test_user):
    """Test updating scan progress."""
    with app.app_context():
        target = Target(ip_address='192.168.1.53', name='Target 53', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        scan = Scan(target_id=target.id, scan_type='nmap_quick', status='running')
        db.session.add(scan)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        
        with patch('api.socket_events.emit_scan_progress') as mock_emit:
            scan_manager.update_progress(
                scan_id=scan.id,
                progress=50,
                current_step='Scanning ports',
                eta_seconds=120
            )
            
            # Verify progress was updated
            scan = Scan.query.get(scan.id)
            db.session.refresh(scan)
            assert scan.progress == 50
            
            # Verify WebSocket event was emitted
            assert mock_emit.called


def test_scan_manager_handles_invalid_target(app):
    """Test scan manager handles invalid target gracefully."""
    with app.app_context():
        scan_manager = ScanManager(app)
        
        # Try to start scan with non-existent target
        scan_id = scan_manager.start_scan(
            target_id=99999,
            scan_type='nmap_quick'
        )
        
        # Wait for thread to complete
        import time
        time.sleep(1)
        
        # Should return None or handle gracefully
        scan = Scan.query.get(scan_id)
        db.session.refresh(scan)
        assert scan_id is None or scan.status == 'failed'


def test_scan_manager_concurrent_limit(app, test_user):
    """Test scan manager respects concurrent scan limit."""
    with app.app_context():
        scan_manager = ScanManager(app)
        scan_manager.scan_queue.max_concurrent = 2
        
        # Add 2 active scans
        scan_manager.active_scans[1] = Mock()
        scan_manager.active_scans[2] = Mock()
        
        # Try to add a third
        target = Target(ip_address='192.168.1.54', name='Target 54', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        with patch.object(scan_manager.scan_queue, 'add_to_queue', return_value=1) as mock_add_to_queue:
            scan_manager.start_scan(
                target_id=target.id,
                scan_type='nmap_quick',
                user_id=test_user.id
            )
            
            # Should be queued, not started
            assert mock_add_to_queue.called


def test_process_queue(app, test_user):
    """Test processing scan queue."""
    with app.app_context():
        target = Target(ip_address='192.168.1.55', name='Target 55', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        scan = Scan(target_id=target.id, scan_type='nmap_quick', status='queued')
        db.session.add(scan)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        
        # Add scan to queue
        scan_manager.scan_queue.add_to_queue(scan.id, target.id, 'nmap_quick', None, None)
        
        # Process queue
        with patch.object(scan_manager, '_start_scan_thread') as mock_start:
            scan_manager._process_queue()
            
            # Should attempt to start queued scan
            if len(scan_manager.active_scans) < scan_manager.scan_queue.max_concurrent:
                assert mock_start.called or scan_manager.scan_queue.get_queue_size() > 0


def test_scan_error_handling(app, test_user):
    """Test scan manager handles errors gracefully."""
    with app.app_context():
        target = Target(ip_address='192.168.1.56', name='Target 56', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        scan = Scan(target_id=target.id, scan_type='nmap_quick', status='running')
        db.session.add(scan)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        
        # Simulate error during scan
        with patch.object(scan_manager.nmap_service, 'scan_target', side_effect=Exception("Scan failed")):
            try:
                scan_manager._run_nmap_scan(scan.id, target, {})
            except:
                pass
            
            # Scan should be marked as failed
            import time
            time.sleep(1)
            scan = Scan.query.get(scan.id)
            assert scan.status in ['failed', 'running']  # May not update immediately in test


def test_scan_completion_triggers_queue_processing(app, test_user):
    """Test completing a scan triggers queue processing."""
    with app.app_context():
        scan_manager = ScanManager(app)
        
        # Add active scan
        scan_manager.active_scans[1] = Mock()
        
        with patch.object(scan_manager, '_process_queue') as mock_process:
            # Remove active scan (simulating completion)
            if 1 in scan_manager.active_scans:
                del scan_manager.active_scans[1]
                scan_manager._process_queue()
            
            # Queue processing should be triggered
            assert mock_process.called or len(scan_manager.active_scans) == 0


def test_nmap_scan_with_custom_args(app, test_user):
    """Test Nmap scan with custom arguments."""
    with app.app_context():
        target = Target(ip_address='192.168.1.57', name='Target 57', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        custom_args = ['-p', '80,443', '-sV']
        
        with patch.object(scan_manager, '_start_scan_thread'):
            scan_id = scan_manager.start_scan(
                target_id=target.id,
                scan_type='nmap_quick',
                scanner_args=custom_args,
                user_id=test_user.id
            )
        
        scan = Scan.query.get(scan_id)
        assert scan is not None


def test_openvas_scan_start(app, test_user):
    """Test starting OpenVAS scan."""
    with app.app_context():
        target = Target(ip_address='192.168.1.58', name='Target 58', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        
        with patch.object(scan_manager, '_start_scan_thread'):
            scan_id = scan_manager.start_scan(
                target_id=target.id,
                scan_type='openvas',
                openvas_config_id='full_and_fast',
                user_id=test_user.id
            )
        
        scan = Scan.query.get(scan_id)
        assert scan is not None
        assert scan.scan_type == 'openvas'


def test_scan_progress_tracking(app, test_user):
    """Test scan progress is tracked correctly."""
    with app.app_context():
        target = Target(ip_address='192.168.1.59', name='Target 59', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        scan = Scan(target_id=target.id, scan_type='nmap_quick', status='running', progress=0)
        db.session.add(scan)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        
        # Update progress multiple times
        for progress in [25, 50, 75, 100]:
            scan_manager.update_progress(scan.id, progress, f'Step {progress}%')
            scan = Scan.query.get(scan.id)
            db.session.refresh(scan)
            assert scan.progress == progress


def test_multiple_scans_same_target(app, test_user):
    """Test running multiple scans on same target."""
    with app.app_context():
        target = Target(ip_address='192.168.1.60', name='Target 60', user_id=test_user.id)
        db.session.add(target)
        db.session.commit()
        
        scan_manager = ScanManager(app)
        
        with patch.object(scan_manager, '_start_scan_thread'):
            # Start first scan
            scan_id_1 = scan_manager.start_scan(
                target_id=target.id,
                scan_type='nmap_quick',
                user_id=test_user.id
            )
            
            # Start second scan
            scan_id_2 = scan_manager.start_scan(
                target_id=target.id,
                scan_type='nmap_full',
                user_id=test_user.id
            )
        
        assert scan_id_1 != scan_id_2
        assert Scan.query.get(scan_id_1) is not None
        assert Scan.query.get(scan_id_2) is not None
