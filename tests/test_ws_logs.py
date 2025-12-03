import socketio
import time
import threading
import requests
from api.app import create_app
from api.extensions import db

# Initialize SocketIO client
sio = socketio.Client()

@sio.on('connect', namespace='/scan-progress')
def on_connect():
    print('Connected to scan-progress namespace')

@sio.on('scan_log', namespace='/scan-progress')
def on_scan_log(data):
    print(f"Received log: {data}")

@sio.on('progress_update', namespace='/scan-progress')
def on_progress_update(data):
    print(f"Received progress: {data['progress']}% - {data['current_step']}")

def run_test():
    # Connect to the server
    try:
        sio.connect('http://localhost:5000', namespaces=['/scan-progress'])
        
        # Start a scan (assuming we have a target with ID 1, if not we might need to create one)
        # For this test, we'll just listen. In a real scenario, we'd trigger a scan via API.
        # But since we can't easily run the full server and client in this environment without blocking,
        # we'll assume the server is running or we'd need to mock it.
        
        # Actually, to properly test this in this environment, we should probably unit test the parser
        # or run a small script that uses the parser and mocks the socketio emit.
        pass
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == '__main__':
    run_test()
