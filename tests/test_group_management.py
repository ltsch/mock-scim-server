"""
Group Management Tests

Tests for SCIM group management functionality including:
- Group CRUD operations
- Group validation
- Group filtering and search
"""

import pytest
from fastapi.testclient import TestClient
from tests.test_utils import BaseEntityTest, create_test_group_data

class TestGroupManagement(BaseEntityTest):
    """Tests for SCIM group management functionality."""
    
    def test_group_list(self, client, sample_api_key):
        """Test listing groups."""
        self._test_entity_list(client, sample_api_key, "Groups")
    
    def test_group_get_by_id(self, client, sample_api_key):
        """Test getting a specific group by ID."""
        self._test_entity_get_by_id(client, sample_api_key, "Groups")
    
    def test_group_create(self, client, sample_api_key):
        """Test creating a new group."""
        test_server_id = self.get_test_server_id()
        unique_group_name = self.get_unique_name("testgroup")
    
        new_group_data = create_test_group_data(unique_group_name)
    
        response = client.post(f"/scim/v2/Groups/?serverID={test_server_id}",
                             headers=self.get_auth_headers(sample_api_key),
                             json=new_group_data)
        assert response.status_code == 201
    
        group = response.json()
        assert group["displayName"] == unique_group_name
        assert group["description"] == f"Test group for unit testing - {unique_group_name}"
        assert "id" in group
        assert "schemas" in group
        assert "meta" in group
    
    def test_group_update(self, client, sample_api_key):
        """Test updating an existing group."""
        test_server_id = self.get_test_server_id()
        
        # First get a list of groups
        response = client.get(f"/scim/v2/Groups/?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        groups = response.json()["Resources"]
        assert len(groups) > 0
        
        # Update the first group
        group_id = groups[0]["id"]
        original_display_name = groups[0]["displayName"]
        updated_display_name = f"Updated {original_display_name}"
        
        update_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": updated_display_name,
            "description": "Updated description"
        }
        
        response = client.put(f"/scim/v2/Groups/{group_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key), 
                            json=update_data)
        assert response.status_code == 200
        
        updated_group = response.json()
        assert updated_group["displayName"] == updated_display_name
        assert updated_group["description"] == "Updated description"
        assert updated_group["id"] == group_id
    
    def test_group_delete(self, client, sample_api_key):
        """Test deleting a group."""
        test_server_id = self.get_test_server_id()
        
        # First get a list of groups
        response = client.get(f"/scim/v2/Groups/?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        groups = response.json()["Resources"]
        assert len(groups) > 0
        
        # Delete the first group
        group_id = groups[0]["id"]
        response = client.delete(f"/scim/v2/Groups/{group_id}?serverID={test_server_id}", 
                               headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 204
        
        # Verify the group is deleted
        response = client.get(f"/scim/v2/Groups/{group_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 404
    
    def test_group_filter(self, client, sample_api_key):
        """Test filtering groups."""
        self._test_entity_filter(client, sample_api_key, "Groups", "displayName", "Group")
    
    def test_group_validation(self, client, sample_api_key):
        """Test group validation."""
        test_server_id = self.get_test_server_id()
        
        # Test creating group with invalid data
        invalid_group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            # Missing required displayName
            "description": "Invalid group"
        }
        
        response = client.post(f"/scim/v2/Groups/?serverID={test_server_id}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=invalid_group_data)
        assert response.status_code == 400
    
    def test_group_not_found(self, client, sample_api_key):
        """Test getting a non-existent group."""
        self._test_entity_not_found(client, sample_api_key, "Groups") 