from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from loguru import logger
from typing import List, Optional

from .database import get_db
from .auth import get_api_key
from .models import ApiKey, Entitlement
from .crud import create_entitlement, get_entitlement, get_entitlements, update_entitlement, delete_entitlement
from .schemas import EntitlementCreate, EntitlementUpdate, EntitlementResponse, EntitlementListResponse
from .utils import entitlement_to_scim_response, create_scim_list_response, parse_scim_filter, validate_scim_id
from .config import settings
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/v2/Entitlements", tags=["Entitlements"])

@router.post("/", response_model=EntitlementResponse, status_code=201)
@limiter.limit(f"{settings.rate_limit_create}/{settings.rate_limit_window}minute")
async def create_entitlement_endpoint(
    request: Request,
    entitlement_data: EntitlementCreate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Create a new entitlement."""
    logger.info(f"Creating entitlement: {entitlement_data.displayName}")
    
    # Create entitlement
    db_entitlement = create_entitlement(db, entitlement_data)
    
    # Convert to SCIM response format
    response = entitlement_to_scim_response(db_entitlement)
    
    logger.info(f"Entitlement created successfully: {db_entitlement.scim_id}")
    return response

@router.get("/", response_model=EntitlementListResponse)
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_entitlements_endpoint(
    request: Request,
    start_index: int = Query(1, ge=1, alias="startIndex", description="1-based index of the first result"),
    count: int = Query(settings.default_page_size, ge=1, le=settings.max_results_per_page, description="Number of results to return"),
    filter: Optional[str] = Query(None, alias="filter", description="SCIM filter query"),
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Get entitlements with optional filtering and pagination."""
    logger.info(f"Getting entitlements: startIndex={start_index}, count={count}, filter={filter}")
    
    # Calculate skip value (convert from 1-based to 0-based)
    skip = start_index - 1
    
    # Get entitlements from database with filter
    entitlements = get_entitlements(db, skip=skip, limit=count, filter_query=filter)
    
    # Get total count for pagination (with filter applied)
    if filter:
        # Get total count of filtered results
        filtered_entitlements = get_entitlements(db, skip=0, limit=settings.max_count_limit, filter_query=filter)
        total_count = len(filtered_entitlements)
    else:
        # Get total count of all entitlements
        total_count = db.query(Entitlement).count()
    
    # Convert to SCIM response format
    resources = [entitlement_to_scim_response(entitlement) for entitlement in entitlements]
    
    response = create_scim_list_response(
        resources=resources,
        total_results=total_count,
        start_index=start_index,
        items_per_page=len(resources)
    )
    
    logger.info(f"Returning {len(resources)} entitlements")
    return response

@router.get("/{entitlement_id}", response_model=EntitlementResponse)
async def get_entitlement_endpoint(
    entitlement_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Get a specific entitlement by ID."""
    logger.info(f"Getting entitlement: {entitlement_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(entitlement_id):
        logger.warning(f"Invalid SCIM ID format: {entitlement_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Get entitlement from database
    entitlement = get_entitlement(db, entitlement_id)
    if not entitlement:
        logger.warning(f"Entitlement not found: {entitlement_id}")
        raise HTTPException(
            status_code=404,
            detail="Entitlement not found"
        )
    
    # Convert to SCIM response format
    response = entitlement_to_scim_response(entitlement)
    
    logger.info(f"Entitlement retrieved successfully: {entitlement_id}")
    return response

@router.put("/{entitlement_id}", response_model=EntitlementResponse)
async def update_entitlement_endpoint(
    entitlement_id: str,
    entitlement_data: EntitlementUpdate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Update an entitlement."""
    logger.info(f"Updating entitlement: {entitlement_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(entitlement_id):
        logger.warning(f"Invalid SCIM ID format: {entitlement_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if entitlement exists
    existing_entitlement = get_entitlement(db, entitlement_id)
    if not existing_entitlement:
        logger.warning(f"Entitlement not found: {entitlement_id}")
        raise HTTPException(
            status_code=404,
            detail="Entitlement not found"
        )
    
    # Update entitlement
    updated_entitlement = update_entitlement(db, entitlement_id, entitlement_data)
    if not updated_entitlement:
        logger.error(f"Failed to update entitlement: {entitlement_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update entitlement"
        )
    
    # Convert to SCIM response format
    response = entitlement_to_scim_response(updated_entitlement)
    
    logger.info(f"Entitlement updated successfully: {entitlement_id}")
    return response

@router.patch("/{entitlement_id}", response_model=EntitlementResponse)
async def patch_entitlement_endpoint(
    entitlement_id: str,
    entitlement_data: EntitlementUpdate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Patch an entitlement (partial update)."""
    logger.info(f"Patching entitlement: {entitlement_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(entitlement_id):
        logger.warning(f"Invalid SCIM ID format: {entitlement_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if entitlement exists
    existing_entitlement = get_entitlement(db, entitlement_id)
    if not existing_entitlement:
        logger.warning(f"Entitlement not found: {entitlement_id}")
        raise HTTPException(
            status_code=404,
            detail="Entitlement not found"
        )
    
    # Update entitlement
    updated_entitlement = update_entitlement(db, entitlement_id, entitlement_data)
    if not updated_entitlement:
        logger.error(f"Failed to patch entitlement: {entitlement_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to patch entitlement"
        )
    
    # Convert to SCIM response format
    response = entitlement_to_scim_response(updated_entitlement)
    
    logger.info(f"Entitlement patched successfully: {entitlement_id}")
    return response

@router.delete("/{entitlement_id}", status_code=204)
async def delete_entitlement_endpoint(
    entitlement_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Delete an entitlement."""
    logger.info(f"Deleting entitlement: {entitlement_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(entitlement_id):
        logger.warning(f"Invalid SCIM ID format: {entitlement_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if entitlement exists
    existing_entitlement = get_entitlement(db, entitlement_id)
    if not existing_entitlement:
        logger.warning(f"Entitlement not found: {entitlement_id}")
        raise HTTPException(
            status_code=404,
            detail="Entitlement not found"
        )
    
    # Delete entitlement
    success = delete_entitlement(db, entitlement_id)
    if not success:
        logger.error(f"Failed to delete entitlement: {entitlement_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete entitlement"
        )
    
    logger.info(f"Entitlement deleted successfully: {entitlement_id}")
    return None 