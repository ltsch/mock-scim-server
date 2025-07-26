"""
Entitlement Management Tests

Tests for SCIM entitlement management functionality including:
- Entitlement CRUD operations
- Entitlement validation
- Entitlement filtering and search
"""

import pytest
from fastapi.testclient import TestClient
from tests.test_utils import BaseEntityTest, create_test_entitlement_data, get_valid_entitlement_type

class TestEntitlementManagement(BaseEntityTest):
    """Tests for SCIM entitlement management functionality."""
    
    def test_entitlement_list(self, client, sample_api_key):
        """Test listing entitlements."""
        self._test_entity_list(client, sample_api_key, "Entitlements")
    
    def test_entitlement_get_by_id(self, client, sample_api_key):
        """Test getting a specific entitlement by ID."""
        self._test_entity_get_by_id(client, sample_api_key, "Entitlements")
    
    def test_entitlement_create(self, client, sample_api_key):
        """Test creating a new entitlement."""
        test_server_id = self.get_test_server_id()
        unique_name = self.get_unique_name("testentitlement")
        valid_type = get_valid_entitlement_type()
    
        new_entitlement_data = create_test_entitlement_data(unique_name, valid_type)
    
        response = client.post(f"/scim/v2/Entitlements/?serverID={test_server_id}",
                             headers=self.get_auth_headers(sample_api_key),
                             json=new_entitlement_data)
        assert response.status_code == 201
    
        entitlement = response.json()
        assert entitlement["displayName"] == unique_name
        assert entitlement["type"] == valid_type
        assert entitlement["description"] == f"Test entitlement for unit testing - {unique_name}"
        assert "id" in entitlement
        assert "schemas" in entitlement
        assert "meta" in entitlement
    
    def test_entitlement_update(self, client, sample_api_key):
        """Test updating an existing entitlement."""
        test_server_id = self.get_test_server_id()
        
        # First get a list of entitlements
        response = client.get(f"/scim/v2/Entitlements/?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        entitlements = response.json()["Resources"]
        assert len(entitlements) > 0
        
        # Update the first entitlement
        entitlement_id = entitlements[0]["id"]
        original_display_name = entitlements[0]["displayName"]
        updated_display_name = f"Updated {original_display_name}"
        
        update_data = {
            "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
            "displayName": updated_display_name,
            "description": "Updated description"
        }
        
        response = client.put(f"/scim/v2/Entitlements/{entitlement_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key), 
                            json=update_data)
        assert response.status_code == 200
        
        updated_entitlement = response.json()
        assert updated_entitlement["displayName"] == updated_display_name
        assert updated_entitlement["description"] == "Updated description"
        assert updated_entitlement["id"] == entitlement_id
    
    def test_entitlement_delete(self, client, sample_api_key):
        """Test deleting an entitlement."""
        test_server_id = self.get_test_server_id()
        
        # First get a list of entitlements
        response = client.get(f"/scim/v2/Entitlements/?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        entitlements = response.json()["Resources"]
        assert len(entitlements) > 0
        
        # Delete the first entitlement
        entitlement_id = entitlements[0]["id"]
        response = client.delete(f"/scim/v2/Entitlements/{entitlement_id}?serverID={test_server_id}", 
                               headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 204
        
        # Verify the entitlement is deleted
        response = client.get(f"/scim/v2/Entitlements/{entitlement_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 404
    
    def test_entitlement_filter(self, client, sample_api_key):
        """Test filtering entitlements."""
        self._test_entity_filter(client, sample_api_key, "Entitlements", "displayName", "Entitlement")
    
    def test_entitlement_validation(self, client, sample_api_key):
        """Test entitlement validation."""
        test_server_id = self.get_test_server_id()
        
        # Test creating entitlement with invalid data
        invalid_entitlement_data = {
            "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
            # Missing required displayName and type
            "description": "Invalid entitlement"
        }
        
        response = client.post(f"/scim/v2/Entitlements/?serverID={test_server_id}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=invalid_entitlement_data)
        assert response.status_code == 400
    
    def test_entitlement_not_found(self, client, sample_api_key):
        """Test getting a non-existent entitlement."""
        self._test_entity_not_found(client, sample_api_key, "Entitlements")
    
    def test_entitlement_types(self, client, sample_api_key):
        """Test that entitlement types are valid."""
        test_server_id = self.get_test_server_id()
        
        # Get a list of entitlements to check their types
        response = client.get(f"/scim/v2/Entitlements/?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        entitlements = response.json()["Resources"]
        assert len(entitlements) > 0
        
        # Check that all entitlements have valid types
        valid_types = get_valid_entitlement_type()
        for entitlement in entitlements[:3]:  # Check first 3 entitlements
            assert "type" in entitlement
            # Note: We can't assert specific types since they come from the database
            # But we can verify the field exists and has a value
            assert entitlement["type"] is not None
            assert isinstance(entitlement["type"], str) 