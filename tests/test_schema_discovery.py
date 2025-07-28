"""
SCIM Schema Discovery Tests

Tests for SCIM schema discovery endpoints including:
- ResourceTypes endpoint
- Schemas endpoint  
- Schema validation
"""

import pytest
from fastapi.testclient import TestClient
from tests.test_utils import get_expected_resource_types, get_expected_schemas, get_config_settings

class TestSchemaDiscovery:
    """Tests for SCIM schema discovery functionality."""
    
    def test_resource_types_no_auth(self, client):
        """Test ResourceTypes endpoint without authentication."""
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]

    def test_resource_types_with_auth(self, client, sample_api_key):
        """Test ResourceTypes endpoint with valid authentication."""
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes", headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["schemas"] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        
        # Get expected resource types from the codebase
        expected_resource_types = get_expected_resource_types()
        expected_count = len(expected_resource_types)
        
        assert data["totalResults"] == expected_count
        assert data["startIndex"] == 1
        assert data["itemsPerPage"] == expected_count
        assert len(data["Resources"]) == expected_count
        
        # Check that all expected resource types are present
        resource_ids = [r["id"] for r in data["Resources"]]
        expected_ids = [r["id"] for r in expected_resource_types]
        
        for expected_id in expected_ids:
            assert expected_id in resource_ids, f"Expected resource type {expected_id} not found in response"
        
        # Verify each resource type has the expected structure
        for resource in data["Resources"]:
            assert "id" in resource
            assert "name" in resource
            assert "endpoint" in resource
            assert "schema" in resource
            assert "description" in resource

    def test_schemas_no_auth(self, client):
        """Test Schemas endpoint without authentication."""
        response = client.get("/scim-identifier/test-server/scim/v2/Schemas")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]

    def test_schemas_with_auth(self, client, sample_api_key):
        """Test Schemas endpoint with valid authentication."""
        response = client.get("/scim-identifier/test-server/scim/v2/Schemas", headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["schemas"] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
        
        # Get expected schemas from the codebase
        expected_schemas = get_expected_schemas()
        expected_count = len(expected_schemas)
        
        assert data["totalResults"] == expected_count
        assert data["startIndex"] == 1
        assert data["itemsPerPage"] == expected_count
        assert len(data["Resources"]) == expected_count
        
        # Verify each schema has the expected structure
        for schema in data["Resources"]:
            assert "schemas" in schema
            assert "id" in schema
            assert "name" in schema
            assert "description" in schema
            assert "attributes" in schema

    def test_schema_by_urn(self, client, sample_api_key):
        """Test getting a specific schema by URN."""
        # Test User schema
        response = client.get("/scim-identifier/test-server/scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User", 
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["schemas"] == ["urn:ietf:params:scim:schemas:core:2.0:User"]
        assert data["id"] == "urn:ietf:params:scim:schemas:core:2.0:User"
        assert data["name"] == "User"
        assert "attributes" in data

    def test_schema_by_urn_not_found(self, client, sample_api_key):
        """Test getting a non-existent schema by URN."""
        response = client.get("/scim-identifier/test-server/scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:NonExistent", 
                            headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 404

    def test_schema_discovery_compliance(self, client, sample_api_key):
        """Test that schema discovery follows SCIM 2.0 compliance."""
        config = get_config_settings()
        
        # Test ResourceTypes endpoint
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes", headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify SCIM 2.0 compliance
        assert "schemas" in data
        assert "totalResults" in data
        assert "startIndex" in data
        assert "itemsPerPage" in data
        assert "Resources" in data
        
        # Verify each resource type follows SCIM 2.0 format
        for resource in data["Resources"]:
            assert "id" in resource
            assert "name" in resource
            assert "endpoint" in resource
            assert "schema" in resource
            assert "description" in resource 