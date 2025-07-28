"""
Entitlement Management Tests

Tests for SCIM entitlement management functionality including:
- Entitlement CRUD operations
- Entitlement validation
- Entitlement filtering and search
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scim_server.database import get_db
from scim_server.main import app
from tests.test_base import DynamicTestDataMixin


class TestEntitlementManagement(DynamicTestDataMixin):
    """Test entitlement management operations using dynamic data from codebase."""

    def test_entitlement_create(self, client, sample_api_key, db_session):
        """Test creating a new entitlement using dynamic data."""
        test_server_id = "test-server"
        entitlement_data = self._generate_valid_entitlement_data(db_session, test_server_id, "_create")

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                              json=entitlement_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify all fields from the request are present in the response
        for field, value in entitlement_data.items():
            assert data[field] == value

    def test_entitlement_list(self, client, sample_api_key):
        """Test listing entitlements."""
        test_server_id = "test-server"
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data
        assert "startIndex" in data
        assert "itemsPerPage" in data

    def test_entitlement_update(self, client, sample_api_key, db_session):
        """Test updating an entitlement using dynamic data."""
        test_server_id = "test-server"
        
        # First create an entitlement
        create_data = self._generate_valid_entitlement_data(db_session, test_server_id, "_update")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        entitlement_id = create_response.json()["id"]

        # Update the entitlement with modified data
        update_data = self._generate_valid_entitlement_data(db_session, test_server_id, "_updated")
        update_data["displayName"] = f"Updated {update_data['displayName']}"
        update_data["description"] = f"Updated description for {update_data['displayName']}"

        response = client.put(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/{entitlement_id}",
                            json=update_data,
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        
        # Verify all fields from the update request are present in the response
        for field, value in update_data.items():
            assert data[field] == value

    def test_entitlement_delete(self, client, sample_api_key, db_session):
        """Test deleting an entitlement."""
        test_server_id = "test-server"
        
        # First create an entitlement
        create_data = self._generate_valid_entitlement_data(db_session, test_server_id, "_delete")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        entitlement_id = create_response.json()["id"]

        # Delete the entitlement
        response = client.delete(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/{entitlement_id}",
                               headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 204

        # Verify entitlement is deleted
        get_response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/{entitlement_id}",
                                 headers={"Authorization": f"Bearer {sample_api_key}"})
        assert get_response.status_code == 404

    def test_entitlement_get_by_id(self, client, sample_api_key, db_session):
        """Test getting an entitlement by ID."""
        test_server_id = "test-server"
        
        # First create an entitlement
        create_data = self._generate_valid_entitlement_data(db_session, test_server_id, "_get")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        entitlement_id = create_response.json()["id"]

        # Get the entitlement by ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/{entitlement_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entitlement_id
        
        # Verify all fields from the create request are present in the response
        for field, value in create_data.items():
            assert data[field] == value

    def test_entitlement_create_with_invalid_data(self, client, sample_api_key, db_session):
        """Test creating an entitlement with invalid data."""
        test_server_id = "test-server"
        
        # Generate invalid data by omitting required fields
        invalid_data = self._generate_invalid_data_missing_required_fields(db_session, test_server_id, "Entitlement")
        
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                              json=invalid_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 400
        error_data = response.json()
        # Check for error in the detail field structure
        assert "detail" in error_data
        assert "error" in error_data["detail"]
        assert "SCIM_VALIDATION_ERROR" in error_data["detail"]["error"]

    def test_entitlement_filter_by_type(self, client, sample_api_key, db_session):
        """Test filtering entitlements by type using dynamic data."""
        test_server_id = "test-server"
        
        # Get entitlement definitions to use valid types
        entitlement_defs = self._get_entitlement_definitions(db_session, test_server_id)
        
        if len(entitlement_defs) < 3:
            # Skip test if not enough entitlement definitions
            pytest.skip("Not enough entitlement definitions for filtering test")
        
        # Create test entitlements with different valid types
        created_entitlements = []
        created_types = []
        for i in range(3):
            entitlement_data = self._generate_valid_entitlement_data(db_session, test_server_id, f"_filter_{i}")
            
            response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                                 json=entitlement_data,
                                 headers={"Authorization": f"Bearer {sample_api_key}"})
            assert response.status_code == 201
            created_entitlements.append(response.json()["id"])
            created_types.append(entitlement_data["type"])

        # Filter by the type of the second entitlement
        filter_type = created_types[1]  # Use the type from the second created entitlement
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/?filter=type eq \"{filter_type}\"",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        
        # Verify that at least one of our created entitlements is returned
        created_ids = set(created_entitlements)
        
        # Check that the entitlement with the filtered type is returned
        matching_entitlements = [resource for resource in data["Resources"] 
                               if resource["id"] in created_ids and resource["type"] == filter_type]
        assert len(matching_entitlements) >= 1, f"Expected at least one entitlement with type {filter_type}"
        
        # Verify that the specific entitlement we expect is in the results
        expected_entitlement_id = created_entitlements[1]  # The second created entitlement
        found_expected = any(resource["id"] == expected_entitlement_id and resource["type"] == filter_type 
                           for resource in data["Resources"])
        assert found_expected, f"Expected entitlement {expected_entitlement_id} with type {filter_type} to be in filtered results" 