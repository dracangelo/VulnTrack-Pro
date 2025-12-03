import socket
import re
from datetime import datetime

class BannerGrabber:
    """Service for grabbing banners from network services"""
    
    def __init__(self, timeout=5):
        self.timeout = timeout
        
        # Common service patterns for fingerprinting
        self.service_patterns = {
            'ssh': [
                (r'SSH-[\d.]+-OpenSSH_([\d.]+)', 'OpenSSH'),
                (r'SSH-[\d.]+-Cisco', 'Cisco SSH'),
                (r'SSH-[\d.]+-dropbear_([\d.]+)', 'Dropbear SSH'),
            ],
            'http': [
                (r'Server:\s*Apache/([\d.]+)', 'Apache'),
                (r'Server:\s*nginx/([\d.]+)', 'nginx'),
                (r'Server:\s*Microsoft-IIS/([\d.]+)', 'Microsoft IIS'),
                (r'Server:\s*lighttpd/([\d.]+)', 'lighttpd'),
            ],
            'ftp': [
                (r'220.*ProFTPD\s+([\d.]+)', 'ProFTPD'),
                (r'220.*vsftpd\s+([\d.]+)', 'vsftpd'),
                (r'220.*FileZilla Server', 'FileZilla'),
                (r'220.*Microsoft FTP Service', 'Microsoft FTP'),
            ],
            'smtp': [
                (r'220.*Postfix', 'Postfix'),
                (r'220.*Sendmail\s+([\d.]+)', 'Sendmail'),
                (r'220.*Microsoft ESMTP MAIL Service', 'Microsoft Exchange'),
                (r'220.*Exim\s+([\d.]+)', 'Exim'),
            ],
            'mysql': [
                (r'[\x00-\xFF]*?([\d.]+)-MariaDB', 'MariaDB'),
                (r'[\x00-\xFF]*?([\d.]+)-MySQL', 'MySQL'),
            ],
            'postgresql': [
                (r'PostgreSQL\s+([\d.]+)', 'PostgreSQL'),
            ],
            'redis': [
                (r'\+PONG', 'Redis'),
                (r'-NOAUTH', 'Redis'),
            ],
            'mongodb': [
                (r'MongoDB', 'MongoDB'),
            ],
            'telnet': [
                (r'Ubuntu', 'Ubuntu Telnet'),
                (r'Debian', 'Debian Telnet'),
            ]
        }
    
    def grab_banner(self, host, port, protocol='tcp'):
        """
        Connect to a port and grab the banner
        
        :param host: Target hostname or IP
        :param port: Port number
        :param protocol: Protocol (tcp/udp)
        :return: Banner string or None
        """
        if protocol != 'tcp':
            # UDP banner grabbing is more complex, skip for now
            return None
        
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect to target
            sock.connect((host, port))
            
            # Try to receive banner
            banner = b''
            
            # Some services send banner immediately
            try:
                banner = sock.recv(4096)
            except socket.timeout:
                pass
            
            # If no banner, try sending common probes
            if not banner:
                banner = self._probe_service(sock, port)
            
            sock.close()
            
            # Decode banner
            if banner:
                try:
                    return banner.decode('utf-8', errors='ignore').strip()
                except:
                    return banner.decode('latin-1', errors='ignore').strip()
            
            return None
            
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            return None
        except Exception as e:
            print(f"Banner grab error on {host}:{port} - {e}")
            return None
    
    def _probe_service(self, sock, port):
        """Send service-specific probes to elicit a response"""
        banner = b''
        
        try:
            # HTTP probe
            if port in [80, 443, 8080, 8443]:
                sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
                banner = sock.recv(4096)
            
            # SMTP probe
            elif port in [25, 587]:
                banner = sock.recv(1024)
                if not banner:
                    sock.send(b'EHLO test\r\n')
                    banner = sock.recv(1024)
            
            # FTP probe
            elif port == 21:
                banner = sock.recv(1024)
            
            # Redis probe
            elif port == 6379:
                sock.send(b'PING\r\n')
                banner = sock.recv(1024)
            
            # MySQL probe
            elif port == 3306:
                banner = sock.recv(1024)
            
            # PostgreSQL probe
            elif port == 5432:
                # PostgreSQL startup message
                startup = b'\x00\x00\x00\x08\x04\xd2\x16\x2f'
                sock.send(startup)
                banner = sock.recv(1024)
            
        except:
            pass
        
        return banner
    
    def grab_banners_bulk(self, host, ports):
        """
        Grab banners from multiple ports
        
        :param host: Target hostname or IP
        :param ports: List of (port, protocol) tuples
        :return: Dictionary of {port: banner}
        """
        results = {}
        
        for port_info in ports:
            if isinstance(port_info, tuple):
                port, protocol = port_info
            else:
                port = port_info
                protocol = 'tcp'
            
            banner = self.grab_banner(host, port, protocol)
            if banner:
                results[port] = banner
        
        return results
    
    def identify_service_from_banner(self, banner, port=None):
        """
        Fingerprint service based on banner patterns
        
        :param banner: Banner string
        :param port: Port number (optional, helps with identification)
        :return: Dictionary with service, product, version
        """
        if not banner:
            return {'service': None, 'product': None, 'version': None}
        
        result = {
            'service': None,
            'product': None,
            'version': None
        }
        
        # Try to match against known patterns
        for service_type, patterns in self.service_patterns.items():
            for pattern, product in patterns:
                match = re.search(pattern, banner, re.IGNORECASE)
                if match:
                    result['service'] = service_type
                    result['product'] = product
                    # Extract version if captured
                    if match.groups():
                        result['version'] = match.group(1)
                    return result
        
        # Port-based fallback identification
        if port and not result['service']:
            port_services = {
                22: 'ssh',
                21: 'ftp',
                23: 'telnet',
                25: 'smtp',
                80: 'http',
                443: 'https',
                3306: 'mysql',
                5432: 'postgresql',
                6379: 'redis',
                27017: 'mongodb',
                3389: 'rdp',
                5900: 'vnc'
            }
            result['service'] = port_services.get(port)
        
        return result
    
    def enrich_service_info(self, banner, port, existing_service=None):
        """
        Enrich existing service information with banner analysis
        
        :param banner: Banner string
        :param port: Port number
        :param existing_service: Existing service name from Nmap
        :return: Enriched service dictionary
        """
        fingerprint = self.identify_service_from_banner(banner, port)
        
        return {
            'service': fingerprint['service'] or existing_service,
            'product': fingerprint['product'],
            'version': fingerprint['version'],
            'banner': banner
        }
