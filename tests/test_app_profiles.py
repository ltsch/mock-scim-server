"""
Tests for App Profiles Functionality

This module tests the app profiles system including:
- App profile creation and management
- CLI commands for app profiles
- Server configuration integration
- Database operations with app profiles
- Integration with existing config.py settings
"""

import pytest
import uuid
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from scim_server.app_profiles import (
    AppType, MutabilityLevel, AppProfileManager, 
    get_app_profile_manager, AttributeConfig, RoleConfig, EntitlementConfig
)
from scim_server.server_config import get_server_config_manager
from scim_server.models import User, AppProfile
from scim_server.config import settings


class TestAppProfileEnums:
    """Test app profile enums and constants."""
    
    def test_app_type_enum(self):
        """Test AppType enum values."""
        assert AppType.HR.value == "hr"
        assert AppType.IT.value == "it"
        assert AppType.SALES.value == "sales"
        assert AppType.MARKETING.value == "marketing"
        assert AppType.FINANCE.value == "finance"
        assert AppType.LEGAL.value == "legal"
        assert AppType.OPERATIONS.value == "operations"
        assert AppType.SECURITY.value == "security"
        assert AppType.CUSTOMER_SUCCESS.value == "customer_success"
        assert AppType.RESEARCH.value == "research"
    
    def test_mutability_level_enum(self):
        """Test MutabilityLevel enum values."""
        assert MutabilityLevel.READ_ONLY.value == "readOnly"
        assert MutabilityLevel.READ_WRITE.value == "readWrite"
        assert MutabilityLevel.IMMUTABLE.value == "immutable"
        assert MutabilityLevel.WRITE_ONCE.value == "writeOnce"


