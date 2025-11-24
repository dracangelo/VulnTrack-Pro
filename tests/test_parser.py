from api.services.vuln_parser import VulnParser
import json

def test_parser():
    parser = VulnParser()
    
    # Mock Nmap data with script output
    mock_data = [
        {
            'port': 80,
            'protocol': 'tcp',
            'service': 'http',
            'product': 'Apache',
            'version': '2.4.49',
            'script': {
                'http-server-header': 'Apache/2.4.49 (Unix)',
                'http-vuln-cve2021-41773': 'VULNERABLE: Path traversal and file disclosure'
            }
        },
        {
            'port': 22,
            'protocol': 'tcp',
            'service': 'ssh',
            'product': 'OpenSSH',
            'version': '8.2p1',
            'script': {}
        }
    ]
    
    print("Parsing mock Nmap data...")
    vulns = parser.parse_nmap_results(mock_data)
    print(json.dumps(vulns, indent=2))

if __name__ == "__main__":
    test_parser()
