from fastapi import FastAPI, Depends, Request, HTTPException
from loguru import logger
import sys
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime

from .database import init_db, get_db
from .auth import get_api_key
# Removed ApiKey import - no longer needed
from .config import settings
# Legacy single-server routers removed - all endpoints now use multi-server path-based routing
from .routing_config import get_routing_config, get_compatibility_info


# Configure logging
logger.remove()

# Always log to console
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level.upper()
)

# Add file logging if enabled
if settings.log_to_file:
    import os
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger.add(
        settings.log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level.upper(),
        rotation=settings.log_file_rotation,
        retention=settings.log_file_retention,
        compression=settings.log_file_compression
    )

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    logger.info("Starting SCIM.Cloud server...")
    init_db()
    logger.info("SCIM.Cloud server started successfully")
    yield
    # Shutdown
    logger.info("Shutting down SCIM.Cloud server...")

app = FastAPI(
    title="SCIM.Cloud Development SCIM Server",
    description="A development-friendly SCIM 2.0 server with Okta compatibility",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming requests with detailed information.
    This helps developers debug routing and client issues.
    """
    # Extract request details
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    authorization = "present" if request.headers.get("authorization") else "missing"
    
    # Log the incoming request
    logger.info(
        f"REQUEST - URL: {request.url.path} | "
        f"Method: {request.method} | "
        f"Client: {client_ip} | "
        f"User-Agent: {user_agent[:100]} | "
        f"Auth: {authorization} | "
        f"Query: {dict(request.query_params)}"
    )
    
    # Process the request
    response = await call_next(request)
    
    # Log the response
    logger.info(
        f"RESPONSE - URL: {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Client: {client_ip}"
    )
    
    return response

# Add custom 404 handler for detailed logging
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """
    Custom 404 handler that logs detailed information about the request.
    This helps developers debug routing and URL issues.
    """
    # Extract detailed request information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    referer = request.headers.get("referer", "none")
    authorization = "present" if request.headers.get("authorization") else "missing"
    
    # Log detailed 404 information
    logger.warning(
        f"404 NOT FOUND - URL: {request.url.path} | "
        f"Method: {request.method} | "
        f"Client: {client_ip} | "
        f"User-Agent: {user_agent[:100]} | "
        f"Referer: {referer} | "
        f"Auth: {authorization} | "
        f"Query: {dict(request.query_params)} | "
        f"Headers: {dict(request.headers)}"
    )
    
    # Provide helpful response for developers
    response_data = {
        "error": "Not Found",
        "message": f"The requested URL '{request.url.path}' was not found on this server",
        "method": request.method,
        "timestamp": str(datetime.now()),
        "help": {
            "available_endpoints": [
                "/healthz",
                "/",
                "/protected",
                "/routing",
                "/scim/v2/Users",
                "/scim/v2/Groups", 
                "/scim/v2/Entitlements",
                "/scim/v2/ResourceTypes",
                "/scim/v2/Schemas",
                "/scim-identifier/{server_id}/scim/v2/Users",
                "/scim-identifier/{server_id}/scim/v2/Groups",
                "/scim-identifier/{server_id}/scim/v2/Entitlements",
                "/scim-identifier/{server_id}/scim/v2/ResourceTypes",
                "/scim-identifier/{server_id}/scim/v2/Schemas"
            ],
            "common_issues": [
                "Check if the URL path is correct",
                "Verify the server_id in path-based URLs",
                "Ensure authentication header is present",
                "Check if the endpoint supports the HTTP method"
            ],
            "debug_info": {
                "requested_path": request.url.path,
                "request_method": request.method,
                "query_parameters": dict(request.query_params),
                "has_authorization": bool(request.headers.get("authorization"))
            }
        }
    }
    
    return JSONResponse(
        status_code=404,
        content=response_data
    )

# Add general exception handler for other HTTP errors
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    General HTTP exception handler for detailed logging of all HTTP errors.
    """
    if exc.status_code == 404:
        # 404s are handled by the specific handler above
        raise exc
    
    # Extract detailed request information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    authorization = "present" if request.headers.get("authorization") else "missing"
    
    # Log detailed error information
    logger.warning(
        f"{exc.status_code} ERROR - URL: {request.url.path} | "
        f"Method: {request.method} | "
        f"Client: {client_ip} | "
        f"User-Agent: {user_agent[:100]} | "
        f"Auth: {authorization} | "
        f"Error: {exc.detail} | "
        f"Query: {dict(request.query_params)}"
    )
    
    # Return the original exception response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include only path-based multi-server routers
# All SCIM endpoints are now accessed via /scim-identifier/{server_id}/scim/v2/...
from .path_based_endpoints import create_path_based_routers
path_based_routers = create_path_based_routers()
for router in path_based_routers:
    app.include_router(router)


@app.get("/healthz", tags=["Health"])
def health_check():
    """Health check endpoint for readiness/liveness probes."""
    return {"status": "ok"}

@app.get("/", tags=["Root"])
def root():
    """Root endpoint with basic server information."""
    return {
        "name": "SCIM.Cloud Development Server",
        "version": "1.0.0",
        "description": "SCIM 2.0 server with Okta compatibility"
    }

@app.get("/protected", tags=["Auth"])
async def protected_endpoint(api_key: str = Depends(get_api_key)):
    """Test endpoint to verify authentication is working."""
    return {
        "message": "Authentication successful",
        "api_key_name": "Test API Key" if api_key == "test" else "Default API Key"
    }

@app.get("/routing", tags=["Configuration"])
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