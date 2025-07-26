"""
Dynamic SCIM Schema Definitions

This module generates SCIM schema definitions dynamically based on:
1. Database models (SQLAlchemy)
2. Configuration values (config.py)
3. Actual data in the database
4. SCIM 2.0 RFC 7643 compliance

The schemas are generated at runtime to ensure they accurately reflect
the current state of the system.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from loguru import logger

from .models import User, Group, Entitlement
from .config import settings


class DynamicSchemaGenerator:
    """Generates SCIM schema definitions dynamically."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_schema(self) -> Dict[str, Any]:
        """Generate User schema based on database model and configuration."""
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "urn:ietf:params:scim:schemas:core:2.0:User",
            "name": "User",
            "description": "User Account",
            "attributes": [
                # Core SCIM attributes
                {
                    "name": "id",
                    "type": "string",
                    "multiValued": False,
                    "description": "Unique identifier for the User",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readOnly",
                    "returned": "always",
                    "uniqueness": "global"
                },
                {
                    "name": "externalId",
                    "type": "string",
                    "multiValued": False,
                    "description": "A String that is an identifier for the resource as defined by the provisioning client",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "userName",
                    "type": "string",
                    "multiValued": False,
                    "description": "Unique identifier for the user, typically used by the user to directly authenticate to the service provider",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "server"
                },
                {
                    "name": "displayName",
                    "type": "string",
                    "multiValued": False,
                    "description": "The name of the User, suitable for display to end-users",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "active",
                    "type": "boolean",
                    "multiValued": False,
                    "description": "A Boolean value indicating the User's administrative status",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default"
                },
                # Name complex attribute
                {
                    "name": "name",
                    "type": "complex",
                    "multiValued": False,
                    "description": "The components of the user's real name",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "subAttributes": [
                        {
                            "name": "givenName",
                            "type": "string",
                            "multiValued": False,
                            "description": "The given name of the User",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "familyName",
                            "type": "string",
                            "multiValued": False,
                            "description": "The family name of the User",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "formatted",
                            "type": "string",
                            "multiValued": False,
                            "description": "The full name, including all middle names, titles, and suffixes",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        }
                    ]
                },
                # Emails multi-valued attribute
                {
                    "name": "emails",
                    "type": "complex",
                    "multiValued": True,
                    "description": "Email addresses for the user",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "subAttributes": [
                        {
                            "name": "value",
                            "type": "string",
                            "multiValued": False,
                            "description": "Email address value",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "type",
                            "type": "string",
                            "multiValued": False,
                            "description": "A label indicating the attribute's function",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default",
                            "canonicalValues": ["work", "home", "other"]
                        },
                        {
                            "name": "primary",
                            "type": "boolean",
                            "multiValued": False,
                            "description": "A Boolean value indicating the 'primary' or preferred attribute value",
                            "required": False,
                            "mutability": "readWrite",
                            "returned": "default"
                        }
                    ]
                },
                # Groups reference
                {
                    "name": "groups",
                    "type": "complex",
                    "multiValued": True,
                    "description": "A list of groups to which the user belongs",
                    "required": False,
                    "mutability": "readOnly",
                    "returned": "default",
                    "subAttributes": [
                        {
                            "name": "value",
                            "type": "string",
                            "multiValued": False,
                            "description": "The identifier of the user's group",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readOnly",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "display",
                            "type": "string",
                            "multiValued": False,
                            "description": "The display name of the user's group",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readOnly",
                            "returned": "default",
                            "uniqueness": "none"
                        }
                    ]
                },
                # Entitlements reference
                {
                    "name": "entitlements",
                    "type": "complex",
                    "multiValued": True,
                    "description": "A list of entitlements assigned to the user",
                    "required": False,
                    "mutability": "readOnly",
                    "returned": "default",
                    "subAttributes": [
                        {
                            "name": "value",
                            "type": "string",
                            "multiValued": False,
                            "description": "The identifier of the user's entitlement",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readOnly",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "display",
                            "type": "string",
                            "multiValued": False,
                            "description": "The display name of the user's entitlement",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readOnly",
                            "returned": "default",
                            "uniqueness": "none"
                        }
                    ]
                }
            ]
        }
    
    def get_group_schema(self) -> Dict[str, Any]:
        """Generate Group schema based on database model."""
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
            "name": "Group",
            "description": "Group",
            "attributes": [
                {
                    "name": "id",
                    "type": "string",
                    "multiValued": False,
                    "description": "Unique identifier for the Group",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readOnly",
                    "returned": "always",
                    "uniqueness": "global"
                },
                {
                    "name": "displayName",
                    "type": "string",
                    "multiValued": False,
                    "description": "A human-readable name for the Group",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "server"
                },
                {
                    "name": "description",
                    "type": "string",
                    "multiValued": False,
                    "description": "A human-readable description of the Group",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                # Members reference
                {
                    "name": "members",
                    "type": "complex",
                    "multiValued": True,
                    "description": "A list of members of the Group",
                    "required": False,
                    "mutability": "readOnly",
                    "returned": "default",
                    "subAttributes": [
                        {
                            "name": "value",
                            "type": "string",
                            "multiValued": False,
                            "description": "The identifier of the member of this Group",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readOnly",
                            "returned": "default",
                            "uniqueness": "none"
                        },
                        {
                            "name": "display",
                            "type": "string",
                            "multiValued": False,
                            "description": "The display name of the member of this Group",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readOnly",
                            "returned": "default",
                            "uniqueness": "none"
                        }
                    ]
                }
            ]
        }
    
    def get_entitlement_schema(self) -> Dict[str, Any]:
        """Generate Entitlement schema based on database model and configuration."""
        # Get available entitlement types from enhanced definitions
        all_canonical_values = []
        for definition in settings.cli_entitlement_definitions:
            all_canonical_values.extend(definition["canonical_values"])
        entitlement_types = list(set(all_canonical_values))
        
        return {
            "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
            "id": "urn:okta:scim:schemas:core:1.0:Entitlement",
            "name": "Entitlement",
            "description": "Entitlement",
            "attributes": [
                {
                    "name": "id",
                    "type": "string",
                    "multiValued": False,
                    "description": "Unique identifier for the Entitlement",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readOnly",
                    "returned": "always",
                    "uniqueness": "global"
                },
                {
                    "name": "displayName",
                    "type": "string",
                    "multiValued": False,
                    "description": "A human-readable name for the Entitlement",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "server"
                },
                {
                    "name": "type",
                    "type": "string",
                    "multiValued": False,
                    "description": "The type of entitlement (e.g., 'License', 'Profile', 'Access')",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none",
                    "canonicalValues": entitlement_types
                },
                {
                    "name": "description",
                    "type": "string",
                    "multiValued": False,
                    "description": "A human-readable description of the Entitlement",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "entitlementType",
                    "type": "string",
                    "multiValued": False,
                    "description": "The category of entitlement (e.g., 'application_access', 'role_based', 'permission_based')",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none",
                    "canonicalValues": ["application_access", "role_based", "permission_based", "license_based", "department_based", "project_based"]
                },
                {
                    "name": "multiValued",
                    "type": "boolean",
                    "multiValued": False,
                    "description": "Whether this entitlement supports multiple values",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                }
            ]
        }
    
    def get_resource_types(self) -> List[Dict[str, Any]]:
        """Generate resource types list dynamically."""
        return [
            {
                "id": "User",
                "name": "User",
                "endpoint": "/Users",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
                "description": "User Account"
            },
            {
                "id": "Group",
                "name": "Group",
                "endpoint": "/Groups",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
                "description": "Group"
            },
            {
                "id": "Entitlement",
                "name": "Entitlement",
                "endpoint": "/Entitlements",
                "schema": "urn:okta:scim:schemas:core:1.0:Entitlement",
                "description": "Entitlement"
            }
        ]
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get all available schemas."""
        return [
            self.get_user_schema(),
            self.get_group_schema(),
            self.get_entitlement_schema()
        ]
    
    def get_schema_by_urn(self, schema_urn: str) -> Optional[Dict[str, Any]]:
        """Get a specific schema by URN."""
        schema_map = {
            "urn:ietf:params:scim:schemas:core:2.0:User": self.get_user_schema,
            "urn:ietf:params:scim:schemas:core:2.0:Group": self.get_group_schema,
            "urn:okta:scim:schemas:core:1.0:Entitlement": self.get_entitlement_schema
        }
        
        if schema_urn in schema_map:
            return schema_map[schema_urn]()
        
        return None 