class TestAppProfileManager:
    """Test AppProfileManager functionality."""
    
    def test_manager_initialization(self):
        """Test that AppProfileManager initializes correctly."""
        manager = AppProfileManager()
        assert manager is not None
        assert hasattr(manager, 'profiles')
        assert len(manager.profiles) == 13  # All 13 app types (including new ones)
    
    def test_get_all_profiles(self):
        """Test getting all profiles."""
        manager = AppProfileManager()
        profiles = manager.get_all_profiles()
        
        assert len(profiles) == 13
        assert AppType.HR in profiles
        assert AppType.IT in profiles
        assert AppType.SALES in profiles
        assert AppType.MARKETING in profiles
        assert AppType.FINANCE in profiles
        assert AppType.LEGAL in profiles
        assert AppType.OPERATIONS in profiles
        assert AppType.SECURITY in profiles
        assert AppType.CUSTOMER_SUCCESS in profiles
        assert AppType.RESEARCH in profiles
    
    def test_get_profile(self):
        """Test getting specific profiles."""
        manager = AppProfileManager()
        
        # Test HR profile
        hr_profile = manager.get_profile(AppType.HR)
        assert hr_profile is not None
        assert hr_profile.app_type == AppType.HR
        assert hr_profile.name == "Human Resources"
        assert "HR application profile" in hr_profile.description
        
        # Test IT profile
        it_profile = manager.get_profile(AppType.IT)
        assert it_profile is not None
        assert it_profile.app_type == AppType.IT
        assert it_profile.name == "Information Technology"
        assert "IT application profile" in it_profile.description
    
    def test_get_profile_by_name(self):
        """Test getting profile by name string."""
        manager = AppProfileManager()
        
        hr_profile = manager.get_profile_by_name("Human Resources")
        assert hr_profile is not None
        assert hr_profile.app_type == AppType.HR
        
        it_profile = manager.get_profile_by_name("Information Technology")
        assert it_profile is not None
        assert it_profile.app_type == AppType.IT
        
        # Test invalid name
        invalid_profile = manager.get_profile_by_name("invalid")
        assert invalid_profile is None
    
    def test_hr_profile_configuration(self):
        """Test HR profile specific configuration."""
        manager = AppProfileManager()
        hr_profile = manager.get_profile(AppType.HR)
        
        assert "System Role" in hr_profile.compatible_entitlements
        assert "Department Access" in hr_profile.compatible_entitlements
        assert "Human Resources" in hr_profile.compatible_departments
        assert "HR Team" in hr_profile.compatible_groups
        
        # Check user attributes
        user_attrs = [attr.name for attr in hr_profile.user_attributes]
        assert "userName" in user_attrs
        assert "displayName" in user_attrs
        assert "emails" in user_attrs
    
    def test_it_profile_configuration(self):
        """Test IT profile specific configuration."""
        manager = AppProfileManager()
        it_profile = manager.get_profile(AppType.IT)
        
        assert "Office 365 License" in it_profile.compatible_entitlements
        assert "GitHub Access" in it_profile.compatible_entitlements
        assert "VPN Access" in it_profile.compatible_entitlements
        assert "IT" in it_profile.compatible_departments
        assert "Engineering" in it_profile.compatible_departments
        assert "Engineering Team" in it_profile.compatible_groups
        assert "Support Team" in it_profile.compatible_groups
    
    def test_sales_profile_configuration(self):
        """Test Sales profile specific configuration."""
        manager = AppProfileManager()
        sales_profile = manager.get_profile(AppType.SALES)
        
        assert "Salesforce Access" in sales_profile.compatible_entitlements
        assert "Sales" in sales_profile.compatible_departments
        assert "Sales Team" in sales_profile.compatible_groups
    
    def test_compatible_entitlements_integration(self):
        """Test that compatible entitlements exist in config.py."""
        manager = AppProfileManager()
        
        for app_type in AppType:
            profile = manager.get_profile(app_type)
            if profile:
                for entitlement_name in profile.compatible_entitlements:
                    # Check that entitlement exists in config
                    found = False
                    for entitlement_def in settings.cli_entitlement_definitions:
                        if entitlement_def["name"] == entitlement_name:
                            found = True
                            break
                    assert found, f"Entitlement '{entitlement_name}' not found in config for {app_type.value}"
    
    def test_compatible_departments_integration(self):
        """Test that compatible departments exist in config.py."""
        manager = AppProfileManager()
        
        for app_type in AppType:
            profile = manager.get_profile(app_type)
            if profile:
                for dept_name in profile.compatible_departments:
                    # Check that department exists in config
                    found = False
                    for dept, _ in settings.cli_department_job_titles:
                        if dept == dept_name:
                            found = True
                            break
                    assert found, f"Department '{dept_name}' not found in config for {app_type.value}"
    
    def test_compatible_groups_integration(self):
        """Test that compatible groups exist in config.py."""
        manager = AppProfileManager()
        
        for app_type in AppType:
            profile = manager.get_profile(app_type)
            if profile:
                for group_name in profile.compatible_groups:
                    # Check that group exists in config
                    assert group_name in settings.cli_group_names, f"Group '{group_name}' not found in config for {app_type.value}"


