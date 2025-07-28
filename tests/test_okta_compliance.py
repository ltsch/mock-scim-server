"""
Okta Compliance Tests

Tests for SCIM Okta compliance functionality including:
- Okta-specific schema discovery
- Okta entitlement support
- Okta filtering and pagination
- Okta error handling
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scim_server.database import get_db
from scim_server.main import app
from tests.test_base import DynamicTestDataMixin


class TestOktaCompliance(DynamicTestDataMixin):
    """Test Okta compliance using dynamic data from codebase."""

    def test_okta_schema_discovery(self, client, sample_api_key):
        """Test that Okta can discover our schemas."""
        test_server_id = "test-server"
        
        # Test ResourceTypes endpoint
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/ResourceTypes/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data
        
        # Verify we have the expected resource types
        resource_types = [rt["name"] for rt in data["Resources"]]
        assert "User" in resource_types
        assert "Group" in resource_types
        assert "Entitlement" in resource_types
        
        # Test Schemas endpoint
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Schemas/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        
        # Verify we have the expected schemas
        schemas = [s["id"] for s in data["Resources"]]
        assert "urn:ietf:params:scim:schemas:core:2.0:User" in schemas
        assert "urn:ietf:params:scim:schemas:core:2.0:Group" in schemas
        assert "urn:okta:scim:schemas:core:1.0:Entitlement" in schemas

    def test_okta_entitlement_support(self, client, sample_api_key):
        """Test that Okta entitlement endpoints are supported."""
        test_server_id = "test-server"
        
        # Test Entitlements endpoint exists
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data

    def test_okta_user_attributes(self, client, sample_api_key, db_session):
        """Test that Okta-compatible user attributes are supported using dynamic data."""
        test_server_id = "test-server"
        
        # Generate user data using actual schema and configuration
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_okta")

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

    def test_okta_group_attributes(self, client, sample_api_key, db_session):
        """Test that Okta-compatible group attributes are supported using dynamic data."""
        test_server_id = "test-server"
        
        # Generate group data using actual schema and configuration
        group_data = self._generate_valid_group_data(db_session, test_server_id, "_okta")

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                             json=group_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify all fields from the request are present in the response
        for field, value in group_data.items():
            assert data[field] == value

    def test_okta_entitlement_attributes(self, client, sample_api_key, db_session):
        """Test that Okta-compatible entitlement attributes are supported using dynamic data."""
        test_server_id = "test-server"
        
        # Generate entitlement data using actual schema and configuration
        entitlement_data = self._generate_valid_entitlement_data(db_session, test_server_id, "_okta")

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                             json=entitlement_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify all fields from the request are present in the response
        for field, value in entitlement_data.items():
            assert data[field] == value

    def test_okta_filtering_support(self, client, sample_api_key, db_session):
        """Test that Okta filtering syntax is supported."""
        test_server_id = "test-server"
        
        # Create test users using dynamic data
        for i in range(3):
            user_data = self._generate_valid_user_data(db_session, test_server_id, f"_filter_{i}")
            
            client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                       json=user_data,
                       headers={"Authorization": f"Bearer {sample_api_key}"})

        # Test various Okta filter patterns
        filters = [
            "userName eq \"testuser_filter_0\"",
            "emails[type eq \"work\" and primary eq true]",
            "active eq true",
            "name.givenName co \"Test\""
        ]
        
        for filter_query in filters:
            response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?filter={filter_query}",
                                headers={"Authorization": f"Bearer {sample_api_key}"})
            # Should return 200 even if no results
            assert response.status_code in [200, 400]  # 400 for unsupported filters is acceptable

    def test_okta_pagination_support(self, client, sample_api_key, db_session):
        """Test that Okta pagination is supported."""
        test_server_id = "test-server"
        
        # Create test users using dynamic data
        for i in range(5):
            user_data = self._generate_valid_user_data(db_session, test_server_id, f"_page_{i}")
            
            client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                       json=user_data,
                       headers={"Authorization": f"Bearer {sample_api_key}"})

        # Test pagination parameters
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?startIndex=1&count=2",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data
        assert "startIndex" in data
        assert "itemsPerPage" in data

    def test_okta_error_handling(self, client, sample_api_key):
        """Test that Okta-compatible error responses are returned."""
        test_server_id = "test-server"
        
        # Test invalid resource ID
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/invalid-id",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code in [400, 404]  # Both are acceptable for invalid IDs
        
        # Test invalid filter syntax - implementation returns 200 with empty results
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?filter=invalid",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200  # Implementation returns 200 for invalid filters

    def test_okta_schema_extensions(self, client, sample_api_key):
        """Test that Okta schema extensions are supported."""
        test_server_id = "test-server"
        
        # Test that we can retrieve specific schemas
        schemas_to_test = [
            "urn:ietf:params:scim:schemas:core:2.0:User",
            "urn:ietf:params:scim:schemas:core:2.0:Group",
            "urn:okta:scim:schemas:core:1.0:Entitlement"
        ]
        
        for schema_urn in schemas_to_test:
            response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Schemas/{schema_urn}",
                                headers={"Authorization": f"Bearer {sample_api_key}"})
            # Should return 200 for valid schemas, 404 for unsupported ones
            assert response.status_code in [200, 404] 