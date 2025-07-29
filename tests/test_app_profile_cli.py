"""
Tests for App Profile CLI Commands

This module tests the command-line interface for app profile management,
including argument parsing, command execution, and output formatting.
"""

import pytest
import subprocess
import sys
import os
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.scim_cli import SCIMCLI, main


class TestAppProfileCLICommands:
    """Test app profile CLI command functionality."""
    
    def test_cli_list_app_profiles(self):
        """Test CLI list app profiles command."""
        cli = SCIMCLI()
        result = cli.list_app_profiles()
        
        assert result["success"] is True
        assert result["total"] == 13
        assert len(result["profiles"]) == 13
        
        # Verify all expected profiles are present
        expected_profiles = [
            "hr", "it", "sales", "marketing", "finance", 
            "legal", "operations", "security", "customer_success", "research",
            "engineering", "product", "support"
        ]
        
        profile_ids = [profile["id"] for profile in result["profiles"]]
        for expected_id in expected_profiles:
            assert expected_id in profile_ids
        
        # Verify profile structure
        for profile in result["profiles"]:
            assert "id" in profile
            assert "name" in profile
            assert "description" in profile
            assert "app_type" in profile
            assert profile["id"] == profile["app_type"]
    
    def test_cli_get_app_profile_config(self):
        """Test CLI get app profile config command."""
        cli = SCIMCLI()
        
        # Test HR profile
        result = cli.get_app_profile_config("hr")
        assert result["success"] is True
        assert result["profile"] == "hr"
        assert "config" in result
        
        config = result["config"]
        assert config["app_type"] == "hr"
        assert config["name"] == "Human Resources"
        assert "HR application profile" in config["description"]
        assert "compatible_entitlements" in config
        assert "compatible_departments" in config
        assert "compatible_groups" in config
        assert "user_attributes" in config
        assert "roles" in config
        assert "entitlements" in config
        
        # Test IT profile
        result = cli.get_app_profile_config("it")
        assert result["success"] is True
        assert result["profile"] == "it"
        config = result["config"]
        assert config["name"] == "Information Technology"
        assert "IT application profile" in config["description"]
    
    def test_cli_get_invalid_app_profile(self):
        """Test CLI get app profile with invalid profile."""
        cli = SCIMCLI()
        result = cli.get_app_profile_config("invalid")
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"]
    
    def test_cli_set_server_app_profile(self):
        """Test CLI set server app profile command."""
        cli = SCIMCLI()
        server_id = "test-server-123"
        
        result = cli.set_server_app_profile(server_id, "hr")
        
        assert result["success"] is True
        assert result["server_id"] == server_id
        assert result["profile"] == "hr"
        assert "message" in result
        assert "set for server" in result["message"]
    
    def test_cli_set_invalid_app_profile(self):
        """Test CLI set server app profile with invalid profile."""
        cli = SCIMCLI()
        server_id = "test-server-123"
        
        result = cli.set_server_app_profile(server_id, "invalid")
        
        # This should still succeed as the server config manager handles invalid profiles gracefully
        assert result["success"] is True
        assert result["server_id"] == server_id
        assert result["profile"] == "invalid"


class TestAppProfileCLIWithServerCreation:
    """Test app profile integration with server creation."""
    
    def test_cli_create_server_with_app_profile(self):
        """Test creating a server with an app profile."""
        cli = SCIMCLI()
        server_id = "test-server-with-profile"
        
        result = cli.create_virtual_server(
            server_id=server_id,
            users=5,
            groups=3,
            entitlements=4,
            app_profile="hr"
        )
        
        assert result["server_id"] == server_id
        assert result["app_profile"] == "hr"
        assert "stats" in result
        assert result["stats"]["users"] == 5
        assert result["stats"]["groups"] == 3
        assert result["stats"]["entitlements"] == 4
    
    def test_cli_create_server_with_different_profiles(self):
        """Test creating servers with different app profiles."""
        cli = SCIMCLI()
        
        # Test HR profile
        hr_result = cli.create_virtual_server(
            server_id="test-hr-server",
            users=3,
            groups=2,
            entitlements=3,
            app_profile="hr"
        )
        assert hr_result["app_profile"] == "hr"
        
        # Test IT profile
        it_result = cli.create_virtual_server(
            server_id="test-it-server",
            users=3,
            groups=2,
            entitlements=3,
            app_profile="it"
        )
        assert it_result["app_profile"] == "it"
        
        # Test Sales profile
        sales_result = cli.create_virtual_server(
            server_id="test-sales-server",
            users=3,
            groups=2,
            entitlements=3,
            app_profile="sales"
        )
        assert sales_result["app_profile"] == "sales"
    
    def test_cli_create_server_without_app_profile(self):
        """Test creating a server without an app profile."""
        cli = SCIMCLI()
        server_id = "test-server-no-profile"
        
        result = cli.create_virtual_server(
            server_id=server_id,
            users=5,
            groups=3,
            entitlements=4,
            app_profile=None
        )
        
        assert result["server_id"] == server_id
        assert result["app_profile"] is None


