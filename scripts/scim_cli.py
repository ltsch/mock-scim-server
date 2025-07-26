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
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scim_server.database import SessionLocal
from scim_server.models import ApiKey, User, Group, Entitlement, Role, UserGroup, UserEntitlement, UserRole
from scim_server.crud_simple import (
    create_user, create_group, create_entitlement, create_role,
    get_users, get_groups, get_entitlements, get_roles,
    delete_user, delete_group, delete_entitlement, delete_role
)
from scim_server.schemas import UserCreate, GroupCreate, EntitlementCreate, RoleCreate
from scim_server.config import settings
from loguru import logger

class SCIMCLI:
    """CLI tool for managing virtual SCIM servers."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.defaults = {
            'users': settings.cli_default_users,
            'groups': settings.cli_default_groups,
            'entitlements': settings.cli_default_entitlements,
            'roles': settings.cli_default_roles
        }
    
    def __del__(self):
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
            role_servers = [r[0] for r in self.db.query(Role.server_id.distinct()).all()]
            
            # Combine and deduplicate
            all_servers = set(user_servers + group_servers + entitlement_servers + role_servers)
            return sorted(list(all_servers))
        except Exception as e:
            logger.error(f"Error getting server IDs: {e}")
            return []
    
    def get_server_stats(self, server_id: str) -> Dict[str, int]:
        """Get statistics for a specific server."""
        try:
            stats = {
                'users': self.db.query(User).filter(User.server_id == server_id).count(),
                'groups': self.db.query(Group).filter(Group.server_id == server_id).count(),
                'entitlements': self.db.query(Entitlement).filter(Entitlement.server_id == server_id).count(),
                'roles': self.db.query(Role).filter(Role.server_id == server_id).count()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            return {'users': 0, 'groups': 0, 'entitlements': 0, 'roles': 0}
    
    def generate_server_id(self) -> str:
        """Generate a unique server ID."""
        return str(uuid.uuid4())
    
    def create_test_api_keys(self):
        """Create test API keys if they don't exist."""
        try:
            # Create test API key using configuration
            test_key = settings.test_api_key
            test_key_hash = hashlib.sha256(test_key.encode()).hexdigest()
            
            existing_key = self.db.query(ApiKey).filter(ApiKey.key_hash == test_key_hash).first()
            if not existing_key:
                api_key = ApiKey(
                    key_hash=test_key_hash,
                    name="Test API Key"
                )
                self.db.add(api_key)
                logger.info(f"Created test API key: {test_key}")
            
            self.db.commit()
            logger.info("Test API keys created successfully")
            
        except Exception as e:
            logger.error(f"Error creating test API keys: {e}")
            self.db.rollback()
    
    def create_test_users(self, server_id: str, count: int):
        """Create test users for a specific server."""
        try:
            existing_count = self.db.query(User).filter(User.server_id == server_id).count()
            if existing_count >= count:
                logger.info(f"Server {server_id} already has {existing_count} users (requested: {count})")
                return
            
            users_to_create = count - existing_count
            logger.info(f"Creating {users_to_create} users for server {server_id}")
            
            for i in range(users_to_create):
                user_num = existing_count + i + 1
                user_data = UserCreate(
                    userName=f"user{user_num}@server-{server_id[:8]}.com",
                    displayName=f"User {user_num}",
                    givenName=f"User{user_num}",
                    familyName=f"Server{server_id[:8]}",
                    emails=[{"value": f"user{user_num}@server-{server_id[:8]}.com", "primary": True}],
                    active=True
                )
                create_user(self.db, user_data, server_id)
            
            self.db.commit()
            logger.info(f"Created {users_to_create} users for server {server_id}")
            
        except Exception as e:
            logger.error(f"Error creating users for server {server_id}: {e}")
            self.db.rollback()
    
    def create_test_groups(self, server_id: str, count: int):
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
    
    def create_test_entitlements(self, server_id: str, count: int):
        """Create test entitlements for a specific server."""
        try:
            existing_count = self.db.query(Entitlement).filter(Entitlement.server_id == server_id).count()
            if existing_count >= count:
                logger.info(f"Server {server_id} already has {existing_count} entitlements (requested: {count})")
                return
            
            entitlements_to_create = count - existing_count
            logger.info(f"Creating {entitlements_to_create} entitlements for server {server_id}")
            
            entitlement_types = settings.cli_entitlement_types
            
            for i in range(entitlements_to_create):
                entitlement_num = existing_count + i + 1
                if i < len(entitlement_types):
                    display_name, entitlement_type = entitlement_types[i]
                else:
                    display_name = f"Entitlement {entitlement_num}"
                    entitlement_type = "Profile"
                
                entitlement_data = EntitlementCreate(
                    displayName=display_name,
                    type=entitlement_type,
                    description=f"Test entitlement {entitlement_num} for server {server_id[:8]}"
                )
                create_entitlement(self.db, entitlement_data, server_id)
            
            self.db.commit()
            logger.info(f"Created {entitlements_to_create} entitlements for server {server_id}")
            
        except Exception as e:
            logger.error(f"Error creating entitlements for server {server_id}: {e}")
            self.db.rollback()
    
    def create_test_roles(self, server_id: str, count: int):
        """Create test roles for a specific server."""
        try:
            existing_count = self.db.query(Role).filter(Role.server_id == server_id).count()
            if existing_count >= count:
                logger.info(f"Server {server_id} already has {existing_count} roles (requested: {count})")
                return
            
            roles_to_create = count - existing_count
            logger.info(f"Creating {roles_to_create} roles for server {server_id}")
            
            role_names = settings.cli_role_names
            
            for i in range(roles_to_create):
                role_num = existing_count + i + 1
                role_name = role_names[i] if i < len(role_names) else f"Role {role_num}"
                
                role_data = RoleCreate(
                    displayName=role_name,
                    description=f"Test role {role_num} for server {server_id[:8]}"
                )
                create_role(self.db, role_data, server_id)
            
            self.db.commit()
            logger.info(f"Created {roles_to_create} roles for server {server_id}")
            
        except Exception as e:
            logger.error(f"Error creating roles for server {server_id}: {e}")
            self.db.rollback()
    
    def create_virtual_server(self, server_id: Optional[str] = None, users: int = None, 
                            groups: int = None, entitlements: int = None, roles: int = None) -> str:
        """Create a new virtual SCIM server with populated data."""
        try:
            # Generate server ID if not provided
            if not server_id:
                server_id = self.generate_server_id()
            
            # Use defaults if not specified
            users = users if users is not None else self.defaults['users']
            groups = groups if groups is not None else self.defaults['groups']
            entitlements = entitlements if entitlements is not None else self.defaults['entitlements']
            roles = roles if roles is not None else self.defaults['roles']
            
            logger.info(f"Creating virtual SCIM server: {server_id}")
            logger.info(f"Configuration: {users} users, {groups} groups, {entitlements} entitlements, {roles} roles")
            
            # Ensure API keys exist
            self.create_test_api_keys()
            
            # Create test data for the server
            self.create_test_users(server_id, users)
            self.create_test_groups(server_id, groups)
            self.create_test_entitlements(server_id, entitlements)
            self.create_test_roles(server_id, roles)
            
            # Get final stats
            stats = self.get_server_stats(server_id)
            
            logger.info(f"Virtual SCIM server '{server_id}' created successfully!")
            logger.info(f"Final stats: {stats['users']} users, {stats['groups']} groups, "
                       f"{stats['entitlements']} entitlements, {stats['roles']} roles")
            
            return server_id
            
        except Exception as e:
            logger.error(f"Error creating virtual server: {e}")
            self.db.rollback()
            raise
    
    def list_servers(self):
        """List all virtual SCIM servers with their statistics."""
        try:
            server_ids = self.get_unique_server_ids()
            
            if not server_ids:
                logger.info("No virtual SCIM servers found in the database.")
                return
            
            logger.info(f"Found {len(server_ids)} virtual SCIM server(s):")
            logger.info("-" * 80)
            
            for server_id in server_ids:
                stats = self.get_server_stats(server_id)
                logger.info(f"Server ID: {server_id}")
                logger.info(f"  Users: {stats['users']}")
                logger.info(f"  Groups: {stats['groups']}")
                logger.info(f"  Entitlements: {stats['entitlements']}")
                logger.info(f"  Roles: {stats['roles']}")
                logger.info("-" * 80)
                
        except Exception as e:
            logger.error(f"Error listing servers: {e}")
    
    def delete_server(self, server_id: str):
        """Delete a virtual SCIM server and all its data."""
        try:
            logger.info(f"Deleting virtual SCIM server: {server_id}")
            
            # Delete all data for this server
            users_deleted = self.db.query(User).filter(User.server_id == server_id).delete()
            groups_deleted = self.db.query(Group).filter(Group.server_id == server_id).delete()
            entitlements_deleted = self.db.query(Entitlement).filter(Entitlement.server_id == server_id).delete()
            roles_deleted = self.db.query(Role).filter(Role.server_id == server_id).delete()
            
            self.db.commit()
            
            logger.info(f"Deleted server '{server_id}' with:")
            logger.info(f"  {users_deleted} users")
            logger.info(f"  {groups_deleted} groups")
            logger.info(f"  {entitlements_deleted} entitlements")
            logger.info(f"  {roles_deleted} roles")
            
        except Exception as e:
            logger.error(f"Error deleting server {server_id}: {e}")
            self.db.rollback()
            raise
    
    def reset_database(self):
        """Reset the entire database (delete all data except API keys)."""
        try:
            logger.warning("This will delete ALL data from the database except API keys!")
            logger.warning("Are you sure you want to continue? (y/N): ", end="")
            
            response = input().strip().lower()
            if response not in ['y', 'yes']:
                logger.info("Database reset cancelled.")
                return
            
            logger.info("Resetting database...")
            
            # Delete all data except API keys
            users_deleted = self.db.query(User).delete()
            groups_deleted = self.db.query(Group).delete()
            entitlements_deleted = self.db.query(Entitlement).delete()
            roles_deleted = self.db.query(Role).delete()
            
            # Clear association tables
            user_groups_deleted = self.db.query(UserGroup).delete()
            user_entitlements_deleted = self.db.query(UserEntitlement).delete()
            user_roles_deleted = self.db.query(UserRole).delete()
            
            self.db.commit()
            
            logger.info("Database reset completed successfully!")
            logger.info(f"Deleted: {users_deleted} users, {groups_deleted} groups, "
                       f"{entitlements_deleted} entitlements, {roles_deleted} roles")
            logger.info(f"Cleared: {user_groups_deleted} user-group relationships, "
                       f"{user_entitlements_deleted} user-entitlement relationships, "
                       f"{user_roles_deleted} user-role relationships")
            
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            self.db.rollback()
            raise
    
    def interactive_create_server(self):
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
            
            roles = input(f"Number of roles (default: {self.defaults['roles']}): ").strip()
            roles = int(roles) if roles else self.defaults['roles']
            
            # Create the server
            created_server_id = self.create_virtual_server(server_id, users, groups, entitlements, roles)
            
            logger.info(f"\nVirtual SCIM server created successfully!")
            logger.info(f"Server ID: {created_server_id}")
            logger.info(f"Access URL: http://localhost:6000/v2/Users?serverID={created_server_id}")
            
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
        except Exception as e:
            logger.error(f"Error creating server: {e}")
    
    def interactive_delete_server(self):
        """Interactive mode for deleting a virtual SCIM server."""
        try:
            server_ids = self.get_unique_server_ids()
            
            if not server_ids:
                logger.info("No virtual SCIM servers found to delete.")
                return
            
            logger.info("Available servers:")
            for i, server_id in enumerate(server_ids, 1):
                stats = self.get_server_stats(server_id)
                logger.info(f"{i}. {server_id} ({stats['users']} users, {stats['groups']} groups)")
            
            choice = input(f"Select server to delete (1-{len(server_ids)}): ").strip()
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(server_ids):
                    server_id = server_ids[choice_idx]
                    self.delete_server(server_id)
                else:
                    logger.error("Invalid selection.")
            except ValueError:
                logger.error("Invalid input. Please enter a number.")
                
        except Exception as e:
            logger.error(f"Error deleting server: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SCIM Server CLI Tool - Manage virtual SCIM servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python scripts/scim_cli.py create
  
  # Command line mode
  python scripts/scim_cli.py create --users 20 --groups 8 --entitlements 12 --roles 6
  
  # List all servers
  python scripts/scim_cli.py list
  
  # Delete a specific server
  python scripts/scim_cli.py delete --server-id abc123
  
  # Reset entire database
  python scripts/scim_cli.py reset
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new virtual SCIM server')
    create_parser.add_argument('--server-id', help='Custom server ID (auto-generated if not provided)')
    create_parser.add_argument('--users', type=int, help='Number of users to create')
    create_parser.add_argument('--groups', type=int, help='Number of groups to create')
    create_parser.add_argument('--entitlements', type=int, help='Number of entitlements to create')
    create_parser.add_argument('--roles', type=int, help='Number of roles to create')
    create_parser.add_argument('--interactive', '-i', action='store_true', 
                              help='Use interactive mode (ignores other parameters)')
    
    # List command
    subparsers.add_parser('list', help='List all virtual SCIM servers')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a virtual SCIM server')
    delete_parser.add_argument('--server-id', required=True, help='Server ID to delete')
    delete_parser.add_argument('--interactive', '-i', action='store_true', 
                              help='Use interactive mode (ignores server-id parameter)')
    
    # Reset command
    subparsers.add_parser('reset', help='Reset the entire database (delete all data except API keys)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = SCIMCLI()
    
    try:
        if args.command == 'create':
            if args.interactive:
                cli.interactive_create_server()
            else:
                server_id = cli.create_virtual_server(
                    server_id=args.server_id,
                    users=args.users,
                    groups=args.groups,
                    entitlements=args.entitlements,
                    roles=args.roles
                )
                logger.info(f"\nVirtual SCIM server created successfully!")
                logger.info(f"Server ID: {server_id}")
                logger.info(f"Access URL: http://localhost:6000/v2/Users?serverID={server_id}")
        
        elif args.command == 'list':
            cli.list_servers()
        
        elif args.command == 'delete':
            if args.interactive:
                cli.interactive_delete_server()
            else:
                cli.delete_server(args.server_id)
        
        elif args.command == 'reset':
            cli.reset_database()
    
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 