class TestAppProfileManagerMethods:
    """Test AppProfileManager utility methods."""
    
    def test_get_compatible_entitlements(self):
        """Test getting compatible entitlements for a profile."""
        manager = AppProfileManager()
        
        hr_entitlements = manager.get_compatible_entitlements(AppType.HR)
        assert "System Role" in hr_entitlements
        assert "Department Access" in hr_entitlements
        
        it_entitlements = manager.get_compatible_entitlements(AppType.IT)
        assert "Office 365 License" in it_entitlements
        assert "GitHub Access" in it_entitlements
    
    def test_get_compatible_departments(self):
        """Test getting compatible departments for a profile."""
        manager = AppProfileManager()
        
        hr_departments = manager.get_compatible_departments(AppType.HR)
        assert "Human Resources" in hr_departments
        
        it_departments = manager.get_compatible_departments(AppType.IT)
        assert "IT" in it_departments
        assert "Engineering" in it_departments
    
    def test_get_compatible_groups(self):
        """Test getting compatible groups for a profile."""
        manager = AppProfileManager()
        
        hr_groups = manager.get_compatible_groups(AppType.HR)
        assert "HR Team" in hr_groups
        
        it_groups = manager.get_compatible_groups(AppType.IT)
        assert "Engineering Team" in it_groups
        assert "Support Team" in it_groups
    
    def test_get_entitlement_definitions_for_profile(self):
        """Test getting entitlement definitions for a profile."""
        manager = AppProfileManager()
        
        hr_definitions = manager.get_entitlement_definitions_for_profile(AppType.HR)
        assert len(hr_definitions) > 0
        
        # Check that returned definitions match compatible entitlements
        hr_profile = manager.get_profile(AppType.HR)
        definition_names = [defn["name"] for defn in hr_definitions]
        for entitlement_name in hr_profile.compatible_entitlements:
            assert entitlement_name in definition_names
    
    def test_get_department_job_titles_for_profile(self):
        """Test getting department job titles for a profile."""
        manager = AppProfileManager()
        
        hr_job_titles = manager.get_department_job_titles_for_profile(AppType.HR)
        assert len(hr_job_titles) > 0
        
        # Check that returned departments match compatible departments
        hr_profile = manager.get_profile(AppType.HR)
        returned_departments = [dept for dept, _ in hr_job_titles]
        for dept_name in hr_profile.compatible_departments:
            assert dept_name in returned_departments
    
    def test_validate_attribute_mutability(self):
        """Test attribute mutability validation."""
        manager = AppProfileManager()
        
        # Test HR profile mutability rules
        assert manager.validate_attribute_mutability(AppType.HR, "userName", "read")
        assert not manager.validate_attribute_mutability(AppType.HR, "userName", "write")
        assert manager.validate_attribute_mutability(AppType.HR, "displayName", "write")
    
    def test_get_visible_attributes(self):
        """Test getting visible attributes for a profile."""
        manager = AppProfileManager()
        
        hr_visible = manager.get_visible_attributes(AppType.HR)
        assert "userName" in hr_visible
        assert "displayName" in hr_visible
    
    def test_get_required_attributes(self):
        """Test getting required attributes for a profile."""
        manager = AppProfileManager()
        
        hr_required = manager.get_required_attributes(AppType.HR)
        assert "userName" in hr_required  # userName is always required
    
    def test_get_roles(self):
        """Test getting roles for a profile."""
        manager = AppProfileManager()
        
        hr_roles = manager.get_roles(AppType.HR)
        assert len(hr_roles) > 0
        assert all(isinstance(role, RoleConfig) for role in hr_roles)
    
    def test_get_entitlements(self):
        """Test getting entitlements for a profile."""
        manager = AppProfileManager()
        
        hr_entitlements = manager.get_entitlements(AppType.HR)
        assert len(hr_entitlements) > 0
        assert all(isinstance(ent, EntitlementConfig) for ent in hr_entitlements)


class TestAppProfileGlobalManager:
    """Test global app profile manager functionality."""
    
    def test_get_app_profile_manager(self):
        """Test global app profile manager access."""
        manager = get_app_profile_manager()
        assert manager is not None
        assert isinstance(manager, AppProfileManager)
        
        # Test that it's a singleton
        manager2 = get_app_profile_manager()
        assert manager is manager2


class TestAppProfileServerConfiguration:
    """Test app profile integration with server configuration."""
    
    def test_server_config_app_profile_methods(self, db_session: Session):
        """Test server configuration app profile methods."""
        config_manager = get_server_config_manager(db_session)
        
        # Test getting available app profiles
        profiles = config_manager.get_available_app_profiles()
        assert len(profiles) == 13
        
        # Check profile structure
        for profile in profiles:
            assert "id" in profile
            assert "name" in profile
            assert "description" in profile
            assert "app_type" in profile
        
        # Test getting specific app profile config
        hr_config = config_manager.get_app_profile_config("hr")
        assert hr_config is not None
        assert hr_config["app_type"] == "hr"
        assert hr_config["name"] == "Human Resources"
        assert "compatible_entitlements" in hr_config
        assert "compatible_departments" in hr_config
        assert "compatible_groups" in hr_config
        assert "user_attributes" in hr_config
        assert "roles" in hr_config
        assert "entitlements" in hr_config
    
    def test_set_server_app_profile(self, db_session: Session):
        """Test setting app profile on a server."""
        config_manager = get_server_config_manager(db_session)
        server_id = str(uuid.uuid4())
        
        # Set app profile
        config_manager.set_server_app_profile(server_id, "hr")
        
        # Verify it was set
        app_profile = config_manager.get_server_app_profile(server_id)
        assert app_profile == "hr"
        
        # Test setting different profile
        config_manager.set_server_app_profile(server_id, "it")
        app_profile = config_manager.get_server_app_profile(server_id)
        assert app_profile == "it"
    
    def test_invalid_app_profile(self, db_session: Session):
        """Test handling of invalid app profiles."""
        config_manager = get_server_config_manager(db_session)
        
        # Test getting invalid app profile config
        invalid_config = config_manager.get_app_profile_config("invalid")
        assert invalid_config is None


