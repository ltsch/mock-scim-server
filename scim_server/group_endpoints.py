from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from loguru import logger
from typing import List, Optional

from .database import get_db
from .auth import get_api_key
from .models import ApiKey, Group
from .crud import create_group, get_group, get_groups, update_group, delete_group
from .schemas import GroupCreate, GroupUpdate, GroupResponse, GroupListResponse
from .utils import group_to_scim_response, create_scim_list_response, parse_scim_filter, validate_scim_id
from .config import settings
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/v2/Groups", tags=["Groups"])

@router.post("/", response_model=GroupResponse, status_code=201)
@limiter.limit(f"{settings.rate_limit_create}/{settings.rate_limit_window}minute")
async def create_group_endpoint(
    request: Request,
    group_data: GroupCreate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Create a new group."""
    logger.info(f"Creating group: {group_data.displayName}")
    
    # Create group
    db_group = create_group(db, group_data)
    
    # Convert to SCIM response format
    response = group_to_scim_response(db_group)
    
    logger.info(f"Group created successfully: {db_group.scim_id}")
    return response

@router.get("/", response_model=GroupListResponse)
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_groups_endpoint(
    request: Request,
    start_index: int = Query(1, ge=1, alias="startIndex", description="1-based index of the first result"),
    count: int = Query(settings.default_page_size, ge=1, le=settings.max_results_per_page, description="Number of results to return"),
    filter: Optional[str] = Query(None, alias="filter", description="SCIM filter query"),
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Get groups with optional filtering and pagination."""
    logger.info(f"Getting groups: startIndex={start_index}, count={count}, filter={filter}")
    
    # Calculate skip value (convert from 1-based to 0-based)
    skip = start_index - 1
    
    # Get groups from database with filter
    groups = get_groups(db, skip=skip, limit=count, filter_query=filter)
    
    # Get total count for pagination (with filter applied)
    if filter:
        # Get total count of filtered results
        filtered_groups = get_groups(db, skip=0, limit=settings.max_count_limit, filter_query=filter)
        total_count = len(filtered_groups)
    else:
        # Get total count of all groups
        total_count = db.query(Group).count()
    
    # Convert to SCIM response format
    resources = [group_to_scim_response(group) for group in groups]
    
    response = create_scim_list_response(
        resources=resources,
        total_results=total_count,
        start_index=start_index,
        items_per_page=len(resources)
    )
    
    logger.info(f"Returning {len(resources)} groups")
    return response

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_endpoint(
    group_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Get a specific group by ID."""
    logger.info(f"Getting group: {group_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(group_id):
        logger.warning(f"Invalid SCIM ID format: {group_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Get group from database
    group = get_group(db, group_id)
    if not group:
        logger.warning(f"Group not found: {group_id}")
        raise HTTPException(
            status_code=404,
            detail="Group not found"
        )
    
    # Convert to SCIM response format
    response = group_to_scim_response(group)
    
    logger.info(f"Group retrieved successfully: {group_id}")
    return response

@router.put("/{group_id}", response_model=GroupResponse)
async def update_group_endpoint(
    group_id: str,
    group_data: GroupUpdate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Update a group."""
    logger.info(f"Updating group: {group_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(group_id):
        logger.warning(f"Invalid SCIM ID format: {group_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if group exists
    existing_group = get_group(db, group_id)
    if not existing_group:
        logger.warning(f"Group not found: {group_id}")
        raise HTTPException(
            status_code=404,
            detail="Group not found"
        )
    
    # Update group
    updated_group = update_group(db, group_id, group_data)
    if not updated_group:
        logger.error(f"Failed to update group: {group_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update group"
        )
    
    # Convert to SCIM response format
    response = group_to_scim_response(updated_group)
    
    logger.info(f"Group updated successfully: {group_id}")
    return response

@router.patch("/{group_id}", response_model=GroupResponse)
async def patch_group_endpoint(
    group_id: str,
    group_data: GroupUpdate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Patch a group (partial update)."""
    logger.info(f"Patching group: {group_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(group_id):
        logger.warning(f"Invalid SCIM ID format: {group_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if group exists
    existing_group = get_group(db, group_id)
    if not existing_group:
        logger.warning(f"Group not found: {group_id}")
        raise HTTPException(
            status_code=404,
            detail="Group not found"
        )
    
    # Update group
    updated_group = update_group(db, group_id, group_data)
    if not updated_group:
        logger.error(f"Failed to patch group: {group_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to patch group"
        )
    
    # Convert to SCIM response format
    response = group_to_scim_response(updated_group)
    
    logger.info(f"Group patched successfully: {group_id}")
    return response

@router.delete("/{group_id}", status_code=204)
async def delete_group_endpoint(
    group_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Delete a group."""
    logger.info(f"Deleting group: {group_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(group_id):
        logger.warning(f"Invalid SCIM ID format: {group_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if group exists
    existing_group = get_group(db, group_id)
    if not existing_group:
        logger.warning(f"Group not found: {group_id}")
        raise HTTPException(
            status_code=404,
            detail="Group not found"
        )
    
    # Delete group
    success = delete_group(db, group_id)
    if not success:
        logger.error(f"Failed to delete group: {group_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete group"
        )
    
    logger.info(f"Group deleted successfully: {group_id}")
    return None 