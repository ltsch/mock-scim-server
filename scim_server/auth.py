from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from loguru import logger
import hashlib
from .database import get_db
from .models import ApiKey

async def get_api_key(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> ApiKey:
    """
    Validate API key from Authorization header.
    Returns the API key object if valid, raises 401 if invalid/missing.
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
    
    # Hash the token for comparison (security best practice)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Look up the API key in the database
    api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == token_hash,
        ApiKey.is_active == True
    ).first()
    
    if not api_key:
        logger.warning(f"Invalid or inactive API key attempted")
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key"
        )
    
    logger.info(f"Valid API key used: {api_key.name}")
    return api_key 