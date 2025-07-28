"""
Comprehensive tests for SCIM schema validation.

Tests cover:
- Required field validation at all levels (top-level and nested)
- Multi-valued attribute validation (both simple and complex)
- Complex attribute validation with nested sub-attributes
- Canonical values validation
- Type validation for all SCIM types
- RFC-compliant error messages
- Edge cases for all resource types
"""

import pytest
import random
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from scim_server.schema_validator import SchemaValidator
from scim_server.schema_definitions import DynamicSchemaGenerator
from scim_server.main import app
from scim_server.config import settings
from tests.conftest import client, db_session


def get_unique_username(base_name: str = "testuser") -> str:
    """Generate a unique username with random 3-digit number to avoid conflicts."""
    random_num = random.randint(100, 999)
    return f"{base_name}{random_num}@example.com"


class TestSchemaValidation:
    """Test comprehensive schema validation for all SCIM resource types."""

    def test_required_field_validation_user(self, client: TestClient, db_session: Session):
        """Test required field validation for User creation."""
        # Missing required userName
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "displayName": "Test User",
                "emails": [{"value": "test@example.com", "primary": True}]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "userName" in error_detail["message"]
        assert error_detail["type"] == "required_field_missing"

        # Valid user creation (displayName is optional)
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username(),
                "emails": [{"value": "test@example.com", "primary": True}]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201

    def test_required_field_validation_group(self, client: TestClient, db_session: Session):
        """Test required field validation for Group creation."""
        # Missing required displayName
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Groups",
            json={
                "description": "Test group"
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "displayName" in error_detail["message"]

    def test_required_field_validation_entitlement(self, client: TestClient, db_session: Session):
        """Test required field validation for Entitlement creation."""
        # Missing required displayName
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Entitlements",
            json={
                "type": "Administrator",
                "description": "Test entitlement"
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "displayName" in error_detail["message"]

        # Missing required type
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Entitlements",
            json={
                "displayName": "Test Entitlement",
                "description": "Test entitlement"
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "type" in error_detail["message"]

    def test_complex_attribute_validation_user_emails(self, client: TestClient, db_session: Session):
        """Test validation of complex email attributes with required sub-attributes."""
        # Missing required 'value' in email - this will fail at Pydantic level
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username(),
                "displayName": "Test User",
                "emails": [{"primary": True}]  # Missing 'value'
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400  # SCIM validation error
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "value" in error_detail["message"]
        assert error_detail["type"] == "required_field_missing"

        # Invalid email value type - this will be caught by SCIM schema validation
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username(),
                "displayName": "Test User",
                "emails": [{"value": 123, "primary": True}]  # Invalid type
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400  # SCIM validation error
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "string" in error_detail["message"]
        assert error_detail["type"] == "type_mismatch"

    def test_multi_valued_complex_attributes(self, client: TestClient, db_session: Session):
        """Test validation of multi-valued complex attributes."""
        # Valid multi-valued emails
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username(),
                "displayName": "Test User",
                "emails": [
                    {"value": "primary@example.com", "primary": True},
                    {"value": "secondary@example.com", "primary": False}
                ]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201

        # Invalid multi-valued emails (missing required value) - fails at Pydantic level
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username(),
                "displayName": "Test User 2",
                "emails": [
                    {"value": "primary@example.com", "primary": True},
                    {"primary": False}  # Missing value
                ]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400  # SCIM validation error
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "value" in error_detail["message"]
        assert error_detail["type"] == "required_field_missing"

    def test_canonical_values_validation(self, client: TestClient, db_session: Session):
        """Test canonical values validation for entitlements."""
        # Invalid entitlement type
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Entitlements",
            json={
                "displayName": "Test Entitlement",
                "type": "InvalidType",  # Not in canonical values
                "description": "Test description"
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "canonical_value" in error_detail["type"]
        assert "InvalidType" in error_detail["message"]

        # Valid entitlement type
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Entitlements",
            json={
                "displayName": "Test Entitlement",
                "type": "Administrator",  # Valid canonical value from the list
                "description": "Test description"
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201

    def test_type_validation_all_types(self, client: TestClient, db_session: Session):
        """Test type validation for all SCIM data types."""
        # String type validation
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": 123,  # Should be string
                "displayName": "Test User"
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "string" in error_detail["message"]

        # Boolean type validation
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username(),
                "displayName": "Test User",
                "active": "not_a_boolean"  # Should be boolean
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "boolean" in error_detail["message"]

        # Integer type validation (if applicable)
        # Note: Most SCIM attributes are strings, but test if any integers exist

    def test_patch_operations_validation(self, client: TestClient, db_session: Session):
        """Test PATCH operation validation with schema constraints."""
        # Create a user first
        user_response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username("patchuser"),
                "displayName": "Patch User",
                "emails": [{"value": "patch@example.com", "primary": True}]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        # Test PATCH with invalid field
        response = client.patch(
            f"/scim-identifier/test-server/scim/v2/Users/{user_id}",
            json={
                "Operations": [
                    {
                        "op": "replace",
                        "path": "invalidField",
                        "value": "test"
                    }
                ]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "invalidField" in error_detail["message"]

        # Test PATCH with invalid email structure
        response = client.patch(
            f"/scim-identifier/test-server/scim/v2/Users/{user_id}",
            json={
                "Operations": [
                    {
                        "op": "replace",
                        "path": "emails",
                        "value": [{"primary": True}]  # Missing required 'value'
                    }
                ]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "value" in error_detail["message"]

    def test_update_operations_validation(self, client: TestClient, db_session: Session):
        """Test UPDATE operation validation with schema constraints."""
        # Create a user first
        user_response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username("updateuser"),
                "displayName": "Update User",
                "emails": [{"value": "update@example.com", "primary": True}]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        # Test UPDATE with invalid email structure
        response = client.put(
            f"/scim-identifier/test-server/scim/v2/Users/{user_id}",
            json={
                "userName": get_unique_username("updateuser"),
                "displayName": "Updated User",
                "emails": [{"primary": True}]  # Missing required 'value'
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "value" in error_detail["message"]

    def test_nested_complex_validation_edge_cases(self, client: TestClient, db_session: Session):
        """Test edge cases for nested complex attribute validation."""
        # Test deeply nested complex attributes (if any exist in schema)
        # Test multi-valued complex attributes with mixed valid/invalid items
        # Test complex attributes with missing optional sub-attributes

        # Example: Test emails with mixed valid/invalid items
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "userName": get_unique_username("edgecase"),
                "displayName": "Edge Case User",
                "emails": [
                    {"value": "valid@example.com", "primary": True},
                    {"primary": False},  # Invalid - missing value
                    {"value": "another@example.com", "primary": False}
                ]
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400  # SCIM validation error
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "value" in error_detail["message"]
        assert error_detail["type"] == "required_field_missing"

    def test_schema_validator_direct_usage(self, db_session: Session):
        """Test SchemaValidator directly for comprehensive validation."""
        schema_generator = DynamicSchemaGenerator(db_session, "test-server")
        validator = SchemaValidator(schema_generator)

        # Test User schema validation
        user_schema = validator.get_schema("User")
        assert "attributes" in user_schema
        assert any(attr["name"] == "userName" for attr in user_schema["attributes"])

        # Test validation of valid user data
        valid_user_data = {
            "userName": get_unique_username(),
            "displayName": "Test User",
            "emails": [{"value": "test@example.com", "primary": True}]
        }
        validated_data = validator.validate_create_request("User", valid_user_data)
        assert validated_data["userName"] == valid_user_data["userName"]

        # Test validation of invalid user data
        invalid_user_data = {
            "displayName": "Test User",
            "emails": [{"value": "test@example.com", "primary": True}]
        }
        with pytest.raises(Exception):
            validator.validate_create_request("User", invalid_user_data)

    def test_rfc_compliant_error_messages(self, client: TestClient, db_session: Session):
        """Test that all error messages are RFC-compliant and consistent."""
        # Test missing required field
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json={
                "displayName": "Test User"
            },
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        
        # Verify RFC-compliant error structure
        assert "error" in error_detail
        assert "message" in error_detail
        assert "field" in error_detail
        assert "type" in error_detail
        assert "resource_type" in error_detail
        assert "help" in error_detail
        
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert error_detail["type"] == "required_field_missing"
        assert error_detail["resource_type"] == "User"

    def test_all_resource_types_validation(self, client: TestClient, db_session: Session):
        """Test schema validation for all resource types (User, Group, Entitlement)."""
        # Test User validation
        user_data = {
            "userName": get_unique_username("alltypes"),
            "displayName": "All Types User",
            "emails": [{"value": "alltypes@example.com", "primary": True}]
        }
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201

        # Test Group validation
        group_data = {
            "displayName": "All Types Group",
            "description": "Test group for all types"
        }
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Groups",
            json=group_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201

        # Test Entitlement validation
        entitlement_data = {
            "displayName": "All Types Entitlement",
            "type": "Administrator",  # Use valid canonical value
            "description": "Test entitlement for all types"
        }
        response = client.post(
            "/scim-identifier/test-server/scim/v2/Entitlements",
            json=entitlement_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201 