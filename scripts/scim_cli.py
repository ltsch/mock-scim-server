#!/usr/bin/env python3
"""
SCIM Server CLI Tool

A command-line interface for managing virtual SCIM servers in the SCIM.Cloud application.
This tool allows developers to create, list, and manage virtual SCIM servers with populated data.
"""

import sys
import os
import uuid
import argparse
# Removed hashlib import - no longer needed
import random
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import names module for realistic name generation
try:
    import names
except ImportError:
    print("Error: 'names' module not found. Please install it with: pip install names")
    sys.exit(1)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.database import SessionLocal, init_db, Base
from scim_server.models import User, Group, Entitlement, UserGroup, UserEntitlement, Schema
from scim_server.crud_simple import (
    create_user, create_group, create_entitlement,
    get_users, get_groups, get_entitlements,
    delete_user, delete_group, delete_entitlement
)
from scim_server.schemas import UserCreate, GroupCreate, EntitlementCreate
from scim_server.config import settings
from scim_server.server_config import get_server_config_manager
from loguru import logger

class SCIMCLI:
    """CLI tool for managing virtual SCIM servers."""
    
    def __init__(self) -> None:
        # Ensure database is initialized with all tables
        self._ensure_database_initialized()
        self.db = SessionLocal()
        self.defaults = {
            'users': settings.cli_default_users,
            'groups': settings.cli_default_groups,
            'entitlements': settings.cli_default_entitlements
        }
    
    def _ensure_database_initialized(self) -> None:
        """Ensure the database is properly initialized with all tables."""
        try:
            # Initialize database with all tables
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def __del__(self) -> None:
        """Cleanup database connection."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_unique_server_ids(self) -> List[str]:
        """Get all unique server IDs from the database."""
        try:
            # Query all tables for unique server IDs
            user_servers = [r[0] for r in self.db.query(User.server_id.distinct()).all()]
            group_servers = [r[0] for r in self.db.query(Group.server_id.distinct()).all()]
            entitlement_servers = [r[0] for r in self.db.query(Entitlement.server_id.distinct()).all()]
            
            # Combine and deduplicate
            all_servers = set(user_servers + group_servers + entitlement_servers)
            return sorted(list(all_servers))
        except Exception as e:
            logger.error(f"Error getting server IDs: {e}")
            return []
    
    def get_server_stats(self, server_id: str) -> Dict[str, int]:
        """Get statistics for a specific server."""
        try:
            # Get basic counts
            users = self.db.query(User).filter(User.server_id == server_id).all()
            groups = self.db.query(Group).filter(Group.server_id == server_id).all()
            entitlements = self.db.query(Entitlement).filter(Entitlement.server_id == server_id).all()
            
            # Get user IDs for relationship counting
            user_ids = [user.id for user in users]
            
            # Count relationships
            user_group_relationships = 0
            user_entitlement_relationships = 0
            
            if user_ids:
                user_group_relationships = self.db.query(UserGroup).filter(UserGroup.user_id.in_(user_ids)).count()
                user_entitlement_relationships = self.db.query(UserEntitlement).filter(UserEntitlement.user_id.in_(user_ids)).count()
            
            stats = {
                'users': len(users),
                'groups': len(groups),
                'entitlements': len(entitlements),
                'user_group_relationships': user_group_relationships,
                'user_entitlement_relationships': user_entitlement_relationships
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return {
                'users': 0, 'groups': 0, 'entitlements': 0,
                'user_group_relationships': 0, 'user_entitlement_relationships': 0
            }
    
    def generate_server_id(self) -> str:
        """Generate a unique server ID."""
        return str(uuid.uuid4())
    
    def create_test_api_keys(self) -> None:
        """Display API key information (no longer stored in database)."""
        try:
            logger.info("API key validation is now centralized in config")
            logger.info(f"Default API key: {settings.default_api_key}")
            logger.info(f"Test API key: {settings.test_api_key}")
            logger.info("API keys are validated against config, not stored in database")
            
        except Exception as e:
            logger.error(f"Error displaying API key info: {e}")
    
    def create_test_users(self, server_id: str, count: int) -> None:
        """Create realistic test users for a specific server with diverse attributes."""
        try:
            existing_count = self.db.query(User).filter(User.server_id == server_id).count()
            if existing_count >= count:
                logger.info(f"Server {server_id} already has {existing_count} users (requested: {count})")
                return
            
            users_to_create = count - existing_count
            logger.info(f"Creating {users_to_create} realistic users for server {server_id}")
            
            # Get available groups and entitlements for this server
            available_groups = get_groups(self.db, server_id=server_id)
            available_entitlements = get_entitlements(self.db, server_id=server_id)
            
            created_users = []
            
            for i in range(users_to_create):
                user_num = existing_count + i + 1
                
                # Generate realistic user data using names module
                full_name = names.get_full_name()
                name_parts = full_name.split()
                first_name = name_parts[0]
                last_name = name_parts[-1] if len(name_parts) > 1 else "User"
                display_name = full_name
                
                # Generate email with realistic patterns
                email_patterns = [
                    f"{first_name.lower()}.{last_name.lower()}",
                    f"{first_name.lower()}{last_name.lower()}",
                    f"{first_name.lower()}{last_name.lower()[0]}",
                    f"{last_name.lower()}.{first_name.lower()}",
                    f"{first_name.lower()}_{last_name.lower()}",
                    f"{first_name.lower()}{random.randint(1, 999)}"
                ]
                email_local = random.choice(email_patterns)
                domain = random.choice(settings.cli_company_domains)
                email = f"{email_local}@{domain}"
                
                # Determine if user should be active
                active = random.random() < settings.cli_user_active_rate
                
                # Create user data
                user_data = UserCreate(
                    userName=email,
                    displayName=display_name,
                    givenName=first_name,
                    familyName=last_name,
                    emails=[{"value": email, "primary": True}],
                    active=active
                )
                
                # Create the user
                user = create_user(self.db, user_data, server_id)
                created_users.append(user)
            
            self.db.commit()
            logger.info(f"Created {users_to_create} realistic users for server {server_id}")
            
            # Create relationships after all users are created
            self._create_user_relationships(server_id, created_users, available_groups, available_entitlements)
            
        except Exception as e:
            logger.error(f"Error creating users for server {server_id}: {e}")
            self.db.rollback()
    
    def _create_user_relationships(self, server_id: str, users: List[User], groups: List[Group], 
                                 entitlements: List[Entitlement]) -> None:
        """Create realistic user relationships with groups and entitlements."""
        try:
            logger.info(f"Creating user relationships for server {server_id}")
            
            for user in users:
                # Determine if user should have multiple groups
                has_multiple_groups = random.random() < settings.cli_user_multiple_groups_rate
                num_groups = random.randint(1, min(settings.cli_max_groups_per_user, len(groups))) if has_multiple_groups else 1
                
                # Assign groups
                if groups:
                    selected_groups = random.sample(groups, min(num_groups, len(groups)))
                    for group in selected_groups:
                        # Check if relationship already exists
                        existing = self.db.query(UserGroup).filter(
                            UserGroup.user_id == user.id,
                            UserGroup.group_id == group.id
                        ).first()
                        
                        if not existing:
                            user_group = UserGroup(user_id=user.id, group_id=group.id)
                            self.db.add(user_group)
                            logger.debug(f"Added user {user.user_name} to group {group.display_name}")
                
                # Determine if user should have entitlements
                if random.random() < settings.cli_user_entitlements_rate and entitlements:
                    num_entitlements = random.randint(1, min(settings.cli_max_entitlements_per_user, len(entitlements)))
                    selected_entitlements = random.sample(entitlements, num_entitlements)
                    
                    for entitlement in selected_entitlements:
                        # Check if relationship already exists
                        existing = self.db.query(UserEntitlement).filter(
                            UserEntitlement.user_id == user.id,
                            UserEntitlement.entitlement_id == entitlement.id
                        ).first()
                        
                        if not existing:
                            user_entitlement = UserEntitlement(user_id=user.id, entitlement_id=entitlement.id)
                            self.db.add(user_entitlement)
                            logger.debug(f"Added entitlement {entitlement.display_name} to user {user.user_name}")
            
            self.db.commit()
            logger.info(f"Created user relationships for server {server_id}")
            
        except Exception as e:
            logger.error(f"Error creating user relationships for server {server_id}: {e}")
            self.db.rollback()
    
    def create_test_groups(self, server_id: str, count: int) -> None:
        """Create test groups for a specific server."""
        try:
            existing_count = self.db.query(Group).filter(Group.server_id == server_id).count()
            if existing_count >= count:
                logger.info(f"Server {server_id} already has {existing_count} groups (requested: {count})")
                return
            
            groups_to_create = count - existing_count
            logger.info(f"Creating {groups_to_create} groups for server {server_id}")
            
            group_names = settings.cli_group_names
            
            for i in range(groups_to_create):
                group_num = existing_count + i + 1
                group_name = group_names[i] if i < len(group_names) else f"Team {group_num}"
                
                group_data = GroupCreate(
                    displayName=group_name,
                    description=f"Test group {group_num} for server {server_id[:8]}"
                )
                create_group(self.db, group_data, server_id)
            
            self.db.commit()
            logger.info(f"Created {groups_to_create} groups for server {server_id}")
            
        except Exception as e:
            logger.error(f"Error creating groups for server {server_id}: {e}")
            self.db.rollback()
    
    def create_test_entitlements(self, server_id: str, count: int) -> None:
        """Create test entitlements for a specific server using enhanced entitlement definitions."""
        try:
            existing_count = self.db.query(Entitlement).filter(Entitlement.server_id == server_id).count()
            if existing_count >= count:
                logger.info(f"Server {server_id} already has {existing_count} entitlements (requested: {count})")
                return
            
            entitlements_to_create = count - existing_count
            logger.info(f"Creating {entitlements_to_create} entitlements for server {server_id}")
            
            # Use the enhanced entitlement definitions from config
            entitlement_definitions = settings.cli_entitlement_definitions
            
            for i in range(entitlements_to_create):
                entitlement_num = existing_count + i + 1
                
                if i < len(entitlement_definitions):
                    # Use predefined entitlement definitions
                    entitlement_def = entitlement_definitions[i]
                    # Select a random canonical value for this entitlement
                    canonical_value = random.choice(entitlement_def["canonical_values"])
                    
                    entitlement_data = EntitlementCreate(
                        displayName=entitlement_def["name"],
                        type=canonical_value,
                        description=entitlement_def["description"],
                        entitlementType=entitlement_def["type"],
                        multiValued=entitlement_def["multi_valued"]
                    )
                    
                    logger.debug(f"Creating entitlement: {entitlement_def['name']} ({canonical_value}) - Multi-valued: {entitlement_def['multi_valued']}")
                else:
                    # Fallback for additional entitlements beyond predefined definitions
                    fallback_types = ["Profile", "License", "Access", "Permission"]
                    fallback_type = random.choice(fallback_types)
                    
                    entitlement_data = EntitlementCreate(
                        displayName=f"Entitlement {entitlement_num}",
                        type=fallback_type,
                        description=f"Additional test entitlement {entitlement_num} for server {server_id[:8]}",
                        entitlementType="permission_based",
                        multiValued=False
                    )
                    
                    logger.debug(f"Creating fallback entitlement: Entitlement {entitlement_num} ({fallback_type})")
                
                create_entitlement(self.db, entitlement_data, server_id)
            
            self.db.commit()
            logger.info(f"Created {entitlements_to_create} entitlements for server {server_id}")
            
        except Exception as e:
            logger.error(f"Error creating entitlements for server {server_id}: {e}")
            self.db.rollback()
    
    def create_virtual_server(self, server_id: Optional[str] = None, users: int = None, 
                            groups: int = None, entitlements: int = None, app_profile: Optional[str] = None) -> Dict[str, Any]:
        """Create a new virtual SCIM server with populated data."""
        try:
            # Generate server ID if not provided
            if not server_id:
                server_id = self.generate_server_id()
            
            # Use defaults if not specified
            users = users if users is not None else self.defaults['users']
            groups = groups if groups is not None else self.defaults['groups']
            entitlements = entitlements if entitlements is not None else self.defaults['entitlements']
            
            logger.info(f"Creating virtual SCIM server: {server_id}")
            logger.info(f"Configuration: {users} users, {groups} groups, {entitlements} entitlements")
            
            # Ensure API keys exist
            self.create_test_api_keys()
            
            # Create test data for the server in the correct order
            # Groups and entitlements must be created before users for relationships
            self.create_test_groups(server_id, groups)
            self.create_test_entitlements(server_id, entitlements)
            self.create_test_users(server_id, users)  # This will also create relationships
            
            # Apply app profile if specified
            if app_profile:
                try:
                    server_config_manager = get_server_config_manager(self.db)
                    server_config_manager.set_server_app_profile(server_id, app_profile)
                    logger.info(f"Applied app profile '{app_profile}' to server {server_id}")
                except Exception as e:
                    logger.warning(f"Failed to apply app profile '{app_profile}': {e}")
            
            # Get final stats
            stats = self.get_server_stats(server_id)
            
            result = {
                "server_id": server_id,
                "stats": stats,
                "app_profile": app_profile,
                "access_url": f"http://{settings.client_host}:{settings.port}{settings.api_base_path}/scim/v2/Users?serverID={server_id}"
            }
            
            logger.info(f"Virtual SCIM server '{server_id}' created successfully!")
            if app_profile:
                logger.info(f"App Profile: {app_profile}")
            logger.info(f"Final stats: {stats['users']} users, {stats['groups']} groups, "
                       f"{stats['entitlements']} entitlements")
            logger.info(f"Relationships: {stats['user_group_relationships']} user-group, "
                       f"{stats['user_entitlement_relationships']} user-entitlement")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating virtual server: {e}")
            self.db.rollback()
            raise
    
    def list_servers(self) -> Dict[str, Any]:
        """List all virtual SCIM servers with their statistics."""
        try:
            server_ids = self.get_unique_server_ids()
            
            if not server_ids:
                logger.info("No virtual SCIM servers found in the database.")
                return {"servers": [], "total": 0}
            
            result = {
                "servers": [],
                "total": len(server_ids)
            }
            
            logger.info(f"Found {len(server_ids)} virtual SCIM server(s):")
            logger.info("-" * 80)
            
            for server_id in server_ids:
                stats = self.get_server_stats(server_id)
                server_data = {
                    "server_id": server_id,
                    "stats": stats
                }
                result["servers"].append(server_data)
                
                logger.info(f"Server ID: {server_id}")
                logger.info(f"  Users: {stats['users']}")
                logger.info(f"  Groups: {stats['groups']}")
                logger.info(f"  Entitlements: {stats['entitlements']}")
                logger.info(f"  User-Group Relationships: {stats['user_group_relationships']}")
                logger.info(f"  User-Entitlement Relationships: {stats['user_entitlement_relationships']}")
                logger.info("-" * 80)
            
            return result
                
        except Exception as e:
            logger.error(f"Error listing servers: {e}")
            return {"error": str(e)}
    
    def delete_server(self, server_id: str) -> Dict[str, Any]:
        """Delete a virtual SCIM server and all its data."""
        try:
            logger.info(f"Deleting virtual SCIM server: {server_id}")
            
            # Delete all data for this server
            users_deleted = self.db.query(User).filter(User.server_id == server_id).delete()
            groups_deleted = self.db.query(Group).filter(Group.server_id == server_id).delete()
            entitlements_deleted = self.db.query(Entitlement).filter(Entitlement.server_id == server_id).delete()
            
            self.db.commit()
            
            result = {
                "server_id": server_id,
                "deleted": {
                    "users": users_deleted,
                    "groups": groups_deleted,
                    "entitlements": entitlements_deleted
                }
            }
            
            logger.info(f"Deleted server '{server_id}' with:")
            logger.info(f"  {users_deleted} users")
            logger.info(f"  {groups_deleted} groups")
            logger.info(f"  {entitlements_deleted} entitlements")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting server {server_id}: {e}")
            self.db.rollback()
            return {"error": str(e)}
    
    def reset_database(self) -> Dict[str, Any]:
        """Reset the entire database (delete all data except API keys)."""
        try:
            logger.warning("This will delete ALL data from the database except API keys!")
            print("Are you sure you want to continue? (y/N): ", end="")
            
            response = input().strip().lower()
            if response not in ['y', 'yes']:
                logger.info("Database reset cancelled.")
                return {"cancelled": True}
            
            logger.info("Resetting database...")
            
            # Delete all data except API keys
            users_deleted = self.db.query(User).delete()
            groups_deleted = self.db.query(Group).delete()
            entitlements_deleted = self.db.query(Entitlement).delete()
    
            
            # Clear association tables
            user_groups_deleted = self.db.query(UserGroup).delete()
            user_entitlements_deleted = self.db.query(UserEntitlement).delete()
    
            
            self.db.commit()
            
            result = {
                "deleted": {
                    "users": users_deleted,
                    "groups": groups_deleted,
                    "entitlements": entitlements_deleted
                },
                "cleared": {
                    "user_group_relationships": user_groups_deleted,
                    "user_entitlement_relationships": user_entitlements_deleted
                }
            }
            
            logger.info("Database reset completed successfully!")
            logger.info(f"Deleted: {users_deleted} users, {groups_deleted} groups, "
                       f"{entitlements_deleted} entitlements")
            logger.info(f"Cleared: {user_groups_deleted} user-group relationships, "
                                   f"{user_entitlements_deleted} user-entitlement relationships")
            
            return result
            
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            self.db.rollback()
            return {"error": str(e)}
    
    def interactive_create_server(self) -> None:
        """Interactive mode for creating a virtual SCIM server."""
        try:
            logger.info("Creating a new virtual SCIM server...")
            logger.info("Press Enter to accept default values.")
            
            # Get server ID (optional)
            server_id = input(f"Server ID (leave empty for auto-generated UUID): ").strip()
            if not server_id:
                server_id = None
            
            # Get counts with defaults
            users = input(f"Number of users (default: {self.defaults['users']}): ").strip()
            users = int(users) if users else self.defaults['users']
            
            groups = input(f"Number of groups (default: {self.defaults['groups']}): ").strip()
            groups = int(groups) if groups else self.defaults['groups']
            
            entitlements = input(f"Number of entitlements (default: {self.defaults['entitlements']}): ").strip()
            entitlements = int(entitlements) if entitlements else self.defaults['entitlements']
            
            # Create the server
            result = self.create_virtual_server(server_id, users, groups, entitlements)
            
            logger.info(f"\nVirtual SCIM server created successfully!")
            logger.info(f"Server ID: {result['server_id']}")
            logger.info(f"Access URL: {result['access_url']}")
            
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
        except Exception as e:
            logger.error(f"Error creating server: {e}")
    
    def interactive_delete_server(self) -> Dict[str, Any]:
        """Interactive mode for deleting a virtual SCIM server."""
        try:
            server_ids = self.get_unique_server_ids()
            
            if not server_ids:
                logger.info("No virtual SCIM servers found to delete.")
                return {"error": "No servers found"}
            
            logger.info("Available servers:")
            for i, server_id in enumerate(server_ids, 1):
                stats = self.get_server_stats(server_id)
                logger.info(f"{i}. {server_id} ({stats['users']} users, {stats['groups']} groups)")
            
            choice = input(f"Select server to delete (1-{len(server_ids)}): ").strip()
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(server_ids):
                    server_id = server_ids[choice_idx]
                    return self.delete_server(server_id)
                else:
                    logger.error("Invalid selection.")
                    return {"error": "Invalid selection"}
            except ValueError:
                logger.error("Invalid input. Please enter a number.")
                return {"error": "Invalid input"}
                
        except Exception as e:
            logger.error(f"Error deleting server: {e}")
            return {"error": str(e)}
    
    def get_server_config(self, server_id: str) -> Dict[str, Any]:
        """Get configuration for a specific server."""
        try:
            config_manager = get_server_config_manager(self.db)
            config = config_manager.get_server_config(server_id)
            return config
        except Exception as e:
            logger.error(f"Error getting server config for {server_id}: {e}")
            return {"error": str(e)}
    
    def update_server_config(self, server_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration for a specific server."""
        try:
            config_manager = get_server_config_manager(self.db)
            config_manager.update_server_config(server_id, updates)
            logger.info(f"Updated configuration for server: {server_id}")
            return {"success": True, "server_id": server_id}
        except Exception as e:
            logger.error(f"Error updating server config for {server_id}: {e}")
            return {"error": str(e)}
    
    def list_server_configs(self) -> Dict[str, Any]:
        """List all server configurations."""
        try:
            server_ids = self.get_unique_server_ids()
            configs = {}
            
            for server_id in server_ids:
                config = self.get_server_config(server_id)
                if "error" not in config:
                    configs[server_id] = config
            
            return {"configs": configs, "total": len(configs)}
        except Exception as e:
            logger.error(f"Error listing server configs: {e}")
            return {"error": str(e)}
    
    def create_server_config(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new server configuration."""
        try:
            config_manager = get_server_config_manager(self.db)
            config_manager._save_server_config(server_id, config)
            logger.info(f"Created configuration for server: {server_id}")
            return {"success": True, "server_id": server_id}
        except Exception as e:
            logger.error(f"Error creating server config for {server_id}: {e}")
            return {"error": str(e)}
    
    def list_app_profiles(self) -> Dict[str, Any]:
        """List all available app profiles."""
        try:
            server_config_manager = get_server_config_manager(self.db)
            profiles = server_config_manager.get_available_app_profiles()
            return {
                "success": True,
                "total": len(profiles),
                "profiles": profiles
            }
        except Exception as e:
            logger.error(f"Error listing app profiles: {e}")
            return {"success": False, "error": str(e)}
    
    def get_app_profile_config(self, profile: str) -> Dict[str, Any]:
        """Get configuration for a specific app profile."""
        try:
            server_config_manager = get_server_config_manager(self.db)
            config = server_config_manager.get_app_profile_config(profile)
            if config:
                return {
                    "success": True,
                    "profile": profile,
                    "config": config
                }
            else:
                return {
                    "success": False,
                    "error": f"App profile '{profile}' not found"
                }
        except Exception as e:
            logger.error(f"Error getting app profile config: {e}")
            return {"success": False, "error": str(e)}
    
    def set_server_app_profile(self, server_id: str, profile: str) -> Dict[str, Any]:
        """Set app profile for a specific server."""
        try:
            server_config_manager = get_server_config_manager(self.db)
            server_config_manager.set_server_app_profile(server_id, profile)
            return {
                "success": True,
                "server_id": server_id,
                "profile": profile,
                "message": f"App profile '{profile}' set for server '{server_id}'"
            }
        except Exception as e:
            logger.error(f"Error setting app profile: {e}")
            return {"success": False, "error": str(e)}
    
    def output_json(self, data: Dict[str, Any]) -> None:
        """Shared function to output data in JSON format."""
        print(json.dumps(data, indent=2))


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SCIM Server CLI Tool - Manage virtual SCIM servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default when no parameters provided)
  python scripts/scim_cli.py create
  
  # Use defaults from config.py
  python scripts/scim_cli.py create --defaults
  
  # Command line mode
  python scripts/scim_cli.py create --users 20 --groups 8 --entitlements 12
  
  # Create server with HR app profile
  python scripts/scim_cli.py create --app-profile hr --defaults
  
  # Create server with IT app profile
  python scripts/scim_cli.py create --app-profile it --users 30 --groups 15 --entitlements 20
  
  # List all servers
  python scripts/scim_cli.py list
  
  # Delete a specific server
  python scripts/scim_cli.py delete --server-id abc123
  
  # Reset entire database
  python scripts/scim_cli.py reset
  
  # Get server configuration
  python scripts/scim_cli.py config get --server-id abc123
  
  # List all server configurations
  python scripts/scim_cli.py config list
  
  # Update server configuration from JSON file
  python scripts/scim_cli.py config update --server-id abc123 --config-file config.json
  
  # List available app profiles
  python scripts/scim_cli.py app-profile list
  
  # Get HR app profile configuration
  python scripts/scim_cli.py app-profile get --profile hr
  
  # Set IT app profile for existing server
  python scripts/scim_cli.py app-profile set --server-id abc123 --profile it
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new virtual SCIM server')
    create_parser.add_argument('--server-id', help='Custom server ID (auto-generated if not provided)')
    create_parser.add_argument('--users', type=int, help='Number of users to create')
    create_parser.add_argument('--groups', type=int, help='Number of groups to create')
    create_parser.add_argument('--entitlements', type=int, help='Number of entitlements to create')
    create_parser.add_argument('--defaults', action='store_true', 
                              help='Use default values from config.py (20 users, 10 groups, 12 entitlements)')
    create_parser.add_argument('--app-profile', choices=['hr', 'it', 'sales', 'marketing', 'finance', 'legal', 'operations', 'security', 'customer_success', 'research'],
                              help='Apply an app profile to the server')
    create_parser.add_argument('--interactive', '-i', action='store_true', 
                              help='Use interactive mode (ignores other parameters)')
    create_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all virtual SCIM servers')
    list_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a virtual SCIM server')
    delete_parser.add_argument('--server-id', required=True, help='Server ID to delete')
    delete_parser.add_argument('--interactive', '-i', action='store_true', 
                              help='Use interactive mode (ignores server-id parameter)')
    delete_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset the entire database (delete all data except API keys)')
    reset_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage server configurations')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Config subcommands')
    
    # Get config command
    get_config_parser = config_subparsers.add_parser('get', help='Get server configuration')
    get_config_parser.add_argument('--server-id', required=True, help='Server ID to get config for')
    get_config_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # List configs command
    list_configs_parser = config_subparsers.add_parser('list', help='List all server configurations')
    list_configs_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # Update config command
    update_config_parser = config_subparsers.add_parser('update', help='Update server configuration')
    update_config_parser.add_argument('--server-id', required=True, help='Server ID to update config for')
    update_config_parser.add_argument('--config-file', help='JSON file containing configuration updates')
    update_config_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # App Profile command
    app_profile_parser = subparsers.add_parser('app-profile', help='Manage app profiles')
    app_profile_subparsers = app_profile_parser.add_subparsers(dest='app_profile_command', help='App profile subcommands')
    
    # List app profiles command
    list_app_profiles_parser = app_profile_subparsers.add_parser('list', help='List available app profiles')
    list_app_profiles_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # Get app profile command
    get_app_profile_parser = app_profile_subparsers.add_parser('get', help='Get app profile configuration')
    get_app_profile_parser.add_argument('--profile', required=True, choices=['hr', 'it', 'sales', 'marketing', 'finance', 'legal', 'operations', 'security', 'customer_success', 'research'],
                                       help='App profile to get configuration for')
    get_app_profile_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    # Set app profile command
    set_app_profile_parser = app_profile_subparsers.add_parser('set', help='Set app profile for a server')
    set_app_profile_parser.add_argument('--server-id', required=True, help='Server ID to set app profile for')
    set_app_profile_parser.add_argument('--profile', required=True, choices=['hr', 'it', 'sales', 'marketing', 'finance', 'legal', 'operations', 'security', 'customer_success', 'research'],
                                       help='App profile to apply')
    set_app_profile_parser.add_argument('--json', action='store_true', help='Output in JSON format for machine parsing')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = SCIMCLI()
    
    try:
        if args.command == 'create':
            # Interactive mode if --interactive flag is set, or if no parameters are provided
            # Non-interactive mode if any of --server-id, --users, --groups, --entitlements are provided
            # Defaults mode if --defaults flag is set
            is_interactive = args.interactive or (not args.server_id and not args.users and not args.groups and not args.entitlements and not args.defaults)
            
            if is_interactive:
                result = cli.interactive_create_server()
            elif args.defaults:
                # Use defaults from config.py
                result = cli.create_virtual_server(
                    server_id=args.server_id,
                    users=settings.cli_default_users,
                    groups=settings.cli_default_groups,
                    entitlements=settings.cli_default_entitlements,
                    app_profile=args.app_profile
                )
                if args.json:
                    cli.output_json(result)
                else:
                    logger.info(f"\nVirtual SCIM server created successfully with defaults!")
                    logger.info(f"Server ID: {result['server_id']}")
                    logger.info(f"Access URL: {result['access_url']}")
                    if args.app_profile:
                        logger.info(f"App Profile: {args.app_profile}")
                    logger.info(f"Created: {settings.cli_default_users} users, {settings.cli_default_groups} groups, {settings.cli_default_entitlements} entitlements")
            else:
                result = cli.create_virtual_server(
                    server_id=args.server_id,
                    users=args.users,
                    groups=args.groups,
                    entitlements=args.entitlements,
                    app_profile=args.app_profile
                )
                if args.json:
                    cli.output_json(result)
                else:
                    logger.info(f"\nVirtual SCIM server created successfully!")
                    logger.info(f"Server ID: {result['server_id']}")
                    logger.info(f"Access URL: {result['access_url']}")
                    if args.app_profile:
                        logger.info(f"App Profile: {args.app_profile}")
        
        elif args.command == 'list':
            result = cli.list_servers()
            if args.json:
                cli.output_json(result)
        
        elif args.command == 'delete':
            if args.interactive:
                result = cli.interactive_delete_server()
            else:
                result = cli.delete_server(args.server_id)
            if args.json:
                cli.output_json(result)
        
        elif args.command == 'reset':
            result = cli.reset_database()
            if args.json:
                cli.output_json(result)
        
        elif args.command == 'config':
            if args.config_command == 'get':
                result = cli.get_server_config(args.server_id)
                if args.json:
                    cli.output_json(result)
                else:
                    logger.info(f"Configuration for server {args.server_id}:")
                    logger.info(json.dumps(result, indent=2))
            
            elif args.config_command == 'list':
                result = cli.list_server_configs()
                if args.json:
                    cli.output_json(result)
                else:
                    logger.info(f"Found {result.get('total', 0)} server configurations:")
                    for server_id, config in result.get('configs', {}).items():
                        logger.info(f"\nServer: {server_id}")
                        logger.info(f"  Enabled Resources: {config.get('enabled_resource_types', [])}")
                        logger.info(f"  Validation Rules: {config.get('validation_rules', {})}")
            
            elif args.config_command == 'update':
                if args.config_file:
                    try:
                        with open(args.config_file, 'r') as f:
                            updates = json.load(f)
                        result = cli.update_server_config(args.server_id, updates)
                        if args.json:
                            cli.output_json(result)
                        else:
                            if "success" in result:
                                logger.info(f"Successfully updated configuration for server {args.server_id}")
                            else:
                                logger.error(f"Failed to update configuration: {result.get('error', 'Unknown error')}")
                    except FileNotFoundError:
                        logger.error(f"Config file not found: {args.config_file}")
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in config file: {args.config_file}")
                else:
                    logger.error("Please provide a config file with --config-file")
        
        elif args.command == 'app-profile':
            if args.app_profile_command == 'list':
                result = cli.list_app_profiles()
                if args.json:
                    cli.output_json(result)
                else:
                    if result.get("success"):
                        logger.info(f"Available app profiles ({result['total']}):")
                        for profile in result['profiles']:
                            logger.info(f"  {profile['id']}: {profile['name']} - {profile['description']}")
                    else:
                        logger.error(f"Failed to list app profiles: {result.get('error', 'Unknown error')}")
            
            elif args.app_profile_command == 'get':
                result = cli.get_app_profile_config(args.profile)
                if args.json:
                    cli.output_json(result)
                else:
                    if result.get("success"):
                        config = result['config']
                        logger.info(f"App Profile: {config['name']}")
                        logger.info(f"Description: {config['description']}")
                        logger.info(f"Compatible Entitlements: {', '.join(config['compatible_entitlements'])}")
                        logger.info(f"Compatible Departments: {', '.join(config['compatible_departments'])}")
                        logger.info(f"Compatible Groups: {', '.join(config['compatible_groups'])}")
                    else:
                        logger.error(f"Failed to get app profile: {result.get('error', 'Unknown error')}")
            
            elif args.app_profile_command == 'set':
                result = cli.set_server_app_profile(args.server_id, args.profile)
                if args.json:
                    cli.output_json(result)
                else:
                    if result.get("success"):
                        logger.info(f"Successfully set app profile '{args.profile}' for server '{args.server_id}'")
                    else:
                        logger.error(f"Failed to set app profile: {result.get('error', 'Unknown error')}")
    
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 