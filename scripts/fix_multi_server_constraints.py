#!/usr/bin/env python3
"""
Database migration script to fix multi-server constraints.
This script removes global unique constraints and adds server-specific composite constraints.
"""

import sqlite3
from loguru import logger

def fix_multi_server_constraints():
    """Fix database constraints for multi-server functionality."""
    logger.info("🔧 Starting multi-server constraint migration...")
    
    conn = sqlite3.connect('scim.db')
    cursor = conn.cursor()
    
    try:
        # Check if we need to run this migration
        cursor.execute("PRAGMA table_info(users)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        # Check if the old global unique constraints exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        has_old_constraints = any('ix_users_user_name' in idx or 'ix_users_email' in idx for idx in indexes)
        
        if not has_old_constraints:
            logger.info("✅ Multi-server constraints already applied, skipping migration")
            return
        
        logger.info("📋 Found old global unique constraints, applying migration...")
        
        # Step 1: Drop old unique indexes
        logger.info("1. Dropping old unique indexes...")
        try:
            cursor.execute("DROP INDEX IF EXISTS ix_users_user_name")
            logger.info("   ✅ Dropped ix_users_user_name index")
        except Exception as e:
            logger.warning(f"   ⚠️ Could not drop ix_users_user_name: {e}")
        
        try:
            cursor.execute("DROP INDEX IF EXISTS ix_users_email")
            logger.info("   ✅ Dropped ix_users_email index")
        except Exception as e:
            logger.warning(f"   ⚠️ Could not drop ix_users_email: {e}")
        
        # Step 2: Create new composite unique constraints
        logger.info("2. Creating new composite unique constraints...")
        
        # Create composite unique constraint for (user_name, server_id)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_user_name_server 
            ON users (user_name, server_id)
        """)
        logger.info("   ✅ Created uq_user_name_server constraint")
        
        # Create composite unique constraint for (email, server_id)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_user_email_server 
            ON users (email, server_id)
        """)
        logger.info("   ✅ Created uq_user_email_server constraint")
        
        # Step 3: Verify the migration
        logger.info("3. Verifying migration...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        new_indexes = [row[0] for row in cursor.fetchall()]
        
        has_new_constraints = all(
            constraint in new_indexes 
            for constraint in ['uq_user_name_server', 'uq_user_email_server']
        )
        
        if has_new_constraints:
            logger.info("   ✅ New constraints verified successfully")
        else:
            raise Exception("Failed to create new constraints")
        
        # Step 4: Test multi-server functionality
        logger.info("4. Testing multi-server functionality...")
        
        # Test that we can have the same username in different servers
        test_username = "test_migration_user@example.com"
        
        # Insert test user in server 'test-server-1'
        cursor.execute("""
            INSERT INTO users (scim_id, user_name, display_name, server_id, active)
            VALUES (?, ?, ?, ?, ?)
        """, (f"test-{test_username}-1", test_username, "Test User 1", "test-server-1", True))
        
        # Insert same username in server 'test-server-2'
        cursor.execute("""
            INSERT INTO users (scim_id, user_name, display_name, server_id, active)
            VALUES (?, ?, ?, ?, ?)
        """, (f"test-{test_username}-2", test_username, "Test User 2", "test-server-2", True))
        
        logger.info("   ✅ Successfully created users with same username in different servers")
        
        # Clean up test data
        cursor.execute("DELETE FROM users WHERE scim_id LIKE 'test-%'")
        logger.info("   ✅ Cleaned up test data")
        
        conn.commit()
        logger.info("🎉 Multi-server constraint migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_multi_server_constraints() 