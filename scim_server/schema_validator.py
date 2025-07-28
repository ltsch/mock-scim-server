"""
SCIM Schema Validator

This module provides comprehensive SCIM schema validation that is dynamic based on
server-specific configurations. Each server ID can have unique attributes and validation rules.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from loguru import logger

from .schema_definitions import DynamicSchemaGenerator
from .server_config import get_server_config_manager


class SchemaValidator:
    """Validates SCIM data against server-specific schemas."""
    
    def __init__(self, schema_generator: DynamicSchemaGenerator):
        self.schema_generator = schema_generator
        self.server_id = schema_generator.server_id
        self.server_config = get_server_config_manager(schema_generator.db).get_server_config(self.server_id)
        self.validation_rules = self.server_config.get("validation_rules", {})
    
    def get_schema(self, resource_type: str) -> Dict[str, Any]:
        """Get server-specific schema for a resource type."""
        schema_map = {
            "User": self.schema_generator.get_user_schema,
            "Group": self.schema_generator.get_group_schema,
            "Entitlement": self.schema_generator.get_entitlement_schema
        }
        
        if resource_type in schema_map:
            return schema_map[resource_type]()
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": "SCIM_VALIDATION_ERROR",
                "message": f"Unknown resource type '{resource_type}'",
                "resource_type": resource_type,
                "server_id": self.server_id,
                "help": f"Resource type '{resource_type}' is not supported by this server."
            }
        )
    
    def validate_create_request(self, resource_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a CREATE request against the server-specific schema.
        Returns cleaned/validated data.
        """
        schema = self.get_schema(resource_type)
        validated_data = {}
        
        # Create attribute lookup for quick access
        attr_lookup = {attr["name"]: attr for attr in schema["attributes"]}
        
        # Check if unknown attributes are allowed
        allow_unknown = self.validation_rules.get("allow_unknown_attributes", False)
        
        for field_name, field_value in data.items():
            if field_name in attr_lookup:
                attr = attr_lookup[field_name]
                validated_value = self._validate_attribute(attr, field_value, resource_type)
                validated_data[field_name] = validated_value
            elif not allow_unknown:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "SCIM_VALIDATION_ERROR",
                        "message": f"Unknown field '{field_name}'",
                        "field": field_name,
                        "resource_type": resource_type,
                        "server_id": self.server_id,
                        "type": "unknown_field",
                        "help": f"The field '{field_name}' does not exist in the {resource_type} schema for this server."
                    }
                )
            # If allow_unknown is True, skip unknown fields
        
        # Validate required fields
        if self.validation_rules.get("validate_required_fields", True):
            self._validate_required_fields(schema, validated_data, resource_type, "create")
        
        return validated_data
    
    def validate_update_request(self, resource_type: str, data: Dict[str, Any], existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an UPDATE request against the server-specific schema.
        Returns cleaned/validated data after merging with existing data.
        """
        schema = self.get_schema(resource_type)
        validated_data = existing_data.copy()
        
        # Create attribute lookup for quick access
        attr_lookup = {attr["name"]: attr for attr in schema["attributes"]}
        
        # Check if unknown attributes are allowed
        allow_unknown = self.validation_rules.get("allow_unknown_attributes", False)
        
        for field_name, field_value in data.items():
            if field_name in attr_lookup:
                attr = attr_lookup[field_name]
                if attr.get("mutability") != "readOnly":
                    validated_value = self._validate_attribute(attr, field_value, resource_type)
                    validated_data[field_name] = validated_value
                else:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "SCIM_VALIDATION_ERROR",
                            "message": f"Cannot modify readOnly field '{field_name}'",
                            "field": field_name,
                            "resource_type": resource_type,
                            "server_id": self.server_id,
                            "type": "readonly_field_modification",
                            "help": f"The field '{field_name}' is read-only and cannot be modified."
                        }
                    )
            elif not allow_unknown:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "SCIM_VALIDATION_ERROR",
                        "message": f"Unknown field '{field_name}'",
                        "field": field_name,
                        "resource_type": resource_type,
                        "server_id": self.server_id,
                        "type": "unknown_field",
                        "help": f"The field '{field_name}' does not exist in the {resource_type} schema for this server."
                    }
                )
        
        return validated_data
    
    def validate_patch_request(self, resource_type: str, operations: List[Dict[str, Any]], existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a PATCH request against the server-specific schema.
        Returns cleaned/validated data after applying patches.
        """
        schema = self.get_schema(resource_type)
        validated_data = existing_data.copy()
        
        # Create attribute lookup for quick access
        attr_lookup = {attr["name"]: attr for attr in schema["attributes"]}
        
        for operation in operations:
            op = operation.get("op", "replace")
            path = operation.get("path")
            value = operation.get("value")
            
            if op == "replace":
                if path:
                    # Single attribute replacement
                    attr_name = path.lstrip("/")
                    if attr_name in attr_lookup:
                        attr = attr_lookup[attr_name]
                        if attr.get("mutability") != "readOnly":
                            validated_value = self._validate_attribute(attr, value, resource_type)
                            validated_data[attr_name] = validated_value
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail={
                                    "error": "SCIM_VALIDATION_ERROR",
                                    "message": f"Cannot modify readOnly field '{attr_name}'",
                                    "field": attr_name,
                                    "operation": "PATCH",
                                    "resource_type": resource_type,
                                    "server_id": self.server_id,
                                    "type": "readonly_field_modification",
                                    "help": f"The field '{attr_name}' is read-only and cannot be modified. Remove this field from your request."
                                }
                            )
                    else:
                        # Check if unknown attributes are allowed
                        allow_unknown = self.validation_rules.get("allow_unknown_attributes", False)
                        if not allow_unknown:
                            raise HTTPException(
                                status_code=400,
                                detail={
                                    "error": "SCIM_VALIDATION_ERROR",
                                    "message": f"Unknown field '{attr_name}'",
                                    "field": attr_name,
                                    "operation": "PATCH",
                                    "resource_type": resource_type,
                                    "server_id": self.server_id,
                                    "type": "unknown_field",
                                    "help": f"The field '{attr_name}' does not exist in the {resource_type} schema for this server. Check the schema definition for valid fields."
                                }
                            )
                else:
                    # Full resource replacement
                    for attr_name, attr_value in value.items():
                        if attr_name in attr_lookup:
                            attr = attr_lookup[attr_name]
                            if attr.get("mutability") != "readOnly":
                                validated_value = self._validate_attribute(attr, attr_value, resource_type)
                                validated_data[attr_name] = validated_value
                            # Skip readOnly fields silently in full replacement
            
            elif op == "add":
                # Add operation for multi-valued attributes
                if path:
                    attr_name = path.lstrip("/")
                    if attr_name in attr_lookup:
                        attr = attr_lookup[attr_name]
                        if attr.get("multiValued", False):
                            existing_values = validated_data.get(attr_name, [])
                            if not isinstance(existing_values, list):
                                existing_values = []
                            validated_value = self._validate_attribute(attr, value, resource_type)
                            if isinstance(validated_value, list):
                                existing_values.extend(validated_value)
                            else:
                                existing_values.append(validated_value)
                            validated_data[attr_name] = existing_values
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail={
                                    "error": "SCIM_VALIDATION_ERROR",
                                    "message": f"Cannot use 'add' operation on single-valued field '{attr_name}'",
                                    "field": attr_name,
                                    "operation": "add",
                                    "resource_type": resource_type,
                                    "server_id": self.server_id,
                                    "type": "invalid_operation_for_field_type",
                                    "help": f"The field '{attr_name}' is single-valued. Use 'replace' operation instead of 'add'."
                                }
                            )
                    else:
                        # Check if unknown attributes are allowed
                        allow_unknown = self.validation_rules.get("allow_unknown_attributes", False)
                        if not allow_unknown:
                            raise HTTPException(
                                status_code=400,
                                detail={
                                    "error": "SCIM_VALIDATION_ERROR",
                                    "message": f"Unknown field '{attr_name}'",
                                    "field": attr_name,
                                    "operation": "add",
                                    "resource_type": resource_type,
                                    "server_id": self.server_id,
                                    "type": "unknown_field",
                                    "help": f"The field '{attr_name}' does not exist in the {resource_type} schema for this server."
                                }
                            )
            
            elif op == "remove":
                # Remove operation
                if path:
                    attr_name = path.lstrip("/")
                    if attr_name in validated_data:
                        if attr_lookup.get(attr_name, {}).get("multiValued", False):
                            # Remove from multi-valued attribute
                            existing_values = validated_data[attr_name]
                            if isinstance(existing_values, list):
                                # Remove specific value if provided
                                if value in existing_values:
                                    existing_values.remove(value)
                                validated_data[attr_name] = existing_values
                        else:
                            # Remove single-valued attribute
                            validated_data.pop(attr_name, None)
                    else:
                        # Check if unknown attributes are allowed
                        allow_unknown = self.validation_rules.get("allow_unknown_attributes", False)
                        if not allow_unknown:
                            raise HTTPException(
                                status_code=400,
                                detail={
                                    "error": "SCIM_VALIDATION_ERROR",
                                    "message": f"Unknown field '{attr_name}'",
                                    "field": attr_name,
                                    "operation": "remove",
                                    "resource_type": resource_type,
                                    "server_id": self.server_id,
                                    "type": "unknown_field",
                                    "help": f"The field '{attr_name}' does not exist in the {resource_type} schema for this server."
                                }
                            )
        
        return validated_data
    
    def _validate_required_fields(self, schema: Dict[str, Any], data: Dict[str, Any], resource_type: str, operation: str = "create") -> None:
        """Validate that all required fields are present."""
        for attr in schema["attributes"]:
            if attr.get("required", False):
                attr_name = attr["name"]
                mutability = attr.get("mutability", "readWrite")
                
                # Skip read-only fields for CREATE operations
                if operation == "create" and mutability == "readOnly":
                    continue
                
                if attr_name not in data:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "SCIM_VALIDATION_ERROR",
                            "message": f"Required field '{attr_name}' is missing",
                            "field": attr_name,
                            "resource_type": resource_type,
                            "server_id": self.server_id,
                            "type": "required_field_missing",
                            "help": f"Add the '{attr_name}' field to your request. This field is required."
                        }
                    )
    
    def _validate_single_value(self, attr: Dict[str, Any], value: Any, resource_type: str = "Unknown") -> Any:
        """Validate a single value against an attribute definition."""
        attr_name = attr["name"]
        attr_type = attr["type"]
        attr_canonical_values = attr.get("canonicalValues", [])
        
        # Type validation
        if attr_type == "string":
            if not isinstance(value, str):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "SCIM_VALIDATION_ERROR",
                        "message": f"Field '{attr_name}' must be a string",
                        "field": attr_name,
                        "provided_value": value,
                        "expected_type": "string",
                        "resource_type": resource_type,
                        "server_id": self.server_id,
                        "type": "type_mismatch",
                        "help": f"Change the value of '{attr_name}' to a string."
                    }
                )
        elif attr_type == "boolean":
            if not isinstance(value, bool):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "SCIM_VALIDATION_ERROR",
                        "message": f"Field '{attr_name}' must be a boolean",
                        "field": attr_name,
                        "provided_value": value,
                        "expected_type": "boolean",
                        "resource_type": resource_type,
                        "server_id": self.server_id,
                        "type": "type_mismatch",
                        "help": f"Change the value of '{attr_name}' to true or false."
                    }
                )
        elif attr_type == "complex":
            if not isinstance(value, dict):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "SCIM_VALIDATION_ERROR",
                        "message": f"Field '{attr_name}' must be an object",
                        "field": attr_name,
                        "provided_value": value,
                        "expected_type": "object",
                        "resource_type": resource_type,
                        "server_id": self.server_id,
                        "type": "type_mismatch",
                        "help": f"Change the value of '{attr_name}' to an object with the required sub-attributes."
                    }
                )
            
            # Validate complex attribute sub-attributes
            sub_attrs = attr.get("subAttributes", [])
            validated_complex = {}
            
            for sub_attr in sub_attrs:
                sub_attr_name = sub_attr["name"]
                sub_attr_required = sub_attr.get("required", False)
                
                if sub_attr_name in value:
                    validated_sub_value = self._validate_single_value(sub_attr, value[sub_attr_name], resource_type)
                    validated_complex[sub_attr_name] = validated_sub_value
                elif sub_attr_required:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "SCIM_VALIDATION_ERROR",
                            "message": f"Required sub-attribute '{sub_attr_name}' is missing in '{attr_name}'",
                            "field": f"{attr_name}.{sub_attr_name}",
                            "resource_type": resource_type,
                            "server_id": self.server_id,
                            "type": "required_field_missing",
                            "help": f"Add the '{sub_attr_name}' field to '{attr_name}'. This field is required."
                        }
                    )
            
            return validated_complex
        
        # Canonical values validation
        if attr_canonical_values and value not in attr_canonical_values:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "SCIM_VALIDATION_ERROR",
                    "message": f"Field '{attr_name}' value '{value}' is not valid",
                    "field": attr_name,
                    "provided_value": value,
                    "allowed_values": attr_canonical_values,
                    "resource_type": resource_type,
                    "server_id": self.server_id,
                    "type": "invalid_canonical_value",
                    "help": f"Use one of the allowed values: {', '.join(attr_canonical_values)}"
                }
            )
        
        return value
    
    def _validate_attribute(self, attr: Dict[str, Any], value: Any, resource_type: str = "Unknown") -> Any:
        """Validate an attribute value against its definition."""
        attr_multi_valued = attr.get("multiValued", False)
        
        if attr_multi_valued:
            if not isinstance(value, list):
                value = [value]
            validated_values = []
            for item in value:
                validated_item = self._validate_single_value(attr, item, resource_type)
                validated_values.append(validated_item)
            return validated_values
        else:
            return self._validate_single_value(attr, value, resource_type)
    
    def filter_response_data(self, resource_type: str, data: Dict[str, Any], requested_attributes: Optional[List[str]] = None, excluded_attributes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Filter response data based on server-specific schema and requested/excluded attributes.
        """
        schema = self.get_schema(resource_type)
        filtered_data = {}
        
        for attr in schema["attributes"]:
            attr_name = attr["name"]
            attr_returned = attr.get("returned", "default")
            
            # Skip if attribute is not in data
            if attr_name not in data:
                continue
            
            # Handle requested attributes
            if requested_attributes and attr_name not in requested_attributes:
                continue
            
            # Handle excluded attributes
            if excluded_attributes and attr_name in excluded_attributes:
                continue
            
            # Handle returned policy
            if attr_returned == "never":
                continue
            elif attr_returned == "always":
                filtered_data[attr_name] = data[attr_name]
            elif attr_returned == "default":
                # Include by default unless explicitly excluded
                if not excluded_attributes or attr_name not in excluded_attributes:
                    filtered_data[attr_name] = data[attr_name]
            elif attr_returned == "request":
                # Only include if explicitly requested
                if requested_attributes and attr_name in requested_attributes:
                    filtered_data[attr_name] = data[attr_name]
        
        return filtered_data


def create_schema_validator(db_session, server_id: str) -> SchemaValidator:
    """Factory function to create a server-specific schema validator."""
    schema_generator = DynamicSchemaGenerator(db_session, server_id)
    return SchemaValidator(schema_generator) 