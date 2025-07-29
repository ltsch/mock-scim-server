"""
Main API router for SCIM server

This module provides the main API endpoints that are served under /api/
"""

from fastapi import APIRouter, Depends
from .auth import get_api_key
from .routing_config import get_routing_config, get_compatibility_info

# Create router for main API endpoints
router = APIRouter(prefix="/api", tags=["API"])


@router.get("/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "SCIM.Cloud Development Server",
        "version": "1.0.0",
        "description": "SCIM 2.0 server with Okta compatibility",
        "endpoints": {
            "frontend": "/frontend/index.html",
            "health": "/healthz",
            "routing": "/api/routing"
        }
    }


@router.get("/protected")
async def protected_endpoint(api_key: str = Depends(get_api_key)):
    """Test endpoint to verify authentication is working."""
    return {
        "message": "Authentication successful",
        "api_key_name": "Test API Key" if api_key == "test" else "Default API Key"
    }


@router.get("/routing")
async def get_routing_info(api_key: str = Depends(get_api_key)):
    """
    Get information about the current routing configuration and SCIM client compatibility.
    This helps developers understand how to configure their SCIM clients.
    """
    routing_config = get_routing_config()
    compatibility_info = get_compatibility_info()
    
    return {
        "routing_strategy": routing_config.strategy.value,
        "enabled_strategies": [s.value for s in routing_config.enabled_strategies],
        "url_patterns": routing_config.get_url_patterns(),
        "compatibility": compatibility_info,
        "recommendations": {
            "best_for_scim_clients": "path_parameter",
            "best_for_okta": "hybrid",
            "best_for_custom_clients": "query_parameter"
        }
    }