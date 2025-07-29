import pytest
from fastapi.testclient import TestClient
from scim_server.main import app, is_internal_network

class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_healthz_no_auth(self, client):
        """Test healthz endpoint without authentication."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_healthz_with_auth(self, client):
        """Test healthz endpoint with authentication (should still work)."""
        response = client.get("/healthz", headers={"Authorization": "Bearer api-key-12345"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_detailed_health_from_localhost(self, client):
        """Test detailed health endpoint from localhost (should work)."""
        # TestClient uses localhost by default, so this should work
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "version" in data
        assert "database" in data
        assert "endpoints" in data
    
    def test_detailed_health_with_auth_from_localhost(self, client):
        """Test detailed health endpoint with authentication from localhost (should work)."""
        response = client.get("/health", headers={"Authorization": "Bearer api-key-12345"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "version" in data
        assert "database" in data
        assert "endpoints" in data
    
    def test_health_endpoints_not_protected_by_auth(self, client):
        """Test that health endpoints are not protected by authentication."""
        # Test with various invalid auth headers
        invalid_headers = [
            {"Authorization": "InvalidFormat"},
            {"Authorization": "Bearer "},
            {"Authorization": "Bearer invalid-token"},
            {"X-API-Key": "invalid-key"},
            {"Authorization": "Basic dXNlcjpwYXNz"}
        ]
        
        for headers in invalid_headers:
            # healthz should work from anywhere
            response = client.get("/healthz", headers=headers)
            assert response.status_code == 200, f"healthz failed with headers: {headers}"
            
            # health should work from localhost (test client) regardless of auth
            response = client.get("/health", headers=headers)
            assert response.status_code == 200, f"health failed with headers: {headers}"
    
    def test_health_endpoints_response_format(self, client):
        """Test that health endpoints return the expected response format."""
        # Test healthz format
        response = client.get("/healthz")
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "ok"
        assert "timestamp" in data
        
        # Test health format
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "version" in data
        assert "database" in data
        assert "endpoints" in data
        assert isinstance(data["endpoints"], dict)
        assert "healthz" in data["endpoints"]
        assert "health" in data["endpoints"]
        assert "frontend" in data["endpoints"]
    
    def test_healthz_accessible_from_anywhere(self, client):
        """Test that healthz endpoint is accessible from any network."""
        # This test verifies that healthz remains publicly accessible
        # (In a real scenario, we'd test with different IPs, but TestClient uses localhost)
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

class TestIPRestriction:
    """Tests for IP address restriction functionality."""
    
    def test_internal_network_detection(self):
        """Test that internal network detection works correctly."""
        # Test localhost addresses
        assert is_internal_network("127.0.0.1") == True
        assert is_internal_network("::1") == True
        
        # Test private networks (RFC 1918)
        assert is_internal_network("10.0.0.1") == True
        assert is_internal_network("172.16.0.1") == True
        assert is_internal_network("192.168.1.1") == True
        
        # Test Docker networks
        assert is_internal_network("172.17.0.1") == True  # Docker default bridge
        assert is_internal_network("192.168.0.1") == True  # Docker bridge networks
        
        # Test link-local addresses
        assert is_internal_network("169.254.0.1") == True
        assert is_internal_network("fe80::1") == True
        
        # Test external addresses (should be denied)
        assert is_internal_network("8.8.8.8") == False  # Google DNS
        assert is_internal_network("1.1.1.1") == False  # Cloudflare DNS
        assert is_internal_network("142.250.190.78") == False  # Google.com
        assert is_internal_network("151.101.1.69") == False  # Reddit.com
        
        # Test invalid IP addresses
        assert is_internal_network("invalid-ip") == False
        assert is_internal_network("") == False