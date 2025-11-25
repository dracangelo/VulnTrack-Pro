from gvm.connections import UnixSocketConnection, TLSConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeTransform
import os
from lxml import etree

class OpenVASScanner:
    def __init__(self, host='127.0.0.1', port=9390, username='admin', password='admin'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.socket_path = os.getenv('GVM_SOCKET', '/var/run/gvmd/gvmd.sock')
    
    def _get_connection(self):
        """Get connection object"""
        # Try socket connection first if path exists
        if os.path.exists(self.socket_path):
            try:
                # Test if we can actually access the socket
                if not os.access(self.socket_path, os.R_OK | os.W_OK):
                    raise PermissionError(f"No permission to access socket: {self.socket_path}")
                    
                return UnixSocketConnection(path=self.socket_path)
            except (PermissionError, OSError) as e:
                print(f"Socket connection failed ({e}), falling back to TLS...")
                # Fallback to TLS
                return TLSConnection(hostname=self.host, port=self.port)
        else:
            return TLSConnection(hostname=self.host, port=self.port)
    
    def test_connection(self):
        """Test connection to OpenVAS/GVM"""
        try:
            connection = self._get_connection()
            with Gmp(connection=connection) as gmp:
                gmp.authenticate(self.username, self.password)
                # Just test if we can authenticate - don't try to parse version
                return True, "Connected to GVM successfully"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    # Default configurations to use when OpenVAS is unreachable
    DEFAULT_CONFIGS = [
        {'id': 'daba56c8-73ec-11df-a475-002264764cea', 'name': 'Full and fast'},
        {'id': '698f691e-7489-11df-9d8c-002264764cea', 'name': 'Full and fast ultimate'},
        {'id': '708f25c4-7489-11df-8094-002264764cea', 'name': 'Full and very deep'},
        {'id': '74db13d6-7489-11df-91b9-002264764cea', 'name': 'Full and very deep ultimate'},
        {'id': 'd21f6c81-2b88-4ac1-b7b4-a2a9f2ad4663', 'name': 'Discovery'},
        {'id': '8715c877-47a0-438d-98a3-27c7a6ab2196', 'name': 'Discovery'},
        {'id': '085569ce-73ed-11df-83c3-002264764cea', 'name': 'Host Discovery'},
        {'id': '2d3f051c-55ba-11e3-bf43-406186ea4fc5', 'name': 'System Discovery'}
    ]

    def get_scan_configs(self):
        """Get available scan configurations"""
        try:
            connection = self._get_connection()
            with Gmp(connection=connection) as gmp:
                gmp.authenticate(self.username, self.password)
                print("Fetching scan configs from GVM...")
                configs = gmp.get_scan_configs()
                print(f"Raw configs response type: {type(configs)}")
                
                config_list = []
                for config in configs.findall('.//config'):
                    config_id = config.get('id')
                    name = config.find('name')
                    if name is not None and config_id:
                        config_list.append({
                            'id': config_id,
                            'name': name.text
                        })
                        print(f"Found config: {name.text} ({config_id})")
                
                print(f"Total configs found: {len(config_list)}")
                return config_list
        except Exception as e:
            print(f"Error getting scan configs: {e}")
            print("Returning default configurations due to connection error.")
            return self.DEFAULT_CONFIGS
    
    def create_target(self, name, hosts):
        """Create a target in OpenVAS"""
        try:
            connection = self._get_connection()
            with Gmp(connection=connection) as gmp:
                gmp.authenticate(self.username, self.password)
                response = gmp.create_target(name=name, hosts=[hosts])
                target_id = response.get('id')
                return target_id
        except Exception as e:
            print(f"Error creating target: {e}")
            return None
    
    def create_task(self, name, target_id, config_id=None):
        """Create a scan task"""
        try:
            connection = self._get_connection()
            with Gmp(connection=connection) as gmp:
                gmp.authenticate(self.username, self.password)
                
                # Use default config if none specified
                if not config_id:
                    configs = gmp.get_scan_configs()
                    # Find "Full and fast" config
                    for config in configs.xpath('config'):
                        if 'Full and fast' in config.find('name').text:
                            config_id = config.get('id')
                            break
                    # Fallback to first config if "Full and fast" not found
                    if not config_id:
                        config = configs.find('.//config')
                        if config is not None:
                            config_id = config.get('id')
                
                # Get default scanner
                scanners = gmp.get_scanners()
                scanner = scanners.find('.//scanner')
                scanner_id = scanner.get('id') if scanner is not None else None
                
                response = gmp.create_task(
                    name=name,
                    config_id=config_id,
                    target_id=target_id,
                    scanner_id=scanner_id
                )
                task_id = response.get('id')
                return task_id
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    def start_task(self, task_id):
        """Start a scan task"""
        try:
            connection = self._get_connection()
            with Gmp(connection=connection) as gmp:
                gmp.authenticate(self.username, self.password)
                response = gmp.start_task(task_id)
                report_id = response.find('.//report_id')
                return report_id.text if report_id is not None else None
        except Exception as e:
            print(f"Error starting task: {e}")
            return None
    
    def get_task_status(self, task_id):
        """Get task status"""
        try:
            connection = self._get_connection()
            with Gmp(connection=connection) as gmp:
                gmp.authenticate(self.username, self.password)
                task = gmp.get_task(task_id)
                
                status_elem = task.find('.//status')
                progress_elem = task.find('.//progress')
                
                status = status_elem.text if status_elem is not None else 'Unknown'
                progress = int(progress_elem.text) if progress_elem is not None else 0
                
                return {
                    'status': status,
                    'progress': progress
                }
        except Exception as e:
            print(f"Error getting task status: {e}")
            return {'status': 'Error', 'progress': 0}
    
    def get_report(self, report_id):
        """Get scan report"""
        try:
            connection = self._get_connection()
            with Gmp(connection=connection) as gmp:
                gmp.authenticate(self.username, self.password)
                report = gmp.get_report(report_id, details=True)
                return report
        except Exception as e:
            print(f"Error getting report: {e}")
            return None
    
    def parse_report(self, report_xml):
        """Parse OpenVAS XML report and extract vulnerabilities"""
        vulnerabilities = []
        
        try:
            results = report_xml.xpath('//result')
            
            for result in results:
                vuln = {
                    'name': result.find('.//name').text if result.find('.//name') is not None else 'Unknown',
                    'severity': float(result.find('.//severity').text) if result.find('.//severity') is not None else 0.0,
                    'description': result.find('.//description').text if result.find('.//description') is not None else '',
                    'host': result.find('.//host').text if result.find('.//host') is not None else '',
                    'port': result.find('.//port').text if result.find('.//port') is not None else '',
                    'nvt_oid': result.find('.//nvt').get('oid') if result.find('.//nvt') is not None else ''
                }
                
                # Map severity to our categories
                if vuln['severity'] >= 9.0:
                    vuln['severity_category'] = 'Critical'
                elif vuln['severity'] >= 7.0:
                    vuln['severity_category'] = 'High'
                elif vuln['severity'] >= 4.0:
                    vuln['severity_category'] = 'Medium'
                elif vuln['severity'] > 0.0:
                    vuln['severity_category'] = 'Low'
                else:
                    vuln['severity_category'] = 'Info'
                
                vulnerabilities.append(vuln)
        
        except Exception as e:
            print(f"Error parsing report: {e}")
        
        return vulnerabilities
    

    def launch_scan(self, target_name, target_hosts, config_id=None):
        """
        Orchestrate the scan launch process:
        1. Create target
        2. Create task
        3. Start task
        """
        print(f"Launching scan for {target_name} ({target_hosts})...")
        
        # 1. Create Target
        target_id = self.create_target(target_name, target_hosts)
        if not target_id:
            print("Failed to create target")
            return None, None
            
        # 2. Create Task
        task_id = self.create_task(f"Scan for {target_name}", target_id, config_id)
        if not task_id:
            print("Failed to create task")
            return None, None
            
        # 3. Start Task
        report_id = self.start_task(task_id)
        if not report_id:
            print("Failed to start task")
            return None, None
            
        return task_id, report_id

    def connect(self):
        """
        Explicit connect method.
        In this implementation, connection is handled per-request in _get_connection,
        so this is a no-op to satisfy ScanManager interface.
        """
        pass
        
    def disconnect(self):
        """
        Explicit disconnect method.
        In this implementation, connection is handled per-request in _get_connection,
        so this is a no-op to satisfy ScanManager interface.
        """
        pass
