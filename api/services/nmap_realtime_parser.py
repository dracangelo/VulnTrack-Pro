import subprocess
import re
import threading
import json
from datetime import datetime

class NmapRealtimeParser:
    """Real-time Nmap scanner with progress parsing and WebSocket updates"""
    
    def __init__(self, scan_manager=None):
        self.scan_manager = scan_manager
        self.process = None
        self.cancelled = False
        
    def scan_target(self, target, arguments, scan_id, app_context):
        """
        Run Nmap scan with real-time progress tracking
        
        :param target: IP address or hostname to scan
        :param arguments: Nmap arguments
        :param scan_id: Scan ID for progress updates
        :param app_context: Flask app context for database operations
        :return: Dictionary containing scan results
        """
        self.cancelled = False
        
        # Ensure verbose mode for progress tracking
        if '-v' not in arguments:
            arguments += ' -v'
        
        # Build command
        cmd = ['nmap'] + arguments.split() + [target]
        
        try:
            # Start Nmap process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Track scan data
            scan_data = {
                'hosts': [],
                'ports': [],
                'raw_output': '',
                'discovered_hosts': 0,
                'total_ports_scanned': 0,
                'open_ports': 0
            }
            
            # Parse output line by line
            for line in iter(self.process.stdout.readline, ''):
                if self.cancelled:
                    self.process.terminate()
                    return {'error': 'Scan cancelled', 'cancelled': True}
                
                scan_data['raw_output'] += line
                
                # Parse progress and emit updates
                self._parse_line(line, scan_data, scan_id, app_context)
            
            # Wait for process to complete
            self.process.wait()
            
            # Parse final results
            results = self._parse_final_results(scan_data['raw_output'])
            
            return results
            
        except Exception as e:
            print(f"Nmap real-time scan error: {e}")
            if self.process:
                self.process.terminate()
            return {'error': str(e)}
    
    def _parse_line(self, line, scan_data, scan_id, app_context):
        """Parse a single line of Nmap output and emit updates"""
        
        # Progress percentage: "About 45.67% done"
        progress_match = re.search(r'About\s+([\d.]+)%\s+done', line)
        if progress_match:
            progress = float(progress_match.group(1))
            self._emit_progress(scan_id, int(progress), 'Scanning in progress...', app_context)
        
        # Discovered hosts: "Nmap scan report for 192.168.1.1"
        host_match = re.search(r'Nmap scan report for (.+)', line)
        if host_match:
            host = host_match.group(1).strip()
            scan_data['discovered_hosts'] += 1
            scan_data['hosts'].append(host)
            self._emit_host_discovered(scan_id, host, scan_data['discovered_hosts'], app_context)
        
        # Open ports: "22/tcp   open  ssh"
        port_match = re.search(r'(\d+)/(tcp|udp)\s+open\s+(\S+)', line)
        if port_match:
            port_num = port_match.group(1)
            protocol = port_match.group(2)
            service = port_match.group(3)
            
            port_info = {
                'port': int(port_num),
                'protocol': protocol,
                'service': service,
                'state': 'open'
            }
            
            scan_data['ports'].append(port_info)
            scan_data['open_ports'] += 1
            self._emit_port_discovered(scan_id, port_info, scan_data['open_ports'], app_context)
        
        # Timing stats: "Stats: 0:00:45 elapsed; 0 hosts completed (1 up), 1 undergoing Service Scan"
        timing_match = re.search(r'Stats:\s+([\d:]+)\s+elapsed', line)
        if timing_match:
            elapsed = timing_match.group(1)
            self._emit_timing_update(scan_id, elapsed, app_context)
        
        # Completed scan: "Nmap done: 1 IP address (1 host up) scanned"
        done_match = re.search(r'Nmap done:\s+(\d+)\s+IP address', line)
        if done_match:
            self._emit_progress(scan_id, 100, 'Scan completed', app_context)
    
    def _parse_final_results(self, raw_output):
        """Parse final Nmap output into structured format"""
        results = {
            'hosts': [],
            'summary': {},
            'raw_output': raw_output
        }
        
        # Extract host information
        host_blocks = re.split(r'Nmap scan report for ', raw_output)[1:]
        
        for block in host_blocks:
            lines = block.split('\n')
            host_info = {
                'host': lines[0].strip(),
                'ports': []
            }
            
            # Extract ports
            for line in lines:
                port_match = re.search(r'(\d+)/(tcp|udp)\s+(\w+)\s+(\S+)', line)
                if port_match:
                    host_info['ports'].append({
                        'port': int(port_match.group(1)),
                        'protocol': port_match.group(2),
                        'state': port_match.group(3),
                        'service': port_match.group(4)
                    })
            
            results['hosts'].append(host_info)
        
        # Extract summary
        summary_match = re.search(r'Nmap done:\s+(.+)', raw_output)
        if summary_match:
            results['summary']['text'] = summary_match.group(1).strip()
        
        return results
    
    def _emit_progress(self, scan_id, progress, message, app_context):
        """Emit progress update via WebSocket"""
        if self.scan_manager:
            self.scan_manager.update_progress(scan_id, progress, message)
    
    def _emit_host_discovered(self, scan_id, host, total_hosts, app_context):
        """Emit host discovery event"""
        from api.extensions import socketio
        
        socketio.emit('nmap_host_discovered', {
            'scan_id': scan_id,
            'host': host,
            'total_hosts': total_hosts,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'scan_{scan_id}', namespace='/scan-progress')
    
    def _emit_port_discovered(self, scan_id, port_info, total_ports, app_context):
        """Emit port discovery event"""
        from api.extensions import socketio
        
        socketio.emit('nmap_port_discovered', {
            'scan_id': scan_id,
            'port': port_info,
            'total_open_ports': total_ports,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'scan_{scan_id}', namespace='/scan-progress')
    
    def _emit_timing_update(self, scan_id, elapsed, app_context):
        """Emit timing update"""
        from api.extensions import socketio
        
        socketio.emit('nmap_timing', {
            'scan_id': scan_id,
            'elapsed': elapsed,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'scan_{scan_id}', namespace='/scan-progress')
    
    def cancel(self):
        """Cancel the running scan"""
        self.cancelled = True
        if self.process:
            self.process.terminate()
    
    def normalize_results(self, scan_results):
        """Normalize scan results to match expected format"""
        normalized = []
        
        if 'hosts' in scan_results:
            for host in scan_results['hosts']:
                for port in host.get('ports', []):
                    normalized.append({
                        'port': port['port'],
                        'protocol': port['protocol'],
                        'state': port['state'],
                        'service': port['service'],
                        'product': '',
                        'version': '',
                        'cpe': '',
                        'script': {}
                    })
        
        return normalized
