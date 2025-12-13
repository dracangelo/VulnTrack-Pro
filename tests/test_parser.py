import pytest
from api.services.vuln_parser import VulnParser

class TestVulnParser:
    @pytest.fixture
    def parser(self):
        return VulnParser()

    def test_parse_empty_input(self, parser):
        assert parser.parse_nmap_results([]) == []
        assert parser.parse_nmap_results(None) == []

    def test_parse_invalid_input(self, parser):
        assert parser.parse_nmap_results("invalid") == []
        assert parser.parse_nmap_results([123]) == [] # Should handle invalid items gracefully

    def test_parse_basic_open_port(self, parser):
        data = [{
            'port': 80,
            'protocol': 'tcp',
            'service': 'http',
            'state': 'open',
            'product': 'Apache',
            'version': '2.4.49'
        }]
        vulns = parser.parse_nmap_results(data)
        assert len(vulns) == 1
        assert vulns[0]['severity'] == 'Info'
        assert 'Open Port 80/tcp' in vulns[0]['name']
        assert 'Apache 2.4.49' in vulns[0]['description']

    def test_parse_script_vuln_cve(self, parser):
        data = [{
            'port': 80,
            'protocol': 'tcp',
            'service': 'http',
            'state': 'open',
            'script': {
                'http-vuln-cve2021-41773': 'VULNERABLE: Path traversal\nCVE-2021-41773\nRisk factor: High'
            }
        }]
        vulns = parser.parse_nmap_results(data)
        # Should have 2 findings: 1 Info (open port) + 1 High (script)
        assert len(vulns) == 2
        
        script_vuln = next(v for v in vulns if v['severity'] != 'Info')
        assert script_vuln['severity'] == 'High'
        assert script_vuln['cve_id'] == 'CVE-2021-41773'
        assert 'http-vuln-cve2021-41773' in script_vuln['name']

    def test_parse_script_vuln_cvss(self, parser):
        data = [{
            'port': 443,
            'protocol': 'tcp',
            'service': 'https',
            'state': 'open',
            'script': {
                'ssl-heartbleed': 'VULNERABLE:\nCVSS: 9.8'
            }
        }]
        vulns = parser.parse_nmap_results(data)
        script_vuln = next(v for v in vulns if v['severity'] != 'Info')
        
        assert script_vuln['severity'] == 'Critical' # 9.8 >= 9.0
        assert script_vuln['cvss_score'] == 9.8

    def test_parse_script_vuln_severity_keywords(self, parser):
        data = [{
            'port': 21,
            'state': 'open',
            'script': {
                'ftp-anon': 'Anonymous FTP login allowed (Low)'
            }
        }]
        vulns = parser.parse_nmap_results(data)
        script_vuln = next(v for v in vulns if v['severity'] != 'Info')
        assert script_vuln['severity'] == 'Low'

    def test_skip_closed_ports(self, parser):
        data = [{
            'port': 80,
            'state': 'closed'
        }]
        vulns = parser.parse_nmap_results(data)
        assert len(vulns) == 0
