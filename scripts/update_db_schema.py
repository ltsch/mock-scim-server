#!/usr/bin/env python3
"""
Script to update database schema for multi-server support
"""

import sqlite3
from loguru import logger

def update_database_schema():
    """Add server_id columns to all entity tables."""
    
    logger.info("Starting database schema update for multi-server support...")
    
    # Connect to the database
    conn = sqlite3.connect('scim.db')
    cursor = conn.cursor()
    
    try:
        # Check if server_id columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'server_id' not in columns:
            logger.info("Adding server_id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN server_id VARCHAR(255) DEFAULT 'default'")
            cursor.execute("CREATE INDEX idx_users_server_id ON users(server_id)")
        
        # Check groups table
        cursor.execute("PRAGMA table_info(groups)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'server_id' not in columns:
            logger.info("Adding server_id column to groups table...")
            cursor.execute("ALTER TABLE groups ADD COLUMN server_id VARCHAR(255) DEFAULT 'default'")
            cursor.execute("CREATE INDEX idx_groups_server_id ON groups(server_id)")
        
        # Check entitlements table
        cursor.execute("PRAGMA table_info(entitlements)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'server_id' not in columns:
            logger.info("Adding server_id column to entitlements table...")
            cursor.execute("ALTER TABLE entitlements ADD COLUMN server_id VARCHAR(255) DEFAULT 'default'")
            cursor.execute("CREATE INDEX idx_entitlements_server_id ON entitlements(server_id)")
        

        
        # Check schemas table
        cursor.execute("PRAGMA table_info(schemas)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'server_id' not in columns:
            logger.info("Adding server_id column to schemas table...")
            cursor.execute("ALTER TABLE schemas ADD COLUMN server_id VARCHAR(255) DEFAULT 'default'")
            cursor.execute("CREATE INDEX idx_schemas_server_id ON schemas(server_id)")
        
        # Commit the changes
        conn.commit()
        logger.info("Database schema updated successfully!")
        
        # Verify the changes
        logger.info("Verifying schema changes...")
        tables = ['users', 'groups', 'entitlements', 'schemas']
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [column[1] for column in cursor.fetchall()]
            if 'server_id' in columns:
                logger.info(f"✅ {table} table has server_id column")
            else:
                logger.error(f"❌ {table} table missing server_id column")
        
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema() 