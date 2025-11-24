import json

class VulnParser:
    def parse_nmap_results(self, scan_data):
        """
        Parses normalized Nmap results into a list of vulnerability dictionaries.
        """
        vulnerabilities = []
        
        # scan_data is a list of dicts from NmapService.normalize_results
        # [{'port': 80, 'service': 'http', 'product': 'Apache', ...}, ...]
        
        for item in scan_data:
            # Basic open port is not necessarily a vulnerability, but for this context
            # we might want to track open ports as "Info" level findings or look for specific things.
            # However, usually Nmap vulns come from scripts (-sC or --script vuln).
            # If we just ran -sV -F, we mostly have open ports.
            # Let's treat every open port as an "Open Port" finding for now, 
            # or if 'script' output exists (not currently in normalize_results), parse that.
            
            # Check for script output which contains actual vulns
            if item.get('script'):
                for script_id, output in item['script'].items():
                    vuln = {
                        'name': f"Nmap Script: {script_id}",
                        'description': output,
                        'severity': 'Medium', # Default for scripts, ideally map script_id to severity
                        'cve_id': None, # Would need regex extraction from output
                        'remediation': 'Check Nmap script output for details.',
                        'raw_data': item
                    }
                    vulnerabilities.append(vuln)
            
            # Also add the open port as Info
            vuln = {
                'name': f"Open Port {item.get('port')}/{item.get('protocol')} ({item.get('service')})",
                'description': f"Port {item.get('port')} is open. Service: {item.get('service')} {item.get('product')} {item.get('version')}",
                'severity': 'Info', # Default to Info for open ports
                'cve_id': None,
                'remediation': 'Ensure this port is intended to be open.',
                'raw_data': item
            }
            vulnerabilities.append(vuln)
            
        return vulnerabilities

    def parse_openvas_results(self, report_xml):
        """
        Parses OpenVAS XML report into vulnerability dictionaries.
        """
        vulnerabilities = []
        # This would require lxml to parse the XML report from OpenVAS.
        # Structure usually involves <result> tags with <name>, <description>, <threat> (severity), etc.
        
        # Mock implementation for now as we don't have real XML yet
        # In a real scenario, we'd use lxml.etree
        
        return vulnerabilities
