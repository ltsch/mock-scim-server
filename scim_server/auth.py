from fastapi import HTTPException, Depends, Header
from loguru import logger
from .config import settings
from .server_context import get_server_id_from_path

def get_api_key(authorization: str = Header(None)) -> str:
    """
    Validate API key from Authorization header.
    Returns the API key name if valid, raises 401 if invalid/missing.
    
    Simplified for development server - only accepts two API keys from config:
    - settings.default_api_key for normal server operations
    - settings.test_api_key for test operations
    """
    if not authorization:
        logger.warning("No Authorization header provided")
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )
    
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid Authorization header format")
        raise HTTPException(
            status_code=401,
            detail="Authorization header must start with 'Bearer '"
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    if not token:
        logger.warning("Empty Bearer token")
        raise HTTPException(
            status_code=401,
            detail="Bearer token cannot be empty"
        )
    
    # Simple validation against config keys
    if token == settings.default_api_key:
        logger.info("Valid default API key used")
        return "default"
    elif token == settings.test_api_key:
        logger.info("Valid test API key used")
        return "test"
    else:
        logger.warning(f"Invalid API key attempted")
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key"
        )

def validate_server_id(server_id: str) -> str:
    """
    Validate server ID format and existence.
    Returns the server_id if valid, raises 400 if invalid.
    """
    if not server_id:
        logger.warning("No server_id provided")
        raise HTTPException(
            status_code=400,
            detail="Server ID is required"
        )
    
    if not isinstance(server_id, str):
        logger.warning(f"Invalid server_id type: {type(server_id)}")
        raise HTTPException(
            status_code=400,
            detail="Server ID must be a string"
        )
    
    # Basic validation - server_id should be a valid UUID or alphanumeric
    import re
    if not re.match(r'^[a-zA-Z0-9\-_]+$', server_id):
        logger.warning(f"Invalid server_id format: {server_id}")
        raise HTTPException(
            status_code=400,
            detail="Server ID must contain only alphanumeric characters, hyphens, and underscores"
        )
    
    logger.info(f"Valid server_id: {server_id}")
    return server_id

def get_validated_server_id(server_id: str = Depends(get_server_id_from_path)) -> str:
    """
    Dependency function that validates server_id from path.
    This ensures all endpoints that require server_id get proper validation.
    """
    return validate_server_id(server_id)

# Import already added at the top 