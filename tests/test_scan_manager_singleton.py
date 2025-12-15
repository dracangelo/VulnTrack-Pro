import pytest
from flask import current_app
from api.services.scan_manager import ScanManager

def test_scan_manager_singleton(app):
    """
    Test that ScanManager is initialized as a singleton and attached to the app.
    """
    with app.app_context():
        # Check if scan_manager is attached to app
        assert hasattr(current_app, 'scan_manager')
        assert isinstance(current_app.scan_manager, ScanManager)
        
        # Check if it's the same instance across calls
        manager1 = current_app.scan_manager
        manager2 = current_app.scan_manager
        assert manager1 is manager2
        
        # Verify active_scans dict is preserved
        manager1.active_scans['test_scan'] = 'running'
        assert 'test_scan' in manager2.active_scans
        assert manager2.active_scans['test_scan'] == 'running'
