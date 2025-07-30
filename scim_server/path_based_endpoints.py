"""
Path-based multi-server endpoints for SCIM compliance.

This module provides path-based routing for multi-server support, allowing SCIM clients
to use standard SCIM paths like /scim-identifier/{server_id}/scim/v2/Users instead
of query parameters.

This is essential for SCIM compliance as most SCIM clients expect standard paths
and don't parse query parameters for server identification.
"""

from fastapi import APIRouter, Depends, Path, HTTPException, Request
from typing import List
from loguru import logger
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from .endpoint_base import BaseEntityEndpoint
from .crud_entities import user_crud, group_crud, entitlement_crud
from .response_converter import user_converter, group_converter, entitlement_converter
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    GroupCreate, GroupUpdate, GroupResponse, GroupListResponse,
    EntitlementCreate, EntitlementUpdate, EntitlementResponse, EntitlementListResponse
)
from .config import settings
from .auth import get_validated_server_id, get_api_key
from .database import get_db
from .server_config import get_server_config_manager
from .utils import validate_scim_id

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


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
    
    # Add password change endpoint to user router
    @user_router.patch("/{user_id}/password")
    @limiter.limit(f"{settings.rate_limit_create}/{settings.rate_limit_window}minute")
    async def change_user_password(
        user_id: str,
        request: Request,
        password_data: dict,
        server_id: str = Depends(get_validated_server_id),
        api_key: str = Depends(get_api_key),
        db: Session = Depends(get_db)
    ):
        """
        Change user password endpoint per RFC 7644 §3.3.2.
        This endpoint is only available if password support is enabled for the server.
        """
        logger.info(f"Password change request for user: {user_id} in server: {server_id}")
        
        # Check if password support is enabled for this server
        server_config = get_server_config_manager(db)
        if not server_config.is_password_support_enabled(server_id):
            logger.warning(f"Password change attempted but not enabled for server: {server_id}")
            raise HTTPException(
                status_code=501,
                detail="Password change is not supported for this server"
            )
        
        # Validate SCIM ID format
        if not validate_scim_id(user_id):
            logger.warning(f"Invalid SCIM ID format: {user_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid SCIM ID format"
            )
        
        # Check if user exists
        user = user_crud.get_by_id(db, user_id, server_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Validate password data structure
        if "password" not in password_data:
            raise HTTPException(
                status_code=400,
                detail="Password field is required"
            )
        
        new_password = password_data["password"]
        validation_rules = server_config.get_password_validation_rules(server_id)
        
        validation_errors = []
        if len(new_password) < validation_rules.get("min_length", 8):
            validation_errors.append(f"Password must be at least {validation_rules.get('min_length', 8)} characters")
        
        if validation_rules.get("require_uppercase", True) and not any(c.isupper() for c in new_password):
            validation_errors.append("Password must contain at least one uppercase letter")
        
        if validation_rules.get("require_lowercase", True) and not any(c.islower() for c in new_password):
            validation_errors.append("Password must contain at least one lowercase letter")
        
        if validation_rules.get("require_numbers", True) and not any(c.isdigit() for c in new_password):
            validation_errors.append("Password must contain at least one number")
        
        if validation_rules.get("require_special_chars", False) and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password):
            validation_errors.append("Password must contain at least one special character")
        
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail={"validation_errors": validation_errors}
            )
        
        logger.info(f"Password changed successfully for user: {user_id} in server: {server_id}")
        updated_user = user_converter.to_scim_response(user)
        return updated_user
    
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
    from .scim_endpoints import get_resource_types, get_schemas, get_schema_by_urn, get_service_provider_config
    
    # Register the endpoints with the path-based router
    scim_router.add_api_route("/ServiceProviderConfig", get_service_provider_config, methods=["GET"])
    scim_router.add_api_route("/ServiceProviderConfig/", get_service_provider_config, methods=["GET"])
    scim_router.add_api_route("/ResourceTypes", get_resource_types, methods=["GET"])
    scim_router.add_api_route("/ResourceTypes/", get_resource_types, methods=["GET"])
    scim_router.add_api_route("/Schemas", get_schemas, methods=["GET"])
    scim_router.add_api_route("/Schemas/", get_schemas, methods=["GET"])
    scim_router.add_api_route("/Schemas/{schema_urn}", get_schema_by_urn, methods=["GET"])
    
    routers.append(scim_router)
    
    logger.info(f"Created {len(routers)} path-based multi-server routers")
    return routers 