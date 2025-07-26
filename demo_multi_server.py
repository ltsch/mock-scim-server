#!/usr/bin/env python3
"""Multi-server SCIM demo"""

import requests
import json

BASE_URL = "http://localhost:6000"
API_KEY = "test-api-key-12345"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def demo():
    print("🚀 Multi-Server SCIM Demo")
    
    # Create users in different servers
    servers = ["demo-server-1", "demo-server-2"]
    
    for server_id in servers:
        user_data = {
            "userName": f"demo_user_{server_id}@example.com",
            "displayName": f"Demo User {server_id}",
            "name": {"givenName": "Demo", "familyName": server_id},
            "emails": [{"value": f"demo_user_{server_id}@example.com", "primary": True}],
            "active": True
        }
        
        response = requests.post(
            f"{BASE_URL}/v2/Users/?serverID={server_id}",
            headers=HEADERS,
            json=user_data
        )
        
        if response.status_code == 201:
            print(f"✅ Created user in {server_id}")
        else:
            print(f"❌ Failed to create user in {server_id}")
    
    # List users in each server
    for server_id in servers:
        response = requests.get(f"{BASE_URL}/v2/Users/?serverID={server_id}", headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📋 {server_id}: {data['totalResults']} users")
        else:
            print(f"❌ Failed to list users in {server_id}")
    
    print("🎉 Demo completed!")

if __name__ == "__main__":
    try:
        demo()
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Run: python run_server.py")
    except Exception as e:
        print(f"❌ Demo failed: {e}") 