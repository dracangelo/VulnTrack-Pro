from api.services.openvas_scanner import OpenVASScanner
import inspect

def test_methods_exist():
    scanner = OpenVASScanner()
    
    methods = ['launch_scan', 'connect', 'disconnect']
    missing = []
    
    for method in methods:
        if not hasattr(scanner, method):
            missing.append(method)
        else:
            print(f"✓ Method '{method}' exists")
            
    if missing:
        print(f"✗ Missing methods: {missing}")
        exit(1)
    else:
        print("All required methods exist.")

    # Test calling them (mocking internal calls would be better, but simple existence check is good first step)
    try:
        scanner.connect()
        print("✓ connect() called successfully")
        scanner.disconnect()
        print("✓ disconnect() called successfully")
    except Exception as e:
        print(f"✗ Error calling connect/disconnect: {e}")
        exit(1)

if __name__ == "__main__":
    test_methods_exist()
