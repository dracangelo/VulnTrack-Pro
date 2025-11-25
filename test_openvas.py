#!/usr/bin/env python3
"""Test OpenVAS connection"""
import sys
import os

# Add project to path
sys.path.insert(0, '/home/vng370/Documents/coding/python/vulnhub')

from api.services.openvas_scanner import OpenVASScanner

def main():
    print("Testing OpenVAS/GVM connection...")
    print(f"Socket path: {os.getenv('GVM_SOCKET', '/var/run/gvmd/gvmd.sock')}")
    
    scanner = OpenVASScanner()
    success, message = scanner.test_connection()
    
    if success:
        print(f"✓ SUCCESS: {message}")
        
        # Try to get configs
        print("\nFetching scan configurations...")
        configs = scanner.get_scan_configs()
        if configs:
            print(f"✓ Found {len(configs)} scan configurations:")
            for config in configs[:5]:  # Show first 5
                print(f"  - {config['name']} (ID: {config['id']})")
        else:
            print("✗ No configurations found")
    else:
        print(f"✗ FAILED: {message}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
