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
        self.connection = None
        self.gmp = None
    
    def connect(self):
        """Establish connection to OpenVAS/GVM"""
        try:
            # Try Unix socket first (local installation)
            socket_path = os.getenv('GVM_SOCKET', '/var/run/gvmd/gvmd.sock')
            if os.path.exists(socket_path):
                self.connection = UnixSocketConnection(path=socket_path)
            else:
                # Fallback to TLS connection
                self.connection = TLSConnection(hostname=self.host, port=self.port)
            
            self.gmp = Gmp(connection=self.connection, transform=EtreeTransform())
            self.gmp.authenticate(self.username, self.password)
            return True
        except Exception as e:
            print(f"OpenVAS connection error: {e}")
            return False
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.disconnect()
    
    def create_target(self, name, hosts):
        """Create a target in OpenVAS"""
        try:
            response = self.gmp.create_target(name=name, hosts=[hosts])
            target_id = response.get('id')
            return target_id
        except Exception as e:
            print(f"Error creating target: {e}")
            return None
    
    def create_task(self, name, target_id, config_id=None):
        """Create a scan task"""
        try:
            # Use default Full and Fast config if not specified
            if not config_id:
                configs = self.gmp.get_scan_configs()
                # Find "Full and fast" config
                for config in configs.xpath('config'):
                    if 'Full and fast' in config.find('name').text:
                        config_id = config.get('id')
                        break
            
            # Get default scanner
            scanners = self.gmp.get_scanners()
            scanner_id = scanners.xpath('scanner')[0].get('id')
            
            response = self.gmp.create_task(
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
            response = self.gmp.start_task(task_id)
            report_id = response.xpath('report_id')[0].text
            return report_id
        except Exception as e:
            print(f"Error starting task: {e}")
            return None
    
    def get_task_status(self, task_id):
        """Get task progress and status"""
        try:
            response = self.gmp.get_task(task_id)
            task = response.xpath('task')[0]
            
            status = task.find('status').text
            progress = int(task.find('progress').text) if task.find('progress') is not None else 0
            
            return {
                'status': status,
                'progress': progress
            }
        except Exception as e:
            print(f"Error getting task status: {e}")
            return {'status': 'Unknown', 'progress': 0}
    
    def get_report(self, report_id):
        """Retrieve scan report"""
        try:
            response = self.gmp.get_report(report_id, details=True)
            return response
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
    
    
    def get_scan_configs(self):
        """Fetch available scan configurations from OpenVAS"""
        try:
            if not self.connect():
                return []
            
            configs_response = self.gmp.get_scan_configs()
            configs = []
            
            for config in configs_response.xpath('config'):
                config_id = config.get('id')
                name = config.find('name').text if config.find('name') is not None else 'Unknown'
                
                # Only include usable configs (not trash)
                if config.find('trash').text == '0':
                    configs.append({
                        'id': config_id,
                        'name': name
                    })
            
            self.disconnect()
            return configs
            
        except Exception as e:
            print(f"Error fetching scan configs: {e}")
            return []
    
    def launch_scan(self, target_name, target_ip, config_id=None):
        """Complete workflow: create target, task, and start scan"""
        try:
            if not self.connect():
                return None, None
            
            # Create target
            target_id = self.create_target(f"{target_name} - {target_ip}", target_ip)
            if not target_id:
                return None, None
            
            # Create task with optional config
            task_id = self.create_task(f"Scan: {target_name}", target_id, config_id)
            if not task_id:
                return None, None
            
            # Start task
            report_id = self.start_task(task_id)
            
            self.disconnect()
            
            return task_id, report_id
        
        except Exception as e:
            print(f"Error launching scan: {e}")
            return None, None
