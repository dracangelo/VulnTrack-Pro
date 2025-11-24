import requests
import json

BASE_URL = 'http://127.0.0.1:5000/api'

def test_ticketing():
    # 1. Create Ticket
    print("Creating ticket...")
    ticket_data = {'title': 'Fix Open Port 80', 'description': 'Port 80 shouldn\'t be open on DB server', 'priority': 'high'}
    res = requests.post(f'{BASE_URL}/tickets/', json=ticket_data)
    if res.status_code != 201:
        print("Failed to create ticket:", res.text)
        return
    ticket_id = res.json()['id']
    print(f"Ticket created with ID: {ticket_id}")

    # 2. Bind Vulnerability (Assuming vuln ID 1 exists from previous tests)
    print("Binding vulnerability...")
    bind_data = {'vuln_ids': [1]}
    res = requests.post(f'{BASE_URL}/tickets/{ticket_id}/bind', json=bind_data)
    print("Bind result:", res.text)
    
    # 3. Get Ticket Details
    print("Fetching tickets...")
    res = requests.get(f'{BASE_URL}/tickets/')
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    test_ticketing()
