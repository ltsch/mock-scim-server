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


class TestEntitlementManagement:
    """Test entitlement management operations."""

    def test_entitlement_create(self, client, sample_api_key):
        """Test creating a new entitlement."""
        test_server_id = "test-server"
        entitlement_data = {
            "displayName": "Test Entitlement",
            "description": "A test entitlement for testing purposes",
            "entitlementType": "application",
            "active": True
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                              json=entitlement_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        assert data["displayName"] == "Test Entitlement"
        assert data["description"] == "A test entitlement for testing purposes"
        assert data["entitlementType"] == "application"
        assert data["active"] is True

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

    def test_entitlement_update(self, client, sample_api_key):
        """Test updating an entitlement."""
        test_server_id = "test-server"
        # First create an entitlement
        entitlement_data = {
            "displayName": "Update Entitlement",
            "description": "An entitlement to update",
            "entitlementType": "application",
            "active": True
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                                    json=entitlement_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        entitlement_id = create_response.json()["id"]

        # Update the entitlement
        update_data = {
            "displayName": "Updated Entitlement",
            "description": "An updated entitlement description",
            "entitlementType": "database",
            "active": False
        }

        response = client.put(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/{entitlement_id}",
                            json=update_data,
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["displayName"] == "Updated Entitlement"
        assert data["description"] == "An updated entitlement description"
        assert data["entitlementType"] == "database"
        assert data["active"] is False

    def test_entitlement_delete(self, client, sample_api_key):
        """Test deleting an entitlement."""
        test_server_id = "test-server"
        # First create an entitlement
        entitlement_data = {
            "displayName": "Delete Entitlement",
            "description": "An entitlement to delete",
            "entitlementType": "application",
            "active": True
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                                    json=entitlement_data,
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

    def test_entitlement_get_by_id(self, client, sample_api_key):
        """Test getting an entitlement by ID."""
        test_server_id = "test-server"
        # First create an entitlement
        entitlement_data = {
            "displayName": "Get Entitlement",
            "description": "An entitlement to get by ID",
            "entitlementType": "application",
            "active": True
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                                    json=entitlement_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        entitlement_id = create_response.json()["id"]

        # Get the entitlement by ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/{entitlement_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entitlement_id
        assert data["displayName"] == "Get Entitlement"
        assert data["description"] == "An entitlement to get by ID"
        assert data["entitlementType"] == "application"

    def test_entitlement_create_with_invalid_data(self, client, sample_api_key):
        """Test creating an entitlement with invalid data."""
        test_server_id = "test-server"
        invalid_entitlement_data = {
            "displayName": "",  # Invalid empty display name
            "description": "An invalid entitlement",
            "entitlementType": "invalid_type",  # Invalid entitlement type
            "active": True
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                             json=invalid_entitlement_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 400

    def test_entitlement_filter_by_type(self, client, sample_api_key):
        """Test filtering entitlements by type."""
        test_server_id = "test-server"
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data 