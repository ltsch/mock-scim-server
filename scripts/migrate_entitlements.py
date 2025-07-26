#!/usr/bin/env python3
"""
Migration script to add missing entitlement columns
"""

import sqlite3
from loguru import logger

def migrate_entitlements():
    """Add missing entitlement columns to the database."""
    
    logger.info("Starting entitlement migration...")
    
    # Connect to the database
    conn = sqlite3.connect('scim.db')
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(entitlements)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'entitlement_type' not in columns:
            logger.info("Adding entitlement_type column to entitlements table...")
            cursor.execute("ALTER TABLE entitlements ADD COLUMN entitlement_type VARCHAR(100)")
        
        if 'multi_valued' not in columns:
            logger.info("Adding multi_valued column to entitlements table...")
            cursor.execute("ALTER TABLE entitlements ADD COLUMN multi_valued BOOLEAN DEFAULT FALSE")
        
        # Commit the changes
        conn.commit()
        logger.info("Entitlement migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(entitlements)")
        columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Entitlements table now has columns: {columns}")
        
    except Exception as e:
        logger.error(f"Error during entitlement migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_entitlements() 