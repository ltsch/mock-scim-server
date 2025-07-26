#!/usr/bin/env python3
"""
Test Dynamic SCIM Schema System

This script tests that the dynamic schema system correctly:
1. Generates schemas based on actual database models
2. Reflects configuration values (like entitlement types)
3. Provides accurate canonical values
4. Removes hardcoded values and uses dynamic generation
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scim_server.database import SessionLocal
from scim_server.schema_definitions import DynamicSchemaGenerator
from scim_server.config import settings


def test_resource_types():
    """Test that resource types are generated dynamically and don't include Role."""
    print("🔍 Testing Resource Types...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db)
        resource_types = schema_generator.get_resource_types()
        
        # Check that we have the expected resource types
        expected_types = ["User", "Group", "Entitlement"]
        actual_types = [rt["id"] for rt in resource_types]
        
        print(f"  ✓ Found {len(resource_types)} resource types")
        print(f"  ✓ Resource types: {', '.join(actual_types)}")
        
        # Verify Role is NOT included (since we removed it)
        if "Role" in actual_types:
            print("  ❌ ERROR: Role is still included in resource types!")
            return False
        else:
            print("  ✓ Role correctly removed from resource types")
        
        # Verify all expected types are present
        for expected_type in expected_types:
            if expected_type not in actual_types:
                print(f"  ❌ ERROR: Missing expected resource type: {expected_type}")
                return False
        
        print("  ✓ All expected resource types present")
        return True
        
    finally:
        db.close()


def test_entitlement_schema_canonical_values():
    """Test that entitlement schema includes canonical values from configuration."""
    print("\n🔍 Testing Entitlement Schema Canonical Values...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db)
        entitlement_schema = schema_generator.get_entitlement_schema()
        
        # Find the type attribute
        type_attribute = None
        for attr in entitlement_schema["attributes"]:
            if attr["name"] == "type":
                type_attribute = attr
                break
        
        if not type_attribute:
            print("  ❌ ERROR: Could not find 'type' attribute in entitlement schema")
            return False
        
        canonical_values = type_attribute.get("canonicalValues", [])
        print(f"  ✓ Found {len(canonical_values)} canonical values")
        
        # Get expected values from enhanced entitlement definitions
        all_canonical_values = []
        for definition in settings.cli_entitlement_definitions:
            all_canonical_values.extend(definition["canonical_values"])
        expected_values = list(set(all_canonical_values))
        print(f"  ✓ Expected {len(expected_values)} values from enhanced definitions")
        
        # Check that all configuration values are present
        missing_values = []
        for expected_value in expected_values:
            if expected_value not in canonical_values:
                missing_values.append(expected_value)
        
        if missing_values:
            print(f"  ❌ ERROR: Missing canonical values: {missing_values}")
            return False
        
        # Check for any unexpected values
        unexpected_values = []
        for canonical_value in canonical_values:
            if canonical_value not in expected_values:
                unexpected_values.append(canonical_value)
        
        if unexpected_values:
            print(f"  ❌ ERROR: Unexpected canonical values: {unexpected_values}")
            return False
        
        print("  ✓ All canonical values match configuration")
        print(f"  ✓ Sample values: {', '.join(canonical_values[:5])}...")
        return True
        
    finally:
        db.close()


def test_schema_structure():
    """Test that schemas have the correct SCIM 2.0 structure."""
    print("\n🔍 Testing Schema Structure...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db)
        
        # Test User schema
        user_schema = schema_generator.get_user_schema()
        required_fields = ["schemas", "id", "name", "description", "attributes"]
        
        for field in required_fields:
            if field not in user_schema:
                print(f"  ❌ ERROR: User schema missing required field: {field}")
                return False
        
        print("  ✓ User schema has correct structure")
        
        # Test Group schema
        group_schema = schema_generator.get_group_schema()
        for field in required_fields:
            if field not in group_schema:
                print(f"  ❌ ERROR: Group schema missing required field: {field}")
                return False
        
        print("  ✓ Group schema has correct structure")
        
        # Test Entitlement schema
        entitlement_schema = schema_generator.get_entitlement_schema()
        for field in required_fields:
            if field not in entitlement_schema:
                print(f"  ❌ ERROR: Entitlement schema missing required field: {field}")
                return False
        
        print("  ✓ Entitlement schema has correct structure")
        
        return True
        
    finally:
        db.close()


def test_schema_by_urn():
    """Test that individual schemas can be retrieved by URN."""
    print("\n🔍 Testing Schema Retrieval by URN...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db)
        
        test_urns = [
            "urn:ietf:params:scim:schemas:core:2.0:User",
            "urn:ietf:params:scim:schemas:core:2.0:Group",
            "urn:okta:scim:schemas:core:1.0:Entitlement"
        ]
        
        for urn in test_urns:
            schema = schema_generator.get_schema_by_urn(urn)
            if not schema:
                print(f"  ❌ ERROR: Could not retrieve schema for URN: {urn}")
                return False
            print(f"  ✓ Retrieved schema for URN: {urn}")
        
        # Test non-existent URN
        non_existent_schema = schema_generator.get_schema_by_urn("urn:non:existent:schema")
        if non_existent_schema:
            print("  ❌ ERROR: Should return None for non-existent URN")
            return False
        print("  ✓ Correctly returns None for non-existent URN")
        
        return True
        
    finally:
        db.close()


def test_configuration_reflection():
    """Test that schema reflects current configuration values."""
    print("\n🔍 Testing Configuration Reflection...")
    
    # Test that entitlement types from enhanced definitions are reflected
    all_canonical_values = []
    for definition in settings.cli_entitlement_definitions:
        all_canonical_values.extend(definition["canonical_values"])
    unique_config_types = list(set(all_canonical_values))
    
    print(f"  ✓ Configuration has {len(unique_config_types)} unique entitlement types")
    print(f"  ✓ Sample config types: {', '.join(unique_config_types[:5])}...")
    
    # Verify the schema generator uses the same values
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db)
        entitlement_schema = schema_generator.get_entitlement_schema()
        
        # Find the type attribute
        type_attribute = None
        for attr in entitlement_schema["attributes"]:
            if attr["name"] == "type":
                type_attribute = attr
                break
        
        schema_canonical_values = type_attribute.get("canonicalValues", [])
        
        # Check that all config values are in schema
        missing_in_schema = []
        for config_type in unique_config_types:
            if config_type not in schema_canonical_values:
                missing_in_schema.append(config_type)
        
        if missing_in_schema:
            print(f"  ❌ ERROR: Configuration values missing from schema: {missing_in_schema}")
            return False
        
        print("  ✓ All configuration values reflected in schema")
        return True
        
    finally:
        db.close()


def main():
    """Run all tests."""
    print("🚀 Testing Dynamic SCIM Schema System")
    print("=" * 50)
    
    tests = [
        test_resource_types,
        test_entitlement_schema_canonical_values,
        test_schema_structure,
        test_schema_by_urn,
        test_configuration_reflection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"  ❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"  ❌ Test error: {test.__name__} - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Dynamic schema system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 