"""
Schema Validation Tests

Tests for SCIM schema validation functionality including:
- Required field validation
- Complex attribute validation
- Multi-valued attribute validation
- Canonical values validation
- Type validation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from loguru import logger

from scim_server.database import get_db
from scim_server.main import app
from scim_server.config import settings
from tests.test_base import DynamicTestDataMixin


def get_unique_username(base_name: str = "testuser") -> str:
    """Generate a unique username for testing."""
    import uuid
    unique_part = str(uuid.uuid4())[:8]
    return f"{base_name}{unique_part}"


class TestSchemaValidation(DynamicTestDataMixin):
    """Test schema validation using dynamic data from codebase."""

    def test_required_field_validation_user(self, client: TestClient, db_session: Session):
        """Test required field validation for User creation using dynamic data."""
        test_server_id = "test-server"
        
        # Get required fields from actual schema
        required_fields = self._get_schema_required_fields(db_session, test_server_id, "User")
        
        # Test missing each required field
        for field in required_fields:
            # Generate valid user data
            user_data = self._generate_valid_user_data(db_session, test_server_id, f"_missing_{field}")
            
            # Remove the required field
            if field in user_data:
                del user_data[field]
            
            response = client.post(
                f"/scim-identifier/{test_server_id}/scim/v2/Users",
                json=user_data,
                headers={"Authorization": f"Bearer {settings.test_api_key}"}
            )
            assert response.status_code == 400
            error_detail = response.json()["detail"]
            assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
            assert field in error_detail["message"]

    def test_required_field_validation_group(self, client: TestClient, db_session: Session):
        """Test required field validation for Group creation using dynamic data."""
        test_server_id = "test-server"
        
        # Get required fields from actual schema
        required_fields = self._get_schema_required_fields(db_session, test_server_id, "Group")
        
        # Test missing each required field
        for field in required_fields:
            # Generate valid group data
            group_data = self._generate_valid_group_data(db_session, test_server_id, f"_missing_{field}")
            
            # Remove the required field
            if field in group_data:
                del group_data[field]
            
            response = client.post(
                f"/scim-identifier/{test_server_id}/scim/v2/Groups",
                json=group_data,
                headers={"Authorization": f"Bearer {settings.test_api_key}"}
            )
            assert response.status_code == 400
            error_detail = response.json()["detail"]
            assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
            assert field in error_detail["message"]

    def test_required_field_validation_entitlement(self, client: TestClient, db_session: Session):
        """Test required field validation for Entitlement creation using dynamic data."""
        test_server_id = "test-server"
        
        # Get required fields from actual schema
        required_fields = self._get_schema_required_fields(db_session, test_server_id, "Entitlement")
        
        # Test missing each required field
        for field in required_fields:
            # Generate valid entitlement data
            entitlement_data = self._generate_valid_entitlement_data(db_session, test_server_id, f"_missing_{field}")
            
            # Remove the required field
            if field in entitlement_data:
                del entitlement_data[field]
            
            response = client.post(
                f"/scim-identifier/{test_server_id}/scim/v2/Entitlements",
                json=entitlement_data,
                headers={"Authorization": f"Bearer {settings.test_api_key}"}
            )
            assert response.status_code == 400
            error_detail = response.json()["detail"]
            assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
            assert field in error_detail["message"]

    def test_complex_attribute_validation_user_emails(self, client: TestClient, db_session: Session):
        """Test complex attribute validation for User emails using dynamic data."""
        test_server_id = "test-server"
        
        # Generate valid user data
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_email_validation")
        
        # Test invalid email structure - missing required 'value'
        invalid_emails = [{"primary": True}]  # Missing required 'value'
        user_data["emails"] = invalid_emails
        
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "value" in error_detail["message"]
        assert error_detail["type"] == "required_field_missing"

        # Test valid email structure - missing optional 'primary' field (should succeed)
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_email_validation_2")
        # Create an email object that's missing the optional 'primary' field
        valid_emails = [{"value": f"test_{self._generate_unique_id()}@{self._get_random_company_domain()}"}]  # Missing optional 'primary'
        user_data["emails"] = valid_emails
        
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201  # Should succeed since 'primary' is optional

    def test_multi_valued_complex_attributes(self, client: TestClient, db_session: Session):
        """Test multi-valued complex attribute validation using dynamic data."""
        test_server_id = "test-server"
        
        # Generate valid user data
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_multi_valued")
        
        # Test multi-valued emails with mixed valid/invalid items
        mixed_emails = [
            {"value": f"valid1_{self._generate_unique_id()}@{self._get_random_company_domain()}", "primary": True},
            {"primary": False},  # Invalid - missing value
            {"value": f"valid2_{self._generate_unique_id()}@{self._get_random_company_domain()}", "primary": False}
        ]
        user_data["emails"] = mixed_emails
        
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "value" in error_detail["message"]

    def test_canonical_values_validation(self, client: TestClient, db_session: Session):
        """Test canonical values validation for entitlements using dynamic data."""
        test_server_id = "test-server"
        
        # Generate valid entitlement data
        entitlement_data = self._generate_valid_entitlement_data(db_session, test_server_id, "_canonical")
        
        # Test invalid canonical value
        entitlement_data["type"] = "invalid_type"
        
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Entitlements",
            json=entitlement_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "invalid_type" in error_detail["message"]

    def test_type_validation_all_types(self, client: TestClient, db_session: Session):
        """Test type validation for all SCIM data types using dynamic data."""
        test_server_id = "test-server"
        
        # Generate valid user data
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_type_validation")
        
        # Test invalid boolean type
        user_data["active"] = "not_a_boolean"
        
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "active" in error_detail["message"]

    def test_patch_operations_validation(self, client: TestClient, db_session: Session):
        """Test PATCH operation validation with schema constraints using dynamic data."""
        test_server_id = "test-server"
        
        # Create a user first using dynamic data
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_patch_test")
        user_response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        # Test PATCH with invalid field
        response = client.patch(
            f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
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
            f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
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
        """Test UPDATE operation validation with schema constraints using dynamic data."""
        test_server_id = "test-server"
        
        # Create a user first using dynamic data
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_update_test")
        user_response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]

        # Test UPDATE with invalid email structure
        update_data = self._generate_valid_user_data(db_session, test_server_id, "_update_invalid")
        update_data["emails"] = [{"primary": True}]  # Missing required 'value'
        
        response = client.put(
            f"/scim-identifier/{test_server_id}/scim/v2/Users/{user_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "value" in error_detail["message"]

    def test_nested_complex_validation_edge_cases(self, client: TestClient, db_session: Session):
        """Test edge cases for nested complex attribute validation using dynamic data."""
        test_server_id = "test-server"
        
        # Generate valid user data
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_edge_case")
        
        # Test emails with mixed valid/invalid items
        mixed_emails = [
            {"value": f"valid1_{self._generate_unique_id()}@{self._get_random_company_domain()}", "primary": True},
            {"primary": False},  # Invalid - missing value
            {"value": f"valid2_{self._generate_unique_id()}@{self._get_random_company_domain()}", "primary": False}
        ]
        user_data["emails"] = mixed_emails
        
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400  # SCIM validation error
        error_detail = response.json()["detail"]
        assert error_detail["error"] == "SCIM_VALIDATION_ERROR"
        assert "value" in error_detail["message"]
        assert error_detail["type"] == "required_field_missing"

    def test_schema_validator_direct_usage(self, db_session: Session):
        """Test schema validator directly without HTTP requests."""
        test_server_id = "test-server"
        
        # Test valid user data
        valid_user_data = self._generate_valid_user_data(db_session, test_server_id, "_direct_test")
        
        # Test invalid user data
        invalid_user_data = self._generate_invalid_data_missing_required_fields(db_session, test_server_id, "User")
        
        # This test would require direct access to the schema validator
        # For now, we'll just verify the data generation works
        assert "userName" in valid_user_data
        assert "userName" not in invalid_user_data

    def test_rfc_compliant_error_messages(self, client: TestClient, db_session: Session):
        """Test that error messages follow RFC 7644 format using dynamic data."""
        test_server_id = "test-server"
        
        # Generate invalid user data
        invalid_user_data = self._generate_invalid_data_missing_required_fields(db_session, test_server_id, "User")
        
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=invalid_user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        
        # Verify RFC-compliant error structure
        assert "error" in error_detail
        assert "message" in error_detail
        assert "field" in error_detail
        assert "resource_type" in error_detail
        assert "server_id" in error_detail
        assert "type" in error_detail

    def test_all_resource_types_validation(self, client: TestClient, db_session: Session):
        """Test validation for all resource types using dynamic data."""
        test_server_id = "test-server"
        
        # Test User validation
        user_data = self._generate_valid_user_data(db_session, test_server_id, "_all_types")
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Users",
            json=user_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201
        
        # Test Group validation
        group_data = self._generate_valid_group_data(db_session, test_server_id, "_all_types")
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Groups",
            json=group_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201
        
        # Test Entitlement validation
        entitlement_data = self._generate_valid_entitlement_data(db_session, test_server_id, "_all_types")
        response = client.post(
            f"/scim-identifier/{test_server_id}/scim/v2/Entitlements",
            json=entitlement_data,
            headers={"Authorization": f"Bearer {settings.test_api_key}"}
        )
        assert response.status_code == 201 