from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
import os
from fastapi.responses import HTMLResponse
import ipaddress

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

# Add custom 404 handler for secure error responses
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """
    Custom 404 handler that logs detailed information for debugging but returns minimal response.
    This prevents information disclosure while maintaining security.
    """
    # Extract request information for logging only
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    authorization = "present" if request.headers.get("authorization") else "missing"
    
    # Log detailed 404 information for debugging (server-side only)
    logger.warning(
        f"404 NOT FOUND - URL: {request.url.path} | "
        f"Method: {request.method} | "
        f"Client: {client_ip} | "
        f"User-Agent: {user_agent[:100]} | "
        f"Auth: {authorization} | "
        f"Query: {dict(request.query_params)}"
    )
    
    # Return minimal, secure response without exposing internal structure
    response_data = {
        "error": "Not Found",
        "message": "The requested resource was not found"
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

# Include frontend API router for web UI endpoints
from frontend.api import router as frontend_router
app.include_router(frontend_router)

# Include main API router
from .api_router import router as api_router
app.include_router(api_router)

# Mount static files for the frontend
app.mount("/frontend/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/healthz", tags=["Health"])
def health_check():
    """Health check endpoint for readiness/liveness probes. No authentication required."""
    try:
        # Basic health check - just return OK status
        # This endpoint is designed for Docker health checks and monitoring
        return {"status": "ok", "timestamp": str(datetime.now())}
    except Exception as e:
        # If there's any error, return 500 to indicate unhealthy state
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/health", tags=["Health"])
def detailed_health_check(request: Request):
    """Detailed health check endpoint for comprehensive monitoring. No authentication required."""
    try:
        # Import here to avoid circular imports
        from .database import SessionLocal
        from sqlalchemy import text
        
        # Check if the request is from an internal network
        client_ip = request.client.host if request.client else "unknown"
        if not is_internal_network(client_ip):
            logger.warning(f"Access to /health from external IP: {client_ip}")
            raise HTTPException(status_code=403, detail="Access denied from external network")

        # Check database connectivity
        db_status = "ok"
        try:
            db = SessionLocal()
            # Try a simple query to verify database is working
            db.execute(text("SELECT 1"))
            db.close()
        except Exception as e:
            db_status = f"error: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        health_info = {
            "status": "ok",
            "timestamp": str(datetime.now()),
            "version": "1.0.0",
            "database": db_status,
            "endpoints": {
                "healthz": "/healthz",
                "health": "/health",
                "frontend": "/frontend/index.html"
            }
        }
        
        # If database is not ok, return 503 (Service Unavailable)
        if db_status != "ok":
            return JSONResponse(
                status_code=503,
                content=health_info
            )
        
        return health_info
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/frontend/index.html", tags=["Frontend"])
async def frontend(request: Request):
    """Frontend web UI endpoint."""
    # Read the HTML file
    with open("frontend/static/index.html", "r") as f:
        html_content = f.read()
    
    # Get the Authorization header from the request
    auth_header = request.headers.get("authorization")
    
    # Inject the Authorization header into the HTML as a meta tag
    if auth_header:
        # Insert the meta tag in the head section
        meta_tag = f'<meta name="authorization" content="{auth_header}">'
        html_content = html_content.replace('<head>', f'<head>\n    {meta_tag}')
    
    return HTMLResponse(content=html_content) 

def is_internal_network(client_ip: str) -> bool:
    """
    Check if the client IP is from an internal/private network.
    Allows access from localhost, Docker networks, and private IP ranges.
    """
    try:
        # Special case for TestClient in testing
        if client_ip == "testclient":
            return True
        
        # Parse the IP address
        ip = ipaddress.ip_address(client_ip)
        
        # Allow localhost
        if ip.is_loopback:
            return True
        
        # Allow private networks (RFC 1918)
        if ip.is_private:
            return True
        
        # Allow link-local addresses
        if ip.is_link_local:
            return True
        
        # Allow Docker default networks (172.16.0.0/12)
        if ip in ipaddress.ip_network('172.16.0.0/12'):
            return True
        
        # Allow Docker bridge networks (192.168.0.0/16)
        if ip in ipaddress.ip_network('192.168.0.0/16'):
            return True
        
        return False
        
    except ValueError:
        # If we can't parse the IP, deny access for security
        logger.warning(f"Invalid IP address format: {client_ip}")
        return False 