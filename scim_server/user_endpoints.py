from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from loguru import logger
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import get_db
from .auth import get_api_key
from .models import ApiKey, User
from .crud import create_user, get_user, get_users, update_user, deactivate_user, get_user_by_username
from .schemas import UserCreate, UserUpdate, UserResponse, UserListResponse
from .utils import user_to_scim_response, create_scim_list_response, parse_scim_filter, validate_scim_id, create_error_response
from .config import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/v2/Users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=201)
@limiter.limit(f"{settings.rate_limit_create}/{settings.rate_limit_window}minute")
async def create_user_endpoint(
    request: Request,
    user_data: UserCreate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Create a new user."""
    logger.info(f"Creating user: {user_data.userName}")
    
    # Check if user already exists
    existing_user = get_user_by_username(db, user_data.userName)
    if existing_user:
        logger.warning(f"User with username {user_data.userName} already exists")
        raise HTTPException(
            status_code=409,
            detail=f"User with username '{user_data.userName}' already exists"
        )
    
    # Create user
    db_user = create_user(db, user_data)
    
    # Convert to SCIM response format
    response = user_to_scim_response(db_user)
    
    logger.info(f"User created successfully: {db_user.scim_id}")
    return response

@router.get("/", response_model=UserListResponse)
@limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
async def get_users_endpoint(
    request: Request,
    start_index: int = Query(1, ge=1, alias="startIndex", description="1-based index of the first result"),
    count: int = Query(settings.default_page_size, ge=1, le=settings.max_results_per_page, description="Number of results to return"),
    filter: Optional[str] = Query(None, alias="filter", description="SCIM filter query"),
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Get users with optional filtering and pagination."""
    logger.info(f"Getting users: startIndex={start_index}, count={count}, filter={filter}")
    
    # Calculate skip value (convert from 1-based to 0-based)
    skip = start_index - 1
    
    # Get users from database with filter
    users = get_users(db, skip=skip, limit=count, filter_query=filter)
    
    # Get total count for pagination (with filter applied)
    if filter:
        # Get total count of filtered results
        filtered_users = get_users(db, skip=0, limit=settings.max_count_limit, filter_query=filter)
        total_count = len(filtered_users)
    else:
        # Get total count of all users
        total_count = db.query(User).count()
    
    # Convert to SCIM response format
    resources = [user_to_scim_response(user) for user in users]
    
    response = create_scim_list_response(
        resources=resources,
        total_results=total_count,
        start_index=start_index,
        items_per_page=len(resources)
    )
    
    logger.info(f"Returning {len(resources)} users")
    return response

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID."""
    logger.info(f"Getting user: {user_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(user_id):
        logger.warning(f"Invalid SCIM ID format: {user_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Get user from database
    user = get_user(db, user_id)
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Convert to SCIM response format
    response = user_to_scim_response(user)
    
    logger.info(f"User retrieved successfully: {user_id}")
    return response

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: str,
    user_data: UserUpdate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Update a user."""
    logger.info(f"Updating user: {user_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(user_id):
        logger.warning(f"Invalid SCIM ID format: {user_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if user exists
    existing_user = get_user(db, user_id)
    if not existing_user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Update user
    updated_user = update_user(db, user_id, user_data)
    if not updated_user:
        logger.error(f"Failed to update user: {user_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user"
        )
    
    # Convert to SCIM response format
    response = user_to_scim_response(updated_user)
    
    logger.info(f"User updated successfully: {user_id}")
    return response

@router.patch("/{user_id}", response_model=UserResponse)
async def patch_user_endpoint(
    user_id: str,
    user_data: UserUpdate,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Patch a user (partial update)."""
    logger.info(f"Patching user: {user_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(user_id):
        logger.warning(f"Invalid SCIM ID format: {user_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if user exists
    existing_user = get_user(db, user_id)
    if not existing_user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Update user
    updated_user = update_user(db, user_id, user_data)
    if not updated_user:
        logger.error(f"Failed to patch user: {user_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to patch user"
        )
    
    # Convert to SCIM response format
    response = user_to_scim_response(updated_user)
    
    logger.info(f"User patched successfully: {user_id}")
    return response

@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """Deactivate a user (soft delete by setting active=False)."""
    logger.info(f"Deactivating user: {user_id}")
    
    # Validate SCIM ID format
    if not validate_scim_id(user_id):
        logger.warning(f"Invalid SCIM ID format: {user_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid SCIM ID format"
        )
    
    # Check if user exists
    existing_user = get_user(db, user_id)
    if not existing_user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Deactivate user (soft delete)
    success = deactivate_user(db, user_id)
    if not success:
        logger.error(f"Failed to deactivate user: {user_id}")
        raise HTTPException(
            status_code=500,
            detail="Failed to deactivate user"
        )
    
    logger.info(f"User deactivated successfully: {user_id}")
    return None 