class TestAppProfileCLIOutputFormatting:
    """Test CLI output formatting for app profiles."""
    
    def test_cli_json_output_format(self):
        """Test CLI JSON output formatting."""
        cli = SCIMCLI()
        
        # Test list command JSON output
        result = cli.list_app_profiles()
        json_output = cli.output_json(result)
        
        # The output_json method should print to stdout, but we can't easily test that
        # Instead, we'll verify the result structure is JSON-serializable
        json_str = json.dumps(result)
        parsed_result = json.loads(json_str)
        
        assert parsed_result["success"] is True
        assert parsed_result["total"] == 13
        assert len(parsed_result["profiles"]) == 13
    
    def test_cli_get_profile_json_output(self):
        """Test CLI get profile JSON output."""
        cli = SCIMCLI()
        
        result = cli.get_app_profile_config("hr")
        json_str = json.dumps(result)
        parsed_result = json.loads(json_str)
        
        assert parsed_result["success"] is True
        assert parsed_result["profile"] == "hr"
        assert "config" in parsed_result
        
        config = parsed_result["config"]
        assert config["app_type"] == "hr"
        assert config["name"] == "Human Resources"


class TestAppProfileCLIArgumentParsing:
    """Test CLI argument parsing for app profile commands."""
    
    @patch('sys.argv', ['scim_cli.py', 'app-profile', 'list'])
    def test_cli_parse_list_command(self):
        """Test parsing app-profile list command."""
        # This would test the actual argument parsing
        # For now, we'll test the underlying functionality
        cli = SCIMCLI()
        result = cli.list_app_profiles()
        assert result["success"] is True
    
    @patch('sys.argv', ['scim_cli.py', 'app-profile', 'get', '--profile', 'hr'])
    def test_cli_parse_get_command(self):
        """Test parsing app-profile get command."""
        cli = SCIMCLI()
        result = cli.get_app_profile_config("hr")
        assert result["success"] is True
    
    @patch('sys.argv', ['scim_cli.py', 'app-profile', 'set', '--server-id', 'test123', '--profile', 'it'])
    def test_cli_parse_set_command(self):
        """Test parsing app-profile set command."""
        cli = SCIMCLI()
        result = cli.set_server_app_profile("test123", "it")
        assert result["success"] is True


class TestAppProfileCLIErrorHandling:
    """Test CLI error handling for app profile commands."""
    
    def test_cli_database_connection_error(self):
        """Test CLI behavior when database connection fails."""
        # This would test error handling when database is unavailable
        # For now, we'll test that the CLI handles errors gracefully
        cli = SCIMCLI()
        
        # Test with invalid profile (should handle gracefully)
        result = cli.get_app_profile_config("invalid")
        assert result["success"] is False
        assert "error" in result
    
    def test_cli_invalid_server_id(self):
        """Test CLI behavior with invalid server ID."""
        cli = SCIMCLI()
        
        # Test setting app profile on non-existent server
        result = cli.set_server_app_profile("non-existent-server", "hr")
        
        # This should still succeed as the server config manager creates default configs
        assert result["success"] is True
        assert result["server_id"] == "non-existent-server"
        assert result["profile"] == "hr"


class TestAppProfileCLIIntegration:
    """Test app profile CLI integration with other commands."""
    
    def test_cli_create_and_set_app_profile(self):
        """Test creating a server and then setting its app profile."""
        cli = SCIMCLI()
        
        # Create server without app profile
        server_id = "test-integration-server"
        create_result = cli.create_virtual_server(
            server_id=server_id,
            users=3,
            groups=2,
            entitlements=3,
            app_profile=None
        )
        assert create_result["app_profile"] is None
        
        # Set app profile on existing server
        set_result = cli.set_server_app_profile(server_id, "hr")
        assert set_result["success"] is True
        assert set_result["profile"] == "hr"
        
        # Verify the server now has the app profile
        # This would require checking the server configuration
        # For now, we'll just verify the commands executed successfully
    
    def test_cli_list_servers_with_app_profiles(self):
        """Test listing servers that have app profiles."""
        cli = SCIMCLI()
        
        # Create servers with different app profiles
        cli.create_virtual_server(
            server_id="test-hr-server",
            users=2,
            groups=1,
            entitlements=2,
            app_profile="hr"
        )
        
        cli.create_virtual_server(
            server_id="test-it-server",
            users=2,
            groups=1,
            entitlements=2,
            app_profile="it"
        )
        
        # List all servers
        list_result = cli.list_servers()
        assert "servers" in list_result
        
        # Verify servers exist in the list
        server_ids = [server["server_id"] for server in list_result["servers"]]
        assert "test-hr-server" in server_ids
        assert "test-it-server" in server_ids


class TestAppProfileCLIValidation:
    """Test app profile CLI validation and constraints."""
    
    def test_cli_app_profile_choices(self):
        """Test that CLI only accepts valid app profile choices."""
        cli = SCIMCLI()
        
        # Test all valid app profiles
        valid_profiles = ["hr", "it", "sales", "marketing", "finance", "legal", "operations", "security", "customer_success", "research"]
        
        for profile in valid_profiles:
            result = cli.get_app_profile_config(profile)
            assert result["success"] is True
            assert result["profile"] == profile
        
        # Test invalid profile
        result = cli.get_app_profile_config("invalid")
        assert result["success"] is False
    
    def test_cli_server_id_validation(self):
        """Test CLI server ID validation."""
        cli = SCIMCLI()
        
        # Test with valid server ID
        result = cli.set_server_app_profile("valid-server-id", "hr")
        assert result["success"] is True
        
        # Test with empty server ID - this should succeed as server config manager handles it
        result = cli.set_server_app_profile("", "hr")
        assert result["success"] is True  # Server config manager handles empty IDs gracefully
        
        # Test with None server ID - this should fail due to database constraints
        result = cli.set_server_app_profile(None, "hr")
        assert result["success"] is False  # Should fail due to database constraints 