"""
User Management Tests

Tests for SCIM user management functionality including:
- User CRUD operations
- User validation
- User filtering and search
"""

import pytest
from fastapi.testclient import TestClient
from tests.test_utils import BaseEntityTest, create_test_user_data, get_valid_entitlement_type

class TestUserManagement(BaseEntityTest):
    """Tests for SCIM user management functionality."""
    
    def test_user_list(self, client, sample_api_key):
        """Test listing users."""
        self._test_entity_list(client, sample_api_key, "Users")
    
    def test_user_get_by_id(self, client, sample_api_key):
        """Test getting a specific user by ID."""
        self._test_entity_get_by_id(client, sample_api_key, "Users")
    
    def test_user_create(self, client, sample_api_key):
        """Test creating a new user."""
        test_server_id = self.get_test_server_id()
        unique_username = self.get_unique_name("testuser") + "@example.com"
    
        new_user_data = create_test_user_data(unique_username)
    
        response = client.post(f"/scim/v2/Users/?serverID={test_server_id}",
                             headers=self.get_auth_headers(sample_api_key),
                             json=new_user_data)
        assert response.status_code == 201
    
        user = response.json()
        assert user["userName"] == unique_username
        assert user["displayName"] == f"Test User {unique_username}"
        assert "id" in user
        assert "schemas" in user
        assert "meta" in user
    
    def test_user_update(self, client, sample_api_key):
        """Test updating an existing user."""
        test_server_id = self.get_test_server_id()
        
        # First get a list of users
        response = client.get(f"/scim/v2/Users/?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        users = response.json()["Resources"]
        assert len(users) > 0
        
        # Update the first user
        user_id = users[0]["id"]
        original_display_name = users[0]["displayName"]
        updated_display_name = f"Updated {original_display_name}"
        
        update_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "displayName": updated_display_name
        }
        
        response = client.put(f"/scim/v2/Users/{user_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key), 
                            json=update_data)
        assert response.status_code == 200
        
        updated_user = response.json()
        assert updated_user["displayName"] == updated_display_name
        assert updated_user["id"] == user_id
    
    def test_user_delete(self, client, sample_api_key):
        """Test deleting a user (soft delete)."""
        test_server_id = self.get_test_server_id()
        
        # First get a list of users
        response = client.get(f"/scim/v2/Users/?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        users = response.json()["Resources"]
        assert len(users) > 0
        
        # Delete the first user
        user_id = users[0]["id"]
        response = client.delete(f"/scim/v2/Users/{user_id}?serverID={test_server_id}", 
                               headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 204  # No Content for successful delete
        
        # Verify the user is deactivated (soft delete)
        response = client.get(f"/scim/v2/Users/{user_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["active"] == False
    
    def test_user_filter(self, client, sample_api_key):
        """Test filtering users."""
        self._test_entity_filter(client, sample_api_key, "Users", "displayName", "User")
    
    def test_user_validation(self, client, sample_api_key):
        """Test user validation."""
        test_server_id = self.get_test_server_id()
        
        # Test creating user with invalid data
        invalid_user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            # Missing required userName
            "displayName": "Invalid User"
        }
        
        response = client.post(f"/scim/v2/Users/?serverID={test_server_id}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=invalid_user_data)
        assert response.status_code == 400
    
    def test_user_not_found(self, client, sample_api_key):
        """Test getting a non-existent user."""
        self._test_entity_not_found(client, sample_api_key, "Users") 