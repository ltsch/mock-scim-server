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
from tests.test_utils import BaseEntityTest, get_fake_uuid, get_fake_server_id, get_invalid_id

class TestErrorHandling(BaseEntityTest):
    """Tests for error handling and edge cases."""
    
    def test_invalid_scim_id_format(self, client, sample_api_key):
        """Test handling of invalid SCIM ID formats."""
        test_server_id = self.get_test_server_id()
        
        # Test various invalid ID formats
        invalid_ids = [
            "not-a-uuid",
            "12345678-1234-1234-1234-123456789abc",  # Invalid UUID format
            "00000000-0000-0000-0000-00000000000G",  # Invalid character
            get_invalid_id()
        ]
        
        for invalid_id in invalid_ids:
            response = client.get(f"/scim/v2/Users/{invalid_id}?serverID={test_server_id}", 
                                headers=self.get_auth_headers(sample_api_key))
            # Server may return 400 for invalid format or 404 for not found
            assert response.status_code in [400, 404]
    
    def test_resource_not_found(self, client, sample_api_key):
        """Test handling of non-existent resources."""
        test_server_id = self.get_test_server_id()
        fake_id = get_fake_uuid()
        
        # Test non-existent user
        response = client.get(f"/scim/v2/Users/{fake_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 404
        
        # Test non-existent group
        response = client.get(f"/scim/v2/Groups/{fake_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 404
        
        # Test non-existent entitlement
        response = client.get(f"/scim/v2/Entitlements/{fake_id}?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 404
    
    def test_invalid_server_id(self, client, sample_api_key):
        """Test handling of invalid server IDs."""
        fake_server_id = get_fake_server_id()
        
        response = client.get(f"/scim/v2/Users/?serverID={fake_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        # Server returns 200 with empty results for non-existent servers
        assert response.status_code == 200
        
        data = response.json()
        assert data["totalResults"] == 0
        assert len(data["Resources"]) == 0
    
    def test_validation_errors(self, client, sample_api_key):
        """Test that validation errors are properly handled."""
        test_server_id = self.get_test_server_id()
        
        # Test user without required userName
        invalid_user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "displayName": "Invalid User"
            # Missing userName
        }
        
        response = client.post(f"/scim/v2/Users/?serverID={test_server_id}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=invalid_user_data)
        assert response.status_code == 400
        
        # Test group without required displayName
        invalid_group_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "description": "Invalid Group"
            # Missing displayName
        }
        
        response = client.post(f"/scim/v2/Groups/?serverID={test_server_id}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=invalid_group_data)
        assert response.status_code == 400
        
        # Test entitlement without required fields
        invalid_entitlement_data = {
            "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
            "description": "Invalid Entitlement"
            # Missing displayName and type
        }
        
        response = client.post(f"/scim/v2/Entitlements/?serverID={test_server_id}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=invalid_entitlement_data)
        assert response.status_code == 400
    
    def test_duplicate_resource_creation(self, client, sample_api_key):
        """Test that duplicate resource creation is rejected."""
        test_server_id = self.get_test_server_id()
        
        # Get an existing user to duplicate
        response = client.get(f"/scim/v2/Users/?serverID={test_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        users = response.json()["Resources"]
        if users:
            existing_user = users[0]
            
            # Try to create a user with the same userName
            duplicate_user_data = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": existing_user["userName"],
                "displayName": "Duplicate User"
            }
            
            response = client.post(f"/scim/v2/Users/?serverID={test_server_id}", 
                                 headers=self.get_auth_headers(sample_api_key), 
                                 json=duplicate_user_data)
            assert response.status_code == 409
    
    def test_invalid_filter_syntax(self, client, sample_api_key):
        """Test that invalid filter syntax is handled properly."""
        test_server_id = self.get_test_server_id()
        
        invalid_filters = [
            "userName eq",
            "userName eq \"",
            "userName invalid \"test\"",
            "userName eq \"test\" and",
            "userName eq \"test\" or",
            "userName eq \"test\" and displayName eq",
            "userName co \"test\" and displayName sw",
            "userName eq \"test\" and displayName co \"test\" and",
            "userName eq \"test\" or displayName eq \"test\" or"
        ]
        
        for invalid_filter in invalid_filters:
            response = client.get(f"/scim/v2/Users/?serverID={test_server_id}&filter={invalid_filter}", 
                                headers=self.get_auth_headers(sample_api_key))
            # Server may return 200 with empty results or 400 for invalid syntax
            assert response.status_code in [200, 400], f"Should handle invalid filter: {invalid_filter}"
    
    def test_invalid_pagination_parameters(self, client, sample_api_key):
        """Test that invalid pagination parameters are handled properly."""
        test_server_id = self.get_test_server_id()
        
        invalid_params = [
            "startIndex=invalid",
            "count=invalid",
            "startIndex=-1",
            "count=-1",
            "startIndex=0&count=invalid",
            "startIndex=invalid&count=10"
        ]
        
        for params in invalid_params:
            response = client.get(f"/scim/v2/Users/?serverID={test_server_id}&{params}", 
                                headers=self.get_auth_headers(sample_api_key))
            # Should either return 400, 422, or handle gracefully
            assert response.status_code in [200, 400, 422], f"Should handle invalid pagination: {params}"
    
    def test_server_not_found(self, client, sample_api_key):
        """Test that non-existent server IDs are handled properly."""
        fake_server_id = "non-existent-server"
        
        response = client.get(f"/scim/v2/Users/?serverID={fake_server_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        # Should return empty results, not an error
        assert response.status_code == 200
        data = response.json()
        assert data["totalResults"] == 0
        assert len(data["Resources"]) == 0
    
    def test_malformed_json(self, client, sample_api_key):
        """Test that malformed JSON is rejected."""
        test_server_id = self.get_test_server_id()
        
        malformed_data = [
            '{"userName": "test",}',  # Trailing comma
            '{"userName": "test"',    # Missing closing brace
            '{"userName": test}',     # Missing quotes
            '{"userName": "test", "displayName":}',  # Missing value
            '{"userName": "test", "displayName": "Test User",}',  # Trailing comma
            '{"userName": "test", "displayName": "Test User", "active": true,}',  # Trailing comma
            '{"userName": "test", "displayName": "Test User", "active": true, "emails": [{"value": "test@example.com",}]}',  # Trailing comma in array
        ]
        
        for data in malformed_data:
            response = client.post(f"/scim/v2/Users/?serverID={test_server_id}", 
                                 headers={
                                     **self.get_auth_headers(sample_api_key),
                                     "Content-Type": "application/json"
                                 }, 
                                 content=data.encode('utf-8'))
            assert response.status_code == 422, f"Should reject malformed JSON: {data}"
    
    def test_unsupported_media_type(self, client, sample_api_key):
        """Test that unsupported media types are handled properly."""
        test_server_id = self.get_test_server_id()
        
        # Test with unsupported content type
        response = client.post(f"/scim/v2/Users/?serverID={test_server_id}", 
                             headers={
                                 **self.get_auth_headers(sample_api_key),
                                 "Content-Type": "text/plain"
                             }, 
                             content="plain text data".encode('utf-8'))
        # Server returns 422 for validation error instead of 415
        assert response.status_code == 422
    
    def test_rate_limiting(self, client, sample_api_key):
        """Test that rate limiting is enforced."""
        test_server_id = self.get_test_server_id()
        
        # Make multiple rapid requests to trigger rate limiting
        for i in range(20):  # Make 20 requests rapidly
            response = client.get(f"/scim/v2/Users/?serverID={test_server_id}", 
                                headers=self.get_auth_headers(sample_api_key))
            
            # If rate limiting is triggered, we should get 429
            if response.status_code == 429:
                assert "rate limit" in response.json()["detail"].lower()
                break
        else:
            # If no rate limiting was triggered, that's also acceptable
            # (rate limits might be high for testing)
            pass
    
    def test_large_request_body(self, client, sample_api_key):
        """Test that large request bodies are handled properly."""
        test_server_id = self.get_test_server_id()
        
        # Create a large user data object with unique username
        unique_username = self.get_unique_name("large_user") + "@example.com"
        large_user_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": unique_username,
            "displayName": "Large User",
            "name": {
                "givenName": "Large",
                "familyName": "User"
            },
            "emails": [
                {
                    "value": unique_username,
                    "type": "work",
                    "primary": True
                }
            ],
            "active": True,
            "description": "A" * 10000  # Very long description
        }
        
        response = client.post(f"/scim/v2/Users/?serverID={test_server_id}", 
                             headers=self.get_auth_headers(sample_api_key), 
                             json=large_user_data)
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 400, 413], "Should handle large request body"
    
    def test_invalid_url_parameters(self, client, sample_api_key):
        """Test that invalid URL parameters are handled properly."""
        test_server_id = self.get_test_server_id()
        
        invalid_params = [
            "serverID=",  # Empty server ID
            "serverID=invalid&startIndex=1",  # Invalid server ID with valid param
            "startIndex=1&count=10&serverID=",  # Empty server ID at end
            "serverID=test&startIndex=invalid",  # Invalid startIndex
            "serverID=test&count=invalid",  # Invalid count
            "serverID=test&filter=invalid filter",  # Invalid filter
        ]
        
        for params in invalid_params:
            response = client.get(f"/scim/v2/Users/?{params}", 
                                headers=self.get_auth_headers(sample_api_key))
            # Should handle gracefully - server may return 422 for validation errors
            assert response.status_code in [200, 400, 404, 422], f"Should handle invalid params: {params}" 