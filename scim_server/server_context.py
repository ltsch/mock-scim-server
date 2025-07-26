from fastapi import Request, Query, Depends
from typing import Optional
from loguru import logger

def get_server_id(server_id: Optional[str] = Query(None, alias="serverID")) -> str:
    """
    Extract server ID from query parameters.
    Returns 'default' if no server ID is provided.
    """
    if server_id:
        logger.info(f"Using server ID: {server_id}")
        return server_id
    else:
        logger.info("No server ID provided, using default")
        return "default" 