"""
Okta SCIM Compliance Tests

Tests to ensure compliance with Okta's specific SCIM 2.0 design requirements.
Based on: https://developer.okta.com/docs/guides/scim-with-entitlements/main/

Tests the specific endpoint sequence, schema formats, and data structures that Okta expects.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scim_server.database import get_db
from scim_server.main import app


class TestOktaCompliance:
    """Test Okta-specific SCIM compliance and extensions."""

    def test_okta_schema_discovery(self, client, sample_api_key):
        """Test that Okta can discover SCIM schemas."""
        test_server_id = "test-server"
        # Test ResourceTypes endpoint
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/ResourceTypes",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data
        
        # Verify expected resource types are present
        resource_types = [rt["name"] for rt in data["Resources"]]
        assert "User" in resource_types
        assert "Group" in resource_types
        assert "Entitlement" in resource_types

        # Test Schemas endpoint
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Schemas",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data
        
        # Verify expected schemas are present
        schemas = [s["name"] for s in data["Resources"]]
        assert "User" in schemas
        assert "Group" in schemas
        assert "Entitlement" in schemas

    def test_okta_entitlement_support(self, client, sample_api_key):
        """Test that Okta entitlements are properly supported."""
        test_server_id = "test-server"
        # Test entitlements endpoint
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        assert "Resources" in data
        assert "totalResults" in data

    def test_okta_user_attributes(self, client, sample_api_key):
        """Test that Okta-specific user attributes are supported."""
        test_server_id = "test-server"
        # Create a user with Okta-specific attributes
        user_data = {
            "userName": "okta_test_user",
            "name": {
                "givenName": "Okta",
                "familyName": "Test",
                "formatted": "Okta Test"
            },
            "emails": [
                {
                    "value": "okta.test@example.com",
                    "primary": True,
                    "type": "work"
                }
            ],
            "phoneNumbers": [
                {
                    "value": "+1-555-123-4567",
                    "type": "work"
                }
            ],
            "addresses": [
                {
                    "type": "work",
                    "formatted": "123 Main St, City, State 12345",
                    "streetAddress": "123 Main St",
                    "locality": "City",
                    "region": "State",
                    "postalCode": "12345",
                    "country": "US"
                }
            ],
            "active": True,
            "title": "Software Engineer",
            "department": "Engineering",
            "organization": "Test Company"
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                             json=user_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify Okta-specific attributes are preserved
        assert data["userName"] == "okta_test_user"
        assert data["name"]["givenName"] == "Okta"
        assert data["name"]["familyName"] == "Test"
        assert data["name"]["formatted"] == "Okta Test"
        assert data["emails"][0]["value"] == "okta.test@example.com"
        assert data["emails"][0]["primary"] is True
        assert data["emails"][0]["type"] == "work"
        assert data["phoneNumbers"][0]["value"] == "+1-555-123-4567"
        assert data["phoneNumbers"][0]["type"] == "work"
        assert data["addresses"][0]["type"] == "work"
        assert data["title"] == "Software Engineer"
        assert data["department"] == "Engineering"
        assert data["organization"] == "Test Company"

    def test_okta_group_attributes(self, client, sample_api_key):
        """Test that Okta-specific group attributes are supported."""
        test_server_id = "test-server"
        # Create a group with Okta-specific attributes
        group_data = {
            "displayName": "Okta Test Group",
            "description": "A test group for Okta compliance",
            "members": []
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
                             json=group_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify Okta-specific attributes are preserved
        assert data["displayName"] == "Okta Test Group"
        assert data["description"] == "A test group for Okta compliance"
        assert data["members"] == []

    def test_okta_entitlement_attributes(self, client, sample_api_key):
        """Test that Okta-specific entitlement attributes are supported."""
        test_server_id = "test-server"
        # Create an entitlement with Okta-specific attributes
        entitlement_data = {
            "displayName": "Okta Test Entitlement",
            "description": "A test entitlement for Okta compliance",
            "entitlementType": "application",
            "active": True
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/",
                             json=entitlement_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 201
        data = response.json()
        
        # Verify Okta-specific attributes are preserved
        assert data["displayName"] == "Okta Test Entitlement"
        assert data["description"] == "A test entitlement for Okta compliance"
        assert data["entitlementType"] == "application"
        assert data["active"] is True

    def test_okta_filtering_support(self, client, sample_api_key):
        """Test that Okta filtering syntax is supported."""
        test_server_id = "test-server"
        # Create test users
        for i in range(3):
            user_data = {
                "userName": f"okta_filter_user_{i}",
                "name": {
                    "givenName": f"Filter{i}",
                    "familyName": "User"
                },
                "emails": [
                    {
                        "value": f"filter{i}@example.com",
                        "primary": True
                    }
                ],
                "active": True
            }
            
            client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                       json=user_data,
                       headers={"Authorization": f"Bearer {sample_api_key}"})

        # Test various Okta filter patterns
        # Simple equality filter
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?filter=userName eq \"okta_filter_user_0\"",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["Resources"]) == 1
        assert data["Resources"][0]["userName"] == "okta_filter_user_0"

        # Contains filter
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?filter=userName co \"okta_filter_user\"",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["Resources"]) >= 3

        # Complex filter with AND
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?filter=userName co \"okta_filter_user\" and active eq true",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["Resources"]) >= 3

    def test_okta_pagination_support(self, client, sample_api_key):
        """Test that Okta pagination parameters are supported."""
        test_server_id = "test-server"
        # Create test users for pagination
        for i in range(5):
            user_data = {
                "userName": f"okta_pag_user_{i}",
                "name": {
                    "givenName": f"Pag{i}",
                    "familyName": "User"
                },
                "emails": [
                    {
                        "value": f"pag{i}@example.com",
                        "primary": True
                    }
                ],
                "active": True
            }
            
            client.post(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                       json=user_data,
                       headers={"Authorization": f"Bearer {sample_api_key}"})

        # Test pagination with startIndex and count
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/?startIndex=1&count=5",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert "startIndex" in data
        assert "itemsPerPage" in data
        assert "totalResults" in data
        assert "Resources" in data

    def test_okta_error_handling(self, client, sample_api_key):
        """Test that Okta-compatible error responses are returned."""
        test_server_id = "test-server"
        fake_id = "99999999-9999-9999-9999-999999999999"
        
        # Test 404 for non-existent resource
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/{fake_id}",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404
        
        # Test 400 for invalid request
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/invalid-id",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 400

        # Test 401 for invalid authentication
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/",
                            headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401

    def test_okta_bulk_operations(self, client, sample_api_key):
        """Test that Okta bulk operations are supported."""
        test_server_id = "test-server"
        # Test bulk user creation
        bulk_data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:BulkRequest"],
            "Operations": [
                {
                    "method": "POST",
                    "path": "/Users",
                    "bulkId": "bulk_user_1",
                    "data": {
                        "userName": "bulk_user_1",
                        "name": {
                            "givenName": "Bulk",
                            "familyName": "User1"
                        },
                        "emails": [
                            {
                                "value": "bulk1@example.com",
                                "primary": True
                            }
                        ],
                        "active": True
                    }
                },
                {
                    "method": "POST",
                    "path": "/Users",
                    "bulkId": "bulk_user_2",
                    "data": {
                        "userName": "bulk_user_2",
                        "name": {
                            "givenName": "Bulk",
                            "familyName": "User2"
                        },
                        "emails": [
                            {
                                "value": "bulk2@example.com",
                                "primary": True
                            }
                        ],
                        "active": True
                    }
                }
            ]
        }

        response = client.post(f"/scim-identifier/{test_server_id}/scim/v2/Bulk",
                             json=bulk_data,
                             headers={"Authorization": f"Bearer {sample_api_key}"})

        assert response.status_code == 200
        data = response.json()
        assert "schemas" in data
        assert "Operations" in data
        assert len(data["Operations"]) == 2

        # Verify both users were created
        for operation in data["Operations"]:
            assert operation["status"]["code"] == "201"
            assert "location" in operation["status"]

    def test_okta_schema_extensions(self, client, sample_api_key):
        """Test that Okta schema extensions are supported."""
        test_server_id = "test-server"
        # Test that the server supports custom schema extensions
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Schemas",
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        schemas = data["Resources"]
        
        # Verify that schemas include proper extensions
        for schema in schemas:
            assert "id" in schema
            assert "name" in schema
            assert "attributes" in schema 