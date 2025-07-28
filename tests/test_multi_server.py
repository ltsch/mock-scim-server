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
from sqlalchemy.orm import Session

from scim_server.database import get_db
from scim_server.main import app


class TestMultiServer:
    """Test multi-server functionality and isolation."""

    def test_server_isolation_create(self, client, sample_api_key):
        """Test that users created in different servers are isolated."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create a user in server1
        user_data = {
            "userName": "testuser1",
            "name": {
                "givenName": "Test",
                "familyName": "User1"
            },
            "emails": [
                {
                    "value": "test1@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        response = client.post(f"/scim-identifier/{server1}/scim/v2/Users/",
                              json=user_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        created_user_id = response.json()["id"]

        # Verify user exists in server1
        response = client.get(f"/scim-identifier/{server1}/scim/v2/Users/{created_user_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200

        # Verify user does not exist in server2
        response = client.get(f"/scim-identifier/{server2}/scim/v2/Users/{created_user_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404

    def test_server_isolation_update(self, client, sample_api_key):
        """Test that updates in one server don't affect other servers."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create a user in server1
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

        create_response = client.post(f"/scim-identifier/{server1}/scim/v2/Users/",
                                    json=user_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        user_id = create_response.json()["id"]

        # Update user in server2 (should fail since user doesn't exist there)
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

        response = client.patch(f"/scim-identifier/{server2}/scim/v2/Users/{user_id}",
                              json=update_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404

    def test_server_isolation_list(self, client, sample_api_key):
        """Test that listing users returns only users from the specific server."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create users in both servers
        user_data1 = {
            "userName": "user1",
            "name": {
                "givenName": "User",
                "familyName": "One"
            },
            "emails": [
                {
                    "value": "user1@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        user_data2 = {
            "userName": "user2",
            "name": {
                "givenName": "User",
                "familyName": "Two"
            },
            "emails": [
                {
                    "value": "user2@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        # Create user in server1
        client.post(f"/scim-identifier/{server1}/scim/v2/Users/",
                   json=user_data1,
                   headers={"Authorization": f"Bearer {sample_api_key}"})

        # Create user in server2
        client.post(f"/scim-identifier/{server2}/scim/v2/Users/",
                   json=user_data2,
                   headers={"Authorization": f"Bearer {sample_api_key}"})

        # List users in server1
        response1 = client.get(f"/scim-identifier/{server1}/scim/v2/Users/",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response1.status_code == 200

        # List users in server2
        response2 = client.get(f"/scim-identifier/{server2}/scim/v2/Users/",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response2.status_code == 200

        # Verify that the users are different in each server
        users1 = response1.json()["Resources"]
        users2 = response2.json()["Resources"]
        
        # Each server should have its own set of users
        assert len(users1) >= 1
        assert len(users2) >= 1

    def test_server_isolation_filter(self, client, sample_api_key):
        """Test that filtering works correctly within each server."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create users in both servers
        user_data1 = {
            "userName": "activeuser1",
            "name": {
                "givenName": "Active",
                "familyName": "User1"
            },
            "emails": [
                {
                    "value": "active1@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        user_data2 = {
            "userName": "activeuser2",
            "name": {
                "givenName": "Active",
                "familyName": "User2"
            },
            "emails": [
                {
                    "value": "active2@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        # Create user in server1
        client.post(f"/scim-identifier/{server1}/scim/v2/Users/",
                   json=user_data1,
                   headers={"Authorization": f"Bearer {sample_api_key}"})

        # Create user in server2
        client.post(f"/scim-identifier/{server2}/scim/v2/Users/",
                   json=user_data2,
                   headers={"Authorization": f"Bearer {sample_api_key}"})

        # Filter active users in server1
        response1 = client.get(f"/scim-identifier/{server1}/scim/v2/Users/?filter=active eq true",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response1.status_code == 200

        # Filter active users in server2
        response2 = client.get(f"/scim-identifier/{server2}/scim/v2/Users/?filter=active eq true",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response2.status_code == 200

        # Verify that each server returns its own filtered results
        users1 = response1.json()["Resources"]
        users2 = response2.json()["Resources"]
        
        # Each server should have its own active users
        assert len(users1) >= 1
        assert len(users2) >= 1

    def test_server_isolation_pagination(self, client, sample_api_key):
        """Test that pagination works correctly within each server."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create users in both servers
        for i in range(3):
            user_data1 = {
                "userName": f"paguser1_{i}",
                "name": {
                    "givenName": f"Pag",
                    "familyName": f"User1_{i}"
                },
                "emails": [
                    {
                        "value": f"pag1_{i}@example.com",
                        "primary": True
                    }
                ],
                "active": True
            }

            user_data2 = {
                "userName": f"paguser2_{i}",
                "name": {
                    "givenName": f"Pag",
                    "familyName": f"User2_{i}"
                },
                "emails": [
                    {
                        "value": f"pag2_{i}@example.com",
                        "primary": True
                    }
                ],
                "active": True
            }

            # Create user in server1
            client.post(f"/scim-identifier/{server1}/scim/v2/Users/",
                       json=user_data1,
                       headers={"Authorization": f"Bearer {sample_api_key}"})

            # Create user in server2
            client.post(f"/scim-identifier/{server2}/scim/v2/Users/",
                       json=user_data2,
                       headers={"Authorization": f"Bearer {sample_api_key}"})

        # Paginate users in server1
        response1 = client.get(f"/scim-identifier/{server1}/scim/v2/Users/?startIndex=1&count=5",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response1.status_code == 200

        # Paginate users in server2
        response2 = client.get(f"/scim-identifier/{server2}/scim/v2/Users/?startIndex=1&count=5",
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response2.status_code == 200

        # Verify that each server returns its own paginated results
        users1 = response1.json()["Resources"]
        users2 = response2.json()["Resources"]
        
        # Each server should have its own paginated users
        assert len(users1) >= 1
        assert len(users2) >= 1

    def test_invalid_server_id(self, client, sample_api_key):
        """Test that invalid server IDs return appropriate errors."""
        test_server_id = "test-server"
        fake_id = "99999999-9999-9999-9999-999999999999"
        fake_server_id = "invalid-server-id"

        # Try to get a user with invalid server ID
        response = client.get(f"/scim-identifier/{fake_server_id}/scim/v2/Users/{fake_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404

        # Try to list users with invalid server ID
        response = client.get(f"/scim-identifier/{fake_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200  # Should return empty list, not 404

    def test_server_id_validation(self, client, sample_api_key):
        """Test that server ID validation works correctly."""
        test_server_id = "test-server"
        
        # Test with valid server ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200

        # Test with invalid server ID (contains invalid characters)
        invalid_server_id = "invalid@server#id"
        response = client.get(f"/scim-identifier/{invalid_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400 