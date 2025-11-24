import threading
import json
import time
from datetime import datetime
from api.extensions import db
from api.models.scan import Scan
from api.models.target import Target
from api.services.nmap_service import NmapService
from api.services.openvas_service import OpenVASService
from api.services.plugin_loader import PluginLoader
from api.services.scan_queue import ScanQueue

class ScanManager:
    def __init__(self, app):
        self.app = app # Need app context for DB operations in threads
        self.nmap_service = NmapService()
        self.openvas_service = OpenVASService()
        self.plugin_loader = PluginLoader()
        self.active_scans = {}  # {scan_id: {'thread': thread, 'should_cancel': False}}
        
        # Initialize scan queue
        from api.config import Config
        self.scan_queue = ScanQueue(max_concurrent=Config.MAX_CONCURRENT_SCANS)

    def start_scan(self, target_id, scan_type, scanner_args=None):
        """
        Starts a scan in a background thread or queues it if at capacity.
        """
        # Create Scan record
        scan = Scan(
            target_id=target_id, 
            scan_type=scan_type, 
            status='pending', 
            started_at=datetime.utcnow(),
            progress=0,
            current_step='Initializing scan...'
        )
        db.session.add(scan)
        db.session.commit()
        
        scan_id = scan.id
        
        # Check if we can start immediately or need to queue
        if len(self.active_scans) >= self.scan_queue.max_concurrent:
            # Queue the scan
            queue_position = self.scan_queue.add_to_queue(scan_id, target_id, scan_type, scanner_args)
            scan.status = 'queued'
            scan.current_step = f'Queued (position {queue_position})'
            scan.queue_position = queue_position
            db.session.commit()
            
            # Emit WebSocket event for queue status
            from api.extensions import socketio
            socketio.emit('scan_queued', {
                'scan_id': scan_id,
                'queue_position': queue_position,
                'message': f'Scan queued at position {queue_position}'
            }, namespace='/scan-progress')
            
            return scan_id
        
        # Start scan immediately
        self._start_scan_thread(scan_id, target_id, scan_type, scanner_args)
        return scan_id
    
    def _start_scan_thread(self, scan_id, target_id, scan_type, scanner_args):
        """Start a scan thread"""
        # Start background thread
        thread = threading.Thread(target=self._run_scan, args=(scan_id, target_id, scan_type, scanner_args))
        thread.daemon = True
        
        # Track active scan
        self.active_scans[scan_id] = {
            'thread': thread,
            'should_cancel': False
        }
        
        thread.start()

    def cancel_scan(self, scan_id):
        """Request cancellation of a running scan"""
        if scan_id in self.active_scans:
            self.active_scans[scan_id]['should_cancel'] = True
            return True
        return False

    def is_cancelled(self, scan_id):
        """Check if scan should be cancelled"""
        if scan_id in self.active_scans:
            return self.active_scans[scan_id]['should_cancel']
        return False

    def update_progress(self, scan_id, progress, current_step, eta_seconds=None):
        """Update scan progress in database and emit WebSocket event"""
        with self.app.app_context():
            scan = Scan.query.get(scan_id)
            if scan:
                scan.progress = progress
                scan.current_step = current_step
                if eta_seconds is not None:
                    scan.eta_seconds = eta_seconds
                db.session.commit()
                
                # Emit WebSocket event
                from api.extensions import socketio
                from datetime import datetime
                
                elapsed = None
                if scan.started_at:
                    elapsed = int((datetime.utcnow() - scan.started_at).total_seconds())
                
                socketio.emit('progress_update', {
                    'id': scan_id,
                    'status': scan.status,
                    'progress': progress,
                    'current_step': current_step,
                    'eta_seconds': eta_seconds,
                    'elapsed_seconds': elapsed,
                    'vuln_count': scan.vuln_count or 0,
                    'vuln_breakdown': scan.vuln_breakdown or {},
                    'target_name': scan.target.name if scan.target else 'Unknown'
                }, room=f'scan_{scan_id}', namespace='/scan-progress')

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
            scan.progress = 5
            scan.current_step = 'Starting scan...'
            db.session.commit()
            
            results = {}
            try:
                # Check for cancellation
                if self.is_cancelled(scan_id):
                    scan.status = 'cancelled'
                    scan.current_step = 'Scan cancelled by user'
                    scan.completed_at = datetime.utcnow()
                    db.session.commit()
                    return
                
                if scan_type == 'nmap':
                    self._run_nmap_scan(scan_id, target, scanner_args)
                elif scan_type == 'openvas':
                    self._run_openvas_scan(scan_id, target)
                elif scan_type.startswith('plugin:'):
                    plugin_name = scan_type.split(':')[1]
                    scan.current_step = f'Running plugin: {plugin_name}'
                    scan.progress = 50
                    db.session.commit()
                    results = self.plugin_loader.run_plugin(plugin_name, target.ip_address, scanner_args)
                    scan.raw_output = json.dumps(results)
                    scan.status = 'completed'
                    scan.progress = 100
                else:
                    results = {'error': f'Unknown scan type: {scan_type}'}
                    scan.status = 'failed'

                if scan.status == 'completed':
                    scan.completed_at = datetime.utcnow()
                    scan.current_step = 'Scan completed'
                    db.session.commit()
                    
                    # Trigger Vulnerability Processing
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
                scan.current_step = f'Error: {str(e)}'
                db.session.commit()
            finally:
                # Cleanup active scan tracking
                if scan_id in self.active_scans:
                    del self.active_scans[scan_id]
                
                # Try to start next queued scan
                self._process_queue()
    
    def _process_queue(self):
        """Process queue and start next scan if slot available"""
        if len(self.active_scans) < self.scan_queue.max_concurrent:
            next_scan = self.scan_queue.get_next()
            if next_scan:
                # Update scan status
                with self.app.app_context():
                    scan = Scan.query.get(next_scan['scan_id'])
                    if scan:
                        scan.status = 'pending'
                        scan.current_step = 'Starting scan...'
                        scan.queue_position = 0
                        db.session.commit()
                
                # Start the scan
                self._start_scan_thread(
                    next_scan['scan_id'],
                    next_scan['target_id'],
                    next_scan['scan_type'],
                    next_scan['scanner_args']
                )
                
                # Emit WebSocket event
                from api.extensions import socketio
                socketio.emit('scan_started_from_queue', {
                    'scan_id': next_scan['scan_id'],
                    'message': 'Scan started from queue'
                }, namespace='/scan-progress')

    def _run_nmap_scan(self, scan_id, target, scanner_args):
        """Run Nmap scan with progress tracking"""
        with self.app.app_context():
            scan = Scan.query.get(scan_id)
            
            # Update progress: Preparing
            scan.progress = 10
            scan.current_step = 'Preparing Nmap scan...'
            db.session.commit()
            
            # Check cancellation
            if self.is_cancelled(scan_id):
                scan.status = 'cancelled'
                scan.current_step = 'Scan cancelled'
                db.session.commit()
                return
            
            # Run Nmap scan
            scan.progress = 20
            scan.current_step = 'Scanning ports...'
            db.session.commit()
            
            raw_results = self.nmap_service.scan_target(target.ip_address, scanner_args or '-F')
            
            # Check cancellation
            if self.is_cancelled(scan_id):
                scan.status = 'cancelled'
                scan.current_step = 'Scan cancelled'
                db.session.commit()
                return
            
            # Simulate progress updates (in real implementation, parse Nmap output)
            scan.progress = 60
            scan.current_step = 'Analyzing results...'
            db.session.commit()
            
            results = self.nmap_service.normalize_results(raw_results)
            
            scan.progress = 90
            scan.current_step = 'Finalizing...'
            db.session.commit()
            
            scan.raw_output = json.dumps(results)
            scan.status = 'completed'
            scan.progress = 100
            scan.current_step = 'Scan completed'
            db.session.commit()

    def _run_openvas_scan(self, scan_id, target):
        """Run OpenVAS scan with progress tracking"""
        with self.app.app_context():
            scan = Scan.query.get(scan_id)
            
            try:
                from api.services.openvas_scanner import OpenVASScanner
                import os
                
                # Initialize OpenVAS scanner
                scanner = OpenVASScanner(
                    host=os.getenv('OPENVAS_HOST', '127.0.0.1'),
                    port=int(os.getenv('OPENVAS_PORT', 9390)),
                    username=os.getenv('OPENVAS_USERNAME', 'admin'),
                    password=os.getenv('OPENVAS_PASSWORD', 'admin')
                )
                
                # Launch scan
                scan.progress = 10
                scan.current_step = 'Connecting to OpenVAS...'
                db.session.commit()
                
                task_id, report_id = scanner.launch_scan(target.name, target.ip_address)
                
                if not task_id:
                    scan.status = 'failed'
                    scan.current_step = 'Failed to connect to OpenVAS'
                    db.session.commit()
                    return
                
                # Store OpenVAS IDs
                scan.openvas_task_id = task_id
                scan.openvas_report_id = report_id
                scan.progress = 20
                scan.current_step = 'OpenVAS scan started...'
                db.session.commit()
                
                # Poll for progress
                scanner.connect()
                while True:
                    status_info = scanner.get_task_status(task_id)
                    scan.progress = min(20 + int(status_info['progress'] * 0.7), 90)
                    scan.current_step = f"OpenVAS scanning... ({status_info['status']})"
                    db.session.commit()
                    
                    if status_info['status'] in ['Done', 'Stopped', 'Interrupted']:
                        break
                    
                    time.sleep(5)  # Poll every 5 seconds
                
                # Get report
                scan.progress = 95
                scan.current_step = 'Retrieving OpenVAS report...'
                db.session.commit()
                
                report_xml = scanner.get_report(report_id)
                vulnerabilities = scanner.parse_report(report_xml)
                
                scanner.disconnect()
                
                # Store results
                scan.raw_output = json.dumps({
                    'task_id': task_id,
                    'report_id': report_id,
                    'vulnerabilities': vulnerabilities
                })
                scan.status = 'completed'
                scan.progress = 100
                scan.current_step = 'OpenVAS scan completed'
                db.session.commit()
                
            except Exception as e:
                print(f"OpenVAS scan error: {e}")
                scan.status = 'failed'
                scan.current_step = f'OpenVAS error: {str(e)}'
                scan.raw_output = json.dumps({'error': str(e)})
                db.session.commit()
