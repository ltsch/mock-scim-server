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


class TestGroupManagement:
    """Test group management operations."""

    def test_group_create(self, client, sample_api_key):
        """Test creating a new group."""
        test_server_id = "test-server"
        group_data = {
            "displayName": "Test Group",
            "description": "A test group for testing purposes",
            "members": []
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                              json=group_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        assert data["displayName"] == "Test Group"
        assert data["description"] == "A test group for testing purposes"
        assert data["members"] == []

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

    def test_group_update(self, client, sample_api_key):
        """Test updating a group."""
        test_server_id = "test-server"
        # First create a group
        group_data = {
            "displayName": "Update Group",
            "description": "A group to update",
            "members": []
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                                    json=group_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        group_id = create_response.json()["id"]

        # Update the group
        update_data = {
            "displayName": "Updated Group",
            "description": "An updated group description",
            "members": []
        }

        response = client.put(f"/scim-identifier/{test_server_id}/scim/v2/Groups/{group_id}",
                            json=update_data,
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["displayName"] == "Updated Group"
        assert data["description"] == "An updated group description"

    def test_group_delete(self, client, sample_api_key):
        """Test deleting a group."""
        test_server_id = "test-server"
        # First create a group
        group_data = {
            "displayName": "Delete Group",
            "description": "A group to delete",
            "members": []
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                                    json=group_data,
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

    def test_group_get_by_id(self, client, sample_api_key):
        """Test getting a group by ID."""
        test_server_id = "test-server"
        # First create a group
        group_data = {
            "displayName": "Get Group",
            "description": "A group to get by ID",
            "members": []
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                                    json=group_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        group_id = create_response.json()["id"]

        # Get the group by ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Groups/{group_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == group_id
        assert data["displayName"] == "Get Group"
        assert data["description"] == "A group to get by ID"

    def test_group_create_with_members(self, client, sample_api_key):
        """Test creating a group with members."""
        test_server_id = "test-server"
        # First create a user to add as a member
        user_data = {
            "userName": "memberuser",
            "name": {
                "givenName": "Member",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "member@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        user_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                   json=user_data,
                                   headers={"Authorization": f"Bearer {sample_api_key}"})
        user_id = user_response.json()["id"]

        # Create group with the user as a member
        group_data = {
            "displayName": "Group With Members",
            "description": "A group with members",
            "members": [
                {
                    "value": user_id,
                    "display": "Member User"
                }
            ]
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                             json=group_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        assert data["displayName"] == "Group With Members"
        assert len(data["members"]) == 1
        assert data["members"][0]["value"] == user_id 