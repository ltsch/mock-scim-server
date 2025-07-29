"""
Routing configuration for multi-server SCIM support.

This module provides easy configuration for different routing strategies
and allows switching between them without code changes.
"""

from enum import Enum
from typing import Dict, Any, List
from loguru import logger
from .server_context import ServerIdSource, configure_server_id_source

class RoutingStrategy(Enum):
    PATH_PARAM = "path_param"        # /scim-identifier/123/scim/v2/Users

class RoutingConfig:
    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.PATH_PARAM):
        self.strategy = strategy
        self.enabled_strategies: List[RoutingStrategy] = [RoutingStrategy.PATH_PARAM]
        self._configure_strategy(strategy)

    def _configure_strategy(self, strategy: RoutingStrategy):
        if strategy == RoutingStrategy.PATH_PARAM:
            self.enabled_strategies = [RoutingStrategy.PATH_PARAM]
            configure_server_id_source(ServerIdSource.PATH_PARAM)
            logger.info("Configured routing strategy: Path Parameter")

    def get_url_patterns(self) -> Dict[str, str]:
        patterns = {
            "users_path": "/scim-identifier/{server_id}/scim/v2/Users",
            "groups_path": "/scim-identifier/{server_id}/scim/v2/Groups",
            "entitlements_path": "/scim-identifier/{server_id}/scim/v2/Entitlements",
            "resource_types_path": "/scim-identifier/{server_id}/scim/v2/ResourceTypes",
            "schemas_path": "/scim-identifier/{server_id}/scim/v2/Schemas",
            "service_provider_config_path": "/scim-identifier/{server_id}/scim/v2/ServiceProviderConfig",
        }
        return patterns

    def get_compatibility_info(self) -> Dict[str, Any]:
        return {
            "method": "path_parameter",
            "description": "RFC 7644-compliant path-based routing only",
            "limitations": "Only path-based routing is supported for SCIM compliance"
        }

    def switch_strategy(self, new_strategy: RoutingStrategy):
        self._configure_strategy(new_strategy)
        self.strategy = new_strategy
        logger.info(f"Switched routing strategy to: {new_strategy}")

def get_routing_config() -> RoutingConfig:
    return RoutingConfig()

def configure_routing(strategy: RoutingStrategy):
    config = RoutingConfig(strategy)
    return config

def get_url_patterns() -> Dict[str, str]:
    return get_routing_config().get_url_patterns()

def get_compatibility_info() -> Dict[str, Any]:
    return get_routing_config().get_compatibility_info() 