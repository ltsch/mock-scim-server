"""
Server Configuration System

This module provides dynamic server-specific configuration that allows each SCIM server ID
to have unique attributes, schemas, and configurations. All functions will be dynamic
based on the current server ID configuration.
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from loguru import logger
import json
import time
from .models import Schema
from .config import settings
# Import app profiles only when needed to avoid circular imports
# from .app_profiles import get_app_profile_manager, AppType


class ServerConfiguration:
    """Dynamic server-specific configuration manager."""
    
    def __init__(self, db: Session):
        self.db = db
        self._server_configs: Dict[str, Tuple[Dict[str, Any], float]] = {}  # Cache: {server_id: (config, timestamp)}
        self._cache_ttl = 30  # Cache expires after 30 seconds
    
    def get_server_config(self, server_id: str) -> Dict[str, Any]:
        """Get configuration for a specific server ID."""
        current_time = time.time()
        
        # Check if we have a cached config and if it's still valid
        if server_id in self._server_configs:
            config, timestamp = self._server_configs[server_id]
            if current_time - timestamp < self._cache_ttl:
                return config
            else:
                # Cache expired, remove it
                del self._server_configs[server_id]
        
        # Load fresh config from database
        config = self._load_server_config(server_id)
        self._server_configs[server_id] = (config, current_time)
        return config
    
    def _load_server_config(self, server_id: str) -> Dict[str, Any]:
        """Load or create server-specific configuration."""
        # Validate server_id is not None
        if server_id is None:
            raise ValueError("server_id cannot be None")
        
        # Try to load from database first
        db_schema = self.db.query(Schema).filter(
            Schema.urn == f"urn:scim:server:{server_id}:config"
        ).first()
        
        if db_schema:
            try:
                config = json.loads(db_schema.schema_definition)
                logger.info(f"Loaded existing configuration for server: {server_id}")
                return config
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in server config for {server_id}, using defaults")
        
        # Create default configuration
        default_config = self._create_default_config(server_id)
        self._save_server_config(server_id, default_config)
        logger.info(f"Created default configuration for server: {server_id}")
        return default_config
    
    def _create_default_config(self, server_id: str) -> Dict[str, Any]:
        """Create default configuration for a server."""
        return {
            "server_id": server_id,
            "name": f"SCIM Server {server_id}",
            "description": f"Dynamic SCIM server with ID {server_id}",
            "app_profile": None,  # No app profile by default
            "enabled_resource_types": ["User", "Group", "Entitlement"],
            "custom_attributes": {},
            "schema_extensions": {},
            "entitlement_types": self._get_server_entitlement_types(server_id),
            "user_attributes": self._get_server_user_attributes(server_id),
            "group_attributes": self._get_server_group_attributes(server_id),
            "validation_rules": self._get_server_validation_rules(server_id),
            "rate_limits": {
                "create": settings.rate_limit_create,
                "read": settings.rate_limit_read,
                "update": settings.rate_limit_create,
                "delete": settings.rate_limit_create
            },
            "api_settings": {
                "max_results_per_page": settings.max_results_per_page,
                "default_page_size": settings.default_page_size
            },
            "password_support": {
                "enabled": False,  # Default to disabled for safety
                "change_password_endpoint": True,  # Whether to expose /Users/{id}/password endpoint
                "password_validation": {
                    "min_length": 8,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_special_chars": False
                }
            }
        }
    
    def _get_server_entitlement_types(self, server_id: str) -> List[Dict[str, Any]]:
        """Get server-specific entitlement types."""
        # Use global settings as base, but allow server-specific overrides
        base_entitlements = settings.cli_entitlement_definitions.copy()
        
        # Server-specific modifications could be added here
        # For now, return the base entitlements
        return base_entitlements
    
    def _get_server_user_attributes(self, server_id: str) -> Dict[str, Any]:
        """Get server-specific user attributes."""
        return {
            "required_attributes": ["userName"],
            "optional_attributes": ["displayName", "emails", "name", "active"],
            "custom_attributes": {},
            "complex_attributes": {
                "emails": {
                    "type": "complex",
                    "multiValued": True,
                    "subAttributes": [
                        {"name": "value", "type": "string", "required": True},
                        {"name": "primary", "type": "boolean", "required": False}
                    ]
                },
                "name": {
                    "type": "complex",
                    "multiValued": False,
                    "subAttributes": [
                        {"name": "givenName", "type": "string", "required": False},
                        {"name": "familyName", "type": "string", "required": False}
                    ]
                }
            }
        }
    
    def _get_server_group_attributes(self, server_id: str) -> Dict[str, Any]:
        """Get server-specific group attributes."""
        return {
            "required_attributes": ["displayName"],
            "optional_attributes": ["description"],
            "custom_attributes": {},
            "complex_attributes": {}
        }
    
    def _get_server_validation_rules(self, server_id: str) -> Dict[str, Any]:
        """Get server-specific validation rules."""
        return {
            "strict_mode": True,
            "allow_unknown_attributes": False,
            "validate_canonical_values": True,
            "validate_required_fields": True,
            "validate_complex_attributes": True
        }
    
    def _save_server_config(self, server_id: str, config: Dict[str, Any]) -> None:
        """Save server configuration to database."""
        # Validate server_id is not None
        if server_id is None:
            raise ValueError("server_id cannot be None")
        
        schema_urn = f"urn:scim:server:{server_id}:config"
        
        # Check if config already exists
        existing_schema = self.db.query(Schema).filter(
            Schema.urn == schema_urn
        ).first()
        
        if existing_schema:
            existing_schema.schema_definition = json.dumps(config)
        else:
            new_schema = Schema(
                urn=schema_urn,
                name=f"Server Configuration - {server_id}",
                description=f"Configuration for SCIM server {server_id}",
                schema_definition=json.dumps(config),
                server_id=server_id
            )
            self.db.add(new_schema)
        
        self.db.commit()
        logger.info(f"Saved configuration for server: {server_id}")
    
    def update_server_config(self, server_id: str, updates: Dict[str, Any]) -> None:
        """Update server configuration."""
        current_config = self.get_server_config(server_id)
        
        # Deep merge updates
        def deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
            result = base.copy()
            for key, value in updates.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        updated_config = deep_merge(current_config, updates)
        self._save_server_config(server_id, updated_config)
        
        # Clear cache
        if server_id in self._server_configs:
            del self._server_configs[server_id]
        
        logger.info(f"Updated configuration for server: {server_id}")
    
    def get_server_attribute_config(self, server_id: str, resource_type: str, attribute_name: str) -> Optional[Dict[str, Any]]:
        """Get server-specific attribute configuration."""
        config = self.get_server_config(server_id)
        
        if resource_type == "User":
            attributes = config.get("user_attributes", {})
        elif resource_type == "Group":
            attributes = config.get("group_attributes", {})
        elif resource_type == "Entitlement":
            # Entitlements use the entitlement_types configuration
            for entitlement in config.get("entitlement_types", []):
                if entitlement.get("name") == attribute_name:
                    return entitlement
            return None
        else:
            return None
        
        # Check custom attributes
        custom_attrs = attributes.get("custom_attributes", {})
        if attribute_name in custom_attrs:
            return custom_attrs[attribute_name]
        
        # Check complex attributes
        complex_attrs = attributes.get("complex_attributes", {})
        if attribute_name in complex_attrs:
            return complex_attrs[attribute_name]
        
        return None
    
    def get_server_validation_rules(self, server_id: str) -> Dict[str, Any]:
        """Get server-specific validation rules."""
        config = self.get_server_config(server_id)
        return config.get("validation_rules", {})
    
    def is_attribute_enabled(self, server_id: str, resource_type: str, attribute_name: str) -> bool:
        """Check if an attribute is enabled for a specific server."""
        config = self.get_server_config(server_id)
        
        if resource_type == "User":
            required_attrs = config.get("user_attributes", {}).get("required_attributes", [])
            optional_attrs = config.get("user_attributes", {}).get("optional_attributes", [])
            custom_attrs = config.get("user_attributes", {}).get("custom_attributes", {})
            complex_attrs = config.get("user_attributes", {}).get("complex_attributes", {})
            
            return (attribute_name in required_attrs or 
                   attribute_name in optional_attrs or 
                   attribute_name in custom_attrs or 
                   attribute_name in complex_attrs)
        
        elif resource_type == "Group":
            required_attrs = config.get("group_attributes", {}).get("required_attributes", [])
            optional_attrs = config.get("group_attributes", {}).get("optional_attributes", [])
            custom_attrs = config.get("group_attributes", {}).get("custom_attributes", {})
            complex_attrs = config.get("group_attributes", {}).get("complex_attributes", {})
            
            return (attribute_name in required_attrs or 
                   attribute_name in optional_attrs or 
                   attribute_name in custom_attrs or 
                   attribute_name in complex_attrs)
        
        elif resource_type == "Entitlement":
            # Check if attribute exists in entitlement types
            for entitlement in config.get("entitlement_types", []):
                if entitlement.get("name") == attribute_name:
                    return True
            return False
        
        return False
    
    def get_enabled_resource_types(self, server_id: str) -> List[str]:
        """Get enabled resource types for a server."""
        config = self.get_server_config(server_id)
        return config.get("enabled_resource_types", ["User", "Group", "Entitlement"])
    
    def get_server_rate_limits(self, server_id: str) -> Dict[str, int]:
        """Get server-specific rate limits."""
        config = self.get_server_config(server_id)
        return config.get("rate_limits", {
            "create": settings.rate_limit_create,
            "read": settings.rate_limit_read,
            "update": settings.rate_limit_create,
            "delete": settings.rate_limit_create
        })
    
    def get_server_app_profile(self, server_id: str) -> Optional[str]:
        """Get the app profile for a specific server."""
        config = self.get_server_config(server_id)
        return config.get("app_profile")
    
    def set_server_app_profile(self, server_id: str, app_profile: str) -> None:
        """Set the app profile for a specific server."""
        config = self.get_server_config(server_id)
        config["app_profile"] = app_profile
        self._save_server_config(server_id, config)
        logger.info(f"Set app profile '{app_profile}' for server {server_id}")
    
    def get_available_app_profiles(self) -> List[Dict[str, Any]]:
        """Get list of available app profiles."""
        try:
            # Import here to avoid circular imports
            from .app_profiles import get_app_profile_manager
            profiles = []
            app_profile_manager = get_app_profile_manager()
            for app_type, profile_config in app_profile_manager.get_all_profiles().items():
                profiles.append({
                    "id": app_type.value,
                    "name": profile_config.name,
                    "description": profile_config.description,
                    "app_type": app_type.value
                })
            return profiles
        except ImportError:
            logger.warning("App profiles not available")
            return []
    
    def get_app_profile_config(self, app_profile: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific app profile."""
        try:
            # Import here to avoid circular imports
            from .app_profiles import get_app_profile_manager, AppType
            app_type = AppType(app_profile)
            app_profile_manager = get_app_profile_manager()
            profile = app_profile_manager.get_profile(app_type)
            if profile:
                return {
                    "app_type": app_type.value,
                    "name": profile.name,
                    "description": profile.description,
                    "compatible_entitlements": profile.compatible_entitlements,
                    "compatible_departments": profile.compatible_departments,
                    "compatible_groups": profile.compatible_groups,
                    "user_attributes": [
                        {
                            "name": attr.name,
                            "mutability": attr.mutability.value,
                            "required": attr.required,
                            "visible": attr.visible,
                            "description": attr.description
                        }
                        for attr in profile.user_attributes
                    ],
                    "roles": [
                        {
                            "name": role.name,
                            "description": role.description,
                            "permissions": role.permissions,
                            "mutability": role.mutability.value
                        }
                        for role in profile.roles
                    ],
                    "entitlements": [
                        {
                            "name": entitlement.name,
                            "type": entitlement.type,
                            "canonical_values": entitlement.canonical_values,
                            "multi_valued": entitlement.multi_valued,
                            "mutability": entitlement.mutability.value,
                            "description": entitlement.description
                        }
                        for entitlement in profile.entitlements
                    ]
                }
        except ValueError:
            logger.warning(f"Invalid app profile: {app_profile}")
            return None
        except ImportError:
            logger.warning(f"App profiles not available: {app_profile}")
            return None
    
    def is_password_support_enabled(self, server_id: str) -> bool:
        """Check if password support is enabled for a server."""
        config = self.get_server_config(server_id)
        password_config = config.get("password_support", {})
        return password_config.get("enabled", False)
    
    def get_password_validation_rules(self, server_id: str) -> Dict[str, Any]:
        """Get password validation rules for a server."""
        config = self.get_server_config(server_id)
        password_config = config.get("password_support", {})
        return password_config.get("password_validation", {})
    
    def enable_password_support(self, server_id: str, enabled: bool = True) -> None:
        """Enable or disable password support for a server."""
        config = self.get_server_config(server_id)
        if "password_support" not in config:
            config["password_support"] = {}
        config["password_support"]["enabled"] = enabled
        self._save_server_config(server_id, config)
        logger.info(f"Password support {'enabled' if enabled else 'disabled'} for server: {server_id}")


# Global server configuration manager
_server_config_manager = None

def get_server_config_manager(db: Session) -> ServerConfiguration:
    """Get the global server configuration manager."""
    global _server_config_manager
    if _server_config_manager is None:
        _server_config_manager = ServerConfiguration(db)
    return _server_config_manager 