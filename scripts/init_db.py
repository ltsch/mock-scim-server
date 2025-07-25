#!/usr/bin/env python3
"""
Database initialization script for SCIM.Cloud
Creates initial API key and sample data for development.
"""
import sys
import os
import hashlib
from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.database import init_db, SessionLocal
from scim_server.models import ApiKey

def create_default_api_key():
    """Create a default API key for development."""
    db = SessionLocal()
    try:
        # Check if default API key already exists
        existing_key = db.query(ApiKey).filter(ApiKey.name == "default-dev-key").first()
        if existing_key:
            logger.info("Default API key already exists")
            return
        
        # Create default API key
        default_token = "dev-api-key-12345"
        key_hash = hashlib.sha256(default_token.encode()).hexdigest()
        
        api_key = ApiKey(
            key_hash=key_hash,
            name="default-dev-key",
            is_active=True
        )
        
        db.add(api_key)
        db.commit()
        
        logger.info("Default API key created successfully")
        logger.info(f"Token: {default_token}")
        logger.info("Use this token in Authorization header: Bearer dev-api-key-12345")
        
    except Exception as e:
        logger.error(f"Error creating default API key: {e}")
        db.rollback()
    finally:
        db.close()

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