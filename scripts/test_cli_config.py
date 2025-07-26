#!/usr/bin/env python3
"""
Test script to verify CLI tool configuration integration.
This script tests that the CLI tool correctly uses configuration values from config.py.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.config import settings
from scripts.scim_cli import SCIMCLI

def test_config_integration():
    """Test that CLI tool uses configuration values correctly."""
    print("Testing CLI tool configuration integration...")
    
    # Test configuration values are accessible
    print(f"✓ CLI Default Users: {settings.cli_default_users}")
    print(f"✓ CLI Default Groups: {settings.cli_default_groups}")
    print(f"✓ CLI Default Entitlements: {settings.cli_default_entitlements}")
    print(f"✓ CLI Default Roles: {settings.cli_default_roles}")
    
    # Test predefined data lists
    print(f"✓ Group Names: {len(settings.cli_group_names)} items")
    print(f"✓ Entitlement Types: {len(settings.cli_entitlement_types)} items")
    print(f"✓ Role Names: {len(settings.cli_role_names)} items")
    
    # Test CLI tool initialization
    try:
        cli = SCIMCLI()
        print("✓ CLI tool initialized successfully")
        
        # Test that defaults match configuration
        assert cli.defaults['users'] == settings.cli_default_users
        assert cli.defaults['groups'] == settings.cli_default_groups
        assert cli.defaults['entitlements'] == settings.cli_default_entitlements
        assert cli.defaults['roles'] == settings.cli_default_roles
        print("✓ CLI defaults match configuration values")
        
        # Test server listing
        servers = cli.get_unique_server_ids()
        print(f"✓ Found {len(servers)} existing servers")
        
        print("\n🎉 All configuration integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_config_integration()
    sys.exit(0 if success else 1) 