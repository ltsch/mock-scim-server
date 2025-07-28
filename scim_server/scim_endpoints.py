from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from loguru import logger
from typing import List, Dict, Any, Callable
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import get_db
from .auth import get_api_key, get_validated_server_id
# Removed ApiKey import - no longer needed
from .config import settings
from .schema_definitions import DynamicSchemaGenerator
from .server_context import get_server_id_from_path

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Construct the API prefix dynamically
api_prefix = f"{settings.api_base_path}/scim/v2"
router = APIRouter(prefix=api_prefix, tags=["SCIM"])

@router.get("/ResourceTypes")
@router.get("/ResourceTypes/")  # With trailing slash
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_resource_types(
    request: Request,
    server_id: str = Depends(get_validated_server_id),
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get available resource types for SCIM schema discovery.
    This endpoint is called by Okta to discover available resource types.
    """
    logger.info(f"ResourceTypes endpoint called for server: {server_id}")
    
    # Generate resource types dynamically based on server configuration
    schema_generator = DynamicSchemaGenerator(db, server_id)
    resource_types = schema_generator.get_resource_types()
    
    response = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resource_types),
        "startIndex": 1,
        "itemsPerPage": len(resource_types),
        "Resources": resource_types
    }
    
    logger.info(f"Returning {len(resource_types)} resource types for server: {server_id}")
    return response

@router.get("/Schemas")
@router.get("/Schemas/")  # With trailing slash
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_schemas(
    request: Request,
    server_id: str = Depends(get_validated_server_id),
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get available schemas for custom extensions.
    This endpoint returns all available schemas for the server.
    """
    logger.info(f"Schemas endpoint called for server: {server_id}")
    
    # Generate schemas dynamically based on server configuration
    schema_generator = DynamicSchemaGenerator(db, server_id)
    schemas = schema_generator.get_all_schemas()
    
    response = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(schemas),
        "startIndex": 1,
        "itemsPerPage": len(schemas),
        "Resources": schemas
    }
    
    logger.info(f"Returning {len(schemas)} schemas for server: {server_id}")
    return response

@router.get("/Schemas/{schema_urn}")
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_schema_by_urn(
    schema_urn: str,
    request: Request,
    server_id: str = Depends(get_validated_server_id),
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get a specific schema by URN.
    This endpoint returns a specific schema for the server.
    """
    logger.info(f"Schema endpoint called for URN: {schema_urn}, server: {server_id}")
    
    # Generate schema dynamically based on server configuration
    schema_generator = DynamicSchemaGenerator(db, server_id)
    schema = schema_generator.get_schema_by_urn(schema_urn)
    
    if not schema:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SCIM_VALIDATION_ERROR",
                "message": f"Schema '{schema_urn}' not found",
                "schema_urn": schema_urn,
                "server_id": server_id,
                "help": f"The schema '{schema_urn}' is not available for this server."
            }
        )
    
    logger.info(f"Returning schema {schema_urn} for server: {server_id}")
    return schema 