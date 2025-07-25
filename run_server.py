#!/usr/bin/env python3
"""
Development server runner for SCIM.Cloud
"""
import uvicorn
from loguru import logger

if __name__ == "__main__":
    logger.info("Starting SCIM.Cloud development server...")
    uvicorn.run(
        "scim_server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    ) 