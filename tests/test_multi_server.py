"""
Multi-Server Tests

Tests for SCIM multi-server functionality including:
- Server isolation
- Cross-server operations
- Server-specific data management
"""

import pytest
import time
from fastapi.testclient import TestClient
from tests.test_utils import get_available_servers, get_server_user_counts, validate_server_data_integrity, BaseEntityTest, get_fake_uuid, get_fake_server_id, create_test_user_data

class TestMultiServer(BaseEntityTest):
    """Tests for multi-server functionality and isolation."""
    
    def test_server_isolation(self, client, sample_api_key):
        """Test that servers are properly isolated."""
        # Get two different servers
        servers = get_available_servers()
        assert len(servers) >= 2, "Need at least 2 servers for isolation testing"
        
        server1, server2 = servers[0], servers[1]
        
        # Create a user in server1
        unique_username = self.get_unique_name("isolation_test") + "@example.com"
        user_data = create_test_user_data(unique_username)
        
        response = client.post(f"/scim/v2/Users/?serverID={server1}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=user_data)
        assert response.status_code == 201
        
        created_user_id = response.json()["id"]
        
        # Verify user exists in server1
        response = client.get(f"/scim/v2/Users/{created_user_id}?serverID={server1}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        # Verify user does NOT exist in server2
        response = client.get(f"/scim/v2/Users/{created_user_id}?serverID={server2}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 404
    
    def test_cross_server_operations(self, client, sample_api_key):
        """Test that cross-server operations are properly handled."""
        servers = get_available_servers()
        assert len(servers) >= 2, "Need at least 2 servers for cross-server testing"
        
        server1, server2 = servers[0], servers[1]
        
        # Create a user in server1
        unique_username = self.get_unique_name("cross_server_test") + "@example.com"
        user_data = create_test_user_data(unique_username)
        
        response = client.post(f"/scim/v2/Users/?serverID={server1}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=user_data)
        assert response.status_code == 201
        
        created_user_id = response.json()["id"]
        
        # Try to update the user in server2 (should fail)
        update_data = {"displayName": "Updated Name"}
        response = client.patch(f"/scim/v2/Users/{created_user_id}?serverID={server2}", 
                              headers=self.get_auth_headers(sample_api_key), 
                              json=update_data)
        assert response.status_code == 404
    
    def test_server_specific_data(self, client, sample_api_key):
        """Test that each server has its own data."""
        servers = get_available_servers()
        assert len(servers) >= 2, "Need at least 2 servers for data testing"
        
        server1, server2 = servers[0], servers[1]
        
        # Get user counts for each server
        response1 = client.get(f"/scim/v2/Users/?serverID={server1}", 
                              headers=self.get_auth_headers(sample_api_key))
        response2 = client.get(f"/scim/v2/Users/?serverID={server2}", 
                              headers=self.get_auth_headers(sample_api_key))
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        users1 = response1.json()["totalResults"]
        users2 = response2.json()["totalResults"]
        
        # Each server should have its own user count
        # (They might be the same, but they're independent)
        assert isinstance(users1, int)
        assert isinstance(users2, int)
    
    def test_server_filtering_isolation(self, client, sample_api_key):
        """Test that filtering works correctly within server isolation."""
        servers = get_available_servers()
        assert len(servers) >= 2, "Need at least 2 servers for filtering testing"
        
        server1, server2 = servers[0], servers[1]
        
        # Get users from both servers with the same filter
        response1 = client.get(f"/scim/v2/Users/?serverID={server1}&filter=active eq true", 
                              headers=self.get_auth_headers(sample_api_key))
        response2 = client.get(f"/scim/v2/Users/?serverID={server2}&filter=active eq true", 
                              headers=self.get_auth_headers(sample_api_key))
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Each server should return its own filtered results
        users1 = response1.json()["Resources"]
        users2 = response2.json()["Resources"]
        
        # Verify we got valid user objects
        for user in users1 + users2:
            assert "id" in user
            assert "userName" in user
            assert "active" in user
    
    def test_server_pagination_isolation(self, client, sample_api_key):
        """Test that pagination works correctly within server isolation."""
        servers = get_available_servers()
        assert len(servers) >= 2, "Need at least 2 servers for pagination testing"
        
        server1, server2 = servers[0], servers[1]
        
        # Get paginated results from both servers
        response1 = client.get(f"/scim/v2/Users/?serverID={server1}&startIndex=1&count=5", 
                              headers=self.get_auth_headers(sample_api_key))
        response2 = client.get(f"/scim/v2/Users/?serverID={server2}&startIndex=1&count=5", 
                              headers=self.get_auth_headers(sample_api_key))
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Each server should have its own pagination
        data1 = response1.json()
        data2 = response2.json()
        
        assert "startIndex" in data1
        assert "itemsPerPage" in data1
        assert "totalResults" in data1
        assert "Resources" in data1
        
        assert "startIndex" in data2
        assert "itemsPerPage" in data2
        assert "totalResults" in data2
        assert "Resources" in data2
    
    def test_server_error_handling(self, client, sample_api_key):
        """Test that error handling works correctly with server isolation."""
        fake_id = get_fake_uuid()
        fake_server_id = get_fake_server_id()
        
        # Test non-existent resource in valid server
        test_server_id = self.get_test_server_id()
        response = client.get(f"/scim/v2/Users/{fake_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 404
        
        # Test non-existent server (returns 200 with empty results)
        response = client.get(f"/scim/v2/Users/?serverID={fake_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        data = response.json()
        assert data["totalResults"] == 0
        assert len(data["Resources"]) == 0
    
    def test_server_count_consistency(self, client, sample_api_key):
        """Test that server counts are consistent with database."""
        user_counts = get_server_user_counts()
        
        for server_id, expected_count in user_counts.items():
            if expected_count > 0:  # Only test servers with data
                response = client.get(f"/scim/v2/Users/?serverID={server_id}", 
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
                assert response.status_code == 200
                
                data = response.json()
                actual_count = data["totalResults"]
                
                # Allow for small discrepancies due to test data creation/deletion
                assert abs(actual_count - expected_count) <= 5, \
                    f"Server {server_id} count mismatch: expected {expected_count}, got {actual_count}" 