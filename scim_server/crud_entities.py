"""
Entity-specific CRUD operations that extend the base CRUD functionality.
"""

import uuid
from typing import Optional, List
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_

from .crud_base import BaseCRUD
from .models import User, Group, Entitlement
from .schemas import UserCreate, UserUpdate, GroupCreate, GroupUpdate, EntitlementCreate, EntitlementUpdate

class UserCRUD(BaseCRUD[User]):
    """User-specific CRUD operations."""
    
    def __init__(self):
        super().__init__(User)
    
    def create_user(self, db: Session, user_data: UserCreate, server_id: str = "default") -> User:
        """Create a new user with proper data transformation."""
        # Transform UserCreate to dict
        data = {
            'scim_id': str(uuid.uuid4()),
            'user_name': user_data.userName,
            'external_id': user_data.externalId,
            'display_name': user_data.displayName,
            'given_name': user_data.name.givenName if user_data.name else None,
            'family_name': user_data.name.familyName if user_data.name else None,
            'email': str(user_data.emails[0].value) if user_data.emails else None,
            'active': user_data.active,
        }
        
        return self.create(db, data, server_id)
    
    def get_by_username(self, db: Session, username: str, server_id: str = "default") -> Optional[User]:
        """Get user by username within a specific server."""
        return self.get_by_field(db, 'user_name', username, server_id)
    
    def update_user(self, db: Session, user_id: str, user_data: UserUpdate, server_id: str = "default") -> Optional[User]:
        """Update user with proper data transformation."""
        # Transform UserUpdate to dict
        update_data = {}
        if hasattr(user_data, 'model_dump'):
            update_dict = user_data.model_dump(exclude_unset=True)
        else:
            # Handle case where user_data is already a dict
            update_dict = user_data
        
        # Map SCIM field names to database field names
        field_mapping = {
            'userName': 'user_name',
            'externalId': 'external_id',
            'displayName': 'display_name',
            'active': 'active'
        }
        
        for scim_field, value in update_dict.items():
            if scim_field in field_mapping:
                update_data[field_mapping[scim_field]] = value
        
        return self.update(db, user_id, update_data, server_id)
    
    def deactivate_user(self, db: Session, user_id: str, server_id: str = "default") -> bool:
        """Deactivate user by setting active=False."""
        return self.update(db, user_id, {'active': False}, server_id) is not None
    
    def _get_db_field_name(self, scim_field: str) -> Optional[str]:
        """Map SCIM field names to database column names for users."""
        field_mapping = {
            'userName': 'user_name',
            'displayName': 'display_name',
            'givenName': 'given_name',
            'familyName': 'family_name',
            'email': 'email',
        }
        return field_mapping.get(scim_field, scim_field)

class GroupCRUD(BaseCRUD[Group]):
    """Group-specific CRUD operations."""
    
    def __init__(self):
        super().__init__(Group)
    
    def create_group(self, db: Session, group_data: GroupCreate, server_id: str = "default") -> Group:
        """Create a new group with proper data transformation."""
        data = {
            'scim_id': str(uuid.uuid4()),
            'display_name': group_data.displayName,
            'description': group_data.description,
        }
        
        return self.create(db, data, server_id)
    
    def update_group(self, db: Session, group_id: str, group_data: GroupUpdate, server_id: str = "default") -> Optional[Group]:
        """Update group with proper data transformation."""
        update_data = {}
        if hasattr(group_data, 'model_dump'):
            update_dict = group_data.model_dump(exclude_unset=True)
        else:
            # Handle case where group_data is already a dict
            update_dict = group_data
        
        field_mapping = {
            'displayName': 'display_name',
            'description': 'description'
        }
        
        for scim_field, value in update_dict.items():
            if scim_field in field_mapping:
                update_data[field_mapping[scim_field]] = value
        
        return self.update(db, group_id, update_data, server_id)
    
    def _get_db_field_name(self, scim_field: str) -> Optional[str]:
        """Map SCIM field names to database column names for groups."""
        field_mapping = {
            'displayName': 'display_name',
            'description': 'description'
        }
        return field_mapping.get(scim_field, scim_field)

class EntitlementCRUD(BaseCRUD[Entitlement]):
    """Entitlement-specific CRUD operations."""
    
    def __init__(self):
        super().__init__(Entitlement)
    
    def create_entitlement(self, db: Session, entitlement_data: EntitlementCreate, server_id: str = "default") -> Entitlement:
        """Create a new entitlement with proper data transformation."""
        data = {
            'scim_id': str(uuid.uuid4()),
            'display_name': entitlement_data.displayName,
            'type': entitlement_data.type,
            'description': entitlement_data.description,
            'entitlement_type': entitlement_data.entitlementType,
            'multi_valued': entitlement_data.multiValued,
        }
        
        return self.create(db, data, server_id)
    
    def update_entitlement(self, db: Session, entitlement_id: str, entitlement_data: EntitlementUpdate, server_id: str = "default") -> Optional[Entitlement]:
        """Update entitlement with proper data transformation."""
        update_data = {}
        if hasattr(entitlement_data, 'model_dump'):
            update_dict = entitlement_data.model_dump(exclude_unset=True)
        else:
            # Handle case where entitlement_data is already a dict
            update_dict = entitlement_data
        
        field_mapping = {
            'displayName': 'display_name',
            'type': 'type',
            'description': 'description',
            'entitlementType': 'entitlement_type',
            'multiValued': 'multi_valued'
        }
        
        for scim_field, value in update_dict.items():
            if scim_field in field_mapping:
                update_data[field_mapping[scim_field]] = value
        
        return self.update(db, entitlement_id, update_data, server_id)
    
    def _get_db_field_name(self, scim_field: str) -> Optional[str]:
        """Map SCIM field names to database column names for entitlements."""
        field_mapping = {
            'displayName': 'display_name',
            'type': 'type',
            'description': 'description',
            'entitlementType': 'entitlement_type',
            'multiValued': 'multi_valued'
        }
        return field_mapping.get(scim_field, scim_field)

# Create instances for easy import
user_crud = UserCRUD()
group_crud = GroupCRUD()
entitlement_crud = EntitlementCRUD() 