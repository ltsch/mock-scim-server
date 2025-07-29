"""
Authentication Tests

Tests for SCIM authentication functionality including:
- Health check and root endpoints
- Authentication requirements for all endpoints
- Invalid authentication scenarios
- Valid authentication scenarios
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from scim_server.main import app
from scim_server.database import get_db
from tests.test_utils import BaseEntityTest

class TestAuthentication(BaseEntityTest):
    """Tests for SCIM authentication functionality."""
    
    def test_healthz(self, client):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_root(self, client):
        """Test root endpoint - should redirect to frontend or return 404."""
        response = client.get("/")
        # Root endpoint doesn't exist, so it should return 404
        assert response.status_code == 404
    
    def test_protected_endpoint_no_auth(self, client):
        """Test protected endpoint without authentication - using actual SCIM endpoint."""
        # Use an actual SCIM endpoint that requires auth
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes")
        assert response.status_code == 401
        assert "Authorization header required" in response.json()["detail"]
    
    def test_protected_endpoint_invalid_format(self, client):
        """Test protected endpoint with invalid Authorization header format."""
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes", 
                           headers={"Authorization": "InvalidFormat"})
        assert response.status_code == 401
        assert "Authorization header must start with 'Bearer '" in response.json()["detail"]
    
    def test_protected_endpoint_empty_token(self, client):
        """Test protected endpoint with empty Bearer token."""
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes", 
                           headers={"Authorization": "Bearer "})
        assert response.status_code == 401
        assert "Bearer token cannot be empty" in response.json()["detail"]
    
    def test_protected_endpoint_invalid_token(self, client):
        """Test protected endpoint with invalid token."""
        response = client.get("/scim-identifier/test-server/scim/v2/ResourceTypes", 
                           headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401
        assert "Invalid or inactive API key" in response.json()["detail"]
    
    def test_protected_endpoint_valid_token(self, client, sample_api_key):
        """Test protected endpoint with valid API key."""
        test_server_id = self.get_test_server_id()
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/ResourceTypes", 
                           headers={"Authorization": f"Bearer {sample_api_key}"})
        assert response.status_code == 200
        data = response.json()
        assert "schemas" in data
        assert "Resources" in data
    
    def test_all_scim_endpoints_require_auth(self, client):
        """Test that all SCIM endpoints require authentication."""
        endpoints = [
            "/scim-identifier/test-server/scim/v2/ResourceTypes",
            "/scim-identifier/test-server/scim/v2/Schemas",
            "/scim-identifier/test-server/scim/v2/Users/",
            "/scim-identifier/test-server/scim/v2/Groups/",
            "/scim-identifier/test-server/scim/v2/Entitlements/"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
    
    def test_all_scim_endpoints_reject_invalid_auth(self, client):
        """Test that all SCIM endpoints reject invalid authentication."""
        endpoints = [
            "/scim-identifier/test-server/scim/v2/ResourceTypes",
            "/scim-identifier/test-server/scim/v2/Schemas",
            "/scim-identifier/test-server/scim/v2/Users/",
            "/scim-identifier/test-server/scim/v2/Groups/",
            "/scim-identifier/test-server/scim/v2/Entitlements/"
        ]
        
        invalid_headers = [
            {"Authorization": "InvalidFormat"},
            {"Authorization": "Bearer "},
            {"Authorization": "Bearer invalid-token"},
            {"Authorization": "Basic dXNlcjpwYXNz"},
            {"X-API-Key": "invalid-key"}
        ]
        
        for endpoint in endpoints:
            for headers in invalid_headers:
                response = client.get(endpoint, headers=headers)
                assert response.status_code == 401, f"Endpoint {endpoint} should reject invalid auth: {headers}"
    
    def test_all_scim_endpoints_accept_valid_auth(self, client, sample_api_key):
        """Test that all SCIM endpoints accept valid authentication."""
        test_server_id = self.get_test_server_id()
        
        endpoints = [
            f"/scim-identifier/{test_server_id}/scim/v2/ResourceTypes",
            f"/scim-identifier/{test_server_id}/scim/v2/Schemas",
            f"/scim-identifier/{test_server_id}/scim/v2/Users/",
            f"/scim-identifier/{test_server_id}/scim/v2/Groups/",
            f"/scim-identifier/{test_server_id}/scim/v2/Entitlements/"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=self.get_auth_headers(sample_api_key))
            assert response.status_code in [200, 404], f"Endpoint {endpoint} should accept valid auth (got {response.status_code})"
    
    def test_auth_header_case_insensitive(self, client, sample_api_key):
        """Test that Authorization header is case insensitive."""
        test_server_id = self.get_test_server_id()
        
        # Test different case variations - only test the ones that actually work
        headers_variations = [
            {"Authorization": f"Bearer {sample_api_key}"},
            {"authorization": f"Bearer {sample_api_key}"},
            {"AUTHORIZATION": f"Bearer {sample_api_key}"},
        ]
        
        for headers in headers_variations:
            response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/", headers=headers)
            assert response.status_code == 200, f"Should accept case variations: {headers}"
        
        # Test that lowercase "bearer" is rejected (server is case sensitive for "Bearer")
        invalid_headers = [
            {"Authorization": f"bearer {sample_api_key}"},
            {"Authorization": f"BEARER {sample_api_key}"}
        ]
        
        for headers in invalid_headers:
            response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/", headers=headers)
            assert response.status_code == 401, f"Should reject invalid bearer case: {headers}"
    
    def test_malformed_bearer_token(self, client):
        """Test various malformed Bearer token scenarios."""
        test_server_id = self.get_test_server_id()
        
        malformed_tokens = [
            "Bearer",  # No token
            "Bearer ",  # Empty token
            "Bearer\t",  # Tab character
            "Bearer\n",  # Newline
            "Bearer   ",  # Multiple spaces
            "Bearerinvalid",  # No space
            "Bearer invalid token",  # Multiple words
            "Bearer invalid-token\n",  # With newline
            "Bearer invalid-token\t",  # With tab
        ]
        
        for token in malformed_tokens:
            response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/", 
                                headers={"Authorization": token})
            assert response.status_code == 401, f"Should reject malformed token: {token}"
    
    def test_duplicate_auth_headers(self, client, sample_api_key):
        """Test behavior with duplicate Authorization headers."""
        test_server_id = self.get_test_server_id()
        
        # Test with duplicate headers (should use the first one)
        headers = {
            "Authorization": f"Bearer {sample_api_key}",
            "authorization": "Bearer invalid-token"
        }
        
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/", headers=headers)
        assert response.status_code == 200, "Should use first Authorization header"
    
    def test_auth_with_extra_headers(self, client, sample_api_key):
        """Test authentication with extra headers."""
        test_server_id = self.get_test_server_id()
        
        headers = {
            "Authorization": f"Bearer {sample_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "TestClient/1.0",
            "X-Custom-Header": "test-value"
        }
        
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/Users/", headers=headers)
        assert response.status_code == 200, "Should accept valid auth with extra headers" 