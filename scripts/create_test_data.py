#!/usr/bin/env python3
"""
Script to create test data for the SCIM server.
This script populates the database with sample users, groups, entitlements, roles, and relationships.
"""

import sys
import os
import uuid
import hashlib
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.database import SessionLocal
from scim_server.models import ApiKey, User, Group, Entitlement, Role, UserGroup, UserEntitlement, UserRole
from loguru import logger

def create_test_api_keys():
    """Create test API keys."""
    db = SessionLocal()
    try:
        # Create test API key
        test_key = "test-api-key-12345"
        test_key_hash = hashlib.sha256(test_key.encode()).hexdigest()
        
        existing_key = db.query(ApiKey).filter(ApiKey.key_hash == test_key_hash).first()
        if not existing_key:
            api_key = ApiKey(
                key_hash=test_key_hash,
                name="Test API Key"
            )
            db.add(api_key)
            logger.info("Created test API key: test-api-key-12345")
        
        db.commit()
        logger.info("Test API keys created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test API keys: {e}")
        db.rollback()
    finally:
        db.close()

def create_test_users():
    """Create test users."""
    db = SessionLocal()
    try:
        users_data = [
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "testuser@example.com",
                "display_name": "Test User",
                "given_name": "Test",
                "family_name": "User",
                "email": "testuser@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "john.doe@example.com",
                "display_name": "John Doe",
                "given_name": "John",
                "family_name": "Doe",
                "email": "john.doe@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "jane.smith@example.com",
                "display_name": "Jane Smith",
                "given_name": "Jane",
                "family_name": "Smith",
                "email": "jane.smith@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "bob.wilson@example.com",
                "display_name": "Bob Wilson",
                "given_name": "Bob",
                "family_name": "Wilson",
                "email": "bob.wilson@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "alice.johnson@example.com",
                "display_name": "Alice Johnson",
                "given_name": "Alice",
                "family_name": "Johnson",
                "email": "alice.johnson@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "charlie.brown@example.com",
                "display_name": "Charlie Brown",
                "given_name": "Charlie",
                "family_name": "Brown",
                "email": "charlie.brown@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "diana.prince@example.com",
                "display_name": "Diana Prince",
                "given_name": "Diana",
                "family_name": "Prince",
                "email": "diana.prince@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "edward.norton@example.com",
                "display_name": "Edward Norton",
                "given_name": "Edward",
                "family_name": "Norton",
                "email": "edward.norton@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "fiona.gallagher@example.com",
                "display_name": "Fiona Gallagher",
                "given_name": "Fiona",
                "family_name": "Gallagher",
                "email": "fiona.gallagher@example.com",
                "active": True
            },
            {
                "scim_id": str(uuid.uuid4()),
                "user_name": "george.martin@example.com",
                "display_name": "George Martin",
                "given_name": "George",
                "family_name": "Martin",
                "email": "george.martin@example.com",
                "active": False  # Inactive user
            }
        ]
        
        for user_data in users_data:
            existing_user = db.query(User).filter(User.user_name == user_data["user_name"]).first()
            if not existing_user:
                user = User(**user_data)
                db.add(user)
                logger.info(f"Created test user: {user_data['display_name']}")
        
        db.commit()
        logger.info("Test users created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test users: {e}")
        db.rollback()
    finally:
        db.close()

def create_test_groups():
    """Create test groups."""
    db = SessionLocal()
    try:
        groups_data = [
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Engineering Team",
                "description": "Software engineering team"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Marketing Team",
                "description": "Marketing and communications team"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Sales Team",
                "description": "Sales and business development team"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "HR Team",
                "description": "Human resources team"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Admins",
                "description": "System administrators"
            }
        ]
        
        for group_data in groups_data:
            existing_group = db.query(Group).filter(Group.scim_id == group_data["scim_id"]).first()
            if not existing_group:
                group = Group(**group_data)
                db.add(group)
                logger.info(f"Created test group: {group_data['display_name']}")
        
        db.commit()
        logger.info("Test groups created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test groups: {e}")
        db.rollback()
    finally:
        db.close()

