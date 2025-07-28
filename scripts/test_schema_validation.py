#!/usr/bin/env python3
"""
Test SCIM Schema Validation System

This script tests that the schema validation system correctly:
1. Enforces required fields
2. Validates canonical values
3. Enforces mutability rules
4. Handles type validation
5. Manages multi-valued attributes
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scim_server.database import SessionLocal
from scim_server.schema_definitions import DynamicSchemaGenerator
from scim_server.schema_validator import SchemaValidator
from fastapi import HTTPException


def test_required_fields_validation():
    """Test that required fields are properly validated."""
    print("🔍 Testing Required Fields Validation...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test User creation with missing required userName
        user_data = {
            "displayName": "Test User",
            "active": True
        }
        
        try:
            validator.validate_create_request("User", user_data)
            print("  ❌ ERROR: Should have failed for missing required userName")
            return False
        except HTTPException as e:
            if "Required field 'userName' is missing" in str(e.detail):
                print("  ✓ Correctly rejected missing required userName")
            else:
                print(f"  ❌ ERROR: Unexpected error: {e.detail}")
                return False
        
        # Test User creation with required userName
        user_data_with_username = {
            "userName": "testuser@example.com",
            "displayName": "Test User",
            "active": True
        }
        
        try:
            validated_data = validator.validate_create_request("User", user_data_with_username)
            if "userName" in validated_data:
                print("  ✓ Correctly accepted user with required userName")
            else:
                print("  ❌ ERROR: userName not in validated data")
                return False
        except HTTPException as e:
            print(f"  ❌ ERROR: Unexpected error: {e.detail}")
            return False
        
        return True
        
    finally:
        db.close()


def test_canonical_values_validation():
    """Test that canonical values are properly validated."""
    print("\n🔍 Testing Canonical Values Validation...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test Entitlement creation with invalid type
        entitlement_data = {
            "displayName": "Test Entitlement",
            "type": "InvalidType",  # This should not be in canonical values
            "description": "Test description"
        }
        
        try:
            validator.validate_create_request("Entitlement", entitlement_data)
            print("  ❌ ERROR: Should have failed for invalid canonical value")
            return False
        except HTTPException as e:
            if "is not valid" in str(e.detail) and "InvalidType" in str(e.detail):
                print("  ✓ Correctly rejected invalid canonical value")
            else:
                print(f"  ❌ ERROR: Unexpected error: {e.detail}")
                return False
        
        # Test Entitlement creation with valid type
        valid_entitlement_data = {
            "displayName": "Test Entitlement",
            "type": "Administrator",  # This should be in canonical values
            "description": "Test description"
        }
        
        try:
            validated_data = validator.validate_create_request("Entitlement", valid_entitlement_data)
            if validated_data["type"] == "Administrator":
                print("  ✓ Correctly accepted valid canonical value")
            else:
                print("  ❌ ERROR: Valid type not preserved in validated data")
                return False
        except HTTPException as e:
            print(f"  ❌ ERROR: Unexpected error: {e.detail}")
            return False
        
        return True
        
    finally:
        db.close()


def test_mutability_validation():
    """Test that mutability rules are properly enforced."""
    print("\n🔍 Testing Mutability Validation...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test that readOnly fields are not included in create requests
        user_data_with_id = {
            "id": "test-id-123",  # This should be readOnly and ignored
            "userName": "testuser@example.com",
            "displayName": "Test User"
        }
        
        try:
            validated_data = validator.validate_create_request("User", user_data_with_id)
            if "id" not in validated_data:
                print("  ✓ Correctly excluded readOnly field from create request")
            else:
                print("  ❌ ERROR: readOnly field should not be in validated data")
                return False
        except HTTPException as e:
            print(f"  ❌ ERROR: Unexpected error: {e.detail}")
            return False
        
        # Test that readOnly fields are preserved in update requests
        existing_user_data = {
            "id": "existing-id-123",
            "userName": "existinguser@example.com",
            "displayName": "Existing User"
        }
        
        update_data = {
            "displayName": "Updated User"
        }
        
        try:
            validated_data = validator.validate_update_request("User", update_data, existing_user_data)
            if validated_data["id"] == "existing-id-123" and validated_data["displayName"] == "Updated User":
                print("  ✓ Correctly preserved readOnly field and updated mutable field")
            else:
                print("  ❌ ERROR: Update validation failed")
                return False
        except HTTPException as e:
            print(f"  ❌ ERROR: Unexpected error: {e.detail}")
            return False
        
        return True
        
    finally:
        db.close()


def test_type_validation():
    """Test that type validation works correctly."""
    print("\n🔍 Testing Type Validation...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test string field with wrong type
        user_data_wrong_type = {
            "userName": 123,  # Should be string
            "displayName": "Test User"
        }
        
        try:
            validator.validate_create_request("User", user_data_wrong_type)
            print("  ❌ ERROR: Should have failed for wrong type")
            return False
        except HTTPException as e:
            if "must be a string" in str(e.detail):
                print("  ✓ Correctly rejected wrong type for string field")
            else:
                print(f"  ❌ ERROR: Unexpected error: {e.detail}")
                return False
        
        # Test boolean field with wrong type
        user_data_wrong_bool = {
            "userName": "testuser@example.com",
            "active": "not a boolean"  # Should be boolean
        }
        
        try:
            validator.validate_create_request("User", user_data_wrong_bool)
            print("  ❌ ERROR: Should have failed for wrong boolean type")
            return False
        except HTTPException as e:
            if "must be a boolean" in str(e.detail):
                print("  ✓ Correctly rejected wrong type for boolean field")
            else:
                print(f"  ❌ ERROR: Unexpected error: {e.detail}")
                return False
        
        # Test correct types
        user_data_correct_types = {
            "userName": "testuser@example.com",
            "displayName": "Test User",
            "active": True
        }
        
        try:
            validated_data = validator.validate_create_request("User", user_data_correct_types)
            if (isinstance(validated_data["userName"], str) and 
                isinstance(validated_data["displayName"], str) and 
                isinstance(validated_data["active"], bool)):
                print("  ✓ Correctly accepted proper types")
            else:
                print("  ❌ ERROR: Types not preserved correctly")
                return False
        except HTTPException as e:
            print(f"  ❌ ERROR: Unexpected error: {e.detail}")
            return False
        
        return True
        
    finally:
        db.close()


def test_multi_valued_attributes():
    """Test that multi-valued attributes are handled correctly."""
    print("\n🔍 Testing Multi-Valued Attributes...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test emails (multi-valued) with single value
        user_data_single_email = {
            "userName": "testuser@example.com",
            "emails": {"value": "test@example.com", "type": "work", "primary": True}
        }
        
        try:
            validated_data = validator.validate_create_request("User", user_data_single_email)
            if isinstance(validated_data["emails"], list) and len(validated_data["emails"]) == 1:
                print("  ✓ Correctly converted single email to list")
            else:
                print("  ❌ ERROR: Single email not converted to list correctly")
                return False
        except HTTPException as e:
            print(f"  ❌ ERROR: Unexpected error: {e.detail}")
            return False
        
        # Test emails with multiple values
        user_data_multiple_emails = {
            "userName": "testuser@example.com",
            "emails": [
                {"value": "work@example.com", "type": "work", "primary": True},
                {"value": "personal@example.com", "type": "home", "primary": False}
            ]
        }
        
        try:
            validated_data = validator.validate_create_request("User", user_data_multiple_emails)
            if isinstance(validated_data["emails"], list) and len(validated_data["emails"]) == 2:
                print("  ✓ Correctly handled multiple emails")
            else:
                print("  ❌ ERROR: Multiple emails not handled correctly")
                return False
        except HTTPException as e:
            print(f"  ❌ ERROR: Unexpected error: {e.detail}")
            return False
        
        return True
        
    finally:
        db.close()


def main():
    """Run all tests."""
    print("🚀 Testing SCIM Schema Validation System")
    print("=" * 50)
    
    tests = [
        test_required_fields_validation,
        test_canonical_values_validation,
        test_mutability_validation,
        test_type_validation,
        test_multi_valued_attributes
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
        print("✅ All tests passed! Schema validation system is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 