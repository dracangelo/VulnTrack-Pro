import requests
import json

BASE_URL = 'http://127.0.0.1:5000/api'

def test_notification():
    # 1. Create User (Assignee)
    print("Creating user...")
    user_data = {'username': 'assignee_user', 'email': 'assignee@example.com', 'password': 'password'}
    res = requests.post(f'{BASE_URL}/users/', json=user_data)
    if res.status_code == 201:
        user_id = res.json()['id']
        print(f"User created with ID: {user_id}")
    else:
        # Assuming user might already exist from previous runs, try to get list or just use ID 1
        print("User creation failed (maybe exists), using ID 1")
        user_id = 1

    # 2. Create Ticket
    print("Creating ticket...")
    ticket_data = {'title': 'Notification Test Ticket', 'priority': 'medium'}
    res = requests.post(f'{BASE_URL}/tickets/', json=ticket_data)
    ticket_id = res.json()['id']
    print(f"Ticket created with ID: {ticket_id}")

    # 3. Assign Ticket (Should trigger notification)
    print("Assigning ticket to user...")
    update_data = {'assignee_id': user_id}
    res = requests.put(f'{BASE_URL}/tickets/{ticket_id}', json=update_data)
    print("Update result:", res.text)
    
    # Check server output for "NOTIFICATION for User..."

if __name__ == "__main__":
    test_notification()