def create_test_entitlements():
    """Create test entitlements."""
    db = SessionLocal()
    try:
        entitlements_data = [
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Office 365 License",
                "type": "License",
                "description": "Microsoft Office 365 license"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Salesforce Access",
                "type": "Profile",
                "description": "Salesforce CRM access"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "GitHub Pro",
                "type": "License",
                "description": "GitHub Pro subscription"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Slack Workspace",
                "type": "Profile",
                "description": "Slack workspace access"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "VPN Access",
                "type": "Profile",
                "description": "Corporate VPN access"
            }
        ]
        
        for entitlement_data in entitlements_data:
            existing_entitlement = db.query(Entitlement).filter(Entitlement.scim_id == entitlement_data["scim_id"]).first()
            if not existing_entitlement:
                entitlement = Entitlement(**entitlement_data)
                db.add(entitlement)
                logger.info(f"Created test entitlement: {entitlement_data['display_name']}")
        
        db.commit()
        logger.info("Test entitlements created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test entitlements: {e}")
        db.rollback()
    finally:
        db.close()

def create_test_roles():
    """Create test roles."""
    db = SessionLocal()
    try:
        roles_data = [
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Developer",
                "description": "Software developer role"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Manager",
                "description": "Team manager role"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Admin",
                "description": "System administrator role"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Analyst",
                "description": "Business analyst role"
            },
            {
                "scim_id": str(uuid.uuid4()),
                "display_name": "Designer",
                "description": "UI/UX designer role"
            }
        ]
        
        for role_data in roles_data:
            existing_role = db.query(Role).filter(Role.scim_id == role_data["scim_id"]).first()
            if not existing_role:
                role = Role(**role_data)
                db.add(role)
                logger.info(f"Created test role: {role_data['display_name']}")
        
        db.commit()
        logger.info("Test roles created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test roles: {e}")
        db.rollback()
    finally:
        db.close()

def create_user_group_relationships():
    """Create user-group relationships."""
    db = SessionLocal()
    try:
        # Get users and groups
        users = db.query(User).all()
        groups = db.query(Group).all()
        
        if not users or not groups:
            logger.warning("No users or groups found for relationship creation")
            return
        
        # Define relationships (user_name -> group_display_name)
        relationships = [
            ("john.doe@example.com", "Engineering Team"),
            ("jane.smith@example.com", "Engineering Team"),
            ("bob.wilson@example.com", "Engineering Team"),
            ("alice.johnson@example.com", "Marketing Team"),
            ("charlie.brown@example.com", "Sales Team"),
            ("diana.prince@example.com", "HR Team"),
            ("edward.norton@example.com", "Admins"),
            ("fiona.gallagher@example.com", "Marketing Team"),
            ("george.martin@example.com", "Sales Team")
        ]
        
        for username, group_name in relationships:
            user = db.query(User).filter(User.user_name == username).first()
            group = db.query(Group).filter(Group.display_name == group_name).first()
            
            if user and group:
                # Check if relationship already exists
                existing_relationship = db.query(UserGroup).filter(
                    UserGroup.user_id == user.id,
                    UserGroup.group_id == group.id
                ).first()
                
                if not existing_relationship:
                    relationship = UserGroup(user_id=user.id, group_id=group.id)
                    db.add(relationship)
                    logger.info(f"Created user-group relationship: {username} -> {group_name}")
        
        db.commit()
        logger.info("User-group relationships created successfully")
        
    except Exception as e:
        logger.error(f"Error creating user-group relationships: {e}")
        db.rollback()
    finally:
        db.close()

