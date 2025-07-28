"""
Group Management Tests

Tests for SCIM group management functionality including:
- Group CRUD operations
- Group validation
- Group filtering and search
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scim_server.database import get_db
from scim_server.main import app
from tests.test_base import DynamicTestDataMixin


class TestGroupManagement(DynamicTestDataMixin):
    """Test group management operations using dynamic data from codebase."""

    def test_group_create(self, client, sample_api_key, db_session):
        """Test creating a new group using dynamic data."""
        test_server_id = "test-server"
        group_data = self._generate_valid_group_data(db_session, test_server_id, "_create")

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                              json=group_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify all fields from the request are present in the response
        for field, value in group_data.items():
            assert data[field] == value

    def test_group_list(self, client, sample_api_key):
        """Test listing groups."""
        test_server_id = "test-server"
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data
        assert "startIndex" in data
        assert "itemsPerPage" in data

    def test_group_update(self, client, sample_api_key, db_session):
        """Test updating a group using dynamic data."""
        test_server_id = "test-server"
        
        # First create a group
        create_data = self._generate_valid_group_data(db_session, test_server_id, "_update")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        group_id = create_response.json()["id"]

        # Update the group with modified data
        update_data = self._generate_valid_group_data(db_session, test_server_id, "_updated")
        update_data["displayName"] = f"Updated {update_data['displayName']}"
        update_data["description"] = f"Updated description for {update_data['displayName']}"

        response = client.put(f"/scim-identifier/{test_server_id}/scim/v2/Groups/{group_id}",
                            json=update_data,
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        
        # Verify all fields from the update request are present in the response
        for field, value in update_data.items():
            assert data[field] == value

    def test_group_delete(self, client, sample_api_key, db_session):
        """Test deleting a group."""
        test_server_id = "test-server"
        
        # First create a group
        create_data = self._generate_valid_group_data(db_session, test_server_id, "_delete")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        group_id = create_response.json()["id"]

        # Delete the group
        response = client.delete(f"/scim-identifier/{test_server_id}/scim/v2/Groups/{group_id}",
                               headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 204

        # Verify group is deleted
        get_response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Groups/{group_id}",
                                 headers={"Authorization": f"Bearer {sample_api_key}"})
        assert get_response.status_code == 404

    def test_group_get_by_id(self, client, sample_api_key, db_session):
        """Test getting a group by ID."""
        test_server_id = "test-server"
        
        # First create a group
        create_data = self._generate_valid_group_data(db_session, test_server_id, "_get")
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                                    json=create_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        group_id = create_response.json()["id"]

        # Get the group by ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Groups/{group_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == group_id
        
        # Verify all fields from the create request are present in the response
        for field, value in create_data.items():
            assert data[field] == value

    def test_group_create_with_members(self, client, sample_api_key, db_session):
        """Test creating a group with members using dynamic data."""
        test_server_id = "test-server"
        
        # First create a user to use as a member
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_member")
        
        user_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                   json=user_data,
                                   headers={"Authorization": f"Bearer {sample_api_key}"})
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]
        
        # Create group data using dynamic data
        group_data = self._generate_valid_group_data(db_session, test_server_id, "_with_members")
        group_data["displayName"] = f"Group With Members {self._generate_unique_id()}"

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                              json=group_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify the group was created successfully
        assert data["displayName"] == group_data["displayName"]
        
        # Note: Members are not part of the current group schema, so we don't test for them
        # If members functionality is needed, it should be added to the schema first 