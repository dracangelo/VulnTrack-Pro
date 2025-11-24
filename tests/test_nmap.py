from api.services.nmap_service import NmapService
import json

def test_scan():
    nm = NmapService()
    print("Scanning localhost...")
    result = nm.scan_target('127.0.0.1')
    print("Raw Result Keys:", result.keys())
    
    normalized = nm.normalize_results(result)
    print("Normalized Results:")
    print(json.dumps(normalized, indent=2))

if __name__ == "__main__":
    test_scan()
