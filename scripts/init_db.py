#!/usr/bin/env python3
"""
Database initialization script for SCIM.Cloud
Creates initial API key and sample data for development.
"""
import sys
import os
# Removed hashlib import - no longer needed
from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.database import init_db, SessionLocal
# Removed ApiKey import - no longer needed

def create_default_api_key():
    """Display API key information for development."""
    from scim_server.config import settings
    
    logger.info("API key validation is now centralized in config")
    logger.info(f"Default API key: {settings.default_api_key}")
    logger.info(f"Test API key: {settings.test_api_key}")
    logger.info(f"Use these tokens in Authorization header: Bearer <key>")

def main():
    """Main initialization function."""
    logger.info("Initializing SCIM.Cloud database...")
    
    # Initialize database tables
    init_db()
    
    # Create default API key
    create_default_api_key()
    
    logger.info("Database initialization complete!")

if __name__ == "__main__":
    main() 