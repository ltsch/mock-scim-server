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
from tests.test_base import DynamicTestDataMixin


class TestErrorHandling(DynamicTestDataMixin):
    """Test error handling and edge cases using dynamic data."""

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
        
        # Test with non-existent server ID - should return empty list, not 404
        response = client.get(f"/scim-identifier/{fake_server_id}/scim/v2/Users/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200  # Should return empty list, not 404

    def test_invalid_request_data(self, client, sample_api_key, db_session):
        """Test handling of invalid request data using dynamic data."""
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
            # Missing displayName and type
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                             json=invalid_entitlement_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

    def test_duplicate_resource_creation(self, client, sample_api_key, db_session):
        """Test handling of duplicate resource creation using dynamic data."""
        test_server_id = "test-server"
        
        # Generate valid user data
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_duplicate")
        
        # Create a user
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 201

        # Try to create the same user again (should fail due to duplicate email)
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 409  # Conflict for duplicate

    def test_invalid_filter_syntax(self, client, sample_api_key):
        """Test handling of invalid filter syntax."""
        test_server_id = "test-server"
        
        # Test invalid filter syntax
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?filter=invalid syntax",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should return 200 with empty results or 400 for invalid syntax
        assert response.status_code in [200, 400]

    def test_invalid_pagination_parameters(self, client, sample_api_key):
        """Test handling of invalid pagination parameters."""
        test_server_id = "test-server"
        
        # Test invalid startIndex
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?startIndex=invalid",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should return 422 for invalid parameter type
        assert response.status_code == 422

        # Test invalid count
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?count=invalid",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should return 422 for invalid parameter type
        assert response.status_code == 422

    def test_malformed_query_parameters(self, client, sample_api_key):
        """Test handling of malformed query parameters."""
        test_server_id = "test-server"
        
        # Test malformed filter
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?filter=",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should return 200 with empty results
        assert response.status_code == 200

    def test_invalid_json_data(self, client, sample_api_key):
        """Test handling of invalid JSON data."""
        test_server_id = "test-server"
        
        # Test with invalid JSON
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             content="invalid json",
                             headers={"Authorization": f"Bearer {sample_api_key}",
                                    "Content-Type": "application/json"})
        assert response.status_code == 422

    def test_invalid_content_type(self, client, sample_api_key):
        """Test handling of invalid content type."""
        test_server_id = "test-server"
        
        # Test with wrong content type
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json={"userName": "test"},
                             headers={"Authorization": f"Bearer {sample_api_key}",
                                    "Content-Type": "text/plain"})
        # Should still work as FastAPI is flexible with content types
        assert response.status_code in [201, 400, 422]

    def test_missing_required_fields(self, client, sample_api_key, db_session):
        """Test handling of missing required fields using dynamic data."""
        test_server_id = "test-server"
        
        # Get required fields from actual schema
        required_fields = self._get_schema_required_fields(db_session, test_server_id, "User")
        
        # Create user data missing required fields
        invalid_user_data = {}
        for field in required_fields:
            if field != "userName":  # Keep one required field to test partial validation
                invalid_user_data[field] = "test_value"
        
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=invalid_user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

    def test_invalid_field_values(self, client, sample_api_key, db_session):
        """Test handling of invalid field values using dynamic data."""
        test_server_id = "test-server"
        
        # Generate valid user data
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_invalid_values")
        
        # Modify with invalid values
        user_data["active"] = "not_a_boolean"  # Should be boolean
        
        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should return 400 for invalid field values
        assert response.status_code == 400

    def test_query_parameter_validation(self, client, sample_api_key):
        """Test validation of query parameters."""
        test_server_id = "test-server"
        
        # Test with valid parameters
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?startIndex=1&count=10",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200

        # Test with invalid parameters
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?startIndex=-1",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        # Should return 422 for invalid parameter values
        assert response.status_code == 422

    def test_unsupported_operations(self, client, sample_api_key):
        """Test handling of unsupported operations."""
        test_server_id = "test-server"
        
        # Test PATCH operation (not implemented)
        response = client.patch(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                              json={"userName": "test"},
                              headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 405  # Method Not Allowed 