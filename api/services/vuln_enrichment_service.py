from datetime import datetime
from api.extensions import db
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.services.cve_service import CVEService
from api.services.exploit_service import ExploitService
import json

class VulnEnrichmentService:
    """Service for enriching vulnerabilities with CVE and exploit data"""
    
    def __init__(self):
        self.cve_service = CVEService()
        self.exploit_service = ExploitService()
    
    def enrich_vulnerability(self, vuln_id):
        """
        Enrich a vulnerability with CVE and exploit data
        
        :param vuln_id: Vulnerability ID
        :return: Enrichment summary
        """
        vuln = Vulnerability.query.get(vuln_id)
        if not vuln:
            return {'error': 'Vulnerability not found'}
        
        # Extract CVE IDs from vulnerability name and description
        cve_ids = self.cve_service.extract_cve_ids(vuln.name)
        if vuln.description:
            cve_ids.extend(self.cve_service.extract_cve_ids(vuln.description))
        
        cve_ids = list(set(cve_ids))  # Deduplicate
        
        if not cve_ids:
            return {'message': 'No CVE IDs found in vulnerability'}
        
        enrichment_data = {
            'cve_ids': cve_ids,
            'cve_details': [],
            'exploits_found': 0,
            'nuclei_templates_found': 0
        }
        
        # Enrich with first CVE (primary)
        primary_cve = cve_ids[0]
        cve_data = self.cve_service.enrich_cve_data(primary_cve)
        
        if cve_data and 'nvd_data' in cve_data and cve_data['nvd_data']:
            nvd = cve_data['nvd_data']
            
            # Update vulnerability with CVE data
            vuln.cve_ids = json.dumps(cve_ids)
            
            if nvd.get('cvss_v3'):
                vuln.cvss_score = nvd['cvss_v3']['score']
                vuln.cvss_vector = nvd['cvss_v3']['vector']
            elif nvd.get('cvss_v2'):
                vuln.cvss_score = nvd['cvss_v2']['score']
                vuln.cvss_vector = nvd['cvss_v2']['vector']
            
            if nvd.get('published_date'):
                try:
                    vuln.cve_published_date = datetime.fromisoformat(
                        nvd['published_date'].replace('Z', '+00:00')
                    )
                except:
                    pass
        
        # Search for exploits
        exploit_sources = {}
        
        # Searchsploit
        try:
            searchsploit_results = self.exploit_service.search_exploits(primary_cve)
            if isinstance(searchsploit_results, list):
                exploit_sources['searchsploit'] = len(searchsploit_results)
                enrichment_data['exploits_found'] += len(searchsploit_results)
        except:
            pass
        
        # Nuclei templates
        if cve_data.get('nuclei_templates'):
            nuclei_count = len(cve_data['nuclei_templates'])
            exploit_sources['nuclei'] = nuclei_count
            enrichment_data['nuclei_templates_found'] = nuclei_count
            vuln.nuclei_templates = json.dumps(cve_data['nuclei_templates'])
        
        # Update exploit availability
        vuln.has_exploit = enrichment_data['exploits_found'] > 0
        vuln.exploit_count = enrichment_data['exploits_found']
        vuln.exploit_sources = json.dumps(exploit_sources)
        
        # Mark as enriched
        vuln.enriched_at = datetime.utcnow()
        vuln.enrichment_source = 'nvd'
        
        db.session.commit()
        
        enrichment_data['cve_details'] = cve_data
        return enrichment_data
    
    def auto_enrich_scan_results(self, scan_id):
        """
        Automatically enrich all vulnerabilities from a scan
        
        :param scan_id: Scan ID
        :return: Number of vulnerabilities enriched
        """
        from api.models.scan import Scan
        
        scan = Scan.query.get(scan_id)
        if not scan:
            return 0
        
        # Get all vulnerability instances from this scan
        vuln_instances = VulnerabilityInstance.query.filter_by(scan_id=scan_id).all()
        
        enriched_count = 0
        processed_vulns = set()
        
        for instance in vuln_instances:
            vuln_id = instance.vulnerability_id
            
            # Skip if already processed in this batch
            if vuln_id in processed_vulns:
                continue
            
            processed_vulns.add(vuln_id)
            
            try:
                result = self.enrich_vulnerability(vuln_id)
                if 'error' not in result:
                    enriched_count += 1
            except Exception as e:
                print(f"Error enriching vulnerability {vuln_id}: {e}")
        
        return enriched_count
    
    def match_exploits_to_vulnerability(self, vuln_id):
        """
        Find all available exploits for a vulnerability
        
        :param vuln_id: Vulnerability ID
        :return: Dictionary with exploit sources
        """
        vuln = Vulnerability.query.get(vuln_id)
        if not vuln:
            return {'error': 'Vulnerability not found'}
        
        results = {
            'vulnerability_id': vuln_id,
            'vulnerability_name': vuln.name,
            'searchsploit': [],
            'nuclei': [],
            'metasploit': []  # Placeholder for future Metasploit integration
        }
        
        # Extract CVE IDs
        cve_ids = []
        if vuln.cve_ids:
            try:
                cve_ids = json.loads(vuln.cve_ids)
            except:
                cve_ids = self.cve_service.extract_cve_ids(vuln.name)
        else:
            cve_ids = self.cve_service.extract_cve_ids(vuln.name)
        
        if not cve_ids:
            return results
        
        primary_cve = cve_ids[0]
        
        # Search exploits
        try:
            searchsploit_results = self.exploit_service.search_exploits(primary_cve)
            if isinstance(searchsploit_results, list):
                results['searchsploit'] = searchsploit_results
        except:
            pass
        
        # Find Nuclei templates
        try:
            if vuln.nuclei_templates:
                results['nuclei'] = json.loads(vuln.nuclei_templates)
            else:
                results['nuclei'] = self.cve_service.find_nuclei_templates(primary_cve)
        except:
            pass
        
        return results
