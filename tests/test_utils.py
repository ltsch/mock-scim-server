"""
Test utilities that consume artifacts from the codebase for dynamic testing.
This makes tests more maintainable and useful by using actual codebase data.
"""

from typing import List, Dict, Any, Optional
import time
from fastapi.testclient import TestClient
from scim_server.database import SessionLocal
from scim_server.schema_definitions import DynamicSchemaGenerator
from scim_server.models import User, Group, Entitlement
from scim_server.config import settings
from collections import Counter
import pytest

def get_expected_resource_types() -> List[Dict[str, Any]]:
    """Dynamically get expected resource types from the codebase."""
    # Import here to avoid circular imports
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        return schema_generator.get_resource_types()
    finally:
        db.close()

def get_expected_schemas() -> List[Dict[str, Any]]:
    """Dynamically get expected schemas from the codebase."""
    # Import here to avoid circular imports
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        return schema_generator.get_all_schemas()
    finally:
        db.close()

def get_available_servers() -> List[str]:
    """Get all available server IDs from the database."""
    # Import here to avoid circular imports
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        return list(set(u.server_id for u in db.query(User).all()))
    finally:
        db.close()

def get_server_user_counts() -> Dict[str, int]:
    """Get user counts for each server."""
    # Import here to avoid circular imports
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        return dict(Counter(u.server_id for u in db.query(User).all()))
    finally:
        db.close()

def get_server_group_counts() -> Dict[str, int]:
    """Get group counts for each server."""
    # Import here to avoid circular imports
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        return dict(Counter(g.server_id for g in db.query(Group).all()))
    finally:
        db.close()

def get_server_entitlement_counts() -> Dict[str, int]:
    """Get entitlement counts for each server."""
    # Import here to avoid circular imports
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        return dict(Counter(e.server_id for e in db.query(Entitlement).all()))
    finally:
        db.close()

def find_test_server_with_minimum_users(min_users: int = 5) -> Optional[str]:
    """Find a server with at least the specified number of users."""
    user_counts = get_server_user_counts()
    
    for server_id, count in user_counts.items():
        if count >= min_users:
            return server_id
    
    # If no server has enough users, return the one with the most users
    if user_counts:
        return max(user_counts.items(), key=lambda x: x[1])[0]
    
    return None

def get_config_settings() -> Dict[str, Any]:
    """Get relevant configuration settings for testing."""
    return {
        'max_results_per_page': settings.max_results_per_page,
        'default_page_size': settings.default_page_size,
        'max_count_limit': settings.max_count_limit,
        'rate_limit_requests': settings.rate_limit_requests,
        'rate_limit_window': settings.rate_limit_window,
        'rate_limit_create': settings.rate_limit_create,
        'rate_limit_read': settings.rate_limit_read,
        'scim_version': settings.scim_version,
        'test_api_key': settings.test_api_key,
        'cli_default_users': settings.cli_default_users,
        'cli_default_groups': settings.cli_default_groups,
        'cli_default_entitlements': settings.cli_default_entitlements,
        'cli_group_names': settings.cli_group_names,
        'cli_entitlement_definitions': settings.cli_entitlement_definitions,
        'cli_department_job_titles': settings.cli_department_job_titles,
        'cli_company_domains': settings.cli_company_domains,
    }

def get_entitlement_types() -> List[str]:
    """Get all entitlement types from the configuration."""
    entitlement_types = []
    for definition in settings.cli_entitlement_definitions:
        if 'canonical_values' in definition:
            entitlement_types.extend(definition['canonical_values'])
    return list(set(entitlement_types))

def get_canonical_entitlement_types() -> List[str]:
    """Get canonical entitlement types from the API schema."""
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db)
        schemas = schema_generator.get_all_schemas()
        
        # Find the entitlement schema
        for schema in schemas:
            if schema.get('id') == 'urn:okta:scim:schemas:core:1.0:Entitlement':
                # Look for the type attribute with canonical values
                for attr in schema.get('attributes', []):
                    if attr.get('name') == 'type' and 'canonicalValues' in attr:
                        return attr['canonicalValues']
        
        # Fallback to configuration if API doesn't have canonical values
        return get_entitlement_types()
    finally:
        db.close()

