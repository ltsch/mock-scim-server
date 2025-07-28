#!/usr/bin/env python3
"""
Test SCIM Server Logging

This script tests the new logging functionality by making various requests
to the SCIM server to verify that 404s and other errors are properly logged.
"""

import requests
import json
import time

def test_logging():
    """Test various requests to trigger logging."""
    base_url = "http://localhost:7001"
    
    print("🧪 Testing SCIM Server Logging")
    print("=" * 50)
    
    # Test 1: Valid request
    print("\n1️⃣ Testing valid request...")
    try:
        response = requests.get(f"{base_url}/healthz")
        print(f"   Status: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: 404 - Non-existent endpoint
    print("\n2️⃣ Testing 404 error...")
    try:
        response = requests.get(f"{base_url}/nonexistent-endpoint")
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            data = response.json()
            print(f"   Error: {data.get('message', 'Unknown error')}")
            print(f"   Help available: {len(data.get('help', {}).get('available_endpoints', []))} endpoints listed")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: 404 - Wrong SCIM path
    print("\n3️⃣ Testing wrong SCIM path...")
    try:
        response = requests.get(f"{base_url}/scim/v2/WrongEndpoint")
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            data = response.json()
            print(f"   Error: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: 401 - Missing authentication
    print("\n4️⃣ Testing 401 error (missing auth)...")
    try:
        response = requests.get(f"{base_url}/scim/v2/Users")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   Expected: Authentication required")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: 405 - Method not allowed
    print("\n5️⃣ Testing 405 error (wrong method)...")
    try:
        response = requests.post(f"{base_url}/healthz", json={})
        print(f"   Status: {response.status_code}")
        if response.status_code == 405:
            print("   Expected: Method not allowed")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 6: Valid SCIM request
    print("\n6️⃣ Testing valid SCIM request...")
    try:
        headers = {"Authorization": "Bearer test-api-key-12345"}
        response = requests.get(f"{base_url}/scim-identifier/test-server/scim/v2/Users", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Users returned: {data.get('totalResults', 0)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Logging test completed!")
    print("📋 Check the logs to see detailed information about each request:")
    print("   - Console output (if running in terminal)")
    print("   - Log file: ./logs/scim_server.log")
    print("   - Use: python3 scripts/check_logs.py --follow")

if __name__ == "__main__":
    test_logging() 