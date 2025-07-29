"""
Comprehensive validation compliance tests.

Tests that all endpoints properly reject requests that don't contain:
1. Valid API key
2. Valid server ID (where applicable)

This ensures strict compliance and security.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from scim_server.config import settings

class TestValidationCompliance:
    """Test that all endpoints properly validate API keys and server IDs."""
    
    def test_scim_endpoints_require_api_key(self, client: TestClient):
        """Test that all SCIM endpoints require valid API key."""
        # Test without Authorization header
        response = client.get("/scim-identifier/test-server/scim/v2/Users")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        # Test with invalid Authorization format
        response = client.get("/scim-identifier/test-server/scim/v2/Users", 
                            headers={"Authorization": "InvalidFormat"})
        assert response.status_code == 401
        assert "Authorization header must start with 'Bearer '" in response.json()["detail"]
        
        # Test with empty Bearer token
        response = client.get("/scim-identifier/test-server/scim/v2/Users", 
                            headers={"Authorization": "Bearer "})
        assert response.status_code == 401
        assert "Bearer token cannot be empty" in response.json()["detail"]
        
        # Test with invalid API key
        response = client.get("/scim-identifier/test-server/scim/v2/Users", 
                            headers={"Authorization": "Bearer invalid-key"})
        assert response.status_code == 401
        assert "Invalid or inactive API key" in response.json()["detail"]
    
    def test_scim_endpoints_require_server_id(self, client: TestClient):
        """Test that all SCIM endpoints require valid server ID."""
        # Test with valid API key but invalid server ID format
        response = client.get("/scim-identifier/invalid@server/scim/v2/Users", 
                            headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 400
        assert "Server ID must contain only alphanumeric characters" in response.json()["detail"]
        
        # Test with valid API key but empty server ID (FastAPI returns 404 for empty path params)
        response = client.get("/scim-identifier//scim/v2/Users", 
                            headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 404  # FastAPI path validation catches this first
    
    def test_scim_discovery_endpoints_validation(self, client: TestClient):
        """Test that SCIM discovery endpoints require both API key and server ID."""
        # Test ResourceTypes endpoint
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes", 
                            headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 200
        
        # Test Schemas endpoint
        response = client.get("/scim-identifier/test-server/scim/v2/Schemas")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        response = client.get("/scim-identifier/test-server/scim/v2/Schemas", 
                            headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 200
        
        # Test specific schema endpoint
        response = client.get("/scim-identifier/test-server/scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        response = client.get("/scim-identifier/test-server/scim/v2/Schemas/urn:ietf:params:scim:schemas:core:2.0:User", 
                            headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 200
    
    def test_crud_endpoints_validation(self, client: TestClient):
        """Test that all CRUD endpoints require both API key and server ID."""
        # Test Users endpoint
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        response = client.post("/scim-identifier/test-server/scim/v2/Users", 
                             json={"userName": f"test_{unique_id}@example.com"})
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        response = client.post("/scim-identifier/test-server/scim/v2/Users", 
                             json={"userName": f"test_{unique_id}@example.com"},
                             headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 201
        
        # Test Groups endpoint
        response = client.post("/scim-identifier/test-server/scim/v2/Groups", 
                             json={"displayName": f"Test Group {unique_id}"})
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        response = client.post("/scim-identifier/test-server/scim/v2/Groups", 
                             json={"displayName": f"Test Group {unique_id}"},
                             headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 201
        
        # Test Entitlements endpoint
        response = client.post("/scim-identifier/test-server/scim/v2/Entitlements", 
                             json={"displayName": f"Test Entitlement {unique_id}", "type": "Administrator"})
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        response = client.post("/scim-identifier/test-server/scim/v2/Entitlements", 
                             json={"displayName": f"Test Entitlement {unique_id}", "type": "Administrator"},
                             headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 201
    
    def test_utility_endpoints_require_api_key(self, client: TestClient):
        """Test that utility endpoints require API key."""
        # Test /api/protected endpoint (which should require auth)
        response = client.get("/api/protected")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        response = client.get("/api/protected", headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 200
        
        # Test /api/routing endpoint (which should require auth)
        response = client.get("/api/routing")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
        
        response = client.get("/api/routing", headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 200
        
        # Test that non-existent endpoints return 404
        response = client.get("/api/servers")
        assert response.status_code == 404
    
    def test_health_endpoints_no_auth_required(self, client: TestClient):
        """Test that health endpoints don't require authentication."""
        # Test /healthz endpoint
        response = client.get("/healthz")
        assert response.status_code == 200
        
        # Test / endpoint (should return 404 since it doesn't exist)
        response = client.get("/")
        assert response.status_code == 404
    
    def test_valid_api_keys_accepted(self, client: TestClient):
        """Test that valid API keys are accepted."""
        # Test with actual SCIM endpoint
        test_server_id = "test-server-123"
        
        # Test default API key
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/ResourceTypes", 
                           headers={"Authorization": f"Bearer {settings.default_api_key}"})
        assert response.status_code == 200
        
        # Test test API key
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/ResourceTypes", 
                           headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 200
    
    def test_server_id_validation_edge_cases(self, client: TestClient):
        """Test server ID validation with various edge cases."""
        # Test with special characters
        response = client.get("/scim-identifier/test@server/scim/v2/Users", 
                            headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 400
        assert "Server ID must contain only alphanumeric characters" in response.json()["detail"]
        
        # Test with spaces (our validation catches this)
        response = client.get("/scim-identifier/test server/scim/v2/Users", 
                            headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 400  # Our validation catches spaces
        assert "Server ID must contain only alphanumeric characters" in response.json()["detail"]
        
        # Test with valid server ID
        response = client.get("/scim-identifier/test-server-123/scim/v2/Users", 
                            headers={"Authorization": f"Bearer {settings.test_api_key}"})
        assert response.status_code == 200
    
    def test_comprehensive_validation_coverage(self, client: TestClient):
        """Test that all HTTP methods require proper validation."""
        base_url = "/scim-identifier/test-server/scim/v2/Users"
        valid_headers = {"Authorization": f"Bearer {settings.test_api_key}"}
        
        # Test GET without auth
        response = client.get(base_url)
        assert response.status_code == 401
        
        # Test POST without auth
        response = client.post(base_url, json={"userName": "test@example.com"})
        assert response.status_code == 401
        
        # Test PUT without auth
        response = client.put(f"{base_url}/test-id", json={"userName": "test@example.com"})
        assert response.status_code == 401
        
        # Test PATCH without auth
        response = client.patch(f"{base_url}/test-id", json={"Operations": [{"op": "replace", "path": "userName", "value": "new@example.com"}]})
        assert response.status_code == 401
        
        # Test DELETE without auth
        response = client.delete(f"{base_url}/test-id")
        assert response.status_code == 401
        
        # Test with valid auth
        response = client.get(base_url, headers=valid_headers)
        assert response.status_code == 200 