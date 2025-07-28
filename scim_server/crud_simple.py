"""
Simplified CRUD operations using centralized base functions.
This module provides a clean interface to all CRUD operations without duplication.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from .crud_entities import user_crud, group_crud, entitlement_crud
from .schemas import UserCreate, UserUpdate, GroupCreate, GroupUpdate, EntitlementCreate, EntitlementUpdate
from .models import User, Group, Entitlement

# User CRUD operations
def create_user(db: Session, user_data: UserCreate, server_id: str) -> User:
    """Create a new user."""
    return user_crud.create_user(db, user_data, server_id)

def get_user(db: Session, user_id: str, server_id: str) -> Optional[User]:
    """Get user by SCIM ID within a specific server."""
    return user_crud.get_by_id(db, user_id, server_id)

def get_user_by_username(db: Session, username: str, server_id: str) -> Optional[User]:
    """Get user by username within a specific server."""
    return user_crud.get_by_username(db, username, server_id)

def get_users(db: Session, server_id: str, skip: int = 0, limit: int = None, filter_query: Optional[str] = None) -> List[User]:
    """Get users with optional filtering within a specific server."""
    return user_crud.get_list(db, server_id, skip, limit, filter_query)

def update_user(db: Session, user_id: str, user_data: UserUpdate, server_id: str) -> Optional[User]:
    """Update user within a specific server."""
    return user_crud.update_user(db, user_id, user_data, server_id)

def deactivate_user(db: Session, user_id: str, server_id: str) -> bool:
    """Deactivate user by setting active=False within a specific server."""
    return user_crud.deactivate_user(db, user_id, server_id)

def delete_user(db: Session, user_id: str, server_id: str) -> bool:
    """Delete user within a specific server."""
    return user_crud.delete(db, user_id, server_id)

# Group CRUD operations
def create_group(db: Session, group_data: GroupCreate, server_id: str) -> Group:
    """Create a new group."""
    return group_crud.create_group(db, group_data, server_id)

def get_group(db: Session, group_id: str, server_id: str) -> Optional[Group]:
    """Get group by SCIM ID within a specific server."""
    return group_crud.get_by_id(db, group_id, server_id)

def get_groups(db: Session, server_id: str, skip: int = 0, limit: int = None, filter_query: Optional[str] = None) -> List[Group]:
    """Get groups with optional filtering within a specific server."""
    return group_crud.get_list(db, server_id, skip, limit, filter_query)

def update_group(db: Session, group_id: str, group_data: GroupUpdate, server_id: str) -> Optional[Group]:
    """Update group within a specific server."""
    return group_crud.update_group(db, group_id, group_data, server_id)

def delete_group(db: Session, group_id: str, server_id: str) -> bool:
    """Delete group within a specific server."""
    return group_crud.delete(db, group_id, server_id)

# Entitlement CRUD operations
def create_entitlement(db: Session, entitlement_data: EntitlementCreate, server_id: str) -> Entitlement:
    """Create a new entitlement."""
    return entitlement_crud.create_entitlement(db, entitlement_data, server_id)

def get_entitlement(db: Session, entitlement_id: str, server_id: str) -> Optional[Entitlement]:
    """Get entitlement by SCIM ID within a specific server."""
    return entitlement_crud.get_by_id(db, entitlement_id, server_id)

def get_entitlements(db: Session, server_id: str, skip: int = 0, limit: int = None, filter_query: Optional[str] = None) -> List[Entitlement]:
    """Get entitlements with optional filtering within a specific server."""
    return entitlement_crud.get_list(db, server_id, skip, limit, filter_query)

def update_entitlement(db: Session, entitlement_id: str, entitlement_data: EntitlementUpdate, server_id: str) -> Optional[Entitlement]:
    """Update entitlement within a specific server."""
    return entitlement_crud.update_entitlement(db, entitlement_id, entitlement_data, server_id)

def delete_entitlement(db: Session, entitlement_id: str, server_id: str) -> bool:
    """Delete entitlement within a specific server."""
    return entitlement_crud.delete(db, entitlement_id, server_id)

 