"""
Path-based multi-server endpoints for SCIM compliance.

This module provides path-based routing for multi-server support, allowing SCIM clients
to use standard SCIM paths like /scim-identifier/{server_id}/scim/v2/Users instead
of query parameters.

This is essential for SCIM compliance as most SCIM clients expect standard paths
and don't parse query parameters for server identification.
"""

from fastapi import APIRouter, Depends, Path
from typing import List
from loguru import logger

from .endpoint_base import BaseEntityEndpoint
from .crud_entities import user_crud, group_crud, entitlement_crud
from .response_converter import user_converter, group_converter, entitlement_converter
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    GroupCreate, GroupUpdate, GroupResponse, GroupListResponse,
    EntitlementCreate, EntitlementUpdate, EntitlementResponse, EntitlementListResponse
)
from .config import settings
from .auth import get_validated_server_id


def create_path_based_routers() -> List[APIRouter]:
    """
    Create path-based routers for multi-server support.
    
    Returns:
        List of routers with path-based server ID support
    """
    routers = []
    
    # User endpoints with path-based server ID
    user_router = APIRouter(
        prefix="/scim-identifier/{server_id}/scim/v2/Users",
        tags=["Users (Path-based)"]
    )
    
    user_endpoints = BaseEntityEndpoint(
        entity_type="User",
        router=user_router,
        crud_operations=user_crud,
        response_converter=user_converter,
        create_schema=UserCreate,
        update_schema=UserUpdate,
        response_schema=UserResponse,
        list_response_schema=UserListResponse,
        schema_uri="urn:ietf:params:scim:schemas:core:2.0:User",
        supports_multi_server=True,
        server_id_dependency=get_validated_server_id
    )
    routers.append(user_router)
    
    # Group endpoints with path-based server ID
    group_router = APIRouter(
        prefix="/scim-identifier/{server_id}/scim/v2/Groups",
        tags=["Groups (Path-based)"]
    )
    
    group_endpoints = BaseEntityEndpoint(
        entity_type="Group",
        router=group_router,
        crud_operations=group_crud,
        response_converter=group_converter,
        create_schema=GroupCreate,
        update_schema=GroupUpdate,
        response_schema=GroupResponse,
        list_response_schema=GroupListResponse,
        schema_uri="urn:ietf:params:scim:schemas:core:2.0:Group",
        supports_multi_server=True,
        server_id_dependency=get_validated_server_id
    )
    routers.append(group_router)
    
    # Entitlement endpoints with path-based server ID
    entitlement_router = APIRouter(
        prefix="/scim-identifier/{server_id}/scim/v2/Entitlements",
        tags=["Entitlements (Path-based)"]
    )
    
    entitlement_endpoints = BaseEntityEndpoint(
        entity_type="Entitlement",
        router=entitlement_router,
        crud_operations=entitlement_crud,
        response_converter=entitlement_converter,
        create_schema=EntitlementCreate,
        update_schema=EntitlementUpdate,
        response_schema=EntitlementResponse,
        list_response_schema=EntitlementListResponse,
        schema_uri="urn:okta:scim:schemas:core:1.0:Entitlement",
        supports_multi_server=True,
        server_id_dependency=get_validated_server_id
    )
    routers.append(entitlement_router)
    
    # Create SCIM discovery endpoints with path-based server ID
    scim_router = APIRouter(
        prefix="/scim-identifier/{server_id}/scim/v2",
        tags=["SCIM Discovery (Path-based)"]
    )
    
    # Import and register SCIM discovery endpoints
    from .scim_endpoints import get_resource_types, get_schemas, get_schema_by_urn
    
    # Register the endpoints with the path-based router
    scim_router.add_api_route("/ResourceTypes", get_resource_types, methods=["GET"])
    scim_router.add_api_route("/ResourceTypes/", get_resource_types, methods=["GET"])
    scim_router.add_api_route("/Schemas", get_schemas, methods=["GET"])
    scim_router.add_api_route("/Schemas/", get_schemas, methods=["GET"])
    scim_router.add_api_route("/Schemas/{schema_urn}", get_schema_by_urn, methods=["GET"])
    
    routers.append(scim_router)
    
    logger.info(f"Created {len(routers)} path-based multi-server routers")
    return routers 