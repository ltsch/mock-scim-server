import pytest
from fastapi.testclient import TestClient

def test_resource_types_no_auth(client):
    """Test ResourceTypes endpoint without authentication."""
    response = client.get("/v2/ResourceTypes")
    assert response.status_code == 401
    assert "Authorization header required" in response.json()["detail"]

def test_resource_types_with_auth(client, sample_api_key):
    """Test ResourceTypes endpoint with valid authentication."""
    response = client.get("/v2/ResourceTypes", headers={"Authorization": f"Bearer {sample_api_key}"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["schemas"] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert data["totalResults"] == 4
    assert data["startIndex"] == 1
    assert data["itemsPerPage"] == 4
    assert len(data["Resources"]) == 4
    
    # Check that all expected resource types are present
    resource_ids = [r["id"] for r in data["Resources"]]
    assert "User" in resource_ids
    assert "Group" in resource_ids
    assert "Entitlement" in resource_ids
    assert "Role" in resource_ids

def test_schemas_no_auth(client):
    """Test Schemas endpoint without authentication."""
    response = client.get("/v2/Schemas")
    assert response.status_code == 401
    assert "Authorization header required" in response.json()["detail"]

def test_schemas_with_auth(client, sample_api_key):
    """Test Schemas endpoint with valid authentication."""
    response = client.get("/v2/Schemas", headers={"Authorization": f"Bearer {sample_api_key}"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["schemas"] == ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    assert data["totalResults"] == 0
    assert data["startIndex"] == 1
    assert data["itemsPerPage"] == 0
    assert len(data["Resources"]) == 0 