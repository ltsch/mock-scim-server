#!/usr/bin/env python3
"""
Test Enhanced SCIM Error Handling

This script tests that the enhanced error handling provides:
1. Detailed error messages with context
2. Helpful troubleshooting guidance
3. Proper error categorization
4. Developer-friendly response format
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


def test_required_field_error():
    """Test that required field errors provide detailed information."""
    print("🔍 Testing Required Field Error Handling...")
    
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
            error_detail = e.detail
            if isinstance(error_detail, dict):
                if (error_detail.get("error") == "SCIM_VALIDATION_ERROR" and
                    error_detail.get("type") == "required_field_missing" and
                    error_detail.get("field") == "userName" and
                    "help" in error_detail):
                    print("  ✓ Required field error provides detailed information")
                    print(f"    - Error type: {error_detail['type']}")
                    print(f"    - Field: {error_detail['field']}")
                    print(f"    - Help: {error_detail['help']}")
                else:
                    print(f"  ❌ ERROR: Unexpected error format: {error_detail}")
                    return False
            else:
                print(f"  ❌ ERROR: Error detail is not a dict: {error_detail}")
                return False
        
        return True
        
    finally:
        db.close()


def test_canonical_values_error():
    """Test that canonical values errors provide detailed information."""
    print("\n🔍 Testing Canonical Values Error Handling...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test Entitlement creation with invalid type
        entitlement_data = {
            "displayName": "Test Entitlement",
            "type": "InvalidType",
            "description": "Test description"
        }
        
        try:
            validator.validate_create_request("Entitlement", entitlement_data)
            print("  ❌ ERROR: Should have failed for invalid canonical value")
            return False
        except HTTPException as e:
            error_detail = e.detail
            if isinstance(error_detail, dict):
                if (error_detail.get("error") == "SCIM_VALIDATION_ERROR" and
                    error_detail.get("type") == "invalid_canonical_value" and
                    error_detail.get("field") == "type" and
                    error_detail.get("provided_value") == "InvalidType" and
                    "allowed_values" in error_detail and
                    "help" in error_detail):
                    print("  ✓ Canonical values error provides detailed information")
                    print(f"    - Error type: {error_detail['type']}")
                    print(f"    - Field: {error_detail['field']}")
                    print(f"    - Provided value: {error_detail['provided_value']}")
                    print(f"    - Allowed values count: {len(error_detail['allowed_values'])}")
                    print(f"    - Help: {error_detail['help']}")
                else:
                    print(f"  ❌ ERROR: Unexpected error format: {error_detail}")
                    return False
            else:
                print(f"  ❌ ERROR: Error detail is not a dict: {error_detail}")
                return False
        
        return True
        
    finally:
        db.close()


def test_type_validation_error():
    """Test that type validation errors provide detailed information."""
    print("\n🔍 Testing Type Validation Error Handling...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test User creation with wrong type for userName
        user_data = {
            "userName": 123,  # Should be string
            "displayName": "Test User"
        }
        
        try:
            validator.validate_create_request("User", user_data)
            print("  ❌ ERROR: Should have failed for wrong type")
            return False
        except HTTPException as e:
            error_detail = e.detail
            if isinstance(error_detail, dict):
                if (error_detail.get("error") == "SCIM_VALIDATION_ERROR" and
                    error_detail.get("type") == "type_mismatch" and
                    error_detail.get("field") == "userName" and
                    error_detail.get("expected_type") == "string" and
                    error_detail.get("provided_type") == "int" and
                    "help" in error_detail):
                    print("  ✓ Type validation error provides detailed information")
                    print(f"    - Error type: {error_detail['type']}")
                    print(f"    - Field: {error_detail['field']}")
                    print(f"    - Expected type: {error_detail['expected_type']}")
                    print(f"    - Provided type: {error_detail['provided_type']}")
                    print(f"    - Help: {error_detail['help']}")
                else:
                    print(f"  ❌ ERROR: Unexpected error format: {error_detail}")
                    return False
            else:
                print(f"  ❌ ERROR: Error detail is not a dict: {error_detail}")
                return False
        
        return True
        
    finally:
        db.close()


def test_mutability_error():
    """Test that mutability errors provide detailed information."""
    print("\n🔍 Testing Mutability Error Handling...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test PATCH operation on readOnly field
        existing_data = {
            "id": "existing-id-123",
            "userName": "existinguser@example.com",
            "displayName": "Existing User"
        }
        
        patch_operations = [
            {
                "op": "replace",
                "path": "/id",
                "value": "new-id-456"
            }
        ]
        
        try:
            validator.validate_patch_request("User", patch_operations, existing_data)
            print("  ❌ ERROR: Should have failed for readOnly field modification")
            return False
        except HTTPException as e:
            error_detail = e.detail
            if isinstance(error_detail, dict):
                if (error_detail.get("error") == "SCIM_VALIDATION_ERROR" and
                    error_detail.get("type") == "readonly_field_modification" and
                    error_detail.get("field") == "id" and
                    error_detail.get("operation") == "PATCH" and
                    "help" in error_detail):
                    print("  ✓ Mutability error provides detailed information")
                    print(f"    - Error type: {error_detail['type']}")
                    print(f"    - Field: {error_detail['field']}")
                    print(f"    - Operation: {error_detail['operation']}")
                    print(f"    - Help: {error_detail['help']}")
                else:
                    print(f"  ❌ ERROR: Unexpected error format: {error_detail}")
                    return False
            else:
                print(f"  ❌ ERROR: Error detail is not a dict: {error_detail}")
                return False
        
        return True
        
    finally:
        db.close()


def test_unknown_field_error():
    """Test that unknown field errors provide detailed information."""
    print("\n🔍 Testing Unknown Field Error Handling...")
    
    db = SessionLocal()
    try:
        schema_generator = DynamicSchemaGenerator(db, "test-server")
        validator = SchemaValidator(schema_generator)
        
        # Test PATCH operation with unknown field
        existing_data = {
            "userName": "existinguser@example.com",
            "displayName": "Existing User"
        }
        
        patch_operations = [
            {
                "op": "replace",
                "path": "/unknownField",
                "value": "some value"
            }
        ]
        
        try:
            validator.validate_patch_request("User", patch_operations, existing_data)
            print("  ❌ ERROR: Should have failed for unknown field")
            return False
        except HTTPException as e:
            error_detail = e.detail
            if isinstance(error_detail, dict):
                if (error_detail.get("error") == "SCIM_VALIDATION_ERROR" and
                    error_detail.get("type") == "unknown_field" and
                    error_detail.get("field") == "unknownField" and
                    error_detail.get("operation") == "PATCH" and
                    "help" in error_detail):
                    print("  ✓ Unknown field error provides detailed information")
                    print(f"    - Error type: {error_detail['type']}")
                    print(f"    - Field: {error_detail['field']}")
                    print(f"    - Operation: {error_detail['operation']}")
                    print(f"    - Help: {error_detail['help']}")
                else:
                    print(f"  ❌ ERROR: Unexpected error format: {error_detail}")
                    return False
            else:
                print(f"  ❌ ERROR: Error detail is not a dict: {error_detail}")
                return False
        
        return True
        
    finally:
        db.close()


def main():
    """Run all tests."""
    print("🚀 Testing Enhanced SCIM Error Handling")
    print("=" * 50)
    
    tests = [
        test_required_field_error,
        test_canonical_values_error,
        test_type_validation_error,
        test_mutability_error,
        test_unknown_field_error
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
        print("✅ All tests passed! Enhanced error handling is working correctly.")
        print("\n🎯 Key Features Verified:")
        print("  ✓ Detailed error categorization (type, field, operation)")
        print("  ✓ Helpful troubleshooting guidance")
        print("  ✓ Context-aware error messages")
        print("  ✓ Developer-friendly response format")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 