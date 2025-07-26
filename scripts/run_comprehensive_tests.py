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
from scim_server.config import settings
BASE_URL = f"http://{settings.client_host}:{settings.port}"
API_KEY = settings.test_api_key
AUTH_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

class ComprehensiveSCIMTester:
    """Comprehensive SCIM testing class for User, Group, and Entitlement management."""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.auth_headers = AUTH_HEADERS
        
        # Store test data for cross-referencing
        self.test_users = []
        self.test_groups = []
        self.test_entitlements = []
        self.test_server_ids = ["default"]  # Default fallback
        
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
    
    def _get_url(self, endpoint: str, server_id: str = None) -> str:
        """Helper method to construct URLs with optional server ID."""
        # Import settings to get API base path
        from scim_server.config import settings
        
        # Construct the full path: api_base_path + /scim/v2 + endpoint
        api_path = f"{settings.api_base_path}/scim/v2{endpoint}"
        url = f"{self.base_url}{api_path}"
        
        if server_id and server_id != "default":
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}serverID={server_id}"
        return url
    
    def _get_users_url(self, server_id: str = None) -> str:
        """Get Users endpoint URL."""
        return self._get_url("/Users/", server_id)
    
    def _get_groups_url(self, server_id: str = None) -> str:
        """Get Groups endpoint URL."""
        return self._get_url("/Groups/", server_id)
    
    def _get_entitlements_url(self, server_id: str = None) -> str:
        """Get Entitlements endpoint URL."""
        return self._get_url("/Entitlements/", server_id)
    
    def _get_user_url(self, user_id: str, server_id: str = None) -> str:
        """Get specific User endpoint URL."""
        return self._get_url(f"/Users/{user_id}", server_id)
    
    def _get_group_url(self, group_id: str, server_id: str = None) -> str:
        """Get specific Group endpoint URL."""
        return self._get_url(f"/Groups/{group_id}", server_id)
    
    def _get_entitlement_url(self, entitlement_id: str, server_id: str = None) -> str:
        """Get specific Entitlement endpoint URL."""
        return self._get_url(f"/Entitlements/{entitlement_id}", server_id)
    
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
        
        # Test all core endpoints
        endpoints = [
            ("/Users/", "Users Endpoint"),
            ("/Groups/", "Groups Endpoint"),
            ("/Entitlements/", "Entitlements Endpoint"),
            ("/ResourceTypes", "Resource Types Endpoint"),
            ("/Schemas", "Schemas Endpoint")
        ]
        
        for endpoint, name in endpoints:
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
        
        return True
    
    def test_schema_discovery(self):
        """Test SCIM schema discovery endpoints."""
        print("\n=== Testing Schema Discovery ===")
        
        # Test ResourceTypes endpoint
        try:
            response = requests.get(f"{self.base_url}{settings.api_base_path}/scim/v2/ResourceTypes", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                resources = data.get('Resources', [])
                
                # Check for expected resource types
                expected_types = ["User", "Group", "Entitlement"]
                found_types = [r['name'] for r in resources]
                
                missing_types = [t for t in expected_types if t not in found_types]
                if missing_types:
                    self.log_test("Resource Types", "FAIL", f"Missing types: {missing_types}")
                else:
                    self.log_test("Resource Types", "PASS", f"Found all expected types: {found_types}")
            else:
                self.log_test("Resource Types", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Resource Types", "ERROR", str(e))
        
        # Test Schemas endpoint
        try:
            response = requests.get(f"{self.base_url}{settings.api_base_path}/scim/v2/Schemas", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                schemas = data.get('Resources', [])
                
                # Check for expected schemas
                expected_schemas = [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:core:2.0:Group", 
                    "urn:okta:scim:schemas:core:1.0:Entitlement"
                ]
                found_schemas = [s['id'] for s in schemas]
                
                missing_schemas = [s for s in expected_schemas if s not in found_schemas]
                if missing_schemas:
                    self.log_test("Schemas", "FAIL", f"Missing schemas: {missing_schemas}")
                else:
                    self.log_test("Schemas", "PASS", f"Found all expected schemas: {len(found_schemas)} total")
            else:
                self.log_test("Schemas", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Schemas", "ERROR", str(e))
    
    def test_user_management(self):
        """Test user management operations."""
        print("\n=== Testing User Management ===")
        
        # Test against each server created by CLI
        for server_id in getattr(self, 'test_server_ids', ['default']):
            print(f"\n--- Testing Server: {server_id} ---")
            
            # 1. List all users and store for dynamic testing
            try:
                response = requests.get(self._get_users_url(server_id), headers=self.auth_headers)
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
                        
                        # 2. Get specific user by ID
                        response = requests.get(self._get_user_url(user_id, server_id), headers=self.auth_headers)
                        if response.status_code == 200:
                            retrieved_user = response.json()
                            if retrieved_user['id'] == user_id:
                                self.log_test("Get User by ID", "PASS", f"Retrieved user: {test_user['userName']}")
                            else:
                                self.log_test("Get User by ID", "FAIL", "Retrieved user ID doesn't match")
                        else:
                            self.log_test("Get User by ID", "FAIL", f"HTTP {response.status_code}")
                    else:
                        self.log_test("Get User by ID", "SKIP", "No users available for testing")
                else:
                    self.log_test("List Users", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("List Users", "ERROR", str(e))
            
            # 3. Create new user
            try:
                new_user_data = {
                    "userName": "comprehensive.test@example.com",
                    "active": True,
                    "displayName": "Comprehensive Test User",
                    "name": {
                        "givenName": "Comprehensive",
                        "familyName": "Test"
                    },
                    "emails": [
                        {
                            "primary": True,
                            "value": "comprehensive.test@example.com",
                            "type": "work"
                        }
                    ]
                }
                
                response = requests.post(self._get_users_url(server_id), headers=self.auth_headers, json=new_user_data)
                if response.status_code == 201:
                    created_user = response.json()
                    new_user_id = created_user['id']
                    self.log_test("Create User", "PASS", f"Created user: {created_user['userName']}")
                    
                    # 4. Update user
                    update_data = {
                        "displayName": "Updated Comprehensive Test User",
                        "name": {
                            "givenName": "Updated",
                            "familyName": "Comprehensive"
                        }
                    }
                    
                    response = requests.put(self._get_user_url(new_user_id, server_id), headers=self.auth_headers, json=update_data)
                    if response.status_code == 200:
                        updated_user = response.json()
                        if updated_user['displayName'] == "Updated Comprehensive Test User":
                            self.log_test("Update User", "PASS", "User updated successfully")
                        else:
                            self.log_test("Update User", "FAIL", "User not updated correctly")
                    else:
                        self.log_test("Update User", "FAIL", f"HTTP {response.status_code}")
                    
                    # 5. Delete user
                    response = requests.delete(self._get_user_url(new_user_id, server_id), headers=self.auth_headers)
                    if response.status_code == 204:
                        # Verify user is deleted
                        response = requests.get(self._get_user_url(new_user_id, server_id), headers=self.auth_headers)
                        if response.status_code == 404:
                            self.log_test("Delete User", "PASS", "User deleted successfully")
                        else:
                            self.log_test("Delete User", "FAIL", "User not deleted")
                    else:
                        self.log_test("Delete User", "FAIL", f"HTTP {response.status_code}")
                else:
                    self.log_test("Create User", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Create User", "ERROR", str(e))
    
    def test_group_management(self):
        """Test group management operations."""
        print("\n=== Testing Group Management ===")
        
        # Test against each server created by CLI
        for server_id in getattr(self, 'test_server_ids', ['default']):
            print(f"\n--- Testing Server: {server_id} ---")
            
            # 1. List all groups and store for dynamic testing
            try:
                response = requests.get(self._get_groups_url(server_id), headers=self.auth_headers)
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
                    
                    # 2. Get specific group by ID
                    response = requests.get(self._get_group_url(group_id, server_id), headers=self.auth_headers)
                    if response.status_code == 200:
                        retrieved_group = response.json()
                        if retrieved_group['id'] == group_id:
                            self.log_test("Get Group by ID", "PASS", f"Retrieved group: {test_group['displayName']}")
                        else:
                            self.log_test("Get Group by ID", "FAIL", "Retrieved group ID doesn't match")
                    else:
                        self.log_test("Get Group by ID", "FAIL", f"HTTP {response.status_code}")
                else:
                    self.log_test("Get Group by ID", "SKIP", "No groups available for testing")
            else:
                self.log_test("List Groups", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("List Groups", "ERROR", str(e))
        
        # 3. Create new group
        try:
            new_group_data = {
                "displayName": "Comprehensive Test Group",
                "description": "A test group for comprehensive testing"
            }
            
            response = requests.post(self._get_groups_url(server_id), headers=self.auth_headers, json=new_group_data)
            if response.status_code == 201:
                created_group = response.json()
                new_group_id = created_group['id']
                self.log_test("Create Group", "PASS", f"Created group: {created_group['displayName']}")
                
                # 4. Update group
                update_data = {
                    "displayName": "Updated Comprehensive Test Group"
                }
                
                response = requests.put(self._get_group_url(new_group_id, server_id), headers=self.auth_headers, json=update_data)
                if response.status_code == 200:
                    updated_group = response.json()
                    if updated_group['displayName'] == "Updated Comprehensive Test Group":
                        self.log_test("Update Group", "PASS", "Group updated successfully")
                    else:
                        self.log_test("Update Group", "FAIL", "Group not updated correctly")
                else:
                    self.log_test("Update Group", "FAIL", f"HTTP {response.status_code}")
                
                # 5. Delete group
                response = requests.delete(self._get_group_url(new_group_id, server_id), headers=self.auth_headers)
                if response.status_code == 204:
                    # Verify group is deleted
                    response = requests.get(self._get_group_url(new_group_id, server_id), headers=self.auth_headers)
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
        """Test entitlement management operations with enhanced features."""
        print("\n=== Testing Entitlement Management ===")
        
        # Test against each server created by CLI
        for server_id in getattr(self, 'test_server_ids', ['default']):
            print(f"\n--- Testing Server: {server_id} ---")
            
            # 1. List all entitlements and store for dynamic testing
            try:
                response = requests.get(self._get_entitlements_url(server_id), headers=self.auth_headers)
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
                        response = requests.get(self._get_entitlement_url(entitlement_id, server_id), headers=self.auth_headers)
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
                "type": "E5",  # Use a valid canonical value from config
                "description": "A test entitlement for comprehensive testing",
                "entitlementType": "application_access",
                "multiValued": False
            }
            
            response = requests.post(self._get_entitlements_url(server_id), headers=self.auth_headers, json=new_entitlement_data)
            if response.status_code == 201:
                created_entitlement = response.json()
                new_entitlement_id = created_entitlement['id']
                self.log_test("Create Entitlement", "PASS", f"Created entitlement: {created_entitlement['displayName']}")
                
                # 4. Update entitlement
                update_data = {
                    "displayName": "Updated Comprehensive Test Entitlement",
                    "entitlementType": "role_based",
                    "multiValued": True
                }
                
                response = requests.put(self._get_entitlement_url(new_entitlement_id, server_id), headers=self.auth_headers, json=update_data)
                if response.status_code == 200:
                    updated_entitlement = response.json()
                    if (updated_entitlement['displayName'] == "Updated Comprehensive Test Entitlement" and 
                    updated_entitlement['entitlementType'] == "role_based" and 
                    updated_entitlement['multiValued'] == True):
                        self.log_test("Update Entitlement", "PASS", "Entitlement updated successfully")
                    else:
                        self.log_test("Update Entitlement", "FAIL", "Entitlement not updated correctly")
                else:
                    self.log_test("Update Entitlement", "FAIL", f"HTTP {response.status_code}")
                
                # 5. Delete entitlement
                response = requests.delete(self._get_entitlement_url(new_entitlement_id, server_id), headers=self.auth_headers)
                if response.status_code == 204:
                    # Verify entitlement is deleted
                    response = requests.get(self._get_entitlement_url(new_entitlement_id, server_id), headers=self.auth_headers)
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
    
    def test_error_handling(self):
        """Test error handling and validation with enhanced error messages."""
        print("\n=== Testing Error Handling ===")
        
        # Test against each server created by CLI
        for server_id in getattr(self, 'test_server_ids', ['default']):
            print(f"\n--- Testing Server: {server_id} ---")
            
            # Test invalid user creation (missing required fields)
            try:
                invalid_user_data = {
                    "active": True,
                    "name": {
                        "givenName": "Invalid",
                        "familyName": "User"
                    }
                    # Missing userName - should fail
                }
                
                response = requests.post(self._get_users_url(server_id), headers=self.auth_headers, json=invalid_user_data)
            if response.status_code == 400:
                error_data = response.json()
                if "detail" in error_data and "error" in error_data["detail"]:
                    self.log_test("Invalid User Creation", "PASS", "Properly rejected user without userName with enhanced error")
                else:
                    self.log_test("Invalid User Creation", "PASS", "Properly rejected user without userName")
            else:
                self.log_test("Invalid User Creation", "FAIL", f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid User Creation", "ERROR", str(e))
        
        # Test invalid entitlement creation (invalid canonical value)
        try:
            invalid_entitlement_data = {
                "displayName": "Invalid Entitlement",
                "type": "InvalidType",  # Should not be in canonical values
                "description": "Test invalid entitlement",
                "entitlementType": "application_access"
            }
            
            response = requests.post(self._get_entitlements_url(server_id), headers=self.auth_headers, json=invalid_entitlement_data)
            if response.status_code == 400:
                error_data = response.json()
                if "detail" in error_data and "error" in error_data["detail"]:
                    self.log_test("Invalid Entitlement Creation", "PASS", "Properly rejected entitlement with invalid type and enhanced error")
                else:
                    self.log_test("Invalid Entitlement Creation", "PASS", "Properly rejected entitlement with invalid type")
            else:
                self.log_test("Invalid Entitlement Creation", "FAIL", f"Should have returned 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Entitlement Creation", "ERROR", str(e))
        
        # Test non-existent resource
        try:
            response = requests.get(self._get_user_url("nonexistent-id", server_id), headers=self.auth_headers)
            if response.status_code == 404:
                self.log_test("Non-existent Resource", "PASS", "Properly returned 404 for non-existent user")
            else:
                self.log_test("Non-existent Resource", "FAIL", f"Should have returned 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Resource", "ERROR", str(e))
        
        # Test enhanced entitlement features
        try:
            # Test multi-valued entitlement creation
            multi_valued_entitlement_data = {
                "displayName": "Multi-Valued Test Entitlement",
                "type": "Administrator",  # Valid canonical value
                "description": "Test multi-valued entitlement",
                "entitlementType": "role_based",
                "multiValued": True
            }
            
            response = requests.post(self._get_entitlements_url(server_id), headers=self.auth_headers, json=multi_valued_entitlement_data)
            if response.status_code == 201:
                created_entitlement = response.json()
                if created_entitlement['multiValued'] == True and created_entitlement['entitlementType'] == "role_based":
                    self.log_test("Multi-Valued Entitlement Creation", "PASS", "Successfully created multi-valued entitlement")
                    
                    # Clean up
                    entitlement_id = created_entitlement['id']
                    requests.delete(self._get_entitlement_url(entitlement_id, server_id), headers=self.auth_headers)
                else:
                    self.log_test("Multi-Valued Entitlement Creation", "FAIL", "Multi-valued fields not set correctly")
            else:
                self.log_test("Multi-Valued Entitlement Creation", "FAIL", f"Should have returned 201, got {response.status_code}")
        except Exception as e:
            self.log_test("Multi-Valued Entitlement Creation", "ERROR", str(e))
    
    def test_pagination_and_filtering(self):
        """Test pagination and filtering capabilities."""
        print("\n=== Testing Pagination and Filtering ===")
        
        # Test against each server created by CLI
        for server_id in getattr(self, 'test_server_ids', ['default']):
            print(f"\n--- Testing Server: {server_id} ---")
            
            # Test pagination
            try:
                response = requests.get(f"{self._get_users_url(server_id)}?startIndex=1&count=5", headers=self.auth_headers)
                if response.status_code == 200:
                    data = response.json()
                    if 'startIndex' in data and 'itemsPerPage' in data:
                        self.log_test("Pagination", "PASS", f"Pagination working: {data['startIndex']}-{data['itemsPerPage']}")
                    else:
                        self.log_test("Pagination", "FAIL", "Missing pagination fields")
                else:
                    self.log_test("Pagination", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Pagination", "ERROR", str(e))
            
            # Test filtering
            try:
                response = requests.get(f"{self._get_users_url(server_id)}?filter=active eq true", headers=self.auth_headers)
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Filtering", "PASS", f"Filter returned {data['totalResults']} active users")
                else:
                    self.log_test("Filtering", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Filtering", "ERROR", str(e))
    
    def test_scim_compliance(self):
        """Test SCIM compliance features and schema validation."""
        print("\n=== Testing SCIM Compliance ===")
        
        # Test against each server created by CLI
        for server_id in getattr(self, 'test_server_ids', ['default']):
            print(f"\n--- Testing Server: {server_id} ---")
            
            # Test User schema compliance
            try:
                response = requests.get(self._get_users_url(server_id), headers=self.auth_headers)
                if response.status_code == 200:
                    data = response.json()
                    if data['Resources']:
                        user = data['Resources'][0]
                        if "schemas" in user and "urn:ietf:params:scim:schemas:core:2.0:User" in user["schemas"]:
                            self.log_test("SCIM User Resource Schema", "PASS", "SCIM user resource schema is correct")
                        else:
                            self.log_test("SCIM User Resource Schema", "FAIL", "Missing required user schema")
                    else:
                        self.log_test("SCIM User Resource Schema", "SKIP", "No users available for testing")
                else:
                    self.log_test("SCIM User Resource Schema", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("SCIM User Resource Schema", "ERROR", str(e))
            
            # Test Group schema compliance
            try:
                response = requests.get(self._get_groups_url(server_id), headers=self.auth_headers)
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
            
            # Test Entitlement schema compliance
            try:
                response = requests.get(self._get_entitlements_url(server_id), headers=self.auth_headers)
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
        
        # Test schema validation for enhanced entitlement fields
        try:
            response = requests.get(f"{self.base_url}{settings.api_base_path}/scim/v2/Schemas", headers=self.auth_headers)
            if response.status_code == 200:
                data = response.json()
                entitlement_schema = None
                for schema in data.get('Resources', []):
                    if schema['id'] == "urn:okta:scim:schemas:core:1.0:Entitlement":
                        entitlement_schema = schema
                        break
                
                if entitlement_schema:
                    # Check for enhanced fields
                    has_entitlement_type = any(attr['name'] == 'entitlementType' for attr in entitlement_schema.get('attributes', []))
                    has_multi_valued = any(attr['name'] == 'multiValued' for attr in entitlement_schema.get('attributes', []))
                    
                    if has_entitlement_type and has_multi_valued:
                        self.log_test("Enhanced Entitlement Schema", "PASS", "Entitlement schema includes enhanced fields")
                    else:
                        self.log_test("Enhanced Entitlement Schema", "FAIL", "Missing enhanced entitlement fields in schema")
                else:
                    self.log_test("Enhanced Entitlement Schema", "FAIL", "Could not find entitlement schema")
            else:
                self.log_test("Enhanced Entitlement Schema", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Enhanced Entitlement Schema", "ERROR", str(e))
    
    def generate_summary(self):
        """Generate a summary of all test results."""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE SCIM TEST SUMMARY")
        print("="*60)
        
        # Count results
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.results if r['status'] == 'ERROR'])
        skipped_tests = len([r for r in self.results if r['status'] == 'SKIP'])
        
        # Calculate duration
        duration = datetime.now() - self.start_time
        
        print(f"⏱️  Test Duration: {duration}")
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Errors: {error_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # Show current data counts
        try:
            users_response = requests.get(f"{self.base_url}/v2/Users/", headers=self.auth_headers)
            groups_response = requests.get(f"{self.base_url}/v2/Groups/", headers=self.auth_headers)
            entitlements_response = requests.get(f"{self.base_url}/v2/Entitlements/", headers=self.auth_headers)
            
            if all(r.status_code == 200 for r in [users_response, groups_response, entitlements_response]):
                users_data = users_response.json()
                groups_data = groups_response.json()
                entitlements_data = entitlements_response.json()
                
                print(f"\n📊 Current Data Counts:")
                print(f"   Users: {users_data['totalResults']}")
                print(f"   Groups: {groups_data['totalResults']}")
                print(f"   Entitlements: {entitlements_data['totalResults']}")
                
                # Show sample data
                if users_data['Resources']:
                    print(f"\n👥 Sample Users:")
                    for user in users_data['Resources'][:3]:  # Show first 3 users
                        print(f"   - {user.get('userName', 'Unknown')} ({user.get('name', {}).get('givenName', 'Unknown')} {user.get('name', {}).get('familyName', 'Unknown')})")
                
                if groups_data['Resources']:
                    print(f"\n🏢 Sample Groups:")
                    for group in groups_data['Resources'][:3]:  # Show first 3 groups
                        print(f"   - {group.get('displayName', 'Unknown')}")
                
                if entitlements_data['Resources']:
                    print(f"\n🎫 Sample Entitlements:")
                    for entitlement in entitlements_data['Resources'][:3]:  # Show first 3 entitlements
                        print(f"   - {entitlement.get('displayName', 'Unknown')} ({entitlement.get('type', 'Unknown')})")
        except Exception as e:
            print(f"⚠️  Could not retrieve current data counts: {e}")
        
        # Show failed tests
        failed_results = [r for r in self.results if r['status'] in ['FAIL', 'ERROR']]
        if failed_results:
            print(f"\n❌ Failed Tests:")
            for result in failed_results:
                print(f"   - {result['test']}: {result.get('details', 'No details')}")
        
        print("\n" + "="*60)
    
    def setup_test_data_via_cli(self):
        """Create test data using the CLI and get server IDs for testing."""
        print("\n=== Setting Up Test Data via CLI ===")
        
        try:
            # Import the CLI module
            import subprocess
            import sys
            import os
            
            # Add the project root to Python path for CLI import
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, project_root)
            
            # Create test servers using CLI
            test_servers = [
                {"name": "comprehensive-test-1", "users": 3, "groups": 2, "entitlements": 3},
                {"name": "comprehensive-test-2", "users": 2, "groups": 1, "entitlements": 2}
            ]
            
            self.test_server_ids = []
            
            for server_config in test_servers:
                try:
                    # Run CLI command to create server with JSON output
                    cmd = [
                        sys.executable, "scripts/scim_cli.py", "create",
                        "--users", str(server_config["users"]),
                        "--groups", str(server_config["groups"]),
                        "--entitlements", str(server_config["entitlements"]),
                        "--json"
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
                    
                    if result.returncode == 0:
                        # Parse JSON output to get server ID
                        try:
                            import json
                            # Find the JSON output in the stdout
                            lines = result.stdout.split('\n')
                            for line in lines:
                                if line.strip().startswith('{'):
                                    data = json.loads(line)
                                    if 'server_id' in data:
                                        server_id = data['server_id']
                                        self.test_server_ids.append(server_id)
                                        self.log_test("CLI Create Server", "PASS", f"Created server {server_config['name']}: {server_id}")
                                        break
                        except (json.JSONDecodeError, KeyError) as e:
                            self.log_test("CLI Create Server", "FAIL", f"Failed to parse JSON output: {e}")
                    else:
                        self.log_test("CLI Create Server", "FAIL", f"Failed to create server {server_config['name']}: {result.stderr}")
                        
                except Exception as e:
                    self.log_test("CLI Create Server", "ERROR", f"Error creating server {server_config['name']}: {str(e)}")
            
            # List all servers to verify with JSON output
            try:
                result = subprocess.run([sys.executable, "scripts/scim_cli.py", "list", "--json"], 
                                      capture_output=True, text=True, cwd=project_root)
                if result.returncode == 0:
                    try:
                        import json
                        # Find the JSON output in the stdout
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if line.strip().startswith('{'):
                                data = json.loads(line)
                                if 'servers' in data:
                                    server_count = data['total']
                                    self.log_test("CLI List Servers", "PASS", f"Successfully listed {server_count} servers")
                                    print("Available servers:")
                                    for server in data['servers']:
                                        print(f"  - {server['server_id']}: {server['stats']['users']} users, {server['stats']['groups']} groups, {server['stats']['entitlements']} entitlements")
                                    break
                    except (json.JSONDecodeError, KeyError) as e:
                        self.log_test("CLI List Servers", "FAIL", f"Failed to parse JSON output: {e}")
                else:
                    self.log_test("CLI List Servers", "FAIL", f"Failed to list servers: {result.stderr}")
            except Exception as e:
                self.log_test("CLI List Servers", "ERROR", str(e))
                
        except Exception as e:
            self.log_test("CLI Setup", "ERROR", f"Failed to setup test data via CLI: {str(e)}")
            # Fallback to using default server
            self.test_server_ids = ["default"]
    
    def run_all_tests(self):
        """Run all comprehensive tests."""
        print("🚀 Starting Comprehensive SCIM Testing")
        print("="*60)
        
        # Verify server is available
        if not self.verify_server_availability():
            print("❌ Server not available. Please start the SCIM server first.")
            return False
        
        # Create test data using CLI and get server IDs
        self.setup_test_data_via_cli()
        
        # Run all test suites
        test_suites = [
            self.test_schema_discovery,
            self.test_user_management,
            self.test_group_management,
            self.test_entitlement_management,
            self.test_error_handling,
            self.test_pagination_and_filtering,
            self.test_scim_compliance
        ]
        
        for test_suite in test_suites:
            try:
                test_suite()
            except Exception as e:
                logger.error(f"Error running {test_suite.__name__}: {e}")
        
        # Generate summary
        self.generate_summary()
        
        return True
    
    def generate_report(self):
        """Generate a detailed JSON report."""
        report = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": str(datetime.now() - self.start_time)
            },
            "summary": {
                "total_tests": len(self.results),
                "passed": len([r for r in self.results if r['status'] == 'PASS']),
                "failed": len([r for r in self.results if r['status'] == 'FAIL']),
                "errors": len([r for r in self.results if r['status'] == 'ERROR']),
                "skipped": len([r for r in self.results if r['status'] == 'SKIP'])
            },
            "results": self.results
        }
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed report saved to: {filename}")
        return filename


def main():
    """Main function to run comprehensive tests."""
    tester = ComprehensiveSCIMTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            # Generate detailed report
            report_file = tester.generate_report()
            print(f"\n✅ Comprehensive testing completed!")
            print(f"📄 Detailed report: {report_file}")
            return 0
        else:
            print("\n❌ Comprehensive testing failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 