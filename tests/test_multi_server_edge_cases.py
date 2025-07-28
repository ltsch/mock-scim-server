"""
Multi-Server Edge Cases and Isolation Tests

Targeted tests for multi-server architecture edge cases and isolation scenarios:
- Server ID validation edge cases
- Cross-server data isolation
- Server-specific constraint validation
- Multi-server concurrent operations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_base import DynamicTestDataMixin


class TestMultiServerEdgeCases(DynamicTestDataMixin):
    """Test multi-server edge cases and isolation scenarios."""

    def test_server_id_validation_edge_cases(self, client, sample_api_key):
        """Test server ID validation edge cases."""
        
        # Test invalid server ID characters
        invalid_server_ids = [
            "server with spaces",
            "server@with@symbols",
            "server/with/slashes",
            "server\\with\\backslashes",
            "server.with.dots",
            "server:with:colons",
            "server;with;semicolons",
            "server,with,commas",
            "server'with'quotes",
            'server"with"quotes',
            "server`with`backticks",
            "server(with)parentheses",
            "server[with]brackets",
            "server{with}braces",
            "server<with>angles",
            "server|with|pipes",
            "server&with&ampersands",
            "server=with=equals",
            "server+with+pluses",
            "server#with#hashes",
            "server%with%percents",
            "server!with!exclamation",
            "server?with?question",
            "server~with~tildes",
            "server^with^carets",
            "server*with*asterisks",
            "server$with$dollars"
        ]
        
        for invalid_server_id in invalid_server_ids:
            response = client.get(f"/scim-identifier/{invalid_server_id}/scim/v2/Users/",
                                headers={"Authorization": f"Bearer {sample_api_key}"})
            # Some invalid characters (like slashes) cause 404 instead of 400 due to URL routing
            assert response.status_code in [400, 404], f"Server ID '{invalid_server_id}' should be rejected"
        
        # Test valid server ID characters
        valid_server_ids = [
            "server123",
            "server-with-hyphens",
            "server_with_underscores",
            "server123-with_underscores",
            "SERVER123",
            "server123-WITH_UNDERSCORES",
            "a",
            "z",
            "0",
            "9",
            "a1b2c3",
            "server-123",
            "server_123",
            "123-server",
            "123_server"
        ]
        
        for valid_server_id in valid_server_ids:
            response = client.get(f"/scim-identifier/{valid_server_id}/scim/v2/Users/",
                                headers={"Authorization": f"Bearer {sample_api_key}"})
            # Should not return 400 for valid server IDs (may return 200 or 401)
            assert response.status_code != 400, f"Server ID '{valid_server_id}' should be accepted"

    def test_cross_server_data_isolation(self, client, sample_api_key, db_session):
        """Test that data is properly isolated between servers."""
        server1_id = "server1"
        server2_id = "server2"
        
        # Create identical users in different servers
        user_data1 = self._generate_valid_user_data(db_session, server1_id, "_server1")
        user_data2 = self._generate_valid_user_data(db_session, server2_id, "_server2")
        
        # Use same username and email for both servers
        same_username = "same_user"
        same_email = "same@example.com"
        
        user_data1["userName"] = same_username
        user_data1["emails"] = [{"value": same_email, "primary": True}]
        user_data2["userName"] = same_username
        user_data2["emails"] = [{"value": same_email, "primary": True}]
        
        # Create user in server1
        response = client.post(f"/scim-identifier/{server1_id}/scim/v2/Users/",
                             json=user_data1,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201
        user1_id = response.json()["id"]
        
        # Create user in server2 (should succeed due to server isolation)
        response = client.post(f"/scim-identifier/{server2_id}/scim/v2/Users/",
                             json=user_data2,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201
        user2_id = response.json()["id"]
        
        # Verify users are different
        assert user1_id != user2_id
        
        # Verify each server can only see its own user
        response = client.get(f"/scim-identifier/{server1_id}/scim/v2/Users/{user1_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        response = client.get(f"/scim-identifier/{server1_id}/scim/v2/Users/{user2_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404  # Should not find user from other server
        
        response = client.get(f"/scim-identifier/{server2_id}/scim/v2/Users/{user2_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        response = client.get(f"/scim-identifier/{server2_id}/scim/v2/Users/{user1_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404  # Should not find user from other server

    def test_server_specific_constraint_validation(self, client, sample_api_key, db_session):
        """Test that server-specific constraints are properly enforced."""
        server1_id = "constraint-server1"
        server2_id = "constraint-server2"
        
        # Create user in server1
        user_data1 = self._generate_valid_user_data(db_session, server1_id, "_constraint1")
        user_data1["userName"] = "duplicate_user"
        user_data1["emails"] = [{"value": "duplicate@example.com", "primary": True}]
        
        response = client.post(f"/scim-identifier/{server1_id}/scim/v2/Users/",
                             json=user_data1,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201
        
        # Try to create duplicate in same server (should fail)
        user_data1_dup = self._generate_valid_user_data(db_session, server1_id, "_constraint1_dup")
        user_data1_dup["userName"] = "duplicate_user"
        user_data1_dup["emails"] = [{"value": "duplicate@example.com", "primary": True}]
        
        response = client.post(f"/scim-identifier/{server1_id}/scim/v2/Users/",
                             json=user_data1_dup,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 409  # Conflict - duplicate in same server
        
        # Create same user in server2 (should succeed due to server isolation)
        user_data2 = self._generate_valid_user_data(db_session, server2_id, "_constraint2")
        user_data2["userName"] = "duplicate_user"
        user_data2["emails"] = [{"value": "duplicate@example.com", "primary": True}]
        
        response = client.post(f"/scim-identifier/{server2_id}/scim/v2/Users/",
                             json=user_data2,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201  # Should succeed - different server

    def test_multi_server_concurrent_operations(self, client, sample_api_key, db_session):
        """Test concurrent operations across multiple servers."""
        server1_id = "concurrent-server1"
        server2_id = "concurrent-server2"
        server3_id = "concurrent-server3"
        
        # Create users in multiple servers concurrently
        user_data_list = []
        for i in range(3):
            for server_id in [server1_id, server2_id, server3_id]:
                user_data = self._generate_valid_user_data(db_session, server_id, f"_concurrent_{i}")
                user_data_list.append((server_id, user_data))
        
        # Create all users
        created_users = []
        for server_id, user_data in user_data_list:
            response = client.post(f"/scim-identifier/{server_id}/scim/v2/Users/",
                                 json=user_data,
                                 headers={"Authorization": f"Bearer {sample_api_key}"})
            assert response.status_code == 201
            created_users.append((server_id, response.json()["id"]))
        
        # Verify each server has its own users
        for server_id in [server1_id, server2_id, server3_id]:
            response = client.get(f"/scim-identifier/{server_id}/scim/v2/Users/",
                                headers={"Authorization": f"Bearer {sample_api_key}"})
            assert response.status_code == 200
            data = response.json()
            assert data["totalResults"] >= 3  # Each server should have at least 3 users

    def test_server_id_case_sensitivity(self, client, sample_api_key, db_session):
        """Test server ID case sensitivity handling."""
        server_id_lower = "case-test-server"
        server_id_upper = "CASE-TEST-SERVER"
        server_id_mixed = "Case-Test-Server"
        
        # Create user in lowercase server
        user_data = self._generate_valid_user_data(db_session, server_id_lower, "_case_test")
        
        response = client.post(f"/scim-identifier/{server_id_lower}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Try to access with different case variations
        # This tests whether server IDs are case-sensitive or case-insensitive
        
        # Test uppercase
        response = client.get(f"/scim-identifier/{server_id_upper}/scim/v2/Users/{user_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should either find the user (case-insensitive) or not find it (case-sensitive)
        assert response.status_code in [200, 404]
        
        # Test mixed case
        response = client.get(f"/scim-identifier/{server_id_mixed}/scim/v2/Users/{user_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code in [200, 404]

    def test_server_id_length_limits(self, client, sample_api_key):
        """Test server ID length limits."""
        
        # Test very long server ID
        long_server_id = "a" * 1000  # 1000 character server ID
        
        response = client.get(f"/scim-identifier/{long_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should either accept or reject based on implementation limits
        assert response.status_code in [200, 400, 414]  # 414 = Request-URI Too Long
        
        # Test empty server ID
        response = client.get("/scim-identifier//scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404  # Empty server ID causes 404 due to URL routing

    def test_multi_server_schema_isolation(self, client, sample_api_key):
        """Test that schemas are properly isolated between servers."""
        server1_id = "schema-server1"
        server2_id = "schema-server2"
        
        # Get schemas from both servers
        response1 = client.get(f"/scim-identifier/{server1_id}/scim/v2/Schemas/",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response1.status_code == 200
        schemas1 = response1.json()
        
        response2 = client.get(f"/scim-identifier/{server2_id}/scim/v2/Schemas/",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response2.status_code == 200
        schemas2 = response2.json()
        
        # Verify both servers have the same core schemas (they should be identical)
        # This tests that schema generation is consistent across servers
        assert schemas1["totalResults"] == schemas2["totalResults"]
        
        # Verify core SCIM schemas are present in both
        schema_ids1 = [s["id"] for s in schemas1["Resources"]]
        schema_ids2 = [s["id"] for s in schemas2["Resources"]]
        
        core_schemas = [
            "urn:ietf:params:scim:schemas:core:2.0:User",
            "urn:ietf:params:scim:schemas:core:2.0:Group",
            "urn:okta:scim:schemas:core:1.0:Entitlement"
        ]
        
        for schema_id in core_schemas:
            assert schema_id in schema_ids1, f"Schema {schema_id} missing from server1"
            assert schema_id in schema_ids2, f"Schema {schema_id} missing from server2"

    def test_multi_server_resource_types_isolation(self, client, sample_api_key):
        """Test that resource types are properly isolated between servers."""
        server1_id = "resource-server1"
        server2_id = "resource-server2"
        
        # Get resource types from both servers
        response1 = client.get(f"/scim-identifier/{server1_id}/scim/v2/ResourceTypes/",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response1.status_code == 200
        resource_types1 = response1.json()
        
        response2 = client.get(f"/scim-identifier/{server2_id}/scim/v2/ResourceTypes/",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response2.status_code == 200
        resource_types2 = response2.json()
        
        # Verify both servers have the same resource types (they should be identical)
        assert resource_types1["totalResults"] == resource_types2["totalResults"]
        
        # Verify core resource types are present in both
        resource_names1 = [rt["name"] for rt in resource_types1["Resources"]]
        resource_names2 = [rt["name"] for rt in resource_types2["Resources"]]
        
        core_resources = ["User", "Group", "Entitlement"]
        
        for resource_name in core_resources:
            assert resource_name in resource_names1, f"Resource {resource_name} missing from server1"
            assert resource_name in resource_names2, f"Resource {resource_name} missing from server2"

    def test_multi_server_filter_isolation(self, client, sample_api_key, db_session):
        """Test that filters are properly isolated between servers."""
        server1_id = "filter-server1"
        server2_id = "filter-server2"
        
        # Create users with same username in different servers
        username = "filter_test_user"
        
        user_data1 = self._generate_valid_user_data(db_session, server1_id, "_filter1")
        user_data1["userName"] = username
        
        user_data2 = self._generate_valid_user_data(db_session, server2_id, "_filter2")
        user_data2["userName"] = username
        
        # Create users
        response = client.post(f"/scim-identifier/{server1_id}/scim/v2/Users/",
                             json=user_data1,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201
        
        response = client.post(f"/scim-identifier/{server2_id}/scim/v2/Users/",
                             json=user_data2,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201
        
        # Test filtering in each server
        filter_query = f'userName eq "{username}"'
        
        response1 = client.get(f"/scim-identifier/{server1_id}/scim/v2/Users?filter={filter_query}",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["totalResults"] == 1  # Should find 1 user in server1
        
        response2 = client.get(f"/scim-identifier/{server2_id}/scim/v2/Users?filter={filter_query}",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["totalResults"] == 1  # Should find 1 user in server2
        
        # Verify the users are different
        user1_id = data1["Resources"][0]["id"]
        user2_id = data2["Resources"][0]["id"]
        assert user1_id != user2_id 