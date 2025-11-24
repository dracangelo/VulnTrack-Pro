import nmap
import json

class NmapService:
    def __init__(self):
        self.nm = nmap.PortScanner()

    def scan_target(self, target, arguments='-sV -T4 -F'):
        """
        Scans a target using Nmap.
        
        :param target: IP address or hostname to scan.
        :param arguments: Nmap arguments (default: -sV -T4 -F for fast service detection).
        :return: Dictionary containing scan results.
        """
        try:
            print(f"Starting Nmap scan on {target} with args: {arguments}")
            self.nm.scan(hosts=target, arguments=arguments)
            
            # actually self.nm[target] gives the host info if it exists
            
            if target in self.nm.all_hosts():
                return self.nm[target]
            else:
                return {'error': 'Host not found or down'}
                
        except Exception as e:
            print(f"Nmap scan error: {e}")
            return {'error': str(e)}

    def get_scan_results(self):
        return self.nm.all_hosts()

    def normalize_results(self, scan_data):
        """
        Normalizes Nmap scan data into a simplified format.
        """
        normalized = []
        # Check if we have a dictionary (single host) or list (multiple hosts - though scan_target returns single host dict usually)
        # The python-nmap returns a dict with structure: {'scan': {...}, 'nmap': {...}} or just the host dict if I returned self.nm[target]
        
        # If I returned self.nm[target], it looks like:
        # {'hostnames': [...], 'addresses': {...}, 'vendor': {}, 'status': {...}, 'tcp': {22: {...}}}
        
        if 'tcp' in scan_data:
            for port, info in scan_data['tcp'].items():
                normalized.append({
                    'port': port,
                    'protocol': 'tcp',
                    'state': info.get('state'),
                    'service': info.get('name'),
                    'product': info.get('product'),
                    'version': info.get('version'),
                    'cpe': info.get('cpe'),
                    'script': info.get('script')
                })
        
        return normalized