def create_user_entitlement_relationships():
    """Create user-entitlement relationships."""
    db = SessionLocal()
    try:
        # Get users and entitlements
        users = db.query(User).all()
        entitlements = db.query(Entitlement).all()
        
        if not users or not entitlements:
            logger.warning("No users or entitlements found for relationship creation")
            return
        
        # Define relationships (user_name -> entitlement_display_name)
        relationships = [
            ("john.doe@example.com", "Office 365 License"),
            ("jane.smith@example.com", "Office 365 License"),
            ("bob.wilson@example.com", "Office 365 License"),
            ("alice.johnson@example.com", "Office 365 License"),
            ("charlie.brown@example.com", "Office 365 License"),
            ("john.doe@example.com", "GitHub Pro"),
            ("jane.smith@example.com", "GitHub Pro"),
            ("bob.wilson@example.com", "GitHub Pro"),
            ("alice.johnson@example.com", "Salesforce Access"),
            ("charlie.brown@example.com", "Salesforce Access"),
            ("diana.prince@example.com", "Slack Workspace"),
            ("edward.norton@example.com", "VPN Access"),
            ("fiona.gallagher@example.com", "Office 365 License"),
            ("george.martin@example.com", "Salesforce Access")
        ]
        
        for username, entitlement_name in relationships:
            user = db.query(User).filter(User.user_name == username).first()
            entitlement = db.query(Entitlement).filter(Entitlement.display_name == entitlement_name).first()
            
            if user and entitlement:
                # Check if relationship already exists
                existing_relationship = db.query(UserEntitlement).filter(
                    UserEntitlement.user_id == user.id,
                    UserEntitlement.entitlement_id == entitlement.id
                ).first()
                
                if not existing_relationship:
                    relationship = UserEntitlement(user_id=user.id, entitlement_id=entitlement.id)
                    db.add(relationship)
                    logger.info(f"Created user-entitlement relationship: {username} -> {entitlement_name}")
        
        db.commit()
        logger.info("User-entitlement relationships created successfully")
        
    except Exception as e:
        logger.error(f"Error creating user-entitlement relationships: {e}")
        db.rollback()
    finally:
        db.close()

def create_user_role_relationships():
    """Create user-role relationships."""
    db = SessionLocal()
    try:
        # Get users and roles
        users = db.query(User).all()
        roles = db.query(Role).all()
        
        if not users or not roles:
            logger.warning("No users or roles found for relationship creation")
            return
        
        # Define relationships (user_name -> role_display_name)
        relationships = [
            ("john.doe@example.com", "Developer"),
            ("jane.smith@example.com", "Developer"),
            ("bob.wilson@example.com", "Developer"),
            ("alice.johnson@example.com", "Analyst"),
            ("charlie.brown@example.com", "Manager"),
            ("diana.prince@example.com", "Manager"),
            ("edward.norton@example.com", "Admin"),
            ("fiona.gallagher@example.com", "Designer"),
            ("george.martin@example.com", "Analyst")
        ]
        
        for username, role_name in relationships:
            user = db.query(User).filter(User.user_name == username).first()
            role = db.query(Role).filter(Role.display_name == role_name).first()
            
            if user and role:
                # Check if relationship already exists
                existing_relationship = db.query(UserRole).filter(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id
                ).first()
                
                if not existing_relationship:
                    relationship = UserRole(user_id=user.id, role_id=role.id)
                    db.add(relationship)
                    logger.info(f"Created user-role relationship: {username} -> {role_name}")
        
        db.commit()
        logger.info("User-role relationships created successfully")
        
    except Exception as e:
        logger.error(f"Error creating user-role relationships: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main function to create all test data."""
    logger.info("Starting test data creation...")
    
    # Create test data in order
    create_test_api_keys()
    create_test_users()
    create_test_groups()
    create_test_entitlements()
    create_test_roles()
    
    # Create relationships
    create_user_group_relationships()
    create_user_entitlement_relationships()
    create_user_role_relationships()
    
    logger.info("Test data creation completed successfully!")
    logger.info("Test API key: test-api-key-12345")

if __name__ == "__main__":
    main() 