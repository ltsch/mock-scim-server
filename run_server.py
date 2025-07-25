#!/usr/bin/env python3
"""
Development server runner for SCIM.Cloud
"""
import uvicorn
from loguru import logger
from scim_server.config import settings

if __name__ == "__main__":
    logger.info("Starting SCIM.Cloud development server...")
    uvicorn.run(
        "scim_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level
    ) 