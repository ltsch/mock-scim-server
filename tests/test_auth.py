import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import hashlib

from scim_server.main import app
from scim_server.database import get_db
from scim_server.models import ApiKey

def test_healthz(client):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SCIM.Cloud Development Server"
    assert data["version"] == "1.0.0"

def test_protected_endpoint_no_auth(client):
    """Test protected endpoint without authentication."""
    response = client.get("/protected")
    assert response.status_code == 401
    assert "Authorization header required" in response.json()["detail"]

def test_protected_endpoint_invalid_format(client):
    """Test protected endpoint with invalid Authorization header format."""
    response = client.get("/protected", headers={"Authorization": "InvalidFormat"})
    assert response.status_code == 401
    assert "Authorization header must start with 'Bearer '" in response.json()["detail"]

def test_protected_endpoint_empty_token(client):
    """Test protected endpoint with empty Bearer token."""
    response = client.get("/protected", headers={"Authorization": "Bearer "})
    assert response.status_code == 401
    assert "Bearer token cannot be empty" in response.json()["detail"]

def test_protected_endpoint_invalid_token(client):
    """Test protected endpoint with invalid token."""
    response = client.get("/protected", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert "Invalid or inactive API key" in response.json()["detail"]

def test_protected_endpoint_valid_token(client, sample_api_key):
    """Test protected endpoint with valid API key."""
    response = client.get("/protected", headers={"Authorization": f"Bearer {sample_api_key}"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Authentication successful"
    assert data["api_key_name"] == "test-key" 