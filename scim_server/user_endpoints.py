"""
Simplified User endpoints using base endpoint classes.
This module eliminates massive code duplication by using the BaseEntityEndpoint class.
"""

from fastapi import APIRouter
from .endpoint_base import BaseEntityEndpoint
from .crud_entities import user_crud
from .response_converter import user_converter
from .schemas import UserCreate, UserUpdate, UserResponse, UserListResponse

# Create router
from .config import settings

# Construct the API prefix dynamically
api_prefix = f"{settings.api_base_path}/scim/v2/Users"
router = APIRouter(prefix=api_prefix, tags=["Users"])

# Create endpoint handler using base class
# This single line replaces 253 lines of duplicated code!
user_endpoints = BaseEntityEndpoint(
    entity_type="User",
    router=router,
    crud_operations=user_crud,
    response_converter=user_converter,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    response_schema=UserResponse,
    list_response_schema=UserListResponse,
    schema_uri="urn:ietf:params:scim:schemas:core:2.0:User",
    supports_multi_server=True
)

# Add password change endpoint
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .database import get_db
from .auth import get_api_key, get_validated_server_id
from .server_config import get_server_config_manager
from .utils import validate_scim_id
from .crud_entities import user_crud
from .response_converter import user_converter
from slowapi import Limiter
from slowapi.util import get_remote_address
from loguru import logger

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@router.patch("/{user_id}/password")
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
    
    # Get password validation rules
    validation_rules = server_config.get_password_validation_rules(server_id)
    
    # Validate password against rules
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
    
    # In a real implementation, you would hash the password and store it
    # For this mock server, we'll just log the password change
    logger.info(f"Password changed successfully for user: {user_id} in server: {server_id}")
    
    # Return the updated user (without password in response)
    updated_user = user_converter.to_scim_response(user)
    return updated_user 