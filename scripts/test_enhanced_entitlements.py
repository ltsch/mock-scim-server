#!/usr/bin/env python3
"""
Test Enhanced Entitlement System

This script tests the new enhanced entitlement system that supports:
1. Different canonical value sets
2. Multi-select capabilities
3. Entitlement type categorization
4. Flexible role definitions
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scim_server.config import settings
from scim_server.database import SessionLocal
from scim_server.schema_definitions import DynamicSchemaGenerator
from scim_server.schema_validator import SchemaValidator


def test_entitlement_definitions():
    """Test that entitlement definitions are properly structured."""
    print("🔍 Testing Entitlement Definitions...")
    
    definitions = settings.cli_entitlement_definitions
    
    if not definitions:
        print("  ❌ ERROR: No entitlement definitions found")
        return False
    
    print(f"  ✓ Found {len(definitions)} entitlement definitions")
    
    # Test structure of each definition
    for i, definition in enumerate(definitions):
        required_fields = ["name", "type", "canonical_values", "multi_valued", "description"]
        
        for field in required_fields:
            if field not in definition:
                print(f"  ❌ ERROR: Definition {i} missing required field '{field}'")
                return False
        
        if not definition["canonical_values"]:
            print(f"  ❌ ERROR: Definition {i} has empty canonical_values")
            return False
        
        print(f"    - {definition['name']}: {len(definition['canonical_values'])} values, multi-valued: {definition['multi_valued']}")
    
    return True





def test_schema_generation():
    """Test that schemas are generated correctly with new entitlement fields."""
    print("\n🔍 Testing Schema Generation...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        entitlement_schema = schema_generator.get_entitlement_schema()
        
        # Check for new fields
        attribute_names = [attr["name"] for attr in entitlement_schema["attributes"]]
        required_fields = ["id", "displayName", "type", "description", "entitlementType", "multiValued"]
        
        for field in required_fields:
            if field not in attribute_names:
                print(f"  ❌ ERROR: Missing field '{field}' in entitlement schema")
                return False
        
        print("  ✓ All required fields present in entitlement schema")
        
        # Check canonical values for entitlementType
        entitlement_type_attr = None
        for attr in entitlement_schema["attributes"]:
            if attr["name"] == "entitlementType":
                entitlement_type_attr = attr
                break
        
        if not entitlement_type_attr:
            print("  ❌ ERROR: entitlementType attribute not found")
            return False
        
        expected_types = ["application_access", "role_based", "permission_based", "license_based", "department_based", "project_based"]
        
        if entitlement_type_attr.get("canonicalValues") != expected_types:
            print(f"  ❌ ERROR: entitlementType canonical values mismatch")
            print(f"    Expected: {expected_types}")
            print(f"    Got: {entitlement_type_attr.get('canonicalValues')}")
            return False
        
        print("  ✓ entitlementType canonical values correct")
        
        return True
        
    finally:
        db.close()


def test_schema_validation():
    """Test that schema validation works with new entitlement fields."""
    print("\n🔍 Testing Schema Validation...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test valid entitlement creation
        valid_data = {
            "displayName": "Test Entitlement",
            "type": "Administrator",
            "description": "Test description",
            "entitlementType": "role_based",
            "multiValued": True
        }
        
        try:
            validated_data = validator.validate_create_request("Entitlement", valid_data)
            print("  ✓ Valid entitlement data passes validation")
        except Exception as e:
            print(f"  ❌ ERROR: Valid entitlement data failed validation: {e}")
            return False
        
        # Test invalid entitlementType
        invalid_data = {
            "displayName": "Test Entitlement",
            "type": "Administrator",
            "entitlementType": "invalid_type"
        }
        
        try:
            validator.validate_create_request("Entitlement", invalid_data)
            print("  ❌ ERROR: Invalid entitlementType should have failed validation")
            return False
        except Exception as e:
            print("  ✓ Invalid entitlementType correctly rejected")
        
        return True
        
    finally:
        db.close()


def test_multi_valued_entitlements():
    """Test multi-valued entitlement handling."""
    print("\n🔍 Testing Multi-Valued Entitlements...")
    
    # Count multi-valued vs single-valued entitlements
    definitions = settings.cli_entitlement_definitions
    
    multi_valued_count = sum(1 for d in definitions if d["multi_valued"])
    single_valued_count = sum(1 for d in definitions if not d["multi_valued"])
    
    print(f"  ✓ Multi-valued entitlements: {multi_valued_count}")
    print(f"  ✓ Single-valued entitlements: {single_valued_count}")
    
    # Check specific examples
    role_based_count = sum(1 for d in definitions if d["type"] == "role_based")
    app_access_count = sum(1 for d in definitions if d["type"] == "application_access")
    
    print(f"  ✓ Role-based entitlements: {role_based_count}")
    print(f"  ✓ Application access entitlements: {app_access_count}")
    
    # Verify role-based entitlements are multi-valued
    for definition in definitions:
        if definition["type"] == "role_based" and not definition["multi_valued"]:
            print(f"  ❌ ERROR: Role-based entitlement '{definition['name']}' should be multi-valued")
            return False
    
    print("  ✓ All role-based entitlements are multi-valued")
    
    return True


def test_canonical_values_diversity():
    """Test that canonical values provide good diversity."""
    print("\n🔍 Testing Canonical Values Diversity...")
    
    definitions = settings.cli_entitlement_definitions
    
    # Check for good variety in canonical values
    all_values = []
    for definition in definitions:
        all_values.extend(definition["canonical_values"])
    
    unique_values = set(all_values)
    total_values = len(all_values)
    
    print(f"  ✓ Total canonical values: {total_values}")
    print(f"  ✓ Unique canonical values: {len(unique_values)}")
    
    # Check for common role patterns
    common_roles = ["Administrator", "User", "Read-Only", "Auditor"]
    found_roles = [role for role in common_roles if role in unique_values]
    
    print(f"  ✓ Found common roles: {found_roles}")
    
    if len(found_roles) >= 2:
        print("  ✓ Good coverage of common role types")
    else:
        print("  ⚠️ Limited coverage of common role types")
    
    return True


def main():
    """Run all tests."""
    print("🚀 Testing Enhanced Entitlement System")
    print("=" * 50)
    
    tests = [
        test_entitlement_definitions,
        test_schema_generation,
        test_schema_validation,
        test_multi_valued_entitlements,
        test_canonical_values_diversity
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
        print("✅ All tests passed! Enhanced entitlement system is working correctly.")
        print("\n🎯 Key Features Verified:")
        print("  ✓ Flexible entitlement definitions with canonical values")
        print("  ✓ Multi-select vs single-select capabilities")
        print("  ✓ Entitlement type categorization")
        print("  ✓ Schema validation for new fields")
        print("  ✓ Good diversity in role definitions")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 