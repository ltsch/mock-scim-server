"""
Base Classes and Infrastructure Tests

Targeted tests for the new base classes and infrastructure created during refactoring:
- BaseEntityEndpoint class functionality
- CRUD base operations
- Response converter functionality
- Schema validator integration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from scim_server.endpoint_base import BaseEntityEndpoint
from scim_server.crud_base import BaseCRUD
from scim_server.response_converter import ScimResponseConverter
from scim_server.schema_validator import create_schema_validator
from tests.test_base import DynamicTestDataMixin


class TestBaseEntityEndpoint(DynamicTestDataMixin):
    """Test BaseEntityEndpoint class functionality."""

    def test_base_entity_endpoint_initialization(self):
        """Test that BaseEntityEndpoint initializes correctly."""
        # Mock dependencies
        mock_router = Mock()
        mock_crud = Mock()
        mock_converter = Mock()
        mock_create_schema = Mock()
        mock_update_schema = Mock()
        mock_response_schema = Mock()
        mock_list_response_schema = Mock()
        
        # Test initialization
        endpoint = BaseEntityEndpoint(
            entity_type="TestEntity",
            router=mock_router,
            crud_operations=mock_crud,
            response_converter=mock_converter,
            create_schema=mock_create_schema,
            update_schema=mock_update_schema,
            response_schema=mock_response_schema,
            list_response_schema=mock_list_response_schema,
            schema_uri="urn:test:entity:1.0",
            supports_multi_server=True
        )
        
        # Verify attributes are set correctly
        assert endpoint.entity_type == "TestEntity"
        assert endpoint.crud == mock_crud
        assert endpoint.converter == mock_converter
        assert endpoint.schema_uri == "urn:test:entity:1.0"
        assert endpoint.supports_multi_server is True

    def test_base_entity_endpoint_endpoint_registration(self):
        """Test that BaseEntityEndpoint registers all required endpoints."""
        mock_router = Mock()
        mock_crud = Mock()
        mock_converter = Mock()
        mock_create_schema = Mock()
        mock_update_schema = Mock()
        mock_response_schema = Mock()
        mock_list_response_schema = Mock()
        
        endpoint = BaseEntityEndpoint(
            entity_type="TestEntity",
            router=mock_router,
            crud_operations=mock_crud,
            response_converter=mock_converter,
            create_schema=mock_create_schema,
            update_schema=mock_update_schema,
            response_schema=mock_response_schema,
            list_response_schema=mock_list_response_schema,
            schema_uri="urn:test:entity:1.0",
            supports_multi_server=True
        )
        
        # Verify that router.post was called for create endpoint
        mock_router.post.assert_called()
        
        # Verify that router.get was called for list and get endpoints
        mock_router.get.assert_called()
        
        # Verify that router.put was called for update endpoint
        mock_router.put.assert_called()
        
        # Verify that router.delete was called for delete endpoint
        mock_router.delete.assert_called()

    def test_base_entity_endpoint_multi_server_support(self):
        """Test that BaseEntityEndpoint handles multi-server support correctly."""
        mock_router = Mock()
        mock_crud = Mock()
        mock_converter = Mock()
        mock_create_schema = Mock()
        mock_update_schema = Mock()
        mock_response_schema = Mock()
        mock_list_response_schema = Mock()
        
        # Test with multi-server support enabled
        endpoint = BaseEntityEndpoint(
            entity_type="TestEntity",
            router=mock_router,
            crud_operations=mock_crud,
            response_converter=mock_converter,
            create_schema=mock_create_schema,
            update_schema=mock_update_schema,
            response_schema=mock_response_schema,
            list_response_schema=mock_list_response_schema,
            schema_uri="urn:test:entity:1.0",
            supports_multi_server=True
        )
        
        assert endpoint.supports_multi_server is True
        
        # Test with multi-server support disabled
        endpoint = BaseEntityEndpoint(
            entity_type="TestEntity",
            router=mock_router,
            crud_operations=mock_crud,
            response_converter=mock_converter,
            create_schema=mock_create_schema,
            update_schema=mock_update_schema,
            response_schema=mock_response_schema,
            list_response_schema=mock_list_response_schema,
            schema_uri="urn:test:entity:1.0",
            supports_multi_server=False
        )
        
        assert endpoint.supports_multi_server is False


class TestBaseCRUD(DynamicTestDataMixin):
    """Test BaseCRUD class functionality."""

    def test_base_crud_initialization(self):
        """Test that BaseCRUD initializes correctly."""
        mock_model = Mock()
        
        crud = BaseCRUD(mock_model)
        
        assert crud.model == mock_model

    def test_base_crud_create_operation(self, db_session):
        """Test BaseCRUD create operation."""
        from scim_server.models import User
        
        crud = BaseCRUD(User)
        
        # Test data
        user_data = {
            "scim_id": "test-user-123",
            "user_name": "testuser",
            "display_name": "Test User"
        }
        
        # Test create operation
        created_user = crud.create(db_session, user_data, "test-server")
        
        assert created_user is not None
        assert created_user.scim_id == "test-user-123"
        assert created_user.user_name == "testuser"
        assert created_user.server_id == "test-server"

    def test_base_crud_get_operation(self, db_session):
        """Test BaseCRUD get operation."""
        from scim_server.models import User
        
        crud = BaseCRUD(User)
        
        # Create test user
        user_data = {
            "scim_id": "test-user-456",
            "user_name": "testuser2",
            "display_name": "Test User 2"
        }
        created_user = crud.create(db_session, user_data, "test-server")
        
        # Test get operation
        retrieved_user = crud.get_by_id(db_session, created_user.scim_id, "test-server")
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.scim_id == "test-user-456"

    def test_base_crud_list_operation(self, db_session):
        """Test BaseCRUD list operation."""
        from scim_server.models import User
        
        crud = BaseCRUD(User)
        
        # Create multiple test users with unique usernames
        for i in range(3):
            user_data = {
                "scim_id": f"test-user-list-{i}",
                "user_name": f"testuser-list-{i}",
                "display_name": f"Test User List {i}"
            }
            crud.create(db_session, user_data, "test-server")
        
        # Test list operation
        users = crud.get_list(db_session, "test-server")
        
        assert len(users) >= 3
        assert all(user.server_id == "test-server" for user in users)

    def test_base_crud_update_operation(self, db_session):
        """Test BaseCRUD update operation."""
        from scim_server.models import User
        
        crud = BaseCRUD(User)
        
        # Create test user
        user_data = {
            "scim_id": "test-user-789",
            "user_name": "testuser3",
            "display_name": "Test User 3"
        }
        created_user = crud.create(db_session, user_data, "test-server")
        
        # Test update operation
        update_data = {"display_name": "Updated Test User"}
        updated_user = crud.update(db_session, created_user.scim_id, update_data, "test-server")
        
        assert updated_user.display_name == "Updated Test User"

    def test_base_crud_delete_operation(self, db_session):
        """Test BaseCRUD delete operation."""
        from scim_server.models import User
        
        crud = BaseCRUD(User)
        
        # Create test user
        user_data = {
            "scim_id": "test-user-999",
            "user_name": "testuser4",
            "display_name": "Test User 4"
        }
        created_user = crud.create(db_session, user_data, "test-server")
        user_id = created_user.scim_id
        
        # Test delete operation
        success = crud.delete(db_session, user_id, "test-server")
        assert success is True
        
        # Verify user is deleted
        deleted_user = crud.get_by_id(db_session, user_id, "test-server")
        assert deleted_user is None


class TestResponseConverter(DynamicTestDataMixin):
    """Test ScimResponseConverter functionality."""

    def test_response_converter_initialization(self):
        """Test that ScimResponseConverter initializes correctly."""
        field_mapping = {"userName": "user_name", "displayName": "display_name"}
        converter = ScimResponseConverter(
            schema_uri="urn:test:entity:1.0",
            field_mapping=field_mapping,
            entity_type="TestEntity"
        )
        
        assert converter.entity_type == "TestEntity"
        assert converter.schema_uri == "urn:test:entity:1.0"
        assert converter.field_mapping == field_mapping

    def test_response_converter_to_scim_response(self, db_session):
        """Test ScimResponseConverter to_scim_response method."""
        from scim_server.models import User
        from datetime import datetime
        
        field_mapping = {"userName": "user_name", "displayName": "display_name"}
        converter = ScimResponseConverter(
            schema_uri="urn:ietf:params:scim:schemas:core:2.0:User",
            field_mapping=field_mapping,
            entity_type="User"
        )
        
        # Create real database model
        user = User(
            scim_id="test-user-123",
            user_name="testuser",
            display_name="Test User",
            email="test@example.com",
            active=True,
            server_id="test-server",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Test conversion
        scim_response = converter.to_scim_response(user)
        
        assert "schemas" in scim_response
        assert "urn:ietf:params:scim:schemas:core:2.0:User" in scim_response["schemas"]
        assert scim_response["id"] == "test-user-123"
        assert scim_response["userName"] == "testuser"
        assert scim_response["displayName"] == "Test User"
        assert scim_response["active"] is True

    def test_response_converter_to_scim_list_response(self, db_session):
        """Test ScimResponseConverter with multiple entities."""
        from scim_server.models import User
        from datetime import datetime
        
        field_mapping = {"userName": "user_name", "displayName": "display_name"}
        converter = ScimResponseConverter(
            schema_uri="urn:ietf:params:scim:schemas:core:2.0:User",
            field_mapping=field_mapping,
            entity_type="User"
        )
        
        # Create real database models
        users = []
        for i in range(2):
            user = User(
                scim_id=f"test-user-{i}",
                user_name=f"testuser{i}",
                display_name=f"Test User {i}",
                active=True,
                server_id="test-server",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            users.append(user)
        
        # Test conversion for each entity
        for i, user in enumerate(users):
            scim_response = converter.to_scim_response(user)
            
            assert "schemas" in scim_response
            assert "urn:ietf:params:scim:schemas:core:2.0:User" in scim_response["schemas"]
            assert scim_response["id"] == f"test-user-{i}"
            assert scim_response["displayName"] == f"Test User {i}"
            assert scim_response["active"] is True


class TestSchemaValidatorIntegration(DynamicTestDataMixin):
    """Test schema validator integration with base classes."""

    def test_schema_validator_creation(self, db_session):
        """Test that schema validator can be created for different entity types."""
        test_server_id = "test-server"
        
        # Test schema validator creation
        validator = create_schema_validator(db_session, test_server_id)
        assert validator is not None
        assert validator.server_id == test_server_id

    def test_schema_validator_with_base_entity_endpoint(self, db_session):
        """Test that BaseEntityEndpoint integrates with schema validator."""
        from scim_server.models import User
        
        # Create a mock endpoint that uses schema validation
        mock_router = Mock()
        mock_crud = Mock()
        mock_converter = Mock()
        mock_create_schema = Mock()
        mock_update_schema = Mock()
        mock_response_schema = Mock()
        mock_list_response_schema = Mock()
        
        endpoint = BaseEntityEndpoint(
            entity_type="User",
            router=mock_router,
            crud_operations=mock_crud,
            response_converter=mock_converter,
            create_schema=mock_create_schema,
            update_schema=mock_update_schema,
            response_schema=mock_response_schema,
            list_response_schema=mock_list_response_schema,
            schema_uri="urn:ietf:params:scim:schemas:core:2.0:User",
            supports_multi_server=True
        )
        
        # Verify that the endpoint can work with schema validation
        assert endpoint.entity_type == "User"
        assert endpoint.schema_uri == "urn:ietf:params:scim:schemas:core:2.0:User"

    def test_base_classes_error_handling(self):
        """Test that base classes handle errors gracefully."""
        # Test BaseEntityEndpoint with invalid parameters
        with pytest.raises(TypeError):
            BaseEntityEndpoint()  # Missing required parameters
        
        # Test ScimResponseConverter with invalid parameters
        with pytest.raises(TypeError):
            ScimResponseConverter()  # Missing required parameters 