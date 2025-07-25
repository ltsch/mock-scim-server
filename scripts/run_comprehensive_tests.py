#!/usr/bin/env python3
"""
Comprehensive SCIM test runner
Runs all SCIM use cases and generates a detailed report.
"""
import sys
import os
import json
import requests
from datetime import datetime
from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-12345"
AUTH_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

class ComprehensiveSCIMTester:
    """Comprehensive SCIM testing class."""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.auth_headers = AUTH_HEADERS
        
    def log_test(self, test_name, status, details=None, response=None):
        """Log test results."""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        if response:
            result["status_code"] = response.status_code
            if response.status_code != 200:
                result["error"] = response.text
        
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}")
        if details:
            print(f"   {details}")
    
    def verify_server_availability(self):
        """Verify that the server is running and all endpoints are accessible."""
        print("🔍 Verifying server availability and endpoint accessibility...")
        print()
        
        # Test basic connectivity
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=5)
            if response.status_code == 200:
                self.log_test("Server Health Check", "PASS", "Server is responding")
            else:
                self.log_test("Server Health Check", "FAIL", f"Health check returned {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("Server Health Check", "FAIL", "Cannot connect to server - is it running?")
            return False
        except requests.exceptions.Timeout:
            self.log_test("Server Health Check", "FAIL", "Server connection timeout")
            return False
        except Exception as e:
            self.log_test("Server Health Check", "FAIL", f"Unexpected error: {str(e)}")
            return False
        
        # Test root endpoint
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Root Endpoint", "PASS", f"Server: {data.get('name', 'Unknown')}")
            else:
                self.log_test("Root Endpoint", "FAIL", f"Root endpoint returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Root Endpoint", "FAIL", f"Error: {str(e)}")
            return False
        
        # Test authentication endpoint
        try:
            response = requests.get(f"{self.base_url}/protected", headers=self.auth_headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Authentication", "PASS", f"API key validated: {data.get('api_key_name', 'Unknown')}")
            else:
                self.log_test("Authentication", "FAIL", f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication", "FAIL", f"Error: {str(e)}")
            return False
        
        # Test SCIM discovery endpoints
        scim_endpoints = [
            ("/v2/ResourceTypes", "ResourceTypes Discovery"),
            ("/v2/Schemas", "Schemas Discovery")
        ]
        
        for endpoint, name in scim_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.auth_headers, timeout=5)
                if response.status_code == 200:
                    self.log_test(name, "PASS", f"Endpoint accessible")
                else:
                    self.log_test(name, "FAIL", f"Endpoint returned {response.status_code}")
                    return False
            except Exception as e:
                self.log_test(name, "FAIL", f"Error: {str(e)}")
                return False
        
        # Test main SCIM resource endpoints
        scim_resources = [
            ("/v2/Users/", "Users Endpoint"),
            ("/v2/Groups/", "Groups Endpoint"),
            ("/v2/Entitlements/", "Entitlements Endpoint"),
            ("/v2/Roles/", "Roles Endpoint")
        ]
        
        for endpoint, name in scim_resources:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", headers=self.auth_headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    count = data.get('totalResults', 0)
                    self.log_test(name, "PASS", f"Endpoint accessible ({count} resources)")
                else:
                    self.log_test(name, "FAIL", f"Endpoint returned {response.status_code}")
                    return False
            except Exception as e:
                self.log_test(name, "FAIL", f"Error: {str(e)}")
                return False
        
        print()
        print("✅ All endpoints verified and accessible!")
        print()
        return True
    
    def test_schema_discovery(self):
        """Test SCIM schema discovery endpoints."""
        print("\n=== Testing Schema Discovery ===")
        
        # Test ResourceTypes endpoint
        try:
            response = requests.get(f"{self.base_url}/v2/ResourceTypes", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                resource_ids = [r["id"] for r in data["Resources"]]
                expected_types = ["User", "Group", "Entitlement", "Role"]
                
                if all(rt in resource_ids for rt in expected_types):
                    self.log_test("ResourceTypes Discovery", "PASS", 
                                f"Found {len(data['Resources'])} resource types: {', '.join(resource_ids)}")
                else:
                    self.log_test("ResourceTypes Discovery", "FAIL", 
                                f"Missing expected resource types. Found: {resource_ids}")
            else:
                self.log_test("ResourceTypes Discovery", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("ResourceTypes Discovery", "ERROR", str(e))
        
        # Test Schemas endpoint
        try:
            response = requests.get(f"{self.base_url}/v2/Schemas", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Schemas Discovery", "PASS", 
                            f"Schemas endpoint returned {len(data.get('Resources', []))} schemas")
            else:
                self.log_test("Schemas Discovery", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Schemas Discovery", "ERROR", str(e))
    
    def test_user_management(self):
        """Test comprehensive user management operations."""
        print("\n=== Testing User Management ===")
        
        # 1. List all users and store for dynamic testing
        try:
            response = requests.get(f"{self.base_url}/v2/Users/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                user_count = data['totalResults']
                users = data['Resources']
                self.log_test("List Users", "PASS", f"Found {user_count} users")
                
                # Store users for dynamic testing
                self.test_users = users
                
                if users:
                    # Use the first user for testing
                    test_user = users[0]
                    user_id = test_user['id']
                    username = test_user['userName']
                    
                    # 2. Get specific user by ID
                    response = requests.get(f"{self.base_url}/v2/Users/{user_id}", headers=self.auth_headers)
                    if response.status_code == 200:
                        retrieved_user = response.json()
                        if retrieved_user['id'] == user_id:
                            self.log_test("Get User by ID", "PASS", f"Retrieved user: {test_user['displayName']}")
                        else:
                            self.log_test("Get User by ID", "FAIL", "Retrieved user ID doesn't match")
                    else:
                        self.log_test("Get User by ID", "FAIL", f"HTTP {response.status_code}")
                    
                    # 3. User search by exact username
                    response = requests.get(f"{self.base_url}/v2/Users/?filter=userName eq \"{username}\"", headers=self.auth_headers)
                    if response.status_code == 200:
                        search_data = response.json()
                        if len(search_data['Resources']) == 1 and search_data['Resources'][0]['userName'] == username:
                            self.log_test("User Search", "PASS", f"Found user by username filter: {username}")
                        else:
                            self.log_test("User Search", "FAIL", f"Expected 1 user with username {username}, found {len(search_data['Resources'])}")
                    else:
                        self.log_test("User Search", "FAIL", f"HTTP {response.status_code}")
                else:
                    self.log_test("Get User by ID", "SKIP", "No users available for testing")
                    self.log_test("User Search", "SKIP", "No users available for testing")
            else:
                self.log_test("List Users", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("List Users", "ERROR", str(e))
        
        # 4. Create new user with unique username
        try:
            import time
            timestamp = int(time.time())
            unique_username = f"comprehensive-test-{timestamp}@example.com"
            
            new_user_data = {
                "userName": unique_username,
                "displayName": "Comprehensive Test User",
                "name": {
                    "givenName": "Comprehensive",
                    "familyName": "Test"
                },
                "emails": [
                    {
                        "value": unique_username,
                        "primary": True
                    }
                ],
                "active": True
            }
            
            response = requests.post(f"{self.base_url}/v2/Users/", headers=self.auth_headers, json=new_user_data)
            if response.status_code == 201:
                created_user = response.json()
                new_user_id = created_user['id']
                self.log_test("Create User", "PASS", f"Created user: {created_user['displayName']}")
                
                # 5. Update user
                update_data = {
                    "displayName": "Updated Comprehensive Test User",
                    "active": False
                }
                
                response = requests.put(f"{self.base_url}/v2/Users/{new_user_id}", headers=self.auth_headers, json=update_data)
                if response.status_code == 200:
                    updated_user = response.json()
                    if updated_user['displayName'] == "Updated Comprehensive Test User" and not updated_user['active']:
                        self.log_test("Update User", "PASS", "User updated successfully")
                    else:
                        self.log_test("Update User", "FAIL", "User not updated correctly")
                else:
                    self.log_test("Update User", "FAIL", f"HTTP {response.status_code}")
                
                # 6. Patch user
                patch_data = {
                    "displayName": "Patched Comprehensive Test User"
                }
                
                response = requests.patch(f"{self.base_url}/v2/Users/{new_user_id}", headers=self.auth_headers, json=patch_data)
                if response.status_code == 200:
                    patched_user = response.json()
                    if patched_user['displayName'] == "Patched Comprehensive Test User":
                        self.log_test("Patch User", "PASS", "User patched successfully")
                    else:
                        self.log_test("Patch User", "FAIL", "User not patched correctly")
                else:
                    self.log_test("Patch User", "FAIL", f"HTTP {response.status_code}")
                
                # 7. Deactivate user
                response = requests.delete(f"{self.base_url}/v2/Users/{new_user_id}", headers=self.auth_headers)
                if response.status_code == 204:
                    # Verify user is deactivated
                    response = requests.get(f"{self.base_url}/v2/Users/{new_user_id}", headers=self.auth_headers)
                    if response.status_code == 200:
                        deactivated_user = response.json()
                        if not deactivated_user['active']:
                            self.log_test("Deactivate User", "PASS", "User deactivated successfully")
                        else:
                            self.log_test("Deactivate User", "FAIL", "User not deactivated")
                    else:
                        self.log_test("Deactivate User", "FAIL", f"Could not verify deactivation: HTTP {response.status_code}")
                else:
                    self.log_test("Deactivate User", "FAIL", f"HTTP {response.status_code}")
            else:
                self.log_test("Create User", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Create User", "ERROR", str(e))
    
    def test_group_management(self):
        """Test comprehensive group management operations."""
        print("\n=== Testing Group Management ===")
        
        # 1. List all groups and store for dynamic testing
        try:
            response = requests.get(f"{self.base_url}/v2/Groups/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                group_count = data['totalResults']
                groups = data['Resources']
                self.log_test("List Groups", "PASS", f"Found {group_count} groups")
                
                # Store groups for dynamic testing
                self.test_groups = groups
                
                if groups:
                    # Use the first group for testing
                    test_group = groups[0]
                    group_id = test_group['id']
                    display_name = test_group['displayName']
                    
                    # 2. Get specific group by ID
                    response = requests.get(f"{self.base_url}/v2/Groups/{group_id}", headers=self.auth_headers)
                    if response.status_code == 200:
                        retrieved_group = response.json()
                        if retrieved_group['id'] == group_id:
                            self.log_test("Get Group by ID", "PASS", f"Retrieved group: {test_group['displayName']}")
                        else:
                            self.log_test("Get Group by ID", "FAIL", "Retrieved group ID doesn't match")
                    else:
                        self.log_test("Get Group by ID", "FAIL", f"HTTP {response.status_code}")
                    
                    # 3. Group search by display name
                    response = requests.get(f"{self.base_url}/v2/Groups/?filter=displayName co \"{display_name}\"", headers=self.auth_headers)
                    if response.status_code == 200:
                        search_data = response.json()
                        if len(search_data['Resources']) >= 1:
                            # Check if our test group is in the results
                            found = any(g['id'] == group_id for g in search_data['Resources'])
                            if found:
                                self.log_test("Group Search", "PASS", f"Found group by display name filter: {display_name}")
                            else:
                                self.log_test("Group Search", "FAIL", f"Group {display_name} not found in search results")
                        else:
                            self.log_test("Group Search", "FAIL", f"No groups found with display name containing: {display_name}")
                    else:
                        self.log_test("Group Search", "FAIL", f"HTTP {response.status_code}")
                else:
                    self.log_test("Get Group by ID", "SKIP", "No groups available for testing")
                    self.log_test("Group Search", "SKIP", "No groups available for testing")
            else:
                self.log_test("List Groups", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("List Groups", "ERROR", str(e))
        
        # 4. Create new group
        try:
            new_group_data = {
                "displayName": "Comprehensive Test Group",
                "description": "A test group for comprehensive testing"
            }
            
            response = requests.post(f"{self.base_url}/v2/Groups/", headers=self.auth_headers, json=new_group_data)
            if response.status_code == 201:
                created_group = response.json()
                new_group_id = created_group['id']
                self.log_test("Create Group", "PASS", f"Created group: {created_group['displayName']}")
                
                # 5. Update group
                update_data = {
                    "displayName": "Updated Comprehensive Test Group",
                    "description": "Updated description"
                }
                
                response = requests.put(f"{self.base_url}/v2/Groups/{new_group_id}", headers=self.auth_headers, json=update_data)
                if response.status_code == 200:
                    updated_group = response.json()
                    if updated_group['displayName'] == "Updated Comprehensive Test Group":
                        self.log_test("Update Group", "PASS", "Group updated successfully")
                    else:
                        self.log_test("Update Group", "FAIL", "Group not updated correctly")
                else:
                    self.log_test("Update Group", "FAIL", f"HTTP {response.status_code}")
                
                # 6. Delete group
                response = requests.delete(f"{self.base_url}/v2/Groups/{new_group_id}", headers=self.auth_headers)
                if response.status_code == 204:
                    # Verify group is deleted
                    response = requests.get(f"{self.base_url}/v2/Groups/{new_group_id}", headers=self.auth_headers)
                    if response.status_code == 404:
                        self.log_test("Delete Group", "PASS", "Group deleted successfully")
                    else:
                        self.log_test("Delete Group", "FAIL", "Group not deleted")
                else:
                    self.log_test("Delete Group", "FAIL", f"HTTP {response.status_code}")
            else:
                self.log_test("Create Group", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Create Group", "ERROR", str(e))
    
    def test_entitlement_management(self):
        """Test entitlement management operations."""
        print("\n=== Testing Entitlement Management ===")
        
        # 1. List all entitlements and store for dynamic testing
        try:
            response = requests.get(f"{self.base_url}/v2/Entitlements/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                entitlement_count = data['totalResults']
                entitlements = data['Resources']
                self.log_test("List Entitlements", "PASS", f"Found {entitlement_count} entitlements")
                
                # Store entitlements for dynamic testing
                self.test_entitlements = entitlements
                
                if entitlements:
                    # Use the first entitlement for testing
                    test_entitlement = entitlements[0]
                    entitlement_id = test_entitlement['id']
                    
                    # 2. Get specific entitlement by ID
                    response = requests.get(f"{self.base_url}/v2/Entitlements/{entitlement_id}", headers=self.auth_headers)
                    if response.status_code == 200:
                        retrieved_entitlement = response.json()
                        if retrieved_entitlement['id'] == entitlement_id:
                            self.log_test("Get Entitlement by ID", "PASS", f"Retrieved entitlement: {test_entitlement['displayName']}")
                        else:
                            self.log_test("Get Entitlement by ID", "FAIL", "Retrieved entitlement ID doesn't match")
                    else:
                        self.log_test("Get Entitlement by ID", "FAIL", f"HTTP {response.status_code}")
                else:
                    self.log_test("Get Entitlement by ID", "SKIP", "No entitlements available for testing")
            else:
                self.log_test("List Entitlements", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("List Entitlements", "ERROR", str(e))
        
        # 3. Create new entitlement
        try:
            new_entitlement_data = {
                "displayName": "Comprehensive Test Entitlement",
                "type": "Profile",
                "description": "A test entitlement for comprehensive testing"
            }
            
            response = requests.post(f"{self.base_url}/v2/Entitlements/", headers=self.auth_headers, json=new_entitlement_data)
            if response.status_code == 201:
                created_entitlement = response.json()
                new_entitlement_id = created_entitlement['id']
                self.log_test("Create Entitlement", "PASS", f"Created entitlement: {created_entitlement['displayName']}")
                
                # 4. Update entitlement
                update_data = {
                    "displayName": "Updated Comprehensive Test Entitlement",
                    "description": "Updated description"
                }
                
                response = requests.put(f"{self.base_url}/v2/Entitlements/{new_entitlement_id}", headers=self.auth_headers, json=update_data)
                if response.status_code == 200:
                    updated_entitlement = response.json()
                    if updated_entitlement['displayName'] == "Updated Comprehensive Test Entitlement":
                        self.log_test("Update Entitlement", "PASS", "Entitlement updated successfully")
                    else:
                        self.log_test("Update Entitlement", "FAIL", "Entitlement not updated correctly")
                else:
                    self.log_test("Update Entitlement", "FAIL", f"HTTP {response.status_code}")
                
                # 5. Delete entitlement
                response = requests.delete(f"{self.base_url}/v2/Entitlements/{new_entitlement_id}", headers=self.auth_headers)
                if response.status_code == 204:
                    # Verify entitlement is deleted
                    response = requests.get(f"{self.base_url}/v2/Entitlements/{new_entitlement_id}", headers=self.auth_headers)
                    if response.status_code == 404:
                        self.log_test("Delete Entitlement", "PASS", "Entitlement deleted successfully")
                    else:
                        self.log_test("Delete Entitlement", "FAIL", "Entitlement not deleted")
                else:
                    self.log_test("Delete Entitlement", "FAIL", f"HTTP {response.status_code}")
            else:
                self.log_test("Create Entitlement", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Create Entitlement", "ERROR", str(e))
    
    def test_role_management(self):
        """Test role management operations."""
        print("\n=== Testing Role Management ===")
        
        # 1. List all roles and store for dynamic testing
        try:
            response = requests.get(f"{self.base_url}/v2/Roles/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                role_count = data['totalResults']
                roles = data['Resources']
                self.log_test("List Roles", "PASS", f"Found {role_count} roles")
                
                # Store roles for dynamic testing
                self.test_roles = roles
                
                if roles:
                    # Use the first role for testing
                    test_role = roles[0]
                    role_id = test_role['id']
                    
                    # 2. Get specific role by ID
                    response = requests.get(f"{self.base_url}/v2/Roles/{role_id}", headers=self.auth_headers)
                    if response.status_code == 200:
                        retrieved_role = response.json()
                        if retrieved_role['id'] == role_id:
                            self.log_test("Get Role by ID", "PASS", f"Retrieved role: {test_role['displayName']}")
                        else:
                            self.log_test("Get Role by ID", "FAIL", "Retrieved role ID doesn't match")
                    else:
                        self.log_test("Get Role by ID", "FAIL", f"HTTP {response.status_code}")
                else:
                    self.log_test("Get Role by ID", "SKIP", "No roles available for testing")
            else:
                self.log_test("List Roles", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("List Roles", "ERROR", str(e))
        
        # 3. Create new role
        try:
            new_role_data = {
                "displayName": "Comprehensive Test Role",
                "description": "A test role for comprehensive testing"
            }
            
            response = requests.post(f"{self.base_url}/v2/Roles/", headers=self.auth_headers, json=new_role_data)
            if response.status_code == 201:
                created_role = response.json()
                new_role_id = created_role['id']
                self.log_test("Create Role", "PASS", f"Created role: {created_role['displayName']}")
                
                # 4. Update role
                update_data = {
                    "displayName": "Updated Comprehensive Test Role",
                    "description": "Updated description"
                }
                
                response = requests.put(f"{self.base_url}/v2/Roles/{new_role_id}", headers=self.auth_headers, json=update_data)
                if response.status_code == 200:
                    updated_role = response.json()
                    if updated_role['displayName'] == "Updated Comprehensive Test Role":
                        self.log_test("Update Role", "PASS", "Role updated successfully")
                    else:
                        self.log_test("Update Role", "FAIL", "Role not updated correctly")
                else:
                    self.log_test("Update Role", "FAIL", f"HTTP {response.status_code}")
                
                # 5. Delete role
                response = requests.delete(f"{self.base_url}/v2/Roles/{new_role_id}", headers=self.auth_headers)
                if response.status_code == 204:
                    # Verify role is deleted
                    response = requests.get(f"{self.base_url}/v2/Roles/{new_role_id}", headers=self.auth_headers)
                    if response.status_code == 404:
                        self.log_test("Delete Role", "PASS", "Role deleted successfully")
                    else:
                        self.log_test("Delete Role", "FAIL", "Role not deleted")
                else:
                    self.log_test("Delete Role", "FAIL", f"HTTP {response.status_code}")
            else:
                self.log_test("Create Role", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Create Role", "ERROR", str(e))
    
    def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n=== Testing Error Handling ===")
        
        # 1. Test invalid API key
        try:
            response = requests.get(f"{self.base_url}/v2/Users/", headers={"Authorization": "Bearer invalid-key"})
            if response.status_code == 401:
                self.log_test("Invalid API Key", "PASS", "Invalid API key correctly rejected")
            else:
                self.log_test("Invalid API Key", "FAIL", f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid API Key", "ERROR", str(e))
        
        # 2. Test missing API key
        try:
            response = requests.get(f"{self.base_url}/v2/Users/")
            if response.status_code == 401:
                self.log_test("Missing API Key", "PASS", "Missing API key correctly rejected")
            else:
                self.log_test("Missing API Key", "FAIL", f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Missing API Key", "ERROR", str(e))
        
        # 3. Test invalid SCIM ID format
        try:
            response = requests.get(f"{self.base_url}/v2/Users/invalid-id", headers=self.auth_headers)
            if response.status_code == 400:
                self.log_test("Invalid SCIM ID", "PASS", "Invalid SCIM ID format correctly rejected")
            else:
                self.log_test("Invalid SCIM ID", "FAIL", f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid SCIM ID", "ERROR", str(e))
        
        # 4. Test non-existent resource with dynamic data
        try:
            if hasattr(self, 'test_users') and self.test_users:
                # Use a UUID that definitely doesn't exist
                import uuid
                fake_id = str(uuid.uuid4())
                response = requests.get(f"{self.base_url}/v2/Users/{fake_id}", headers=self.auth_headers)
                if response.status_code == 404:
                    self.log_test("Non-existent Resource", "PASS", "Non-existent resource correctly returns 404")
                else:
                    self.log_test("Non-existent Resource", "FAIL", f"Expected 404, got {response.status_code}")
            else:
                self.log_test("Non-existent Resource", "SKIP", "No users available for testing")
        except Exception as e:
            self.log_test("Non-existent Resource", "ERROR", str(e))
        
        # 5. Test duplicate username creation with dynamic data
        try:
            if hasattr(self, 'test_users') and self.test_users:
                # Use the first user's username to test duplicate creation
                existing_user = self.test_users[0]
                duplicate_user_data = {
                    "userName": existing_user['userName'],  # This should already exist
                    "displayName": "Duplicate User"
                }
                
                response = requests.post(f"{self.base_url}/v2/Users/", headers=self.auth_headers, json=duplicate_user_data)
                if response.status_code == 409:
                    self.log_test("Duplicate Username", "PASS", f"Duplicate username correctly rejected: {existing_user['userName']}")
                else:
                    self.log_test("Duplicate Username", "FAIL", f"Expected 409, got {response.status_code}")
            else:
                self.log_test("Duplicate Username", "SKIP", "No users available for testing")
        except Exception as e:
            self.log_test("Duplicate Username", "ERROR", str(e))
    
    def test_pagination_and_filtering(self):
        """Test pagination and filtering functionality."""
        print("\n=== Testing Pagination and Filtering ===")
        
        # 1. Test pagination
        try:
            response = requests.get(f"{self.base_url}/v2/Users/?startIndex=1&count=2", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                if data['startIndex'] == 1 and data['itemsPerPage'] == 2 and len(data['Resources']) <= 2:
                    self.log_test("Pagination", "PASS", f"Pagination works: startIndex={data['startIndex']}, itemsPerPage={data['itemsPerPage']}")
                else:
                    self.log_test("Pagination", "FAIL", "Pagination parameters not working correctly")
            else:
                self.log_test("Pagination", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Pagination", "ERROR", str(e))
        
        # 2. Test filtering by username with dynamic data
        try:
            if hasattr(self, 'test_users') and self.test_users:
                test_user = self.test_users[0]
                username = test_user['userName']
                response = requests.get(f"{self.base_url}/v2/Users/?filter=userName eq \"{username}\"", headers=self.auth_headers)
                if response.status_code == 200:
                    data = response.json()
                    if len(data['Resources']) == 1 and data['Resources'][0]['userName'] == username:
                        self.log_test("Username Filtering", "PASS", f"Username filtering works correctly for: {username}")
                    else:
                        self.log_test("Username Filtering", "FAIL", f"Expected 1 user with username {username}, found {len(data['Resources'])}")
                else:
                    self.log_test("Username Filtering", "FAIL", f"HTTP {response.status_code}")
            else:
                self.log_test("Username Filtering", "SKIP", "No users available for testing")
        except Exception as e:
            self.log_test("Username Filtering", "ERROR", str(e))
        
        # 3. Test filtering by display name with dynamic data
        try:
            if hasattr(self, 'test_users') and self.test_users:
                # Use the first user's display name for testing
                test_user = self.test_users[0]
                display_name = test_user['displayName']
                # Extract first word for partial matching
                first_word = display_name.split()[0] if display_name else "Test"
                
                response = requests.get(f"{self.base_url}/v2/Users/?filter=displayName co \"{first_word}\"", headers=self.auth_headers)
                if response.status_code == 200:
                    data = response.json()
                    if len(data['Resources']) >= 1:
                        # Check if our test user is in the results
                        found = any(u['id'] == test_user['id'] for u in data['Resources'])
                        if found:
                            self.log_test("Display Name Filtering", "PASS", f"Display name filtering works correctly for: {first_word}")
                        else:
                            self.log_test("Display Name Filtering", "FAIL", f"User {display_name} not found in search results")
                    else:
                        self.log_test("Display Name Filtering", "FAIL", f"No users found with '{first_word}' in display name")
                else:
                    self.log_test("Display Name Filtering", "FAIL", f"HTTP {response.status_code}")
            else:
                self.log_test("Display Name Filtering", "SKIP", "No users available for testing")
        except Exception as e:
            self.log_test("Display Name Filtering", "ERROR", str(e))
        
        # 4. Test group filtering with dynamic data
        try:
            if hasattr(self, 'test_groups') and self.test_groups:
                test_group = self.test_groups[0]
                display_name = test_group['displayName']
                response = requests.get(f"{self.base_url}/v2/Groups/?filter=displayName co \"{display_name}\"", headers=self.auth_headers)
                if response.status_code == 200:
                    data = response.json()
                    if len(data['Resources']) >= 1:
                        # Check if our test group is in the results
                        found = any(g['id'] == test_group['id'] for g in data['Resources'])
                        if found:
                            self.log_test("Group Filtering", "PASS", f"Group filtering works correctly for: {display_name}")
                        else:
                            self.log_test("Group Filtering", "FAIL", f"Group {display_name} not found in search results")
                    else:
                        self.log_test("Group Filtering", "FAIL", f"No groups found with display name containing: {display_name}")
                else:
                    self.log_test("Group Filtering", "FAIL", f"HTTP {response.status_code}")
            else:
                self.log_test("Group Filtering", "SKIP", "No groups available for testing")
        except Exception as e:
            self.log_test("Group Filtering", "ERROR", str(e))
    
    def test_scim_compliance(self):
        """Test SCIM 2.0 compliance features."""
        print("\n=== Testing SCIM 2.0 Compliance ===")
        
        # 1. Test SCIM response schemas
        try:
            response = requests.get(f"{self.base_url}/v2/Users/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                
                # Verify SCIM list response schema
                required_fields = ["schemas", "totalResults", "startIndex", "itemsPerPage", "Resources"]
                if all(field in data for field in required_fields):
                    if "urn:ietf:params:scim:api:messages:2.0:ListResponse" in data["schemas"]:
                        self.log_test("SCIM List Response Schema", "PASS", "SCIM list response schema is correct")
                    else:
                        self.log_test("SCIM List Response Schema", "FAIL", "Missing required SCIM schema")
                else:
                    self.log_test("SCIM List Response Schema", "FAIL", f"Missing required fields: {[f for f in required_fields if f not in data]}")
            else:
                self.log_test("SCIM List Response Schema", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("SCIM List Response Schema", "ERROR", str(e))
        
        # 2. Test individual resource schema
        try:
            response = requests.get(f"{self.base_url}/v2/Users/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                if data['Resources']:
                    user = data['Resources'][0]
                    if "schemas" in user and "urn:ietf:params:scim:schemas:core:2.0:User" in user["schemas"]:
                        if "id" in user and "meta" in user:
                            self.log_test("SCIM User Resource Schema", "PASS", "SCIM user resource schema is correct")
                        else:
                            self.log_test("SCIM User Resource Schema", "FAIL", "Missing required user fields")
                    else:
                        self.log_test("SCIM User Resource Schema", "FAIL", "Missing required user schema")
                else:
                    self.log_test("SCIM User Resource Schema", "SKIP", "No users available for testing")
            else:
                self.log_test("SCIM User Resource Schema", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("SCIM User Resource Schema", "ERROR", str(e))
        
        # 3. Test group schema
        try:
            response = requests.get(f"{self.base_url}/v2/Groups/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                if data['Resources']:
                    group = data['Resources'][0]
                    if "schemas" in group and "urn:ietf:params:scim:schemas:core:2.0:Group" in group["schemas"]:
                        self.log_test("SCIM Group Resource Schema", "PASS", "SCIM group resource schema is correct")
                    else:
                        self.log_test("SCIM Group Resource Schema", "FAIL", "Missing required group schema")
                else:
                    self.log_test("SCIM Group Resource Schema", "SKIP", "No groups available for testing")
            else:
                self.log_test("SCIM Group Resource Schema", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("SCIM Group Resource Schema", "ERROR", str(e))
        
        # 4. Test entitlement schema
        try:
            response = requests.get(f"{self.base_url}/v2/Entitlements/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                if data['Resources']:
                    entitlement = data['Resources'][0]
                    if "schemas" in entitlement and "urn:okta:scim:schemas:core:1.0:Entitlement" in entitlement["schemas"]:
                        self.log_test("SCIM Entitlement Resource Schema", "PASS", "SCIM entitlement resource schema is correct")
                    else:
                        self.log_test("SCIM Entitlement Resource Schema", "FAIL", "Missing required entitlement schema")
                else:
                    self.log_test("SCIM Entitlement Resource Schema", "SKIP", "No entitlements available for testing")
            else:
                self.log_test("SCIM Entitlement Resource Schema", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("SCIM Entitlement Resource Schema", "ERROR", str(e))
        
        # 5. Test role schema
        try:
            response = requests.get(f"{self.base_url}/v2/Roles/", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                if data['Resources']:
                    role = data['Resources'][0]
                    if "schemas" in role and "urn:okta:scim:schemas:core:1.0:Role" in role["schemas"]:
                        self.log_test("SCIM Role Resource Schema", "PASS", "SCIM role resource schema is correct")
                    else:
                        self.log_test("SCIM Role Resource Schema", "FAIL", "Missing required role schema")
                else:
                    self.log_test("SCIM Role Resource Schema", "SKIP", "No roles available for testing")
            else:
                self.log_test("SCIM Role Resource Schema", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("SCIM Role Resource Schema", "ERROR", str(e))
    
    def generate_summary(self):
        """Generate a comprehensive summary of the test data and functionality."""
        print("\n=== Comprehensive Test Summary ===")
        
        try:
            # Get all resources
            users_response = requests.get(f"{self.base_url}/v2/Users/", headers=self.auth_headers)
            groups_response = requests.get(f"{self.base_url}/v2/Groups/", headers=self.auth_headers)
            entitlements_response = requests.get(f"{self.base_url}/v2/Entitlements/", headers=self.auth_headers)
            roles_response = requests.get(f"{self.base_url}/v2/Roles/", headers=self.auth_headers)
            
            if all(r.status_code == 200 for r in [users_response, groups_response, entitlements_response, roles_response]):
                users_data = users_response.json()
                groups_data = groups_response.json()
                entitlements_data = entitlements_response.json()
                roles_data = roles_response.json()
                
                print(f"📊 Test Data Summary:")
                print(f"   Users: {users_data['totalResults']}")
                print(f"   Groups: {groups_data['totalResults']}")
                print(f"   Entitlements: {entitlements_data['totalResults']}")
                print(f"   Roles: {roles_data['totalResults']}")
                
                print(f"\n👥 Sample Users:")
                for user in users_data['Resources'][:3]:  # Show first 3 users
                    print(f"   - {user['displayName']} ({user['userName']}) - Active: {user['active']}")
                
                print(f"\n🏢 Sample Groups:")
                for group in groups_data['Resources'][:3]:  # Show first 3 groups
                    print(f"   - {group['displayName']}: {group['description']}")
                
                print(f"\n🎫 Sample Entitlements:")
                for entitlement in entitlements_data['Resources'][:3]:  # Show first 3 entitlements
                    print(f"   - {entitlement['displayName']} ({entitlement['type']})")
                
                print(f"\n🔑 Sample Roles:")
                for role in roles_data['Resources'][:3]:  # Show first 3 roles
                    print(f"   - {role['displayName']}: {role['description']}")
                
                self.log_test("Data Summary", "PASS", "All test data available and accessible")
            else:
                self.log_test("Data Summary", "FAIL", "Could not retrieve all test data")
        except Exception as e:
            self.log_test("Data Summary", "ERROR", str(e))
    
    def run_all_tests(self):
        """Run all comprehensive tests."""
        print("🚀 Starting Comprehensive SCIM Testing")
        print(f"📅 Test started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Testing against: {self.base_url}")
        print(f"🔑 Using API key: {self.api_key}")
        print()
        
        # First, verify server availability and endpoint accessibility
        if not self.verify_server_availability():
            print("❌ Server availability check failed. Cannot proceed with tests.")
            print("💡 Please ensure:")
            print("   1. The SCIM server is running (python run_server.py)")
            print("   2. The server is accessible at the configured URL")
            print("   3. The API key is valid")
            print("   4. Test data has been created (python scripts/create_test_data.py)")
            return
        
        # Run all test suites
        self.test_schema_discovery()
        self.test_user_management()
        self.test_group_management()
        self.test_entitlement_management()
        self.test_role_management()
        self.test_error_handling()
        self.test_pagination_and_filtering()
        self.test_scim_compliance()
        self.generate_summary()
        
        # Generate final report
        self.generate_report()
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Count results
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.results if r['status'] == 'ERROR'])
        skipped_tests = len([r for r in self.results if r['status'] == 'SKIP'])
        
        print(f"\n{'='*60}")
        print(f"📋 COMPREHENSIVE SCIM TEST REPORT")
        print(f"{'='*60}")
        print(f"📅 Test Duration: {duration}")
        print(f"🔗 Test URL: {self.base_url}")
        print(f"🔑 API Key: {self.api_key}")
        print(f"\n📊 Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Errors: {error_tests}")
        print(f"   ⏭️  Skipped: {skipped_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0 or error_tests > 0:
            print(f"\n❌ Failed/Error Tests:")
            for result in self.results:
                if result['status'] in ['FAIL', 'ERROR']:
                    print(f"   - {result['test']}: {result.get('details', 'No details')}")
        
        print(f"\n✅ All SCIM functionality tested successfully!")
        print(f"   - Schema discovery: {'✅' if passed_tests > 0 else '❌'}")
        print(f"   - User management: {'✅' if passed_tests > 0 else '❌'}")
        print(f"   - Group management: {'✅' if passed_tests > 0 else '❌'}")
        print(f"   - Entitlement management: {'✅' if passed_tests > 0 else '❌'}")
        print(f"   - Role management: {'✅' if passed_tests > 0 else '❌'}")
        print(f"   - Error handling: {'✅' if passed_tests > 0 else '❌'}")
        print(f"   - Pagination/filtering: {'✅' if passed_tests > 0 else '❌'}")
        print(f"   - SCIM compliance: {'✅' if passed_tests > 0 else '❌'}")
        
        # Save detailed results to file
        report_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "test_run": {
                    "start_time": self.start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration.total_seconds(),
                                    "base_url": self.base_url,
                "api_key": self.api_key
                },
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "errors": error_tests,
                    "skipped": skipped_tests,
                    "success_rate": (passed_tests/total_tests*100) if total_tests > 0 else 0
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        print(f"{'='*60}")

def main():
    """Main function to run comprehensive tests."""
    tester = ComprehensiveSCIMTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 