class TestAppProfileDatabaseOperations:
    """Test app profile database operations."""
    
    def test_app_profile_model_creation(self, db_session: Session):
        """Test creating AppProfile database records."""
        profile_id = str(uuid.uuid4())
        app_profile = AppProfile(
            profile_id=profile_id,
            name="Test Profile",
            description="Test app profile",
            app_type="test",
            configuration={"test": "config"},
            is_active=True
        )
        
        db_session.add(app_profile)
        db_session.commit()
        
        # Verify it was created
        retrieved = db_session.query(AppProfile).filter_by(profile_id=profile_id).first()
        assert retrieved is not None
        assert retrieved.name == "Test Profile"
        assert retrieved.app_type == "test"
        assert retrieved.configuration == {"test": "config"}
        assert retrieved.is_active is True
    
    def test_user_app_profile_association(self, db_session: Session):
        """Test associating users with app profiles."""
        # Create app profile
        profile_id = str(uuid.uuid4())
        app_profile = AppProfile(
            profile_id=profile_id,
            name="Test Profile",
            description="Test app profile",
            app_type="test",
            is_active=True
        )
        db_session.add(app_profile)
        db_session.commit()
        
        # Create user with app profile
        user = User(
            scim_id=str(uuid.uuid4()),
            user_name="testuser@example.com",
            display_name="Test User",
            server_id=str(uuid.uuid4()),
            app_profile_id=profile_id
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify association
        retrieved_user = db_session.query(User).filter_by(user_name="testuser@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.app_profile_id == profile_id
        
        # Verify relationship
        assert retrieved_user.app_profile_id == app_profile.profile_id


class TestAppProfileCLI:
    """Test app profile CLI functionality."""
    
    def test_cli_app_profile_list_command(self, client):
        """Test CLI app profile list command."""
        # This would test the actual CLI command execution
        # For now, we'll test the underlying functionality
        from scripts.scim_cli import SCIMCLI
        
        cli = SCIMCLI()
        result = cli.list_app_profiles()
        
        assert result["success"] is True
        assert result["total"] == 13
        assert len(result["profiles"]) == 13
        
        # Check that all expected profiles are present
        profile_ids = [profile["id"] for profile in result["profiles"]]
        expected_ids = ["hr", "it", "sales", "marketing", "finance", "legal", "operations", "security", "customer_success", "research", "engineering", "product", "support"]
        for expected_id in expected_ids:
            assert expected_id in profile_ids
    
    def test_cli_app_profile_get_command(self, client):
        """Test CLI app profile get command."""
        from scripts.scim_cli import SCIMCLI
        
        cli = SCIMCLI()
        result = cli.get_app_profile_config("hr")
        
        assert result["success"] is True
        assert result["profile"] == "hr"
        assert "config" in result
        
        config = result["config"]
        assert config["app_type"] == "hr"
        assert config["name"] == "Human Resources"
        assert "compatible_entitlements" in config
        assert "compatible_departments" in config
        assert "compatible_groups" in config
    
    def test_cli_app_profile_set_command(self, client):
        """Test CLI app profile set command."""
        from scripts.scim_cli import SCIMCLI
        
        cli = SCIMCLI()
        server_id = str(uuid.uuid4())
        
        result = cli.set_server_app_profile(server_id, "it")
        
        assert result["success"] is True
        assert result["server_id"] == server_id
        assert result["profile"] == "it"
        assert "message" in result
    
    def test_cli_invalid_app_profile(self, client):
        """Test CLI with invalid app profile."""
        from scripts.scim_cli import SCIMCLI
        
        cli = SCIMCLI()
        result = cli.get_app_profile_config("invalid")
        
        assert result["success"] is False
        assert "error" in result


class TestAppProfileIntegration:
    """Test app profile integration with existing systems."""
    
    def test_app_profile_with_server_creation(self, db_session: Session):
        """Test creating a server with an app profile."""
        from scripts.scim_cli import SCIMCLI
        
        cli = SCIMCLI()
        result = cli.create_virtual_server(
            server_id=str(uuid.uuid4()),
            users=5,
            groups=3,
            entitlements=4,
            app_profile="hr"
        )
        
        assert result["app_profile"] == "hr"
        assert "server_id" in result
        assert "stats" in result
        
        # Verify server has app profile set
        config_manager = get_server_config_manager(db_session)
        app_profile = config_manager.get_server_app_profile(result["server_id"])
        assert app_profile == "hr"
    
    def test_app_profile_entitlement_filtering(self, db_session: Session):
        """Test that app profiles filter entitlements correctly."""
        manager = AppProfileManager()
        
        # Get HR profile entitlements
        hr_entitlements = manager.get_entitlement_definitions_for_profile(AppType.HR)
        hr_entitlement_names = [ent["name"] for ent in hr_entitlements]
        
        # Get IT profile entitlements
        it_entitlements = manager.get_entitlement_definitions_for_profile(AppType.IT)
        it_entitlement_names = [ent["name"] for ent in it_entitlements]
        
        # HR and IT should have different entitlement sets
        # Note: They may share some common entitlements like "System Role" and "Department Access"
        assert len(hr_entitlement_names) > 0
        assert len(it_entitlement_names) > 0
        assert set(hr_entitlement_names) != set(it_entitlement_names)  # They should be different sets
    
    def test_app_profile_department_filtering(self, db_session: Session):
        """Test that app profiles filter departments correctly."""
        manager = AppProfileManager()
        
        # Get HR profile departments
        hr_departments = manager.get_department_job_titles_for_profile(AppType.HR)
        hr_department_names = [dept for dept, _ in hr_departments]
        
        # Get IT profile departments
        it_departments = manager.get_department_job_titles_for_profile(AppType.IT)
        it_department_names = [dept for dept, _ in it_departments]
        
        # HR and IT should have different department sets
        assert len(set(hr_department_names) & set(it_department_names)) < len(hr_department_names)
        assert len(set(hr_department_names) & set(it_department_names)) < len(it_department_names)


class TestAppProfileEdgeCases:
    """Test app profile edge cases and error handling."""
    
    def test_nonexistent_app_profile(self):
        """Test handling of nonexistent app profiles."""
        manager = AppProfileManager()
        
        # Test with invalid app type
        profile = manager.get_profile_by_name("nonexistent")
        assert profile is None
        
        entitlements = manager.get_compatible_entitlements(AppType.HR)  # Valid
        assert len(entitlements) > 0
    
    def test_empty_compatible_lists(self):
        """Test profiles with empty compatible lists."""
        manager = AppProfileManager()
        
        # All profiles should have at least some compatible items
        for app_type in AppType:
            profile = manager.get_profile(app_type)
            if profile:
                assert len(profile.compatible_entitlements) > 0
                assert len(profile.compatible_departments) > 0
                assert len(profile.compatible_groups) > 0
    
    def test_app_profile_consistency(self):
        """Test that app profiles are internally consistent."""
        manager = AppProfileManager()
        
        for app_type in AppType:
            profile = manager.get_profile(app_type)
            if profile:
                # Check that all user attributes have valid mutability levels
                for attr in profile.user_attributes:
                    assert isinstance(attr.mutability, MutabilityLevel)
                    assert attr.name is not None
                    assert len(attr.name) > 0
                
                # Check that all roles have valid mutability levels
                for role in profile.roles:
                    assert isinstance(role.mutability, MutabilityLevel)
                    assert role.name is not None
                    assert len(role.name) > 0
                    assert len(role.permissions) > 0
                
                # Check that all entitlements have valid mutability levels
                for ent in profile.entitlements:
                    assert isinstance(ent.mutability, MutabilityLevel)
                    assert ent.name is not None
                    assert len(ent.name) > 0
                    assert ent.type is not None
                    assert len(ent.canonical_values) > 0 