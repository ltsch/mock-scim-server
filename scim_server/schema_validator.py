"""
SCIM Schema Validation System

This module provides validation and enforcement of SCIM schema requirements:
- Required fields validation
- Mutability enforcement (readOnly vs readWrite)
- Multi-valued attribute handling
- Canonical values validation
- Type validation
- Uniqueness constraints

The validator ensures that all endpoints honor the schema requirements
without overcomplicating the developer experience.
"""

from typing import Dict, Any, List, Optional, Union
from loguru import logger
from fastapi import HTTPException

from .schema_definitions import DynamicSchemaGenerator


class SchemaValidator:
    """Validates and enforces SCIM schema requirements."""
    
    def __init__(self, schema_generator: DynamicSchemaGenerator):
        self.schema_generator = schema_generator
        self._schema_cache = {}
    
    def get_schema(self, resource_type: str) -> Dict[str, Any]:
        """Get schema for a resource type with caching."""
        if resource_type not in self._schema_cache:
            schema_map = {
                "User": self.schema_generator.get_user_schema,
                "Group": self.schema_generator.get_group_schema,
                "Entitlement": self.schema_generator.get_entitlement_schema
            }
            if resource_type in schema_map:
                self._schema_cache[resource_type] = schema_map[resource_type]()
            else:
                raise ValueError(f"Unknown resource type: {resource_type}")
        
        return self._schema_cache[resource_type]
    
    def validate_create_request(self, resource_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a CREATE request against the schema.
        Returns cleaned/validated data.
        """
        schema = self.get_schema(resource_type)
        validated_data = {}
        
        for attr in schema["attributes"]:
            attr_name = attr["name"]
            attr_required = attr.get("required", False)
            attr_mutability = attr.get("mutability", "readWrite")
            
            # Skip readOnly attributes in create requests
            if attr_mutability == "readOnly":
                continue
            
            # Check required fields
            if attr_required and attr_name not in data:
                # Get field description for better error message
                attr_description = attr.get("description", "No description available")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "SCIM_VALIDATION_ERROR",
                        "message": f"Required field '{attr_name}' is missing",
                        "field": attr_name,
                        "description": attr_description,
                        "type": "required_field_missing",
                        "resource_type": resource_type,
                        "help": f"Add the '{attr_name}' field to your request. This field is required for {resource_type} creation."
                    }
                )
            
            # Validate field if present
            if attr_name in data:
                validated_value = self._validate_attribute(attr, data[attr_name], resource_type)
                validated_data[attr_name] = validated_value
        
        return validated_data
    
    def validate_update_request(self, resource_type: str, data: Dict[str, Any], existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an UPDATE request against the schema.
        Returns cleaned/validated data merged with existing data.
        """
        schema = self.get_schema(resource_type)
        validated_data = existing_data.copy()
        
        for attr in schema["attributes"]:
            attr_name = attr["name"]
            attr_mutability = attr.get("mutability", "readWrite")
            
            # Skip readOnly attributes in update requests
            if attr_mutability == "readOnly":
                continue
            
            # Update field if present in request
            if attr_name in data:
                validated_value = self._validate_attribute(attr, data[attr_name], resource_type)
                validated_data[attr_name] = validated_value
        
        return validated_data
    
    def validate_patch_request(self, resource_type: str, operations: List[Dict[str, Any]], existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a PATCH request against the schema.
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
                                    "type": "readonly_field_modification",
                                    "resource_type": resource_type,
                                    "help": f"The field '{attr_name}' is read-only and cannot be modified. Remove this field from your request."
                                }
                            )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error": "SCIM_VALIDATION_ERROR",
                                "message": f"Unknown field '{attr_name}'",
                                "field": attr_name,
                                "operation": "PATCH",
                                "type": "unknown_field",
                                "resource_type": resource_type,
                                "help": f"The field '{attr_name}' does not exist in the {resource_type} schema. Check the schema definition for valid fields."
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
                                    "type": "invalid_operation_for_field_type",
                                    "resource_type": resource_type,
                                    "help": f"The field '{attr_name}' is single-valued. Use 'replace' operation instead of 'add'."
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
                                if value in existing_values:
                                    existing_values.remove(value)
                                else:
                                    raise HTTPException(
                                        status_code=400,
                                        detail={
                                            "error": "SCIM_VALIDATION_ERROR",
                                            "message": f"Value '{value}' not found in field '{attr_name}'",
                                            "field": attr_name,
                                            "operation": "remove",
                                            "value_to_remove": value,
                                            "type": "value_not_found",
                                            "resource_type": resource_type,
                                            "help": f"The value '{value}' does not exist in the field '{attr_name}'. Check the current values before removing."
                                        }
                                    )
                        else:
                            # Remove single-valued attribute
                            del validated_data[attr_name]
        
        return validated_data
    
    def _validate_attribute(self, attr: Dict[str, Any], value: Any, resource_type: str = "Unknown") -> Any:
        """Validate a single attribute against its schema definition."""
        attr_name = attr["name"]
        attr_type = attr["type"]
        attr_multi_valued = attr.get("multiValued", False)
        attr_canonical_values = attr.get("canonicalValues", [])
        
        # Handle multi-valued attributes
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
    
    def _validate_single_value(self, attr: Dict[str, Any], value: Any, resource_type: str = "Unknown") -> Any:
        """Validate a single value against attribute schema."""
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
                        "expected_type": "string",
                        "provided_type": type(value).__name__,
                        "provided_value": value,
                        "type": "type_mismatch",
                        "resource_type": resource_type,
                        "help": f"Change the value of '{attr_name}' to a string (text) value."
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
                        "expected_type": "boolean",
                        "provided_type": type(value).__name__,
                        "provided_value": value,
                        "type": "type_mismatch",
                        "resource_type": resource_type,
                        "help": f"Change the value of '{attr_name}' to true or false."
                    }
                )
        elif attr_type == "integer":
            if not isinstance(value, int):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "SCIM_VALIDATION_ERROR",
                        "message": f"Field '{attr_name}' must be an integer",
                        "field": attr_name,
                        "expected_type": "integer",
                        "provided_type": type(value).__name__,
                        "provided_value": value,
                        "type": "type_mismatch",
                        "resource_type": resource_type,
                        "help": f"Change the value of '{attr_name}' to a whole number."
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
                        "expected_type": "object",
                        "provided_type": type(value).__name__,
                        "provided_value": value,
                        "type": "type_mismatch",
                        "resource_type": resource_type,
                        "help": f"Change the value of '{attr_name}' to an object with the required sub-attributes."
                    }
                )
            
            # Validate complex attribute sub-attributes
            sub_attrs = attr.get("subAttributes", [])
            validated_complex = {}
            
            for sub_attr in sub_attrs:
                sub_attr_name = sub_attr["name"]
                if sub_attr_name in value:
                    validated_sub_value = self._validate_single_value(sub_attr, value[sub_attr_name])
                    validated_complex[sub_attr_name] = validated_sub_value
            
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
                    "type": "invalid_canonical_value",
                    "resource_type": resource_type,
                    "help": f"Use one of the allowed values: {', '.join(attr_canonical_values)}"
                }
            )
        
        return value
    
    def filter_response_data(self, resource_type: str, data: Dict[str, Any], requested_attributes: Optional[List[str]] = None, excluded_attributes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Filter response data based on schema and requested/excluded attributes.
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


def create_schema_validator(db_session) -> SchemaValidator:
    """Factory function to create a schema validator."""
    schema_generator = DynamicSchemaGenerator(db_session)
    return SchemaValidator(schema_generator) 