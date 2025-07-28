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


class TestUserManagement:
    """Test user management operations."""

    def test_user_create(self, client, sample_api_key):
        """Test creating a new user."""
        test_server_id = "test-server"
        user_data = {
            "userName": "testuser",
            "name": {
                "givenName": "Test",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "test@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                              json=user_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        assert data["userName"] == "testuser"
        assert data["name"]["givenName"] == "Test"
        assert data["name"]["familyName"] == "User"
        assert data["emails"][0]["value"] == "test@example.com"
        assert data["active"] is True

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

    def test_user_update(self, client, sample_api_key):
        """Test updating a user."""
        test_server_id = "test-server"
        # First create a user
        user_data = {
            "userName": "updateuser",
            "name": {
                "givenName": "Update",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "update@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                    json=user_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        user_id = create_response.json()["id"]

        # Update the user
        update_data = {
            "userName": "updateduser",
            "name": {
                "givenName": "Updated",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "updated@example.com",
                    "primary": True
                }
            ],
            "active": False
        }

        response = client.put(f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
                            json=update_data,
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["userName"] == "updateduser"
        assert data["name"]["givenName"] == "Updated"
        assert data["name"]["familyName"] == "User"
        assert data["emails"][0]["value"] == "updated@example.com"
        assert data["active"] is False

    def test_user_delete(self, client, sample_api_key):
        """Test deleting a user."""
        test_server_id = "test-server"
        # First create a user
        user_data = {
            "userName": "deleteuser",
            "name": {
                "givenName": "Delete",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "delete@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                    json=user_data,
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

    def test_user_get_by_id(self, client, sample_api_key):
        """Test getting a user by ID."""
        test_server_id = "test-server"
        # First create a user
        user_data = {
            "userName": "getuser",
            "name": {
                "givenName": "Get",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "get@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                    json=user_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        user_id = create_response.json()["id"]

        # Get the user by ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["userName"] == "getuser"
        assert data["name"]["givenName"] == "Get"
        assert data["name"]["familyName"] == "User"

    def test_user_create_with_invalid_data(self, client, sample_api_key):
        """Test creating a user with invalid data."""
        test_server_id = "test-server"
        invalid_user_data = {
            "userName": "",  # Invalid empty username
            "name": {
                "givenName": "Invalid",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "invalid@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=invalid_user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 400 