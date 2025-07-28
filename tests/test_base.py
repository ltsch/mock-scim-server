"""
Base Test Class with Dynamic Data Utilities

This module provides a base test class that generates dynamic test data
from the actual codebase configuration and schemas, ensuring tests always
use valid, up-to-date data instead of hardcoded values.
"""

import uuid
import random
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from scim_server.config import settings
from scim_server.schema_definitions import DynamicSchemaGenerator
from scim_server.server_config import get_server_config_manager


class DynamicTestDataMixin:
    """Mixin class that provides dynamic test data generation utilities."""
    
    def _get_schema_generator(self, db: Session, server_id: str) -> DynamicSchemaGenerator:
        """Get schema generator for a server."""
        return DynamicSchemaGenerator(db, server_id)
    
    def _get_server_config(self, db: Session, server_id: str) -> Dict[str, Any]:
        """Get server configuration for a server."""
        config_manager = get_server_config_manager(db)
        return config_manager.get_server_config(server_id)
    
    def _get_entitlement_definitions(self, db: Session, server_id: str) -> List[Dict[str, Any]]:
        """Get entitlement definitions from server configuration."""
        config = self._get_server_config(db, server_id)
        return config.get("entitlement_types", settings.cli_entitlement_definitions)
    
    def _get_group_names(self) -> List[str]:
        """Get group names from configuration."""
        return settings.cli_group_names.copy()
    
    def _get_department_job_titles(self) -> List[tuple]:
        """Get department and job title mappings from configuration."""
        return settings.cli_department_job_titles.copy()
    
    def _get_company_domains(self) -> List[str]:
        """Get company domains from configuration."""
        return settings.cli_company_domains.copy()
    
    def _generate_unique_id(self, prefix: str = "") -> str:
        """Generate a unique identifier for test data."""
        unique_part = str(uuid.uuid4())[:8]
        return f"{prefix}{unique_part}" if prefix else unique_part
    
    def _get_random_entitlement_definition(self, db: Session, server_id: str) -> Dict[str, Any]:
        """Get a random entitlement definition from configuration."""
        definitions = self._get_entitlement_definitions(db, server_id)
        return random.choice(definitions)
    
    def _get_random_canonical_value(self, db: Session, server_id: str, entitlement_type: str = None) -> str:
        """Get a random canonical value from entitlement definitions."""
        definitions = self._get_entitlement_definitions(db, server_id)
        
        if entitlement_type:
            # Find definition with matching type
            for definition in definitions:
                if definition.get("type") == entitlement_type:
                    canonical_values = definition.get("canonical_values", [])
                    if canonical_values:
                        return random.choice(canonical_values)
        
        # Fallback: get from any definition
        for definition in definitions:
            canonical_values = definition.get("canonical_values", [])
            if canonical_values:
                return random.choice(canonical_values)
        
        return "Administrator"  # Fallback value
    
    def _get_random_group_name(self) -> str:
        """Get a random group name from configuration."""
        group_names = self._get_group_names()
        return random.choice(group_names)
    
    def _get_random_department_and_job_title(self) -> tuple[str, str]:
        """Get a random department and job title from configuration."""
        dept_job_titles = self._get_department_job_titles()
        department, job_titles = random.choice(dept_job_titles)
        job_title = random.choice(job_titles)
        return department, job_title
    
    def _get_random_company_domain(self) -> str:
        """Get a random company domain from configuration."""
        domains = self._get_company_domains()
        return random.choice(domains)
    
    def _generate_valid_user_data(self, db: Session, server_id: str, suffix: str = "") -> Dict[str, Any]:
        """Generate valid user data based on actual schema and configuration."""
        schema_generator = self._get_schema_generator(db, server_id)
        user_schema = schema_generator.get_user_schema()
        
        # Generate unique identifiers
        unique_id = self._generate_unique_id("user")
        domain = self._get_random_company_domain()
        department, job_title = self._get_random_department_and_job_title()
        
        # Build user data based on actual schema
        user_data = {
            "userName": f"testuser_{unique_id}{suffix}",
            "displayName": f"Test User {unique_id}{suffix}",
            "emails": [{
                "value": f"testuser_{unique_id}{suffix}@{domain}",
                "primary": True
            }],
            "active": True
        }
        
        # Add name if it's in the schema
        for attr in user_schema.get("attributes", []):
            if attr["name"] == "name" and attr.get("required", False):
                user_data["name"] = {
                    "givenName": f"Test{suffix}",
                    "familyName": f"User{unique_id}"
                }
                break
        
        return user_data
    
    def _generate_valid_group_data(self, db: Session, server_id: str, suffix: str = "") -> Dict[str, Any]:
        """Generate valid group data based on actual schema and configuration."""
        schema_generator = self._get_schema_generator(db, server_id)
        group_schema = schema_generator.get_group_schema()
        
        # Get random group name from configuration
        group_name = self._get_random_group_name()
        unique_id = self._generate_unique_id("group")
        
        # Build group data based on actual schema
        group_data = {
            "displayName": f"{group_name} {unique_id}{suffix}",
            "description": f"A test group for {group_name} - {unique_id}{suffix}"
        }
        
        return group_data
    
    def _generate_valid_entitlement_data(self, db: Session, server_id: str, suffix: str = "") -> Dict[str, Any]:
        """Generate valid entitlement data based on actual schema and configuration."""
        schema_generator = self._get_schema_generator(db, server_id)
        entitlement_schema = schema_generator.get_entitlement_schema()
        
        # Get random entitlement definition from configuration
        entitlement_def = self._get_random_entitlement_definition(db, server_id)
        unique_id = self._generate_unique_id("ent")
        
        # Build entitlement data based on actual schema
        entitlement_data = {
            "displayName": f"{entitlement_def['name']} {unique_id}{suffix}",
            "type": self._get_random_canonical_value(db, server_id, entitlement_def.get("type")),
            "description": f"{entitlement_def['description']} - {unique_id}{suffix}"
        }
        
        return entitlement_data
    
    def _get_schema_required_fields(self, db: Session, server_id: str, resource_type: str) -> List[str]:
        """Get required fields from actual schema."""
        schema_generator = self._get_schema_generator(db, server_id)
        
        if resource_type == "User":
            schema = schema_generator.get_user_schema()
        elif resource_type == "Group":
            schema = schema_generator.get_group_schema()
        elif resource_type == "Entitlement":
            schema = schema_generator.get_entitlement_schema()
        else:
            return []
        
        required_fields = []
        for attr in schema.get("attributes", []):
            if attr.get("required", False) and attr["name"] not in ["id", "schemas", "meta"]:
                required_fields.append(attr["name"])
        
        return required_fields
    
    def _get_schema_optional_fields(self, db: Session, server_id: str, resource_type: str) -> List[str]:
        """Get optional fields from actual schema."""
        schema_generator = self._get_schema_generator(db, server_id)
        
        if resource_type == "User":
            schema = schema_generator.get_user_schema()
        elif resource_type == "Group":
            schema = schema_generator.get_group_schema()
        elif resource_type == "Entitlement":
            schema = schema_generator.get_entitlement_schema()
        else:
            return []
        
        optional_fields = []
        for attr in schema.get("attributes", []):
            if not attr.get("required", False) and attr["name"] not in ["id", "schemas", "meta"]:
                optional_fields.append(attr["name"])
        
        return optional_fields
    
    def _generate_invalid_data_missing_required_fields(self, db: Session, server_id: str, resource_type: str) -> Dict[str, Any]:
        """Generate invalid data by omitting required fields."""
        return {}  # Empty dict will trigger required field validation
    
    def _generate_invalid_data_wrong_types(self, db: Session, server_id: str, resource_type: str) -> Dict[str, Any]:
        """Generate invalid data with wrong data types."""
        # Generate valid data first, then corrupt it
        if resource_type == "User":
            data = self._generate_valid_user_data(db, server_id, "_invalid")
            data["active"] = "not_a_boolean"  # Should be boolean
            data["emails"] = "not_an_array"    # Should be array
        elif resource_type == "Group":
            data = self._generate_valid_group_data(db, server_id, "_invalid")
            data["displayName"] = 123  # Should be string
        elif resource_type == "Entitlement":
            data = self._generate_valid_entitlement_data(db, server_id, "_invalid")
            data["type"] = 456  # Should be string
        else:
            data = {}
        
        return data
    
    def _get_test_api_key(self) -> str:
        """Get the test API key from configuration."""
        return settings.test_api_key
    
    def _get_default_api_key(self) -> str:
        """Get the default API key from configuration."""
        return settings.default_api_key 