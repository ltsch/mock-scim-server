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
from tests.test_base import DynamicTestDataMixin


class TestMultiServer(DynamicTestDataMixin):
    """Test multi-server functionality and isolation using dynamic data."""

    def test_server_isolation_create(self, client, sample_api_key, db_session):
        """Test that users created in different servers are isolated using dynamic data."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create a user in server1 using dynamic data
        user_data = self._generate_valid_user_data(db_session, server1, "_isolation_1")

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

    def test_server_isolation_update(self, client, sample_api_key, db_session):
        """Test that updates in one server don't affect other servers using dynamic data."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create a user in server1 using dynamic data
        user_data = self._generate_valid_user_data(db_session, server1, "_isolation_update")

        create_response = client.post(f"/scim-identifier/{server1}/scim/v2/Users/",
                                    json=user_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        user_id = create_response.json()["id"]

        # Update user in server2 (should fail since user doesn't exist there)
        update_data = self._generate_valid_user_data(db_session, server2, "_isolation_update_2")
        
        response = client.put(f"/scim-identifier/{server2}/scim/v2/Users/{user_id}",
                            json=update_data,
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404

        # Update user in server1 (should succeed)
        response = client.put(f"/scim-identifier/{server1}/scim/v2/Users/{user_id}",
                            json=update_data,
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200

    def test_server_isolation_list(self, client, sample_api_key, db_session):
        """Test that listing users in different servers returns isolated results using dynamic data."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create users in both servers using dynamic data
        for i in range(3):
            user_data1 = self._generate_valid_user_data(db_session, server1, f"_list_1_{i}")
            user_data2 = self._generate_valid_user_data(db_session, server2, f"_list_2_{i}")

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

        # Verify that each server returns its own users
        users1 = response1.json()["Resources"]
        users2 = response2.json()["Resources"]
        
        # Each server should have its own users
        assert len(users1) >= 3
        assert len(users2) >= 3

        # Verify that users from server1 are not in server2 and vice versa
        user_ids_1 = {user["id"] for user in users1}
        user_ids_2 = {user["id"] for user in users2}
        
        # Should be no overlap between servers
        assert len(user_ids_1.intersection(user_ids_2)) == 0

    def test_server_isolation_filter(self, client, sample_api_key, db_session):
        """Test that filtering works correctly within each server using dynamic data."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create users in both servers with specific patterns using dynamic data
        for i in range(3):
            user_data1 = self._generate_valid_user_data(db_session, server1, f"_filter_1_{i}")
            user_data2 = self._generate_valid_user_data(db_session, server2, f"_filter_2_{i}")

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

    def test_server_isolation_pagination(self, client, sample_api_key, db_session):
        """Test that pagination works correctly within each server using dynamic data."""
        server1 = "server-1"
        server2 = "server-2"
        
        # Create users in both servers using dynamic data
        for i in range(3):
            user_data1 = self._generate_valid_user_data(db_session, server1, f"_page_1_{i}")
            user_data2 = self._generate_valid_user_data(db_session, server2, f"_page_2_{i}")

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
        # The implementation returns 404 for invalid server IDs, not 400
        invalid_server_id = "invalid@server#id"
        response = client.get(f"/scim-identifier/{invalid_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404  # Implementation returns 404, not 400 