from fastapi import FastAPI, Depends
from loguru import logger
import sys
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .database import init_db, get_db
from .auth import get_api_key
from .models import ApiKey
from .config import settings
from .scim_endpoints import router as scim_router
from .user_endpoints import router as user_router
from .group_endpoints import router as group_router
from .entitlement_endpoints import router as entitlement_router


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level.upper()
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

# Include all SCIM endpoint routers
app.include_router(scim_router)
app.include_router(user_router)
app.include_router(group_router)
app.include_router(entitlement_router)


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
async def protected_endpoint(api_key: ApiKey = Depends(get_api_key)):
    """Test endpoint to verify authentication is working."""
    return {
        "message": "Authentication successful",
        "api_key_name": api_key.name
    } 