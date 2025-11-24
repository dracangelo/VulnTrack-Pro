#!/usr/bin/env python3
"""
Test script for VulnTrack Pro advanced scanning features
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_openvas_configs():
    """Test OpenVAS configuration endpoints"""
    print("\n=== Testing OpenVAS Configuration Endpoints ===")
    
    # Test connection
    print("Testing OpenVAS connection...")
    response = requests.get(f"{BASE_URL}/api/openvas/test-connection")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Fetch configs
    print("\nFetching OpenVAS configs...")
    response = requests.get(f"{BASE_URL}/api/openvas/configs")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Success: {data.get('success')}")
    print(f"Configs found: {len(data.get('configs', []))}")
    if data.get('configs'):
        print(f"First config: {data['configs'][0]}")

def test_schedule_validation():
    """Test schedule cron validation"""
    print("\n=== Testing Schedule Cron Validation ===")
    
    test_crons = [
        "0 2 * * *",  # Daily at 2 AM
        "*/30 * * * *",  # Every 30 minutes
        "0 9 * * 1",  # Every Monday at 9 AM
        "invalid cron"  # Invalid
    ]
    
    for cron in test_crons:
        print(f"\nValidating: {cron}")
        response = requests.post(
            f"{BASE_URL}/api/schedules/validate-cron",
            json={"cron_expression": cron}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

def test_schedule_crud():
    """Test schedule CRUD operations"""
    print("\n=== Testing Schedule CRUD Operations ===")
    
    # Get targets first
    print("Fetching targets...")
    response = requests.get(f"{BASE_URL}/api/targets/")
    targets = response.json()
    
    if not targets:
        print("No targets found. Please create a target first.")
        return
    
    target_id = targets[0]['id']
    print(f"Using target ID: {target_id}")
    
    # Create schedule
    print("\nCreating schedule...")
    schedule_data = {
        "name": "Test Automated Scan",
        "description": "Test schedule created by test script",
        "target_id": target_id,
        "scan_type": "nmap",
        "scanner_args": "-F",
        "cron_expression": "*/5 * * * *",  # Every 5 minutes
        "enabled": False  # Disabled for testing
    }
    
    response = requests.post(
        f"{BASE_URL}/api/schedules/",
        json=schedule_data
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        schedule = response.json()
        schedule_id = schedule['id']
        print(f"Created schedule ID: {schedule_id}")
        print(f"Next run: {schedule.get('next_run')}")
        
        # List schedules
        print("\nListing all schedules...")
        response = requests.get(f"{BASE_URL}/api/schedules/")
        schedules = response.json()
        print(f"Total schedules: {len(schedules)}")
        
        # Update schedule
        print(f"\nUpdating schedule {schedule_id}...")
        response = requests.put(
            f"{BASE_URL}/api/schedules/{schedule_id}",
            json={"description": "Updated description"}
        )
        print(f"Status: {response.status_code}")
        
        # Toggle schedule
        print(f"\nToggling schedule {schedule_id}...")
        response = requests.post(f"{BASE_URL}/api/schedules/{schedule_id}/toggle")
        print(f"Status: {response.status_code}")
        updated_schedule = response.json()
        print(f"Enabled: {updated_schedule.get('enabled')}")
        
        # Delete schedule
        print(f"\nDeleting schedule {schedule_id}...")
        response = requests.delete(f"{BASE_URL}/api/schedules/{schedule_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    else:
        print(f"Failed to create schedule: {response.json()}")

def test_queue_status():
    """Test queue status endpoint"""
    print("\n=== Testing Queue Status ===")
    
    response = requests.get(f"{BASE_URL}/api/scans/queue/status")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Max concurrent: {data.get('max_concurrent')}")
    print(f"Active scans: {data.get('active_count')}")
    print(f"Queue size: {data.get('queue_size')}")

def main():
    print("VulnTrack Pro - Advanced Features Test Suite")
    print("=" * 50)
    
    try:
        # Test queue status
        test_queue_status()
        
        # Test OpenVAS endpoints
        test_openvas_configs()
        
        # Test schedule validation
        test_schedule_validation()
        
        # Test schedule CRUD
        test_schedule_crud()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to VulnTrack Pro.")
        print("Please ensure the application is running on http://localhost:5000")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    main()
