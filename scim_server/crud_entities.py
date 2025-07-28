"""
Entity-specific CRUD operations that extend the base CRUD functionality.
"""

import uuid
from typing import Optional, List
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_

from .crud_base import BaseCRUD
from .models import User, Group, Entitlement, UserGroup, UserEntitlement
from .schemas import UserCreate, UserUpdate, GroupCreate, GroupUpdate, EntitlementCreate, EntitlementUpdate

class UserCRUD(BaseCRUD[User]):
    """User-specific CRUD operations."""
    
    def __init__(self):
        super().__init__(User)
    
    def create_user(self, db: Session, user_data: UserCreate, server_id: str) -> User:
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
    
    def get_by_username(self, db: Session, username: str, server_id: str) -> Optional[User]:
        """Get user by username within a specific server."""
        return self.get_by_field(db, 'user_name', username, server_id)
    
    def update_user(self, db: Session, user_id: str, user_data: dict, server_id: str) -> Optional[User]:
        """Update user with proper data transformation."""
        # Transform validated data to database format
        update_data = {}
        
        # Map SCIM field names to database field names
        field_mapping = {
            'userName': 'user_name',
            'externalId': 'external_id',
            'displayName': 'display_name',
            'active': 'active'
        }
        
        # Handle simple fields
        for scim_field, value in user_data.items():
            if scim_field in field_mapping:
                update_data[field_mapping[scim_field]] = value
            elif scim_field == 'name' and isinstance(value, dict):
                # Handle complex name object
                if 'givenName' in value:
                    update_data['given_name'] = value['givenName']
                if 'familyName' in value:
                    update_data['family_name'] = value['familyName']
            elif scim_field == 'emails' and isinstance(value, list) and len(value) > 0:
                # Handle emails array - take the first primary email or first email
                email_obj = value[0]
                if isinstance(email_obj, dict) and 'value' in email_obj:
                    update_data['email'] = email_obj['value']
        
        return self.update(db, user_id, update_data, server_id)
    
    def deactivate_user(self, db: Session, user_id: str, server_id: str) -> bool:
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
    
    def create_group(self, db: Session, group_data: GroupCreate, server_id: str) -> Group:
        """Create a new group with proper data transformation."""
        data = {
            'scim_id': str(uuid.uuid4()),
            'display_name': group_data.displayName,
            'description': group_data.description,
        }
        
        return self.create(db, data, server_id)
    
    def update_group(self, db: Session, group_id: str, group_data: dict, server_id: str) -> Optional[Group]:
        """Update group with proper data transformation."""
        update_data = {}
        
        # Map SCIM field names to database field names
        field_mapping = {
            'displayName': 'display_name',
            'description': 'description'
        }
        
        for scim_field, value in group_data.items():
            if scim_field in field_mapping:
                update_data[field_mapping[scim_field]] = value
        
        return self.update(db, group_id, update_data, server_id)
    
    def add_member_to_group(self, db: Session, group_id: str, user_id: str, server_id: str) -> bool:
        """Add a user to a group."""
        # Verify both group and user exist in the same server
        group = self.get(db, group_id, server_id)
        if not group:
            return False
        
        user = user_crud.get(db, user_id, server_id)
        if not user:
            return False
        
        # Check if relationship already exists
        existing = db.query(UserGroup).filter(
            UserGroup.group_id == group.id,
            UserGroup.user_id == user.id
        ).first()
        
        if existing:
            return True  # Already a member
        
        # Create the relationship
        user_group = UserGroup(user_id=user.id, group_id=group.id)
        db.add(user_group)
        db.commit()
        return True
    
    def remove_member_from_group(self, db: Session, group_id: str, user_id: str, server_id: str) -> bool:
        """Remove a user from a group."""
        # Verify both group and user exist in the same server
        group = self.get(db, group_id, server_id)
        if not group:
            return False
        
        user = user_crud.get(db, user_id, server_id)
        if not user:
            return False
        
        # Find and remove the relationship
        user_group = db.query(UserGroup).filter(
            UserGroup.group_id == group.id,
            UserGroup.user_id == user.id
        ).first()
        
        if user_group:
            db.delete(user_group)
            db.commit()
            return True
        
        return False
    
    def get_group_members(self, db: Session, group_id: str, server_id: str) -> List[User]:
        """Get all members of a group."""
        group = self.get_by_id(db, group_id, server_id)
        if not group:
            return []
        
        # Get user IDs for this group
        user_group_relations = db.query(UserGroup).filter(
            UserGroup.group_id == group.id
        ).all()
        
        user_ids = [relation.user_id for relation in user_group_relations]
        
        # Get the actual user objects
        users = db.query(User).filter(
            User.id.in_(user_ids),
            User.server_id == server_id
        ).all()
        
        return users
    
    def get_user_groups(self, db: Session, user_id: str, server_id: str) -> List[Group]:
        """Get all groups that a user belongs to."""
        user = user_crud.get(db, user_id, server_id)
        if not user:
            return []
        
        # Get group IDs for this user
        user_group_relations = db.query(UserGroup).filter(
            UserGroup.user_id == user.id
        ).all()
        
        group_ids = [relation.group_id for relation in user_group_relations]
        
        # Get the actual group objects
        groups = db.query(Group).filter(
            Group.id.in_(group_ids),
            Group.server_id == server_id
        ).all()
        
        return groups
    
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
    
    def create_entitlement(self, db: Session, entitlement_data: EntitlementCreate, server_id: str) -> Entitlement:
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
    
    def update_entitlement(self, db: Session, entitlement_id: str, entitlement_data: dict, server_id: str) -> Optional[Entitlement]:
        """Update entitlement with proper data transformation."""
        update_data = {}
        
        # Map SCIM field names to database field names
        field_mapping = {
            'displayName': 'display_name',
            'type': 'type',
            'description': 'description',
            'entitlementType': 'entitlement_type',
            'multiValued': 'multi_valued'
        }
        
        for scim_field, value in entitlement_data.items():
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