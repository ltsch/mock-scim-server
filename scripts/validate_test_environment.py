#!/usr/bin/env python3
"""
Test environment validation script.
This script validates that the SCIM server test environment is properly configured.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.database import SessionLocal
from scim_server.models import ApiKey, User, Group, Entitlement
from loguru import logger

def validate_test_environment():
    """Validate that the test environment is properly configured."""
    logger.info("🔍 Validating SCIM server test environment...")
    
    db = SessionLocal()
    try:
        # Check API keys
        api_keys = db.query(ApiKey).count()
        logger.info(f"📋 Found {api_keys} API keys in database")
        
        # Check test data
        users = db.query(User).count()
        groups = db.query(Group).count()
        entitlements = db.query(Entitlement).count()
        
        logger.info(f"👥 Found {users} users in database")
        logger.info(f"🏢 Found {groups} groups in database")
        logger.info(f"🎫 Found {entitlements} entitlements in database")
        
        # Validate minimum requirements
        validation_passed = True
        
        if users < 5:
            logger.error(f"❌ Expected at least 5 users, found {users}")
            validation_passed = False
        else:
            logger.info(f"✅ Users: {users} (minimum 5 required)")
        
        if groups < 5:
            logger.error(f"❌ Expected at least 5 groups, found {groups}")
            validation_passed = False
        else:
            logger.info(f"✅ Groups: {groups} (minimum 5 required)")
            
        if entitlements < 5:
            logger.error(f"❌ Expected at least 5 entitlements, found {entitlements}")
            validation_passed = False
        else:
            logger.info(f"✅ Entitlements: {entitlements} (minimum 5 required)")
        
        # Check for specific test users
        test_users = ["john.doe@example.com", "jane.smith@example.com", "bob.wilson@example.com"]
        logger.info("🔍 Checking for required test users...")
        for username in test_users:
            user = db.query(User).filter(User.user_name == username).first()
            if not user:
                logger.error(f"❌ Required test user '{username}' not found")
                validation_passed = False
            else:
                logger.info(f"✅ Found test user: {username}")
        
        # Check for specific test groups
        test_groups = ["Engineering Team", "Marketing Team", "Sales Team"]
        logger.info("🔍 Checking for required test groups...")
        for group_name in test_groups:
            group = db.query(Group).filter(Group.display_name == group_name).first()
            if not group:
                logger.error(f"❌ Required test group '{group_name}' not found")
                validation_passed = False
            else:
                logger.info(f"✅ Found test group: {group_name}")
        
        # Check for test API key
        from scim_server.config import settings
        test_key = settings.test_api_key
        import hashlib
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()
        api_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        if not api_key:
            logger.error(f"❌ Required test API key '{test_key}' not found")
            validation_passed = False
        else:
            logger.info(f"✅ Found test API key: {test_key}")
        
        if validation_passed:
            logger.info("🎉 Test environment validation PASSED")
            logger.info("✅ All tests should run successfully")
            return True
        else:
            logger.error("💥 Test environment validation FAILED")
            logger.error("📝 To fix, run: python scripts/create_test_data.py")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test environment validation failed with error: {e}")
        return False
    finally:
        db.close()

def main():
    """Main function to run validation."""
    success = validate_test_environment()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 