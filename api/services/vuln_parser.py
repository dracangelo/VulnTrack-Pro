import json
import logging
import re

# Configure logger
logger = logging.getLogger(__name__)

class VulnParser:
    def parse_nmap_results(self, scan_data):
        """
        Parses normalized Nmap results into a list of vulnerability dictionaries.
        """
        vulnerabilities = []
        
        logger.info(f"Parsing Nmap results: {len(scan_data) if isinstance(scan_data, list) else 'invalid'} items")
        
        # Validate input
        if not scan_data:
            logger.warning("Empty scan_data provided to parse_nmap_results")
            return vulnerabilities
        
        if not isinstance(scan_data, list):
            logger.error(f"Invalid scan_data type: {type(scan_data)}. Expected list.")
            return vulnerabilities
        
        # scan_data is a list of dicts from NmapService.normalize_results
        # [{'port': 80, 'service': 'http', 'product': 'Apache', ...}, ...]
        
        for idx, item in enumerate(scan_data):
            try:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping invalid item at index {idx}: {type(item)}")
                    continue
                
                # Extract port information
                port = item.get('port')
                protocol = item.get('protocol', 'tcp')
                service = item.get('service', 'unknown')
                product = item.get('product', '')
                version = item.get('version', '')
                state = item.get('state', 'open')
                
                # Only process open ports
                if state != 'open':
                    logger.debug(f"Skipping non-open port: {port}/{protocol} (state: {state})")
                    continue
                
                if not port:
                    logger.warning(f"Item at index {idx} missing port number: {item}")
                    continue
                
                # Check for script output which contains actual vulns
                if item.get('script'):
                    for script_id, output in item['script'].items():
                        # Extract CVEs
                        cve_ids = re.findall(r'CVE-\d{4}-\d+', output)
                        cve_id = cve_ids[0] if cve_ids else None
                        
                        # Extract Severity/Risk Factor
                        severity = 'Medium' # Default
                        if 'Risk factor: High' in output or 'High' in output: # Simple heuristic
                            severity = 'High'
                        elif 'Risk factor: Critical' in output or 'Critical' in output:
                            severity = 'Critical'
                        elif 'Risk factor: Low' in output or 'Low' in output:
                            severity = 'Low'
                            
                        # Extract CVSS
                        cvss_score = None
                        cvss_match = re.search(r'CVSS:?\s*(\d+\.\d+)', output)
                        if cvss_match:
                            try:
                                cvss_score = float(cvss_match.group(1))
                                # Update severity based on CVSS if found
                                if cvss_score >= 9.0: severity = 'Critical'
                                elif cvss_score >= 7.0: severity = 'High'
                                elif cvss_score >= 4.0: severity = 'Medium'
                                else: severity = 'Low'
                            except ValueError:
                                pass

                        vuln = {
                            'name': f"Nmap Script: {script_id}",
                            'description': output,
                            'severity': severity,
                            'cve_id': cve_id,
                            'cvss_score': cvss_score,
                            'remediation': 'Check Nmap script output for details.',
                            'port': port,
                            'protocol': protocol,
                            'service': service,
                            'raw_data': item
                        }
                        vulnerabilities.append(vuln)
                        logger.debug(f"Added script vulnerability: {script_id} on port {port}")
                
                # Add the open port as Info-level finding
                # Build descriptive name and description
                service_info = f"{service}"
                if product:
                    service_info += f" ({product}"
                    if version:
                        service_info += f" {version}"
                    service_info += ")"
                
                vuln = {
                    'name': f"Open Port {port}/{protocol} - {service}",
                    'description': f"Port {port}/{protocol} is open running {service_info}. " +
                                   f"Ensure this service is authorized and properly secured.",
                    'severity': 'Info',
                    'cve_id': None,
                    'remediation': 'Verify this port should be accessible. Review service configuration and apply security hardening.',
                    'port': port,
                    'protocol': protocol,
                    'service': service,
                    'raw_data': item
                }
                vulnerabilities.append(vuln)
                logger.debug(f"Added open port finding: {port}/{protocol} ({service})")
                
            except Exception as e:
                logger.error(f"Error parsing item at index {idx}: {e}", exc_info=True)
                continue
        
        logger.info(f"Successfully parsed {len(vulnerabilities)} findings from {len(scan_data)} scan items")
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
