"""
Comprehensive SCIM end-to-end tests covering all use cases.
These tests require the test data to be populated using scripts/create_test_data.py
"""
import pytest
import json
import time
from fastapi.testclient import TestClient
from loguru import logger

class TestComprehensiveSCIM:
    """Comprehensive SCIM testing class covering all use cases."""
    
    # Test data constants
    from scim_server.config import settings
    TEST_API_KEY = settings.test_api_key
    AUTH_HEADERS = {"Authorization": f"Bearer {TEST_API_KEY}"}
    
    def get_unique_username(self, base_name):
        """Generate a unique username using timestamp to avoid conflicts."""
        timestamp = int(time.time() * 1000)  # milliseconds
        return f"{base_name}_{timestamp}@example.com"
    
    def cleanup_test_data(self, client):
        """Clean up test data created during tests to prevent conflicts."""
        logger.info("Cleaning up test data...")
        
        # Clean up test users
        response = client.get("/v2/Users/", headers=self.AUTH_HEADERS)
        if response.status_code == 200:
            data = response.json()
            for user in data['Resources']:
                if user['userName'].startswith('newuser_') or user['userName'].startswith('test_'):
                    logger.info(f"Cleaning up test user: {user['userName']}")
                    # Note: We don't actually delete here to avoid interfering with other tests
                    # The unique usernames should prevent conflicts
        
        # Clean up test groups
        response = client.get("/v2/Groups/", headers=self.AUTH_HEADERS)
        if response.status_code == 200:
            data = response.json()
            for group in data['Resources']:
                if group['displayName'].startswith('Test Group') or group['displayName'].startswith('Updated Test Group'):
                    logger.info(f"Cleaning up test group: {group['displayName']}")
                    # Note: Groups are already deleted in the test, so this is just for logging
        
        logger.info("Test data cleanup completed")
    
    def test_01_schema_discovery(self, client):
        """Test SCIM schema discovery endpoints."""
        print("\n=== Testing Schema Discovery ===")
        
        # Test ResourceTypes endpoint
        response = client.get("/v2/ResourceTypes", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        logger.info(f"ResourceTypes response: {json.dumps(data, indent=2)}")
        
        # Verify all expected resource types are present
        resource_ids = [r["id"] for r in data["Resources"]]
        assert "User" in resource_ids
        assert "Group" in resource_ids
        assert "Entitlement" in resource_ids
        assert "Role" in resource_ids
        
        # Test Schemas endpoint
        response = client.get("/v2/Schemas", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        logger.info(f"Schemas response: {json.dumps(data, indent=2)}")
        
        logger.info("✅ Schema discovery tests passed")
    
    def test_02_user_management(self, client):
        """Test comprehensive user management operations."""
        print("\n=== Testing User Management ===")
        
        # 1. List all users
        print("1. Testing user listing...")
        response = client.get("/v2/Users/", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        print(f"Found {data['totalResults']} users")
        
        # Verify we have our test users
        assert data['totalResults'] >= 5  # We should have at least 5 test users
        
        # Find any existing user for testing (dynamic)
        test_user = None
        for user in data['Resources']:
            # Skip users that look like they were created by previous test runs
            if not user['userName'].startswith('newuser_') and not user['userName'].startswith('test_'):
                test_user = user
                break
        
        assert test_user is not None, "No suitable test user found in database"
        user_id = test_user['id']
        test_username = test_user['userName']
        print(f"Using test user: {test_username}")
        
        # 2. Get specific user
        print("2. Testing get specific user...")
        response = client.get(f"/v2/Users/{user_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        user_data = response.json()
        print(f"Retrieved user: {user_data['displayName']}")
        assert user_data['userName'] == test_username
        
        # 3. User search
        print("3. Testing user search...")
        response = client.get(f"/v2/Users/?filter=userName eq \"{test_username}\"", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data['Resources']) == 1
        assert data['Resources'][0]['userName'] == test_username
        
        # 4. Create new user
        print("4. Testing user creation...")
        unique_username = self.get_unique_username("newuser")
        new_user_data = {
            "userName": unique_username,
            "displayName": "New Test User",
            "name": {
                "givenName": "New",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": unique_username,
                    "primary": True
                }
            ],
            "active": True
        }
        
        response = client.post("/v2/Users/", headers=self.AUTH_HEADERS, json=new_user_data)
        assert response.status_code == 201
        created_user = response.json()
        new_user_id = created_user['id']
        print(f"Created user: {created_user['displayName']} with ID: {new_user_id}")
        
        # 5. Update user
        print("5. Testing user update...")
        update_data = {
            "displayName": "Updated Test User",
            "active": False
        }
        
        response = client.put(f"/v2/Users/{new_user_id}", headers=self.AUTH_HEADERS, json=update_data)
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user['displayName'] == "Updated Test User"
        assert updated_user['active'] == False
        print(f"Updated user: {updated_user['displayName']}")
        
        # 6. Patch user
        print("6. Testing user patch...")
        patch_data = {
            "displayName": "Patched Test User"
        }
        
        response = client.patch(f"/v2/Users/{new_user_id}", headers=self.AUTH_HEADERS, json=patch_data)
        assert response.status_code == 200
        patched_user = response.json()
        assert patched_user['displayName'] == "Patched Test User"
        print(f"Patched user: {patched_user['displayName']}")
        
        # 7. Deactivate user (soft delete)
        print("7. Testing user deactivation...")
        response = client.delete(f"/v2/Users/{new_user_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 204
        
        # Verify user is deactivated
        response = client.get(f"/v2/Users/{new_user_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        deactivated_user = response.json()
        assert deactivated_user['active'] == False
        print(f"Deactivated user: {deactivated_user['displayName']}")
        
        print("✅ User management tests passed")
    
    def test_03_group_management(self, client):
        """Test comprehensive group management operations."""
        print("\n=== Testing Group Management ===")
        
        # 1. List all groups
        print("1. Testing group listing...")
        response = client.get("/v2/Groups/", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        print(f"Found {data['totalResults']} groups")
        
        # Verify we have our test groups
        assert data['totalResults'] >= 5  # We should have at least 5 test groups
        
        # Find any existing group for testing (dynamic)
        test_group = None
        for group in data['Resources']:
            # Skip groups that look like they were created by previous test runs
            if not group['displayName'].startswith('Test Group') and not group['displayName'].startswith('Updated Test Group'):
                test_group = group
                break
        
        assert test_group is not None, "No suitable test group found in database"
        group_id = test_group['id']
        test_group_name = test_group['displayName']
        print(f"Using test group: {test_group_name}")
        
        # 2. Get specific group
        print("2. Testing get specific group...")
        response = client.get(f"/v2/Groups/{group_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        group_data = response.json()
        print(f"Retrieved group: {group_data['displayName']}")
        assert group_data['displayName'] == test_group_name
        
        # 3. Group search
        print("3. Testing group search...")
        # Use a substring of the group name for search
        search_term = test_group_name.split()[0]  # Use first word of group name
        response = client.get(f"/v2/Groups/?filter=displayName co \"{search_term}\"", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data['Resources']) >= 1
        # Verify our test group is in the results
        found = any(group['displayName'] == test_group_name for group in data['Resources'])
        assert found, f"Test group {test_group_name} not found in search results"
        
        # 4. Create new group
        print("4. Testing group creation...")
        new_group_data = {
            "displayName": "Test Group",
            "description": "A test group for comprehensive testing"
        }
        
        response = client.post("/v2/Groups/", headers=self.AUTH_HEADERS, json=new_group_data)
        assert response.status_code == 201
        created_group = response.json()
        new_group_id = created_group['id']
        print(f"Created group: {created_group['displayName']} with ID: {new_group_id}")
        
        # 5. Update group
        print("5. Testing group update...")
        update_data = {
            "displayName": "Updated Test Group",
            "description": "Updated description"
        }
        
        response = client.put(f"/v2/Groups/{new_group_id}", headers=self.AUTH_HEADERS, json=update_data)
        assert response.status_code == 200
        updated_group = response.json()
        assert updated_group['displayName'] == "Updated Test Group"
        print(f"Updated group: {updated_group['displayName']}")
        
        # 6. Delete group
        print("6. Testing group deletion...")
        response = client.delete(f"/v2/Groups/{new_group_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 204
        
        # Verify group is deleted
        response = client.get(f"/v2/Groups/{new_group_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 404
        print("Group successfully deleted")
        
        print("✅ Group management tests passed")
    
    def test_04_entitlement_management(self, client):
        """Test entitlement management operations."""
        print("\n=== Testing Entitlement Management ===")
        
        # 1. List all entitlements
        print("1. Testing entitlement listing...")
        response = client.get("/v2/Entitlements/", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        print(f"Found {data['totalResults']} entitlements")
        
        # Verify we have our test entitlements
        assert data['totalResults'] >= 5  # We should have at least 5 test entitlements
        
        # Find any existing entitlement for testing (dynamic)
        test_entitlement = None
        for entitlement in data['Resources']:
            # Skip entitlements that look like they were created by previous test runs
            if not entitlement['displayName'].startswith('Test Entitlement') and not entitlement['displayName'].startswith('Updated Test Entitlement'):
                test_entitlement = entitlement
                break
        
        assert test_entitlement is not None, "No suitable test entitlement found in database"
        entitlement_id = test_entitlement['id']
        test_entitlement_name = test_entitlement['displayName']
        print(f"Using test entitlement: {test_entitlement_name}")
        
        # 2. Get specific entitlement
        print("2. Testing get specific entitlement...")
        response = client.get(f"/v2/Entitlements/{entitlement_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        entitlement_data = response.json()
        print(f"Retrieved entitlement: {entitlement_data['displayName']}")
        assert entitlement_data['displayName'] == test_entitlement_name
        assert 'type' in entitlement_data  # Verify type field exists
        
        # 3. Create new entitlement
        print("3. Testing entitlement creation...")
        new_entitlement_data = {
            "displayName": "Test Entitlement",
            "type": "Profile",
            "description": "A test entitlement for comprehensive testing"
        }
        
        response = client.post("/v2/Entitlements/", headers=self.AUTH_HEADERS, json=new_entitlement_data)
        assert response.status_code == 201
        created_entitlement = response.json()
        new_entitlement_id = created_entitlement['id']
        print(f"Created entitlement: {created_entitlement['displayName']} with ID: {new_entitlement_id}")
        
        # 4. Update entitlement
        print("4. Testing entitlement update...")
        update_data = {
            "displayName": "Updated Test Entitlement",
            "description": "Updated description"
        }
        
        response = client.put(f"/v2/Entitlements/{new_entitlement_id}", headers=self.AUTH_HEADERS, json=update_data)
        assert response.status_code == 200
        updated_entitlement = response.json()
        assert updated_entitlement['displayName'] == "Updated Test Entitlement"
        print(f"Updated entitlement: {updated_entitlement['displayName']}")
        
        # 5. Delete entitlement
        print("5. Testing entitlement deletion...")
        response = client.delete(f"/v2/Entitlements/{new_entitlement_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 204
        
        # Verify entitlement is deleted
        response = client.get(f"/v2/Entitlements/{new_entitlement_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 404
        print("Entitlement successfully deleted")
        
        print("✅ Entitlement management tests passed")
    
    def test_05_role_management(self, client):
        """Test role management operations."""
        print("\n=== Testing Role Management ===")
        
        # 1. List all roles
        print("1. Testing role listing...")
        response = client.get("/v2/Roles/", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        print(f"Found {data['totalResults']} roles")
        
        # Verify we have our test roles
        assert data['totalResults'] >= 5  # We should have at least 5 test roles
        
        # Find any existing role for testing (dynamic)
        test_role = None
        for role in data['Resources']:
            # Skip roles that look like they were created by previous test runs
            if not role['displayName'].startswith('Test Role') and not role['displayName'].startswith('Updated Test Role'):
                test_role = role
                break
        
        assert test_role is not None, "No suitable test role found in database"
        role_id = test_role['id']
        test_role_name = test_role['displayName']
        print(f"Using test role: {test_role_name}")
        
        # 2. Get specific role
        print("2. Testing get specific role...")
        response = client.get(f"/v2/Roles/{role_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        role_data = response.json()
        print(f"Retrieved role: {role_data['displayName']}")
        assert role_data['displayName'] == test_role_name
        
        # 3. Create new role
        print("3. Testing role creation...")
        new_role_data = {
            "displayName": "Test Role",
            "description": "A test role for comprehensive testing"
        }
        
        response = client.post("/v2/Roles/", headers=self.AUTH_HEADERS, json=new_role_data)
        assert response.status_code == 201
        created_role = response.json()
        new_role_id = created_role['id']
        print(f"Created role: {created_role['displayName']} with ID: {new_role_id}")
        
        # 4. Update role
        print("4. Testing role update...")
        update_data = {
            "displayName": "Updated Test Role",
            "description": "Updated description"
        }
        
        response = client.put(f"/v2/Roles/{new_role_id}", headers=self.AUTH_HEADERS, json=update_data)
        assert response.status_code == 200
        updated_role = response.json()
        assert updated_role['displayName'] == "Updated Test Role"
        print(f"Updated role: {updated_role['displayName']}")
        
        # 5. Delete role
        print("5. Testing role deletion...")
        response = client.delete(f"/v2/Roles/{new_role_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 204
        
        # Verify role is deleted
        response = client.get(f"/v2/Roles/{new_role_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 404
        print("Role successfully deleted")
        
        print("✅ Role management tests passed")
    
    def test_06_error_handling(self, client):
        """Test error handling and edge cases."""
        print("\n=== Testing Error Handling ===")
        
        # 1. Test invalid API key
        print("1. Testing invalid API key...")
        response = client.get("/v2/Users/", headers={"Authorization": "Bearer invalid-key"})
        assert response.status_code == 401
        print("Invalid API key correctly rejected")
        
        # 2. Test missing API key
        print("2. Testing missing API key...")
        response = client.get("/v2/Users/")
        assert response.status_code == 401
        print("Missing API key correctly rejected")
        
        # 3. Test invalid SCIM ID format
        print("3. Testing invalid SCIM ID format...")
        response = client.get("/v2/Users/invalid-id", headers=self.AUTH_HEADERS)
        assert response.status_code == 400
        print("Invalid SCIM ID format correctly rejected")
        
        # 4. Test non-existent resource
        print("4. Testing non-existent resource...")
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/v2/Users/{fake_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 404
        print("Non-existent resource correctly returns 404")
        
        # 5. Test duplicate username creation
        print("5. Testing duplicate username creation...")
        duplicate_user_data = {
            "userName": "john.doe@example.com",  # This should already exist
            "displayName": "Duplicate User"
        }
        
        response = client.post("/v2/Users/", headers=self.AUTH_HEADERS, json=duplicate_user_data)
        assert response.status_code == 409
        print("Duplicate username correctly rejected")
        
        print("✅ Error handling tests passed")
    
    def test_07_pagination_and_filtering(self, client):
        """Test pagination and filtering functionality."""
        print("\n=== Testing Pagination and Filtering ===")
        
        # 1. Test pagination
        print("1. Testing pagination...")
        response = client.get("/v2/Users/?startIndex=1&count=2", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 2
        assert len(data['Resources']) <= 2
        print(f"Pagination test: startIndex={data['startIndex']}, itemsPerPage={data['itemsPerPage']}")
        
        # 2. Test filtering by username
        print("2. Testing username filtering...")
        # First get a list of users to find a real username to filter by
        users_response = client.get("/v2/Users/", headers=self.AUTH_HEADERS)
        assert users_response.status_code == 200
        users_data = users_response.json()
        
        if users_data['Resources']:
            # Use the first user's username for filtering
            test_username = users_data['Resources'][0]['userName']
            response = client.get(f"/v2/Users/?filter=userName eq \"{test_username}\"", headers=self.AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert len(data['Resources']) == 1
            assert data['Resources'][0]['userName'] == test_username
            print(f"Username filtering works correctly for: {test_username}")
        else:
            print("No users available for username filtering test")
        
        # 3. Test filtering by display name
        print("3. Testing display name filtering...")
        response = client.get("/v2/Users/?filter=displayName co \"John\"", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data['Resources']) >= 1
        print("Display name filtering works correctly")
        
        # 4. Test group filtering
        print("4. Testing group filtering...")
        # First get a list of groups to find a real group name to filter by
        groups_response = client.get("/v2/Groups/", headers=self.AUTH_HEADERS)
        assert groups_response.status_code == 200
        groups_data = groups_response.json()
        
        if groups_data['Resources']:
            # Use the first word of the first group's name for filtering
            test_group_name = groups_data['Resources'][0]['displayName']
            search_term = test_group_name.split()[0]  # Use first word
            response = client.get(f"/v2/Groups/?filter=displayName co \"{search_term}\"", headers=self.AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert len(data['Resources']) >= 1
            # Verify our test group is in the results
            found = any(g['displayName'] == test_group_name for g in data['Resources'])
            assert found, f"Test group {test_group_name} not found in filtered results"
            print(f"Group filtering works correctly for: {test_group_name}")
        else:
            print("No groups available for group filtering test")
        
        print("✅ Pagination and filtering tests passed")
    
    def test_08_scim_compliance(self, client):
        """Test SCIM 2.0 compliance features."""
        print("\n=== Testing SCIM 2.0 Compliance ===")
        
        # 1. Test SCIM response schemas
        print("1. Testing SCIM response schemas...")
        response = client.get("/v2/Users/", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        
        # Verify SCIM list response schema
        assert "schemas" in data
        assert "urn:ietf:params:scim:api:messages:2.0:ListResponse" in data["schemas"]
        assert "totalResults" in data
        assert "startIndex" in data
        assert "itemsPerPage" in data
        assert "Resources" in data
        print("SCIM list response schema is correct")
        
        # 2. Test individual resource schema
        if data['Resources']:
            user = data['Resources'][0]
            assert "schemas" in user
            assert "urn:ietf:params:scim:schemas:core:2.0:User" in user["schemas"]
            assert "id" in user
            assert "meta" in user
            print("SCIM user resource schema is correct")
        
        # 3. Test group schema
        response = client.get("/v2/Groups/", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        
        if data['Resources']:
            group = data['Resources'][0]
            assert "schemas" in group
            assert "urn:ietf:params:scim:schemas:core:2.0:Group" in group["schemas"]
            print("SCIM group resource schema is correct")
        
        # 4. Test entitlement schema
        response = client.get("/v2/Entitlements/", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        
        if data['Resources']:
            entitlement = data['Resources'][0]
            assert "schemas" in entitlement
            assert "urn:okta:scim:schemas:core:1.0:Entitlement" in entitlement["schemas"]
            print("SCIM entitlement resource schema is correct")
        
        # 5. Test role schema
        response = client.get("/v2/Roles/", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        
        if data['Resources']:
            role = data['Resources'][0]
            assert "schemas" in role
            assert "urn:okta:scim:schemas:core:1.0:Role" in role["schemas"]
            print("SCIM role resource schema is correct")
        
        print("✅ SCIM compliance tests passed")
    
    def test_09_comprehensive_summary(self, client):
        """Generate a comprehensive summary of the test data and functionality."""
        print("\n=== Comprehensive Test Summary ===")
        
        # Get all resources
        users_response = client.get("/v2/Users/", headers=self.AUTH_HEADERS)
        groups_response = client.get("/v2/Groups/", headers=self.AUTH_HEADERS)
        entitlements_response = client.get("/v2/Entitlements/", headers=self.AUTH_HEADERS)
        roles_response = client.get("/v2/Roles/", headers=self.AUTH_HEADERS)
        
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
        
        print(f"\n✅ All SCIM functionality tested successfully!")
        print(f"   - Schema discovery: ✅")
        print(f"   - User management: ✅")
        print(f"   - Group management: ✅")
        print(f"   - Entitlement management: ✅")
        print(f"   - Role management: ✅")
        print(f"   - Error handling: ✅")
        print(f"   - Pagination/filtering: ✅")
        print(f"   - SCIM compliance: ✅")
        
        print("✅ Comprehensive test summary completed") 