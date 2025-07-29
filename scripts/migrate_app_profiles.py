#!/usr/bin/env python3
"""
Database Migration Script for App Profiles

This script adds the necessary database schema changes to support app profiles:
1. Creates the app_profiles table
2. Adds app_profile_id column to the users table
3. Creates the AppProfile model in the database
"""

import sys
import os
from sqlalchemy import text, inspect

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.database import SessionLocal, init_db, engine, Base
from scim_server.models import User, AppProfile
from loguru import logger

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)

def check_table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def migrate_app_profiles():
    """Migrate database to support app profiles."""
    logger.info("Starting app profiles database migration...")
    
    db = SessionLocal()
    
    try:
        # Check if app_profiles table exists
        if not check_table_exists('app_profiles'):
            logger.info("Creating app_profiles table...")
            AppProfile.__table__.create(engine, checkfirst=True)
            logger.info("app_profiles table created successfully")
        else:
            logger.info("app_profiles table already exists")
        
        # Check if app_profile_id column exists in users table
        if not check_column_exists('users', 'app_profile_id'):
            logger.info("Adding app_profile_id column to users table...")
            
            # Add the column
            with engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN app_profile_id VARCHAR(255) 
                    REFERENCES app_profiles(profile_id)
                """))
                conn.commit()
            
            logger.info("app_profile_id column added successfully")
        else:
            logger.info("app_profile_id column already exists in users table")
        
        # Verify the migration
        logger.info("Verifying migration...")
        
        if check_table_exists('app_profiles'):
            logger.info("✅ app_profiles table exists")
        else:
            logger.error("❌ app_profiles table does not exist")
            return False
        
        if check_column_exists('users', 'app_profile_id'):
            logger.info("✅ app_profile_id column exists in users table")
        else:
            logger.error("❌ app_profile_id column does not exist in users table")
            return False
        
        logger.info("🎉 App profiles database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main migration function."""
    logger.info("Starting app profiles database migration...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Run migration
    success = migrate_app_profiles()
    
    if success:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 