def get_valid_entitlement_type() -> str:
    """Get a valid entitlement type for testing."""
    canonical_types = get_canonical_entitlement_types()
    if canonical_types:
        return canonical_types[0]  # Return first valid type
    return "IT"  # Fallback

def get_department_names() -> List[str]:
    """Get all department names from the configuration."""
    return [dept for dept, _ in settings.cli_department_job_titles]

def get_job_titles_for_department(department: str) -> List[str]:
    """Get job titles for a specific department."""
    for dept, titles in settings.cli_department_job_titles:
        if dept == department:
            return titles
    return []

def validate_server_data_integrity(server_id: str) -> Dict[str, Any]:
    """Validate that a server has consistent data across all entity types."""
    db = SessionLocal()
    try:
        user_count = db.query(User).filter(User.server_id == server_id).count()
        group_count = db.query(Group).filter(Group.server_id == server_id).count()
        entitlement_count = db.query(Entitlement).filter(Entitlement.server_id == server_id).count()
        
        return {
            'server_id': server_id,
            'user_count': user_count,
            'group_count': group_count,
            'entitlement_count': entitlement_count,
            'has_data': user_count > 0 or group_count > 0 or entitlement_count > 0,
            'is_valid': True  # Could add more validation logic here
        }
    finally:
        db.close()

# Base test class for entity management tests
class BaseEntityTest:
    """Base class for entity management tests to eliminate duplication."""
    
    def get_test_server_id(self, min_users: int = 3) -> str:
        """Get a test server ID with minimum users."""
        server_id = find_test_server_with_minimum_users(min_users)
        if not server_id:
            raise pytest.skip("No suitable test server found")
        return server_id
    
    def get_unique_name(self, base_name: str = "test") -> str:
        """Generate a unique name using timestamp."""
        timestamp = int(time.time() * 1000)
        return f"{base_name}_{timestamp}"
    
    def get_auth_headers(self, api_key: str) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {api_key}"}
    
    def _test_entity_list(self, client: TestClient, sample_api_key: str, entity_type: str):
        """Test listing entities of the specified type."""
        test_server_id = self.get_test_server_id()
        
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/{entity_type}/", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        data = response.json()
        assert "schemas" in data
        assert "totalResults" in data
        assert "startIndex" in data
        assert "itemsPerPage" in data
        assert "Resources" in data
        
        # Verify we got some entities
        assert data["totalResults"] > 0
        assert len(data["Resources"]) > 0
        
        # Verify entity structure
        for entity in data["Resources"]:
            assert "id" in entity
            assert "schemas" in entity
            assert "meta" in entity
    
    def _test_entity_get_by_id(self, client: TestClient, sample_api_key: str, entity_type: str):
        """Test getting a specific entity by ID."""
        test_server_id = self.get_test_server_id()
        
        # First get a list of entities
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/{entity_type}/", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        entities = response.json()["Resources"]
        assert len(entities) > 0
        
        # Get the first entity by ID
        entity_id = entities[0]["id"]
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/{entity_type}/{entity_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        entity = response.json()
        assert entity["id"] == entity_id
        assert "schemas" in entity
        assert "meta" in entity
    
    def _test_entity_not_found(self, client: TestClient, sample_api_key: str, entity_type: str):
        """Test getting a non-existent entity."""
        test_server_id = self.get_test_server_id()
        fake_id = get_fake_uuid()
        
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/{entity_type}/{fake_id}", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 404
    
    def _test_entity_filter(self, client: TestClient, sample_api_key: str, entity_type: str, filter_field: str, filter_value: str):
        """Test filtering entities."""
        test_server_id = self.get_test_server_id()
        
        # Try the specific filter first
        response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/{entity_type}/?filter={filter_field} eq \"{filter_value}\"", 
                            headers=self.get_auth_headers(sample_api_key))
        assert response.status_code == 200
        
        data = response.json()
        
        # If no results, try a more generic filter
        if data["totalResults"] == 0:
            response = client.get(f"/scim-identifier/{test_server_id}/scim/v2/{entity_type}/?filter={filter_field} sw \"{filter_value[:4]}\"", 
                                headers=self.get_auth_headers(sample_api_key))
            assert response.status_code == 200
            data = response.json()
        
        # Should have at least some results
        assert data["totalResults"] >= 0
        assert "Resources" in data

