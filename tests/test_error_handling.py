"""
Error Handling Tests

Tests for SCIM error handling functionality including:
- Validation errors
- Not found errors
- Rate limiting
- Malformed requests
"""

import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scim_server.database import get_db
from scim_server.main import app


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_resource_id(self, client, sample_api_key):
        """Test handling of invalid resource IDs."""
        test_server_id = "test-server"
        invalid_id = "invalid-uuid-format"
        fake_id = "99999999-9999-9999-9999-999999999999"

        # Test invalid UUID format
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/{invalid_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

        # Test non-existent user
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/{fake_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404

        # Test non-existent group
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Groups/{fake_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404

        # Test non-existent entitlement
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/{fake_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404

    def test_invalid_server_id(self, client, sample_api_key):
        """Test handling of invalid server IDs."""
        fake_server_id = "fake-server-id"
        
        # Test with non-existent server ID
        response = client.get(f"/scim-identifier/{fake_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200  # Should return empty list, not 404

    def test_invalid_request_data(self, client, sample_api_key):
        """Test handling of invalid request data."""
        test_server_id = "test-server"
        # Test creating user with missing required fields
        invalid_user_data = {
            "name": {
                "givenName": "Test",
                "familyName": "User"
            }
            # Missing userName
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=invalid_user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

        # Test creating group with missing required fields
        invalid_group_data = {
            "description": "A test group"
            # Missing displayName
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                             json=invalid_group_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

        # Test creating entitlement with missing required fields
        invalid_entitlement_data = {
            "description": "A test entitlement"
            # Missing displayName and entitlementType
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                             json=invalid_entitlement_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

    def test_duplicate_resource_creation(self, client, sample_api_key):
        """Test handling of duplicate resource creation."""
        test_server_id = "test-server"
        # Create a user
        user_data = {
            "userName": "duplicate_user",
            "name": {
                "givenName": "Duplicate",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "duplicate@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201

        # Try to create the same user again
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 409  # Conflict

    def test_invalid_filter_syntax(self, client, sample_api_key):
        """Test handling of invalid filter syntax."""
        test_server_id = "test-server"
        invalid_filter = "invalid filter syntax"

        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?filter={invalid_filter}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

    def test_invalid_pagination_parameters(self, client, sample_api_key):
        """Test handling of invalid pagination parameters."""
        test_server_id = "test-server"
        # Test invalid startIndex
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?startIndex=invalid",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

        # Test invalid count
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?count=invalid",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

        # Test negative startIndex
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?startIndex=-1",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

        # Test zero count
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?count=0",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

    def test_malformed_query_parameters(self, client, sample_api_key):
        """Test handling of malformed query parameters."""
        test_server_id = "test-server"
        fake_server_id = "fake-server-id"
        
        # Test empty server ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?startIndex=1&count=10",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200

        # Test with invalid server ID
        response = client.get(f"/scim-identifier/{fake_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200  # Should return empty list

    def test_invalid_json_data(self, client, sample_api_key):
        """Test handling of invalid JSON data."""
        test_server_id = "test-server"
        # Test with malformed JSON
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             data="invalid json",
                             headers={"Authorization": f"Bearer {sample_api_key}", "Content-Type": "application/json"})
        assert response.status_code == 422

        # Test with empty JSON
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json={},
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

    def test_invalid_content_type(self, client, sample_api_key):
        """Test handling of invalid content type."""
        test_server_id = "test-server"
        user_data = {
            "userName": "test_user",
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

        # Test with wrong content type
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}", "Content-Type": "text/plain"})
        assert response.status_code == 422

    def test_missing_required_fields(self, client, sample_api_key):
        """Test handling of missing required fields."""
        test_server_id = "test-server"
        # Test user without userName
        user_data = {
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
        assert response.status_code == 400

        # Test user without emails
        user_data = {
            "userName": "test_user",
            "name": {
                "givenName": "Test",
                "familyName": "User"
            },
            "active": True
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

    def test_invalid_field_values(self, client, sample_api_key):
        """Test handling of invalid field values."""
        test_server_id = "test-server"
        # Test user with invalid email format
        user_data = {
            "userName": "test_user",
            "name": {
                "givenName": "Test",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "invalid-email",
                    "primary": True
                }
            ],
            "active": True
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

        # Test user with invalid active value
        user_data = {
            "userName": "test_user",
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
            "active": "invalid"
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

    def test_query_parameter_validation(self, client, sample_api_key):
        """Test validation of query parameters."""
        test_server_id = "test-server"
        # Test various invalid query parameter combinations
        invalid_params = [
            "serverID=",  # Empty server ID
            "serverID=invalid&startIndex=1",  # Invalid server ID with valid param
            "startIndex=1&count=10&serverID=",  # Empty server ID at end
            "serverID=test&startIndex=invalid",  # Invalid startIndex
            "serverID=test&count=invalid",  # Invalid count
            "serverID=test&filter=invalid filter",  # Invalid filter
        ]

        for params in invalid_params:
            response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?{params}",
                                headers={"Authorization": f"Bearer {sample_api_key}"})
            # Should handle gracefully, either 200 with empty results or 400 for invalid params
            assert response.status_code in [200, 400]

    def test_unsupported_operations(self, client, sample_api_key):
        """Test handling of unsupported operations."""
        test_server_id = "test-server"
        # Test PATCH operation (if not supported)
        user_data = {
            "userName": "patch_user",
            "name": {
                "givenName": "Patch",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": "patch@example.com",
                    "primary": True
                }
            ],
            "active": True
        }

        # Create a user first
        create_response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                                    json=user_data,
                                    headers={"Authorization": f"Bearer {sample_api_key}"})
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        # Test PATCH operation
        patch_data = {
            "userName": "updated_patch_user"
        }

        response = client.patch(f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
                              json=patch_data,
                              headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should either be supported (200) or not supported (405)
        assert response.status_code in [200, 405] 