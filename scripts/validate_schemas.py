#!/usr/bin/env python3
"""
Schema validation script for SCIM.Cloud server.
Validates server responses against IETF SCIM schemas and Okta extensions.
"""

import sys
import os
import json
import argparse
import requests
from jsonschema import validate, ValidationError
from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_schema(schema_path):
    """Load a JSON schema from file."""
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load schema {schema_path}: {e}")
        return None

def validate_response(schema, response_data, resource_type):
    """Validate a response against a schema."""
    try:
        validate(instance=response_data, schema=schema)
        logger.info(f"✅ {resource_type} response is schema compliant")
        return True
    except ValidationError as e:
        logger.error(f"❌ {resource_type} response failed schema validation:")
        logger.error(f"   Path: {e.path}")
        logger.error(f"   Message: {e.message}")
        logger.error(f"   Schema path: {e.schema_path}")
        return False

def get_server_response(base_url, endpoint, api_key):
    """Get a response from the server."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(f"{base_url}{endpoint}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get {endpoint}: HTTP {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error getting {endpoint}: {e}")
        return None

def validate_user_responses(base_url, api_key):
    """Validate user responses."""
    logger.info("🔍 Validating User responses...")
    
    # Load user schema
    user_schema = load_schema("schemas/scim-user-schema.json")
    if not user_schema:
        return False
    
    # Get user list response
    users_response = get_server_response(base_url, "/v2/Users/", api_key)
    if not users_response or 'Resources' not in users_response:
        logger.error("Failed to get users response")
        return False
    
    # Validate each user
    all_valid = True
    for i, user in enumerate(users_response['Resources'][:3]):  # Test first 3 users
        logger.info(f"  Validating user {i+1}: {user.get('userName', 'Unknown')}")
        if not validate_response(user_schema, user, f"User {i+1}"):
            all_valid = False
    
    return all_valid

def validate_group_responses(base_url, api_key):
    """Validate group responses."""
    logger.info("🔍 Validating Group responses...")
    
    # Load group schema
    group_schema = load_schema("schemas/scim-group-schema.json")
    if not group_schema:
        return False
    
    # Get group list response
    groups_response = get_server_response(base_url, "/v2/Groups/", api_key)
    if not groups_response or 'Resources' not in groups_response:
        logger.error("Failed to get groups response")
        return False
    
    # Validate each group
    all_valid = True
    for i, group in enumerate(groups_response['Resources'][:3]):  # Test first 3 groups
        logger.info(f"  Validating group {i+1}: {group.get('displayName', 'Unknown')}")
        if not validate_response(group_schema, group, f"Group {i+1}"):
            all_valid = False
    
    return all_valid

def validate_entitlement_responses(base_url, api_key):
    """Validate entitlement responses."""
    logger.info("🔍 Validating Entitlement responses...")
    
    # Load entitlement schema
    entitlement_schema = load_schema("schemas/okta-entitlement-schema.json")
    if not entitlement_schema:
        return False
    
    # Get entitlement list response
    entitlements_response = get_server_response(base_url, "/v2/Entitlements/", api_key)
    if not entitlements_response or 'Resources' not in entitlements_response:
        logger.error("Failed to get entitlements response")
        return False
    
    # Validate each entitlement
    all_valid = True
    for i, entitlement in enumerate(entitlements_response['Resources'][:3]):  # Test first 3 entitlements
        logger.info(f"  Validating entitlement {i+1}: {entitlement.get('displayName', 'Unknown')}")
        if not validate_response(entitlement_schema, entitlement, f"Entitlement {i+1}"):
            all_valid = False
    
    return all_valid



def validate_list_responses(base_url, api_key):
    """Validate SCIM list response format."""
    logger.info("🔍 Validating SCIM List Response format...")
    
    # Define list response schema
    list_schema = {
        "type": "object",
        "properties": {
            "schemas": {
                "type": "array",
                "items": {"type": "string"},
                "contains": {"const": "urn:ietf:params:scim:api:messages:2.0:ListResponse"}
            },
            "totalResults": {"type": "integer"},
            "startIndex": {"type": "integer"},
            "itemsPerPage": {"type": "integer"},
            "Resources": {"type": "array"}
        },
        "required": ["schemas", "totalResults", "startIndex", "itemsPerPage", "Resources"]
    }
    
    # Test each endpoint
    endpoints = ["/v2/Users/", "/v2/Groups/", "/v2/Entitlements/"]
    all_valid = True
    
    for endpoint in endpoints:
        response = get_server_response(base_url, endpoint, api_key)
        if response:
            logger.info(f"  Validating list response for {endpoint}")
            if not validate_response(list_schema, response, f"List Response {endpoint}"):
                all_valid = False
        else:
            all_valid = False
    
    return all_valid

def validate_schema_files():
    """Validate that all schema files are valid JSON Schema."""
    logger.info("🔍 Validating schema files...")
    
    schema_files = [
        "schemas/scim-user-schema.json",
        "schemas/scim-group-schema.json", 
        "schemas/okta-entitlement-schema.json",
        "schemas/scim-schema-schema.json"
    ]
    
    all_valid = True
    for schema_file in schema_files:
        try:
            schema = load_schema(schema_file)
            if schema:
                # Basic JSON Schema validation
                if not isinstance(schema, dict):
                    logger.error(f"❌ {schema_file}: Schema must be an object")
                    all_valid = False
                elif "$schema" not in schema:
                    logger.warning(f"⚠️  {schema_file}: Missing $schema property")
                else:
                    logger.info(f"✅ {schema_file}: Valid JSON Schema")
            else:
                all_valid = False
        except Exception as e:
            logger.error(f"❌ {schema_file}: {e}")
            all_valid = False
    
    return all_valid

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate SCIM server responses against schemas")
    parser.add_argument("--url", default=None, help="Server base URL (defaults to config)")
    parser.add_argument("--api-key", default=None, help="API key for authentication (defaults to config)")
    parser.add_argument("--validate-schemas-only", action="store_true", help="Only validate schema files, don't test server")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    logger.info("🚀 Starting SCIM Schema Validation")
    
    # Validate schema files first
    if not validate_schema_files():
        logger.error("❌ Schema file validation failed")
        return False
    
    if args.validate_schemas_only:
        logger.info("✅ Schema files are valid")
        return True
    
    # Check if server is running
    try:
        health_response = requests.get(f"{args.url}/healthz")
        if health_response.status_code != 200:
            logger.error("❌ Server is not responding")
            return False
        logger.info("✅ Server is responding")
    except Exception as e:
        logger.error(f"❌ Cannot connect to server: {e}")
        return False
    
    # Use config values if none provided
    if args.url is None:
        from scim_server.config import settings
        args.url = f"http://{settings.host}:{settings.port}"
        logger.info(f"Using server URL from config: {args.url}")
    
    if args.api_key is None:
        from scim_server.config import settings
        args.api_key = settings.test_api_key
        logger.info(f"Using API key from config: {args.api_key}")
    
    # Run validations
    results = {
        "list_responses": validate_list_responses(args.url, args.api_key),
        "users": validate_user_responses(args.url, args.api_key),
        "groups": validate_group_responses(args.url, args.api_key),
        "entitlements": validate_entitlement_responses(args.url, args.api_key),

    }
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📋 SCIM Schema Validation Summary")
    logger.info("="*60)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name.replace('_', ' ').title()}")
        if not result:
            all_passed = False
    
    logger.info("="*60)
    if all_passed:
        logger.info("🎉 All schema validations passed! SCIM server is compliant.")
    else:
        logger.error("⚠️  Some schema validations failed. Review the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 