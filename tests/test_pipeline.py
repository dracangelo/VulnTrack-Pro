import requests
import time
import json

BASE_URL = 'http://127.0.0.1:5000/api'

def test_pipeline():
    # 1. Create Target
    print("Creating target...")
    target_data = {'name': 'Scan Test Target', 'ip_address': '127.0.0.1', 'description': 'Test target for scan pipeline'}
    res = requests.post(f'{BASE_URL}/targets/', json=target_data)
    if res.status_code != 201:
        print("Failed to create target:", res.text)
        return
    target_id = res.json()['id']
    print(f"Target created with ID: {target_id}")

    # 2. Start Scan
    print("Starting Nmap scan...")
    scan_data = {'target_id': target_id, 'scan_type': 'nmap', 'args': '-sV -T4 -F'}
    res = requests.post(f'{BASE_URL}/scans/', json=scan_data)
    if res.status_code != 201:
        print("Failed to start scan:", res.text)
        return
    scan_id = res.json()['scan_id']
    print(f"Scan started with ID: {scan_id}")

    # 3. Poll Status
    print("Polling scan status...")
    while True:
        res = requests.get(f'{BASE_URL}/scans/')
        scans = res.json()
        my_scan = next((s for s in scans if s['id'] == scan_id), None)
        
        if not my_scan:
            print("Scan not found in list!")
            break
            
        print(f"Status: {my_scan['status']}")
        
        if my_scan['status'] in ['completed', 'failed']:
            break
        
        time.sleep(2)

    print("Scan finished.")
    
    # 4. Verify Results
    print("Verifying vulnerabilities...")
    res = requests.get(f'{BASE_URL}/vulns/instances')
    instances = res.json()
    print(f"Found {len(instances)} vulnerability instances.")
    if len(instances) > 0:
        print("First instance:", instances[0])
    else:
        print("No vulnerabilities found! (Might be expected if localhost has no open ports or scan failed)")
        # Check raw output
        res = requests.get(f'{BASE_URL}/scans/{scan_id}')
        print("Scan Raw Output:", res.json().get('raw_output'))

if __name__ == "__main__":
    test_pipeline()
