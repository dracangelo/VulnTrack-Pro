from api.services.openvas_scanner import OpenVASScanner

def test_default_configs():
    scanner = OpenVASScanner()
    
    print("Fetching configs (expecting defaults due to connection failure)...")
    configs = scanner.get_scan_configs()
    
    if configs and len(configs) > 0:
        print(f"✓ Successfully retrieved {len(configs)} configurations")
        print(f"First config: {configs[0]}")
        
        # Verify it matches our defaults
        if configs[0]['name'] == 'Full and fast':
             print("✓ Configs appear to be the defaults")
        else:
             print("? Configs might be real or different defaults")
    else:
        print("✗ Failed to retrieve configs")
        exit(1)

if __name__ == "__main__":
    test_default_configs()
