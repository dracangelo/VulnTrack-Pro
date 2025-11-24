import requests
from api.extensions import db
from api.models.activity_log import ActivityLog
from api import create_app

BASE_URL = 'http://127.0.0.1:5000/api'

def test_activity():
    # 1. Create Ticket via API (should trigger log)
    print("Creating ticket to trigger log...")
    ticket_data = {'title': 'Activity Log Test Ticket', 'priority': 'low'}
    res = requests.post(f'{BASE_URL}/tickets/', json=ticket_data)
    if res.status_code != 201:
        print("Failed to create ticket:", res.text)
        return
    ticket_id = res.json()['id']
    print(f"Ticket created with ID: {ticket_id}")

    # 2. Verify Log in DB directly (since we don't have an API for logs yet)
    print("Verifying log in database...")
    app = create_app()
    with app.app_context():
        log = ActivityLog.query.filter_by(target_type='Ticket', target_id=ticket_id).first()
        if log:
            print(f"Log found! Action: {log.action}, Details: {log.details}")
        else:
            print("No log found for this ticket.")

if __name__ == "__main__":
    test_activity()
