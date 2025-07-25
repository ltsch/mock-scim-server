import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_create_user(client, sample_api_key):
    """Test creating a new user."""
    user_data = {
        "userName": "testuser@example.com",
        "displayName": "Test User",
        "name": {
            "givenName": "Test",
            "familyName": "User"
        },
        "emails": [
            {
                "value": "testuser@example.com",
                "primary": True
            }
        ],
        "active": True
    }
    
    response = client.post(
        "/v2/Users/",
        headers={"Authorization": "Bearer test-api-key"},
        json=user_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["userName"] == "testuser@example.com"
    assert data["displayName"] == "Test User"
    assert data["active"] == True
    assert "id" in data
    assert "schemas" in data
    assert "meta" in data

def test_create_user_duplicate_username(client, sample_api_key):
    """Test creating a user with duplicate username."""
    user_data = {
        "userName": "duplicate@example.com",
        "displayName": "Duplicate User"
    }
    
    # Create first user
    response1 = client.post(
        "/v2/Users/",
        headers={"Authorization": "Bearer test-api-key"},
        json=user_data
    )
    assert response1.status_code == 201
    
    # Try to create second user with same username
    response2 = client.post(
        "/v2/Users/",
        headers={"Authorization": "Bearer test-api-key"},
        json=user_data
    )
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"]

def test_get_users(client, sample_api_key):
    """Test getting users list."""
    response = client.get(
        "/v2/Users/",
        headers={"Authorization": "Bearer test-api-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "schemas" in data
    assert "totalResults" in data
    assert "startIndex" in data
    assert "itemsPerPage" in data
    assert "Resources" in data

def test_get_user_by_id(client, sample_api_key):
    """Test getting a specific user by ID."""
    # First create a user
    user_data = {
        "userName": "getuser@example.com",
        "displayName": "Get User"
    }
    
    create_response = client.post(
        "/v2/Users/",
        headers={"Authorization": "Bearer test-api-key"},
        json=user_data
    )
    assert create_response.status_code == 201
    
    user_id = create_response.json()["id"]
    
    # Get the user by ID
    response = client.get(
        f"/v2/Users/{user_id}",
        headers={"Authorization": "Bearer test-api-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["userName"] == "getuser@example.com"

def test_get_user_not_found(client, sample_api_key):
    """Test getting a user that doesn't exist."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = client.get(
        f"/v2/Users/{fake_id}",
        headers={"Authorization": "Bearer test-api-key"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_update_user(client, sample_api_key):
    """Test updating a user."""
    # First create a user
    user_data = {
        "userName": "updateuser@example.com",
        "displayName": "Update User"
    }
    
    create_response = client.post(
        "/v2/Users/",
        headers={"Authorization": "Bearer test-api-key"},
        json=user_data
    )
    assert create_response.status_code == 201
    
    user_id = create_response.json()["id"]
    
    # Update the user
    update_data = {
        "displayName": "Updated User",
        "active": False
    }
    
    response = client.put(
        f"/v2/Users/{user_id}",
        headers={"Authorization": "Bearer test-api-key"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["displayName"] == "Updated User"
    assert data["active"] == False

def test_patch_user(client, sample_api_key):
    """Test patching a user."""
    # First create a user
    user_data = {
        "userName": "patchuser@example.com",
        "displayName": "Patch User"
    }
    
    create_response = client.post(
        "/v2/Users/",
        headers={"Authorization": "Bearer test-api-key"},
        json=user_data
    )
    assert create_response.status_code == 201
    
    user_id = create_response.json()["id"]
    
    # Patch the user
    patch_data = {
        "displayName": "Patched User"
    }
    
    response = client.patch(
        f"/v2/Users/{user_id}",
        headers={"Authorization": "Bearer test-api-key"},
        json=patch_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["displayName"] == "Patched User"

def test_delete_user(client, sample_api_key):
    """Test deleting a user."""
    # First create a user
    user_data = {
        "userName": "deleteuser@example.com",
        "displayName": "Delete User"
    }
    
    create_response = client.post(
        "/v2/Users/",
        headers={"Authorization": "Bearer test-api-key"},
        json=user_data
    )
    assert create_response.status_code == 201
    
    user_id = create_response.json()["id"]
    
    # Delete the user
    response = client.delete(
        f"/v2/Users/{user_id}",
        headers={"Authorization": "Bearer test-api-key"}
    )
    
    assert response.status_code == 204
    
    # Verify user is deactivated (soft delete)
    get_response = client.get(
        f"/v2/Users/{user_id}",
        headers={"Authorization": "Bearer test-api-key"}
    )
    assert get_response.status_code == 200
    assert get_response.json()["active"] == False

def test_user_endpoints_require_auth(client):
    """Test that user endpoints require authentication."""
    endpoints = [
        ("POST", "/v2/Users/"),
        ("GET", "/v2/Users/"),
        ("GET", "/v2/Users/00000000-0000-0000-0000-000000000000"),
        ("PUT", "/v2/Users/00000000-0000-0000-0000-000000000000"),
        ("PATCH", "/v2/Users/00000000-0000-0000-0000-000000000000"),
        ("DELETE", "/v2/Users/00000000-0000-0000-0000-000000000000")
    ]
    
    for method, endpoint in endpoints:
        if method == "POST":
            response = client.post(endpoint, json={})
        elif method == "GET":
            response = client.get(endpoint)
        elif method == "PUT":
            response = client.put(endpoint, json={})
        elif method == "PATCH":
            response = client.patch(endpoint, json={})
        elif method == "DELETE":
            response = client.delete(endpoint)
        
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"] 