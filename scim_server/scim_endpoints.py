from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from loguru import logger
from typing import List, Dict, Any
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import get_db
from .auth import get_api_key
from .models import ApiKey
from .config import settings
from .schema_definitions import DynamicSchemaGenerator

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Construct the API prefix dynamically
api_prefix = f"{settings.api_base_path}/scim/v2"
router = APIRouter(prefix=api_prefix, tags=["SCIM"])

@router.get("/ResourceTypes")
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_resource_types(
    request: Request,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get available resource types for SCIM schema discovery.
    This endpoint is called by Okta to discover available resource types.
    """
    logger.info("ResourceTypes endpoint called")
    
    # Generate resource types dynamically
    schema_generator = DynamicSchemaGenerator(db)
    resource_types = schema_generator.get_resource_types()
    
    response = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resource_types),
        "startIndex": 1,
        "itemsPerPage": len(resource_types),
        "Resources": resource_types
    }
    
    logger.info(f"Returning {len(resource_types)} resource types")
    return response

@router.get("/Schemas")
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_schemas(
    request: Request,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get available schemas for custom extensions.
    This endpoint is called by Okta to discover custom schema extensions.
    """
    logger.info("Schemas endpoint called")
    
    # Generate schemas dynamically
    schema_generator = DynamicSchemaGenerator(db)
    schemas = schema_generator.get_all_schemas()
    
    response = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(schemas),
        "startIndex": 1,
        "itemsPerPage": len(schemas),
        "Resources": schemas
    }
    
    logger.info(f"Returning {len(schemas)} schemas")
    return response


@router.get("/Schemas/{schema_urn}")
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_schema_by_urn(
    schema_urn: str,
    request: Request,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get a specific schema by URN.
    This endpoint is called by SCIM clients to get detailed schema information.
    """
    logger.info(f"Schema endpoint called for URN: {schema_urn}")
    
    # Generate schema dynamically
    schema_generator = DynamicSchemaGenerator(db)
    schema = schema_generator.get_schema_by_urn(schema_urn)
    
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema not found: {schema_urn}")
    
    logger.info(f"Returning schema for URN: {schema_urn}")
    return schema 