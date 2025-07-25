from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from loguru import logger
from typing import List, Optional

from .database import get_db
from .auth import get_api_key
from .models import ApiKey, Role
from .crud import create_role, get_role, get_roles, update_role, delete_role
from .schemas import RoleCreate, RoleUpdate, RoleResponse, RoleListResponse
from .utils import role_to_scim_response, create_scim_list_response, parse_scim_filter, validate_scim_id
from .config import settings
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/v2/Roles", tags=["Roles"])

@router.post("/", response_model=RoleResponse, status_code=201)
@limiter.limit(f"{settings.rate_limit_create}/{settings.rate_limit_window}minute")
async def create_role_endpoint(
    request: Request,
    role_data: RoleCreate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Create a new role."""
    logger.info(f"Creating role: {role_data.displayName}")
    
    # Create role
    db_role = create_role(db, role_data)
    
    # Convert to SCIM response format
    response = role_to_scim_response(db_role)
    
    logger.info(f"Role created successfully: {db_role.scim_id}")
    return response

@router.get("/", response_model=RoleListResponse)
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_roles_endpoint(
    request: Request,
    start_index: int = Query(1, ge=1, alias="startIndex", description="1-based index of the first result"),
    count: int = Query(settings.default_page_size, ge=1, le=settings.max_results_per_page, description="Number of results to return"),
    filter: Optional[str] = Query(None, alias="filter", description="SCIM filter query"),
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Get roles with optional filtering and pagination."""
    logger.info(f"Getting roles: startIndex={start_index}, count={count}, filter={filter}")
    
    # Calculate skip value (convert from 1-based to 0-based)
    skip = start_index - 1
    
    # Get roles from database with filter
    roles = get_roles(db, skip=skip, limit=count, filter_query=filter)
    
    # Get total count for pagination (with filter applied)
    if filter:
        # Get total count of filtered results
        filtered_roles = get_roles(db, skip=0, limit=settings.max_count_limit, filter_query=filter)
        total_count = len(filtered_roles)
    else:
        # Get total count of all roles
        total_count = db.query(Role).count()
    
    # Convert to SCIM response format
    resources = [role_to_scim_response(role) for role in roles]
    
    response = create_scim_list_response(
        resources=resources,
        total_results=total_count,
        start_index=start_index,
        items_per_page=len(resources)
    )
    
    logger.info(f"Returning {len(resources)} roles")
    return response

@router.get("/{role_id}", response_model=RoleResponse)
async def get_role_endpoint(
    role_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Get a specific role by ID."""
    logger.info(f"Getting role: {role_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(role_id):
        logger.warning(f"Invalid SCIM ID format: {role_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Get role from database
    role = get_role(db, role_id)
    if not role:
        logger.warning(f"Role not found: {role_id}")
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    # Convert to SCIM response format
    response = role_to_scim_response(role)
    
    logger.info(f"Role retrieved successfully: {role_id}")
    return response

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role_endpoint(
    role_id: str,
    role_data: RoleUpdate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Update a role."""
    logger.info(f"Updating role: {role_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(role_id):
        logger.warning(f"Invalid SCIM ID format: {role_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if role exists
    existing_role = get_role(db, role_id)
    if not existing_role:
        logger.warning(f"Role not found: {role_id}")
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    # Update role
    updated_role = update_role(db, role_id, role_data)
    if not updated_role:
        logger.error(f"Failed to update role: {role_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update role"
        )
    
    # Convert to SCIM response format
    response = role_to_scim_response(updated_role)
    
    logger.info(f"Role updated successfully: {role_id}")
    return response

@router.patch("/{role_id}", response_model=RoleResponse)
async def patch_role_endpoint(
    role_id: str,
    role_data: RoleUpdate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Patch a role (partial update)."""
    logger.info(f"Patching role: {role_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(role_id):
        logger.warning(f"Invalid SCIM ID format: {role_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if role exists
    existing_role = get_role(db, role_id)
    if not existing_role:
        logger.warning(f"Role not found: {role_id}")
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    # Update role
    updated_role = update_role(db, role_id, role_data)
    if not updated_role:
        logger.error(f"Failed to patch role: {role_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to patch role"
        )
    
    # Convert to SCIM response format
    response = role_to_scim_response(updated_role)
    
    logger.info(f"Role patched successfully: {role_id}")
    return response

@router.delete("/{role_id}", status_code=204)
async def delete_role_endpoint(
    role_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Delete a role."""
    logger.info(f"Deleting role: {role_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(role_id):
        logger.warning(f"Invalid SCIM ID format: {role_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if role exists
    existing_role = get_role(db, role_id)
    if not existing_role:
        logger.warning(f"Role not found: {role_id}")
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    # Delete role
    success = delete_role(db, role_id)
    if not success:
        logger.error(f"Failed to delete role: {role_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete role"
        )
    
    logger.info(f"Role deleted successfully: {role_id}")
    return None 