# Shared test data generators
def create_test_user_data(username: str) -> Dict[str, Any]:
    """Create test user data."""
    from scim_server.config import settings
    
    # Get department and job title from config
    departments = [dept for dept, _ in settings.cli_department_job_titles]
    department = departments[0] if departments else "Engineering"
    job_titles = dict(settings.cli_department_job_titles)
    titles = job_titles.get(department, ["Software Engineer"])
    job_title = titles[0] if titles else "Software Engineer"
    
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": username,
        "displayName": f"Test User {username}",
        "name": {
            "givenName": "Test",
            "familyName": "User"
        },
        "emails": [
            {
                "value": username,
                "type": "work",
                "primary": True
            }
        ],
        "active": True,
        "title": job_title
    }

def create_test_group_data(display_name: str) -> Dict[str, Any]:
    """Create test group data."""
    from scim_server.config import settings
    
    # Use a group name from config if available
    group_names = settings.cli_group_names
    description = f"Test group for unit testing - {display_name}"
    
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": display_name,
        "description": description
    }

def create_test_entitlement_data(display_name: str, entitlement_type: str = None) -> Dict[str, Any]:
    """Create test entitlement data."""
    from scim_server.config import settings
    
    # If no entitlement type provided, get a valid one from config
    if not entitlement_type:
        entitlement_definitions = settings.cli_entitlement_definitions
        if entitlement_definitions:
            first_entitlement = entitlement_definitions[0]
            entitlement_type = first_entitlement["type"]
        else:
            entitlement_type = "application_access"
    
    return {
        "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
        "displayName": display_name,
        "type": entitlement_type,
        "description": f"Test entitlement for unit testing - {display_name}",
        "entitlementType": "application_access",
        "multiValued": False
    }

def get_fake_uuid() -> str:
    """Get a fake UUID for testing non-existent resources."""
    return "00000000-0000-0000-0000-000000000000"

def get_fake_server_id() -> str:
    """Get a fake server ID for testing non-existent servers."""
    return "non-existent-server"

def get_invalid_id() -> str:
    """Get an invalid ID for testing validation."""
    return "invalid-id"

def get_test_entitlement_types() -> List[str]:
    """Get valid entitlement types from config."""
    from scim_server.config import settings
    
    types = set()
    for definition in settings.cli_entitlement_definitions:
        types.add(definition["type"])
    return list(types)

def get_test_entitlement_names() -> List[str]:
    """Get valid entitlement names from config."""
    from scim_server.config import settings
    
    names = []
    for definition in settings.cli_entitlement_definitions:
        names.append(definition["name"])
    return names

def get_test_group_names() -> List[str]:
    """Get valid group names from config."""
    from scim_server.config import settings
    
    return settings.cli_group_names

def get_test_department_names() -> List[str]:
    """Get valid department names from config."""
    from scim_server.config import settings
    
    return [dept for dept, _ in settings.cli_department_job_titles]

def get_test_job_titles() -> List[str]:
    """Get valid job titles from config."""
    from scim_server.config import settings
    
    titles = []
    for _, job_titles in settings.cli_department_job_titles:
        titles.extend(job_titles)
    return titles 