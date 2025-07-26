"""
Simplified CRUD operations using centralized base functions.
This module provides a clean interface to all CRUD operations without duplication.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from .crud_entities import user_crud, group_crud, entitlement_crud, role_crud
from .schemas import UserCreate, UserUpdate, GroupCreate, GroupUpdate, EntitlementCreate, EntitlementUpdate, RoleCreate, RoleUpdate
from .models import User, Group, Entitlement, Role

# User CRUD operations
def create_user(db: Session, user_data: UserCreate, server_id: str = "default") -> User:
    """Create a new user."""
    return user_crud.create_user(db, user_data, server_id)

def get_user(db: Session, user_id: str, server_id: str = "default") -> Optional[User]:
    """Get user by SCIM ID within a specific server."""
    return user_crud.get_by_id(db, user_id, server_id)

def get_user_by_username(db: Session, username: str, server_id: str = "default") -> Optional[User]:
    """Get user by username within a specific server."""
    return user_crud.get_by_username(db, username, server_id)

def get_users(db: Session, skip: int = 0, limit: int = None, filter_query: Optional[str] = None, server_id: str = "default") -> List[User]:
    """Get users with optional filtering within a specific server."""
    return user_crud.get_list(db, skip, limit, filter_query, server_id)

def update_user(db: Session, user_id: str, user_data: UserUpdate, server_id: str = "default") -> Optional[User]:
    """Update user within a specific server."""
    return user_crud.update_user(db, user_id, user_data, server_id)

def deactivate_user(db: Session, user_id: str, server_id: str = "default") -> bool:
    """Deactivate user by setting active=False within a specific server."""
    return user_crud.deactivate_user(db, user_id, server_id)

def delete_user(db: Session, user_id: str, server_id: str = "default") -> bool:
    """Delete user within a specific server."""
    return user_crud.delete(db, user_id, server_id)

# Group CRUD operations
def create_group(db: Session, group_data: GroupCreate, server_id: str = "default") -> Group:
    """Create a new group."""
    return group_crud.create_group(db, group_data, server_id)

def get_group(db: Session, group_id: str, server_id: str = "default") -> Optional[Group]:
    """Get group by SCIM ID within a specific server."""
    return group_crud.get_by_id(db, group_id, server_id)

def get_groups(db: Session, skip: int = 0, limit: int = None, filter_query: Optional[str] = None, server_id: str = "default") -> List[Group]:
    """Get groups with optional filtering within a specific server."""
    return group_crud.get_list(db, skip, limit, filter_query, server_id)

def update_group(db: Session, group_id: str, group_data: GroupUpdate, server_id: str = "default") -> Optional[Group]:
    """Update group within a specific server."""
    return group_crud.update_group(db, group_id, group_data, server_id)

def delete_group(db: Session, group_id: str, server_id: str = "default") -> bool:
    """Delete group within a specific server."""
    return group_crud.delete(db, group_id, server_id)

# Entitlement CRUD operations
def create_entitlement(db: Session, entitlement_data: EntitlementCreate, server_id: str = "default") -> Entitlement:
    """Create a new entitlement."""
    return entitlement_crud.create_entitlement(db, entitlement_data, server_id)

def get_entitlement(db: Session, entitlement_id: str, server_id: str = "default") -> Optional[Entitlement]:
    """Get entitlement by SCIM ID within a specific server."""
    return entitlement_crud.get_by_id(db, entitlement_id, server_id)

def get_entitlements(db: Session, skip: int = 0, limit: int = None, filter_query: Optional[str] = None, server_id: str = "default") -> List[Entitlement]:
    """Get entitlements with optional filtering within a specific server."""
    return entitlement_crud.get_list(db, skip, limit, filter_query, server_id)

def update_entitlement(db: Session, entitlement_id: str, entitlement_data: EntitlementUpdate, server_id: str = "default") -> Optional[Entitlement]:
    """Update entitlement within a specific server."""
    return entitlement_crud.update_entitlement(db, entitlement_id, entitlement_data, server_id)

def delete_entitlement(db: Session, entitlement_id: str, server_id: str = "default") -> bool:
    """Delete entitlement within a specific server."""
    return entitlement_crud.delete(db, entitlement_id, server_id)

# Role CRUD operations
def create_role(db: Session, role_data: RoleCreate, server_id: str = "default") -> Role:
    """Create a new role."""
    return role_crud.create_role(db, role_data, server_id)

def get_role(db: Session, role_id: str, server_id: str = "default") -> Optional[Role]:
    """Get role by SCIM ID within a specific server."""
    return role_crud.get_by_id(db, role_id, server_id)

def get_roles(db: Session, skip: int = 0, limit: int = None, filter_query: Optional[str] = None, server_id: str = "default") -> List[Role]:
    """Get roles with optional filtering within a specific server."""
    return role_crud.get_list(db, skip, limit, filter_query, server_id)

def update_role(db: Session, role_id: str, role_data: RoleUpdate, server_id: str = "default") -> Optional[Role]:
    """Update role within a specific server."""
    return role_crud.update_role(db, role_id, role_data, server_id)

def delete_role(db: Session, role_id: str, server_id: str = "default") -> bool:
    """Delete role within a specific server."""
    return role_crud.delete(db, role_id, server_id) 