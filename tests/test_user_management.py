"""
User Management Tests

Tests for SCIM user management functionality including:
- User CRUD operations
- User validation
- User filtering and search
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scim_server.database import get_db
from scim_server.main import app
from tests.test_base import DynamicTestDataMixin


class TestUserManagement(DynamicTestDataMixin):
    """Test user management operations using dynamic data from codebase."""

    def test_user_create(self, client, sample_api_key, db_session):
        """Test creating a new user using dynamic data."""
        test_server_id = "test-server"
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_create")

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                              json=user_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify all fields from the request are present in the response
        for field, value in user_data.items():
            if field == "emails":
                # Handle complex email array
                assert len(data[field]) == len(value)
                for i, email in enumerate(value):
                    assert data[field][i]["value"] == email["value"]
                    assert data[field][i]["primary"] == email["primary"]
            elif field == "name":
                # Handle complex name object
                assert data[field]["givenName"] == value["givenName"]
                assert data[field]["familyName"] == value["familyName"]
            else:
                assert data[field] == value

    def test_user_list(self, client, sample_api_key):
        """Test listing users."""
        test_server_id = "test-server"
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data
        assert "startIndex" in data
        assert "itemsPerPage" in data

    def test_user_update(self, client, sample_api_key, db_session):
        """Test updating a user using dynamic data."""
        test_server_id = "test-server"
        
        # First create a user
        create_data = self._generate_valid_user_data(db_session, test_server_id, "_update")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        user_id = create_response.json()["id"]

        # Update the user with modified data
        update_data = self._generate_valid_user_data(db_session, test_server_id, "_updated")
        update_data["displayName"] = f"Updated {update_data['displayName']}"
        
        # Only update name if it exists in the data
        if "name" in update_data:
            update_data["name"]["givenName"] = "Updated"
            update_data["name"]["familyName"] = "User"
        
        # Update email if it exists
        if "emails" in update_data and len(update_data["emails"]) > 0:
            update_data["emails"][0]["value"] = f"updated_{self._generate_unique_id()}@{self._get_random_company_domain()}"
        
        update_data["active"] = False

        response = client.put(f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
                            json=update_data,
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        
        # Verify all fields from the update request are present in the response
        for field, value in update_data.items():
            if field == "emails":
                # Handle complex email array
                assert len(data[field]) == len(value)
                for i, email in enumerate(value):
                    assert data[field][i]["value"] == email["value"]
                    assert data[field][i]["primary"] == email["primary"]
            elif field == "name":
                # Handle complex name object
                assert data[field]["givenName"] == value["givenName"]
                assert data[field]["familyName"] == value["familyName"]
            else:
                assert data[field] == value

    def test_user_delete(self, client, sample_api_key, db_session):
        """Test deleting a user."""
        test_server_id = "test-server"
        
        # First create a user
        create_data = self._generate_valid_user_data(db_session, test_server_id, "_delete")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        user_id = create_response.json()["id"]

        # Delete the user
        response = client.delete(f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
                               headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 204

        # Verify user is deleted
        get_response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
                                 headers={"Authorization": f"Bearer {sample_api_key}"})
        assert get_response.status_code == 404

    def test_user_get_by_id(self, client, sample_api_key, db_session):
        """Test getting a user by ID."""
        test_server_id = "test-server"
        
        # First create a user
        create_data = self._generate_valid_user_data(db_session, test_server_id, "_get")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        user_id = create_response.json()["id"]

        # Get the user by ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        
        # Verify all fields from the create request are present in the response
        for field, value in create_data.items():
            if field == "emails":
                # Handle complex email array
                assert len(data[field]) == len(value)
                for i, email in enumerate(value):
                    assert data[field][i]["value"] == email["value"]
                    assert data[field][i]["primary"] == email["primary"]
            elif field == "name":
                # Handle complex name object
                assert data[field]["givenName"] == value["givenName"]
                assert data[field]["familyName"] == value["familyName"]
            else:
                assert data[field] == value

    def test_user_create_with_invalid_data(self, client, sample_api_key, db_session):
        """Test creating a user with invalid data."""
        test_server_id = "test-server"
        
        # Generate invalid data by omitting required fields
        invalid_data = self._generate_invalid_data_missing_required_fields(db_session, test_server_id, "User")
        
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                              json=invalid_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 400
        error_data = response.json()
        # Check for error in the detail field structure
        assert "detail" in error_data
        assert "error" in error_data["detail"]
        assert "SCIM_VALIDATION_ERROR" in error_data["detail"]["error"] 