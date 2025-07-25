from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger
from typing import List, Dict, Any

from .database import get_db
from .auth import get_api_key
from .models import ApiKey

router = APIRouter(prefix="/v2", tags=["SCIM"])

@router.get("/ResourceTypes")
async def get_resource_types(
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get available resource types for SCIM schema discovery.
    This endpoint is called by Okta to discover available resource types.
    """
    logger.info("ResourceTypes endpoint called")
    
    # Return the standard SCIM resource types as defined in the README
    resource_types = [
        {
            "id": "User",
            "name": "User",
            "endpoint": "/Users",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
        },
        {
            "id": "Group",
            "name": "Group", 
            "endpoint": "/Groups",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:Group"
        },
        {
            "id": "Entitlement",
            "name": "Entitlement",
            "endpoint": "/Entitlements",
            "schema": "urn:okta:scim:schemas:core:1.0:Entitlement"
        },
        {
            "id": "Role",
            "name": "Role",
            "endpoint": "/Roles", 
            "schema": "urn:okta:scim:schemas:core:1.0:Role"
        }
    ]
    
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
async def get_schemas(
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Get available schemas for custom extensions.
    This endpoint is called by Okta to discover custom schema extensions.
    """
    logger.info("Schemas endpoint called")
    
    # For now, return empty list since we don't have custom schemas yet
    # This can be extended later to return schemas from the database
    response = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "startIndex": 1,
        "itemsPerPage": 0,
        "Resources": []
    }
    
    logger.info("Returning 0 custom schemas")
    return response 