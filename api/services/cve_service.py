import os
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timedelta
import json

class CVEService:
    def __init__(self):
        # Default paths to check for nuclei templates
        self.template_paths = [
            os.path.expanduser('~/nuclei-templates'),
            os.path.expanduser('~/.local/nuclei-templates'),
            '/usr/share/nuclei-templates'
        ]
        self.templates_dir = self._find_templates_dir()
        
        # NVD API configuration
        self.nvd_api_base = 'https://services.nvd.nist.gov/rest/json/cves/2.0'
        self.nvd_cache = {}  # Simple in-memory cache
        self.cache_ttl = timedelta(hours=24)

    def _find_templates_dir(self):
        for path in self.template_paths:
            if os.path.exists(path) and os.path.isdir(path):
                return path
        return None

    def find_nuclei_templates(self, cve_id):
        """
        Find Nuclei templates matching a CVE ID.
        """
        if not cve_id or not self.templates_dir:
            return []
            
        cve_id = cve_id.upper()
        matches = []
        
        # Walk through the templates directory
        for root, _, files in os.walk(self.templates_dir):
            for file in files:
                if file.endswith('.yaml'):
                    # Check if filename contains CVE ID (simple heuristic)
                    # Nuclei templates usually follow cve-YYYY-XXXX.yaml format
                    if cve_id.lower() in file.lower():
                        full_path = os.path.join(root, file)
                        relative_path = os.path.relpath(full_path, self.templates_dir)
                        
                        # Read file to get name/description if possible
                        name = file
                        severity = 'unknown'
                        try:
                            with open(full_path, 'r') as f:
                                content = f.read()
                                # Basic parsing for 'name:' and 'severity:' fields
                                for line in content.splitlines():
                                    if line.strip().startswith('name:'):
                                        name = line.split(':', 1)[1].strip().strip('"\'')
                                    elif line.strip().startswith('severity:'):
                                        severity = line.split(':', 1)[1].strip().lower()
                        except:
                            pass
                            
                        matches.append({
                            'name': name,
                            'path': relative_path,
                            'full_path': full_path,
                            'severity': severity
                        })
                        
        return matches

    def fetch_cve_from_nvd(self, cve_id):
        """
        Fetch detailed CVE data from NVD API 2.0
        Returns comprehensive CVE information including CVSS scores
        """
        # Check cache first
        if cve_id in self.nvd_cache:
            cached_data, cached_time = self.nvd_cache[cve_id]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_data
        
        try:
            # NVD API 2.0 endpoint
            url = f"{self.nvd_api_base}?cveId={cve_id}"
            
            headers = {
                'User-Agent': 'VulnTrack-Pro/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return {'error': f'NVD API returned status {response.status_code}'}
            
            data = response.json()
            
            if 'vulnerabilities' not in data or len(data['vulnerabilities']) == 0:
                return {'error': 'CVE not found in NVD database'}
            
            # Extract CVE data
            vuln = data['vulnerabilities'][0]['cve']
            
            # Parse description
            description = ''
            if 'descriptions' in vuln:
                for desc in vuln['descriptions']:
                    if desc['lang'] == 'en':
                        description = desc['value']
                        break
            
            # Parse CVSS scores
            cvss_v3 = None
            cvss_v2 = None
            severity = 'UNKNOWN'
            
            if 'metrics' in vuln:
                # CVSS v3
                if 'cvssMetricV31' in vuln['metrics']:
                    cvss_data = vuln['metrics']['cvssMetricV31'][0]['cvssData']
                    cvss_v3 = {
                        'score': cvss_data['baseScore'],
                        'vector': cvss_data['vectorString'],
                        'severity': cvss_data['baseSeverity']
                    }
                    severity = cvss_data['baseSeverity']
                elif 'cvssMetricV30' in vuln['metrics']:
                    cvss_data = vuln['metrics']['cvssMetricV30'][0]['cvssData']
                    cvss_v3 = {
                        'score': cvss_data['baseScore'],
                        'vector': cvss_data['vectorString'],
                        'severity': cvss_data['baseSeverity']
                    }
                    severity = cvss_data['baseSeverity']
                
                # CVSS v2 (fallback)
                if 'cvssMetricV2' in vuln['metrics']:
                    cvss_data = vuln['metrics']['cvssMetricV2'][0]['cvssData']
                    cvss_v2 = {
                        'score': cvss_data['baseScore'],
                        'vector': cvss_data['vectorString']
                    }
            
            # Parse CPE list
            cpe_list = []
            if 'configurations' in vuln:
                for config in vuln['configurations']:
                    for node in config.get('nodes', []):
                        for cpe_match in node.get('cpeMatch', []):
                            if 'criteria' in cpe_match:
                                cpe_list.append(cpe_match['criteria'])
            
            # Parse references
            references = []
            if 'references' in vuln:
                for ref in vuln['references'][:10]:  # Limit to 10 references
                    references.append({
                        'url': ref['url'],
                        'source': ref.get('source', 'Unknown')
                    })
            
            # Build result
            result = {
                'cve_id': cve_id,
                'description': description,
                'cvss_v3': cvss_v3,
                'cvss_v2': cvss_v2,
                'severity': severity,
                'published_date': vuln.get('published', ''),
                'last_modified': vuln.get('lastModified', ''),
                'cpe_list': list(set(cpe_list)),  # Deduplicate
                'references': references
            }
            
            # Cache the result
            self.nvd_cache[cve_id] = (result, datetime.now())
            
            return result
            
        except requests.exceptions.Timeout:
            return {'error': 'NVD API request timed out'}
        except requests.exceptions.RequestException as e:
            return {'error': f'NVD API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Error parsing NVD data: {str(e)}'}

    def search_exploit_db_online(self, cve_id):
        """
        Search Exploit-DB website for exploits (web scraping fallback)
        Returns list of exploit results
        """
        try:
            # Exploit-DB search URL
            url = f"https://www.exploit-db.com/search?cve={cve_id}"
            
            # Note: This would require web scraping or API access
            # For now, return the search URL
            return {
                'search_url': url,
                'note': 'Use searchsploit command for detailed results'
            }
        except Exception as e:
            return {'error': str(e)}

    def enrich_cve_data(self, cve_id):
        """
        Comprehensive CVE enrichment combining multiple sources
        """
        enrichment = {
            'cve_id': cve_id,
            'nvd_data': None,
            'nuclei_templates': [],
            'exploit_db_link': f"https://www.exploit-db.com/search?cve={cve_id}",
            'enriched_at': datetime.utcnow().isoformat()
        }
        
        # Fetch from NVD
        nvd_data = self.fetch_cve_from_nvd(cve_id)
        if 'error' not in nvd_data:
            enrichment['nvd_data'] = nvd_data
        
        # Find Nuclei templates
        templates = self.find_nuclei_templates(cve_id)
        enrichment['nuclei_templates'] = templates
        
        # Add useful links
        enrichment['links'] = self.get_cve_details(cve_id)
        
        return enrichment

    def get_cve_details(self, cve_id):
        """
        Get basic details/links for a CVE.
        """
        return {
            'cve_id': cve_id,
            'nvd_link': f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            'mitre_link': f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id}",
            'exploit_db_link': f"https://www.exploit-db.com/search?cve={cve_id}",
            'github_search': f"https://github.com/search?q={cve_id}+poc&type=repositories"
        }
    
    def extract_cve_ids(self, text):
        """
        Extract CVE IDs from text using regex
        Returns list of CVE IDs found
        """
        import re
        if not text:
            return []
        
        # Pattern: CVE-YYYY-NNNNN
        pattern = r'CVE-\d{4}-\d{4,7}'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        # Normalize to uppercase and deduplicate
        return list(set([cve.upper() for cve in matches]))

