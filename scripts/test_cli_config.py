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
    
    # Test predefined data lists
    print(f"✓ Group Names: {len(settings.cli_group_names)} items")
    print(f"✓ Entitlement Definitions: {len(settings.cli_entitlement_definitions)} items")
    
    # Test enhanced configuration
    print(f"✓ Department-Job Title Pairs: {len(settings.cli_department_job_titles)} departments")
    total_job_titles = sum(len(titles) for _, titles in settings.cli_department_job_titles)
    print(f"✓ Total Job Titles: {total_job_titles} across all departments")
    print(f"✓ Company Domains: {len(settings.cli_company_domains)} items")
    
    # Test distribution settings
    print(f"✓ User Active Rate: {settings.cli_user_active_rate}")
    print(f"✓ User Department Rate: {settings.cli_user_department_rate}")
    print(f"✓ User Job Title Rate: {settings.cli_user_job_title_rate}")
    print(f"✓ User Multiple Groups Rate: {settings.cli_user_multiple_groups_rate}")
    print(f"✓ User Entitlements Rate: {settings.cli_user_entitlements_rate}")

    
    # Test relationship limits
    print(f"✓ Max Groups Per User: {settings.cli_max_groups_per_user}")
    print(f"✓ Max Entitlements Per User: {settings.cli_max_entitlements_per_user}")

    
    # Test CLI tool initialization
    try:
        cli = SCIMCLI()
        print("✓ CLI tool initialized successfully")
        
        # Test that defaults match configuration
        assert cli.defaults['users'] == settings.cli_default_users
        assert cli.defaults['groups'] == settings.cli_default_groups
        assert cli.defaults['entitlements'] == settings.cli_default_entitlements
        print("✓ CLI defaults match configuration values")
        
        # Test names module integration
        try:
            import names
            test_name = names.get_full_name()
            print(f"✓ Names module working: {test_name}")
        except ImportError:
            print("⚠ Names module not available")
        
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