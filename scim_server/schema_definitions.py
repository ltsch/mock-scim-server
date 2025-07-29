"""
Dynamic SCIM Schema Definitions

This module generates SCIM schema definitions dynamically based on:
1. Database models (SQLAlchemy)
2. Server-specific configuration (server_config.py)
3. Actual data in the database
4. SCIM 2.0 RFC 7643 compliance

The schemas are generated at runtime to ensure they accurately reflect
the current state of the system and each server's unique configuration.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from loguru import logger

from .models import User, Group, Entitlement
from .config import settings
from .server_config import get_server_config_manager


class DynamicSchemaGenerator:
    """Generates SCIM schema definitions dynamically based on server configuration."""
    
    def __init__(self, db: Session, server_id: str):
        self.db = db
        self.server_id = server_id
        self.server_config = get_server_config_manager(db).get_server_config(server_id)
    
    def get_user_schema(self) -> Dict[str, Any]:
        """Generate User schema based on server-specific configuration."""
        user_attrs = self.server_config.get("user_attributes", {})
        required_attrs = user_attrs.get("required_attributes", ["userName"])
        optional_attrs = user_attrs.get("optional_attributes", ["displayName", "emails", "name", "active"])
        complex_attrs = user_attrs.get("complex_attributes", {})
        
        attributes = []
        
        # Core SCIM attributes - including required 'schemas' field per RFC 7643 §3.1
        attributes.extend([
            {
                "name": "schemas",
                "type": "string",
                "multiValued": True,
                "description": "URIs of schemas used to define the attributes of the current resource",
                "required": True,
                "caseExact": False,
                "mutability": "readWrite",
                "returned": "default",
                "uniqueness": "none"
            },
            {
                "name": "id",
                "type": "string",
                "multiValued": False,
                "description": "Unique identifier for the User",
                "required": False,  # Not required for CREATE operations (readOnly)
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
            }
        ])
        
        # Server-specific required attributes
        for attr_name in required_attrs:
            if attr_name == "userName":
                attributes.append({
                    "name": "userName",
                    "type": "string",
                    "multiValued": False,
                    "description": "Unique identifier for the user, typically used by the user to directly authenticate to the service provider",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "server"
                })
            elif attr_name == "displayName":
                attributes.append({
                    "name": "displayName",
                    "type": "string",
                    "multiValued": False,
                    "description": "The name of the User, suitable for display to end-users",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                })
        
        # Server-specific optional attributes
        for attr_name in optional_attrs:
            if attr_name == "displayName" and "displayName" not in required_attrs:
                attributes.append({
                    "name": "displayName",
                    "type": "string",
                    "multiValued": False,
                    "description": "The name of the User, suitable for display to end-users",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                })
            elif attr_name == "active":
                attributes.append({
                    "name": "active",
                    "type": "boolean",
                    "multiValued": False,
                    "description": "A Boolean value indicating the User's administrative status",
                    "required": False,
                    "mutability": "readWrite",
                    "returned": "default"
                })
        
        # Server-specific complex attributes
        for attr_name, attr_config in complex_attrs.items():
            if attr_name == "emails":
                attributes.append({
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
                            "required": True,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default"
                        },
                        {
                            "name": "primary",
                            "type": "boolean",
                            "multiValued": False,
                            "description": "A Boolean value indicating the 'primary' or preferred attribute value for this attribute",
                            "required": False,
                            "mutability": "readWrite",
                            "returned": "default"
                        }
                    ]
                })
            elif attr_name == "name":
                attributes.append({
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
                            "returned": "default"
                        },
                        {
                            "name": "familyName",
                            "type": "string",
                            "multiValued": False,
                            "description": "The family name of the User",
                            "required": False,
                            "caseExact": False,
                            "mutability": "readWrite",
                            "returned": "default"
                        }
                    ]
                })
        
        # Server-specific custom attributes
        custom_attrs = user_attrs.get("custom_attributes", {})
        for attr_name, attr_config in custom_attrs.items():
            attributes.append(attr_config)
        
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "urn:ietf:params:scim:schemas:core:2.0:User",
            "name": "User",
            "description": "User Account",
            "attributes": attributes
        }
    
    def get_group_schema(self) -> Dict[str, Any]:
        """Generate Group schema based on server-specific configuration."""
        group_attrs = self.server_config.get("group_attributes", {})
        required_attrs = group_attrs.get("required_attributes", ["displayName"])
        optional_attrs = group_attrs.get("optional_attributes", ["description"])
        complex_attrs = group_attrs.get("complex_attributes", {})
        
        attributes = []
        
        # Core SCIM attributes - including required 'schemas' field per RFC 7643 §3.1
        attributes.extend([
            {
                "name": "schemas",
                "type": "string",
                "multiValued": True,
                "description": "URIs of schemas used to define the attributes of the current resource",
                "required": True,
                "caseExact": False,
                "mutability": "readWrite",
                "returned": "default",
                "uniqueness": "none"
            },
            {
                "name": "id",
                "type": "string",
                "multiValued": False,
                "description": "Unique identifier for the Group",
                "required": False,  # Not required for CREATE operations (readOnly)
                "caseExact": False,
                "mutability": "readOnly",
                "returned": "always",
                "uniqueness": "global"
            }
        ])
        
        # Server-specific required attributes
        for attr_name in required_attrs:
            if attr_name == "displayName":
                attributes.append({
                    "name": "displayName",
                    "type": "string",
                    "multiValued": False,
                    "description": "A human-readable name for the Group",
                    "required": True,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default",
                    "uniqueness": "none"
                })
        
        # Server-specific optional attributes
        for attr_name in optional_attrs:
            if attr_name == "description":
                attributes.append({
                    "name": "description",
                    "type": "string",
                    "multiValued": False,
                    "description": "A human-readable description of the Group",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readWrite",
                    "returned": "default"
                })
        
        # Server-specific complex attributes
        for attr_name, attr_config in complex_attrs.items():
            attributes.append(attr_config)
        
        # Add members attribute for group membership
        attributes.append({
            "name": "members",
            "type": "complex",
            "multiValued": True,
            "description": "A list of members of the Group",
            "required": False,
            "caseExact": False,
            "mutability": "readWrite",
            "returned": "default",
            "subAttributes": [
                {
                    "name": "value",
                    "type": "string",
                    "multiValued": False,
                    "description": "Identifier of the member of this Group",
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
                    "description": "A human-readable name for the member",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readOnly",
                    "returned": "default",
                    "uniqueness": "none"
                },
                {
                    "name": "$ref",
                    "type": "reference",
                    "multiValued": False,
                    "description": "The URI of the corresponding resource",
                    "required": False,
                    "caseExact": False,
                    "mutability": "readOnly",
                    "returned": "default",
                    "uniqueness": "none"
                }
            ]
        })
        
        # Server-specific custom attributes
        custom_attrs = group_attrs.get("custom_attributes", {})
        for attr_name, attr_config in custom_attrs.items():
            attributes.append(attr_config)
        
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
            "name": "Group",
            "description": "Group",
            "attributes": attributes
        }
    
    def get_entitlement_schema(self) -> Dict[str, Any]:
        """Generate Entitlement schema based on server-specific configuration."""
        entitlement_types = self.server_config.get("entitlement_types", [])
        
        # Generate canonical values from server-specific entitlement types
        canonical_values = []
        for entitlement in entitlement_types:
            canonical_values.extend(entitlement.get("canonical_values", []))
        
        attributes = [
            {
                "name": "schemas",
                "type": "string",
                "multiValued": True,
                "description": "URIs of schemas used to define the attributes of the current resource",
                "required": True,
                "caseExact": False,
                "mutability": "readWrite",
                "returned": "default",
                "uniqueness": "none"
            },
            {
                "name": "id",
                "type": "string",
                "multiValued": False,
                "description": "Unique identifier for the Entitlement",
                "required": False,  # Not required for CREATE operations (readOnly)
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
                "uniqueness": "none"
            },
            {
                "name": "type",
                "type": "string",
                "multiValued": False,
                "description": "The type of entitlement",
                "required": True,
                "caseExact": False,
                "mutability": "readWrite",
                "returned": "default",
                "uniqueness": "none",
                "canonicalValues": canonical_values
            },
            {
                "name": "description",
                "type": "string",
                "multiValued": False,
                "description": "A human-readable description of the Entitlement",
                "required": False,
                "caseExact": False,
                "mutability": "readWrite",
                "returned": "default"
            }
        ]
        
        return {
            "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
            "id": "urn:okta:scim:schemas:core:1.0:Entitlement",
            "name": "Entitlement",
            "description": "Entitlement",
            "attributes": attributes
        }
    
    def get_resource_types(self) -> List[Dict[str, Any]]:
        """Get resource types based on server-specific enabled types."""
        enabled_types = self.server_config.get("enabled_resource_types", ["User", "Group", "Entitlement"])
        
        resource_types = []
        
        if "User" in enabled_types:
            resource_types.append({
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": "User",
                "name": "User",
                "description": "User Account",
                "endpoint": "/Users",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
            })
        
        if "Group" in enabled_types:
            resource_types.append({
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                "id": "Group",
                "name": "Group",
                "description": "Group",
                "endpoint": "/Groups",
                "schema": "urn:ietf:params:scim:schemas:core:2.0:Group"
            })
        
        if "Entitlement" in enabled_types:
            resource_types.append({
                "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
                "id": "Entitlement",
                "name": "Entitlement",
                "description": "Entitlement",
                "endpoint": "/Entitlements",
                "schema": "urn:okta:scim:schemas:core:1.0:Entitlement"
            })
        
        return resource_types
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get all schemas based on server-specific enabled types."""
        enabled_types = self.server_config.get("enabled_resource_types", ["User", "Group", "Entitlement"])
        
        schemas = []
        
        if "User" in enabled_types:
            schemas.append(self.get_user_schema())
        
        if "Group" in enabled_types:
            schemas.append(self.get_group_schema())
        
        if "Entitlement" in enabled_types:
            schemas.append(self.get_entitlement_schema())
        
        return schemas
    
    def get_schema_by_urn(self, schema_urn: str) -> Optional[Dict[str, Any]]:
        """Get schema by URN based on server-specific configuration."""
        if schema_urn == "urn:ietf:params:scim:schemas:core:2.0:User":
            return self.get_user_schema()
        elif schema_urn == "urn:ietf:params:scim:schemas:core:2.0:Group":
            return self.get_group_schema()
        elif schema_urn == "urn:okta:scim:schemas:core:1.0:Entitlement":
            return self.get_entitlement_schema()
        else:
            # Check for custom schemas in server configuration
            schema_extensions = self.server_config.get("schema_extensions", {})
            if schema_urn in schema_extensions:
                return schema_extensions[schema_urn]
        
        return None 