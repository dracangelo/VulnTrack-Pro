from gvm.connections import UnixSocketConnection, TLSConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeTransform
from gvm.errors import GvmError

class OpenVASService:
    def __init__(self, connection_type='socket', socket_path=None, hostname=None, port=9390, username=None, password=None):
        self.connection_type = connection_type
        self.socket_path = socket_path
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.gmp = None

    def connect(self):
        try:
            if self.connection_type == 'socket':
                path = self.socket_path or '/run/gvmd/gvmd.sock'
                connection = UnixSocketConnection(path=path)
            elif self.connection_type == 'tls':
                connection = TLSConnection(hostname=self.hostname, port=self.port)
            else:
                raise ValueError("Invalid connection type")

            self.gmp = Gmp(connection=connection, transform=EtreeTransform())
            self.gmp.connect()
            
            if self.username and self.password:
                self.gmp.authenticate(self.username, self.password)
                
            return True
        except Exception as e:
            print(f"OpenVAS connection error: {e}")
            return False

    def start_scan(self, target_ip, scan_config_id=None, scanner_id=None):
        """
        Launches a scan in OpenVAS.
        Requires creating a target first, then a task, then starting the task.
        """
        if not self.gmp:
            if not self.connect():
                return {'error': 'Could not connect to OpenVAS'}

        try:
            # 1. Create Target
            target_name = f"Scan Target {target_ip}"
            response = self.gmp.create_target(name=target_name, hosts=[target_ip], port_list_id="33d0cd82-57c6-11e1-8ed1-406186ea4fc5") # Default port list
            target_id = response.get('id')

            # 2. Create Task
            # Default scan config (Full and fast): daba56c8-73ec-11df-a475-002264764cea
            config_id = scan_config_id or "daba56c8-73ec-11df-a475-002264764cea"
            # OpenVAS Default scanner: 08b69003-5fc2-4037-a479-93b440211c73
            scanner_id = scanner_id or "08b69003-5fc2-4037-a479-93b440211c73"
            
            task_name = f"Scan Task {target_ip}"
            response = self.gmp.create_task(name=task_name, config_id=config_id, target_id=target_id, scanner_id=scanner_id)
            task_id = response.get('id')

            # 3. Start Task
            response = self.gmp.start_task(task_id=task_id)
            report_id = response.get('report_id')
            
            return {'task_id': task_id, 'report_id': report_id}

        except GvmError as e:
            print(f"OpenVAS scan error: {e}")
            return {'error': str(e)}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {'error': str(e)}

    def get_report(self, report_id):
        if not self.gmp:
            if not self.connect():
                return {'error': 'Could not connect to OpenVAS'}
        
        try:
            response = self.gmp.get_report(report_id=report_id)
            return response
        except Exception as e:
            return {'error': str(e)}
