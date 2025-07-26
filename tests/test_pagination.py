import pytest
from fastapi.testclient import TestClient
from scim_server.config import settings
from tests.test_utils import find_test_server_with_minimum_users, get_config_settings

class TestPagination:
    """Comprehensive pagination tests that would catch the issues we found."""
    
    TEST_API_KEY = settings.test_api_key
    AUTH_HEADERS = {"Authorization": f"Bearer {TEST_API_KEY}"}
    
    def get_test_server_id(self):
        """Dynamically get a server ID with multiple users for testing."""
        return find_test_server_with_minimum_users(min_users=5)
    
    def get_config(self):
        """Get configuration settings for testing."""
        return get_config_settings()
    
    def test_pagination_start_index_mapping(self, client):
        """Test that startIndex query parameter is properly mapped to start_index."""
        # This test would have caught the missing alias="startIndex" issue
        
        # Use a server with multiple users
        test_server_id = self.get_test_server_id()
        
        # Test first page
        response = client.get(f"/scim/v2/Users/?startIndex=1&count=2&serverID={test_server_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 2
        assert len(data['Resources']) == 2
        
        # Test second page - this would have failed before the fix
        response = client.get(f"/scim/v2/Users/?startIndex=3&count=2&serverID={test_server_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data['startIndex'] == 3  # This was returning 1 before the fix
        assert data['itemsPerPage'] == 2
        assert len(data['Resources']) == 2
        
        # Verify we got different users on different pages
        first_page_users = set(user['userName'] for user in client.get(f"/scim/v2/Users/?startIndex=1&count=2&serverID={test_server_id}", headers=self.AUTH_HEADERS).json()['Resources'])
        second_page_users = set(user['userName'] for user in client.get(f"/scim/v2/Users/?startIndex=3&count=2&serverID={test_server_id}", headers=self.AUTH_HEADERS).json()['Resources'])
        assert first_page_users != second_page_users, "Different pages should return different users"
    
    def test_pagination_consistency(self, client):
        """Test that pagination returns consistent results in order."""
        # This test would have caught the missing ORDER BY issue
        
        # Use a server with multiple users
        test_server_id = self.get_test_server_id()
        
        # Get all users with pagination
        all_users = []
        page = 1
        while True:
            response = client.get(f"/scim/v2/Users/?startIndex={page}&count=2&serverID={test_server_id}", headers=self.AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()
            
            if not data['Resources']:
                break
                
            all_users.extend(data['Resources'])
            page += 2
            
            if len(data['Resources']) < 2:
                break
        
        # Verify we got all users
        assert len(all_users) > 0
        
        # Verify no duplicates (this would have failed without ORDER BY)
        usernames = [user['userName'] for user in all_users]
        assert len(usernames) == len(set(usernames)), "Pagination should not return duplicate users"
    
    def test_pagination_edge_cases(self, client):
        """Test pagination edge cases."""
        
        # Use a server with multiple users
        test_server_id = self.get_test_server_id()
        
        # Test single record per page
        response = client.get(f"/scim/v2/Users/?startIndex=1&count=1&serverID={test_server_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data['startIndex'] == 1
        assert data['itemsPerPage'] == 1
        assert len(data['Resources']) == 1
        
        # Test middle page
        response = client.get(f"/scim/v2/Users/?startIndex=5&count=1&serverID={test_server_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data['startIndex'] == 5
        assert data['itemsPerPage'] == 1
        assert len(data['Resources']) == 1
        
        # Test beyond available records
        response = client.get(f"/scim/v2/Users/?startIndex=999&count=1&serverID={test_server_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data['startIndex'] == 999
        assert data['itemsPerPage'] == 0
        assert len(data['Resources']) == 0
    
    def test_pagination_with_filtering(self, client):
        """Test pagination works correctly with filtering."""
        
        # Use a server with multiple users
        test_server_id = self.get_test_server_id()
        
        # Test pagination with filter - look for users with "John" in display name
        response = client.get(f"/scim/v2/Users/?startIndex=1&count=2&filter=displayName%20co%20%22John%22&serverID={test_server_id}", headers=self.AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data['startIndex'] == 1
        
        # If we find users with "John", verify the filter works
        if data['totalResults'] > 0:
            assert data['totalResults'] >= 1
            # Verify filtered results
            for user in data['Resources']:
                assert 'John' in user['displayName']
        else:
            # If no users with "John", test with a different filter that should work
            response = client.get(f"/scim/v2/Users/?startIndex=1&count=2&filter=displayName%20co%20%22User%22&serverID={test_server_id}", headers=self.AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert data['startIndex'] == 1
            assert data['totalResults'] >= 1
            # Verify filtered results
            for user in data['Resources']:
                assert 'User' in user['displayName']
    
    def test_all_resource_types_pagination(self, client):
        """Test pagination works for all resource types."""
        
        # Use a server with multiple users
        test_server_id = self.get_test_server_id()
        
        resource_types = ['Users', 'Groups', 'Entitlements']
        
        for resource_type in resource_types:
            # Test first page
            response = client.get(f"/scim/v2/{resource_type}/?startIndex=1&count=2&serverID={test_server_id}", headers=self.AUTH_HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert data['startIndex'] == 1
            assert data['itemsPerPage'] <= 2
            
            # Test second page if there are enough records
            if data['totalResults'] > 2:
                response = client.get(f"/scim/v2/{resource_type}/?startIndex=3&count=2&serverID={test_server_id}", headers=self.AUTH_HEADERS)
                assert response.status_code == 200
                data = response.json()
                assert data['startIndex'] == 3
                assert data['itemsPerPage'] <= 2 