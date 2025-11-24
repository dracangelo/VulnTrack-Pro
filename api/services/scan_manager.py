import threading
import json
from datetime import datetime
from api.extensions import db
from api.models.scan import Scan
from api.models.target import Target
from api.services.nmap_service import NmapService
from api.services.openvas_service import OpenVASService
from api.services.plugin_loader import PluginLoader

class ScanManager:
    def __init__(self, app):
        self.app = app # Need app context for DB operations in threads
        self.nmap_service = NmapService()
        self.openvas_service = OpenVASService()
        self.plugin_loader = PluginLoader()

    def start_scan(self, target_id, scan_type, scanner_args=None):
        """
        Starts a scan in a background thread.
        """
        # Create Scan record
        scan = Scan(target_id=target_id, scan_type=scan_type, status='pending', started_at=datetime.utcnow())
        db.session.add(scan)
        db.session.commit()
        
        scan_id = scan.id
        
        # Start background thread
        thread = threading.Thread(target=self._run_scan, args=(scan_id, target_id, scan_type, scanner_args))
        thread.start()
        
        return scan_id

    def _run_scan(self, scan_id, target_id, scan_type, scanner_args):
        """
        Internal method to run the scan logic.
        """
        with self.app.app_context():
            scan = Scan.query.get(scan_id)
            target = Target.query.get(target_id)
            
            if not scan or not target:
                print(f"Scan {scan_id} or Target {target_id} not found in thread")
                return

            scan.status = 'running'
            db.session.commit()
            
            results = {}
            try:
                if scan_type == 'nmap':
                    raw_results = self.nmap_service.scan_target(target.ip_address, scanner_args or '-sV -T4 -F')
                    results = self.nmap_service.normalize_results(raw_results)
                elif scan_type == 'openvas':
                    # OpenVAS is async by nature (task based), but we might want to wait for it or just launch it
                    # For simplicity here, we launch it and store the task ID. 
                    # Real implementation would need polling or callbacks.
                    # Let's just launch and return the task info for now.
                    results = self.openvas_service.start_scan(target.ip_address)
                elif scan_type.startswith('plugin:'):
                    plugin_name = scan_type.split(':')[1]
                    results = self.plugin_loader.run_plugin(plugin_name, target.ip_address, scanner_args)
                else:
                    results = {'error': f'Unknown scan type: {scan_type}'}
                    scan.status = 'failed'

                scan.raw_output = json.dumps(results)
                if scan.status != 'failed':
                    scan.status = 'completed'
                scan.completed_at = datetime.utcnow()
                db.session.commit()
                
                # Trigger Vulnerability Processing
                if scan.status == 'completed':
                    try:
                        from api.services.vuln_manager import VulnManager
                        vuln_manager = VulnManager()
                        vuln_manager.process_scan_results(scan_id)
                    except Exception as e:
                        print(f"Error processing vulnerabilities: {e}")
                
            except Exception as e:
                print(f"Scan error: {e}")
                scan.status = 'failed'
                scan.raw_output = json.dumps({'error': str(e)})
                scan.completed_at = datetime.utcnow()
                db.session.commit()
