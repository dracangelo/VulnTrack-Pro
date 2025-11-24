import requests

BASE_URL = 'http://127.0.0.1:5000'

def test_errors():
    print("Testing 404 Error...")
    res = requests.get(f'{BASE_URL}/non-existent-route')
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    
    if res.status_code == 404 and res.headers['Content-Type'] == 'application/json':
        print("404 JSON response verified.")
    else:
        print("404 verification failed.")

if __name__ == "__main__":
    test_errors()
