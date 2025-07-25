from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from loguru import logger

from .models import User, Group, Entitlement, Role, UserGroup, UserEntitlement, UserRole
from .schemas import UserCreate, UserUpdate, GroupCreate, GroupUpdate, EntitlementCreate, EntitlementUpdate, RoleCreate, RoleUpdate

# User CRUD operations
def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    logger.info(f"Creating user: {user_data.userName}")
    
    # Generate SCIM ID
    scim_id = str(uuid.uuid4())
    
    # Create user object
    db_user = User(
        scim_id=scim_id,
        user_name=user_data.userName,
        external_id=user_data.externalId,
        display_name=user_data.displayName,
        given_name=user_data.name.givenName if user_data.name else None,
        family_name=user_data.name.familyName if user_data.name else None,
        email=str(user_data.emails[0].value) if user_data.emails else None,
        active=user_data.active
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User created successfully: {scim_id}")
    return db_user

def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get user by SCIM ID."""
    return db.query(User).filter(User.scim_id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.user_name == username).first()

def get_users(db: Session, skip: int = 0, limit: int = None, filter_query: Optional[str] = None) -> List[User]:
    """Get users with optional filtering."""
    from .config import settings
    if limit is None:
        limit = settings.default_page_size
    query = db.query(User)
    
    if filter_query:
        logger.info(f"Applying filter: {filter_query}")
        from .utils import parse_scim_filter
        filter_info = parse_scim_filter(filter_query)
        
        if filter_info:
            field = filter_info['field']
            operator = filter_info['operator']
            value = filter_info['value']
            logger.info(f"Parsed filter: field={field}, operator={operator}, value={value}")
            
            if field == 'userName':
                if operator == 'eq':
                    query = query.filter(User.user_name == value)
                    logger.info(f"Applied userName eq filter: {value}")
                elif operator == 'co':
                    query = query.filter(User.user_name.contains(value))
                    logger.info(f"Applied userName co filter: {value}")
            elif field == 'displayName':
                if operator == 'eq':
                    query = query.filter(User.display_name == value)
                    logger.info(f"Applied displayName eq filter: {value}")
                elif operator == 'co':
                    query = query.filter(User.display_name.contains(value))
                    logger.info(f"Applied displayName co filter: {value}")
            elif field == 'email':
                if operator == 'eq':
                    query = query.filter(User.email == value)
                    logger.info(f"Applied email eq filter: {value}")
                elif operator == 'co':
                    query = query.filter(User.email.contains(value))
                    logger.info(f"Applied email co filter: {value}")
        else:
            logger.warning(f"Could not parse filter: {filter_query}")
            # Fallback to simple contains search
            query = query.filter(
                or_(
                    User.user_name.contains(filter_query),
                    User.display_name.contains(filter_query),
                    User.email.contains(filter_query)
                )
            )
    else:
        logger.info("No filter applied")
    
    result = query.order_by(User.id).offset(skip).limit(limit).all()
    logger.info(f"Query returned {len(result)} users")
    return result

def update_user(db: Session, user_id: str, user_data: UserUpdate) -> Optional[User]:
    """Update user."""
    logger.info(f"Updating user: {user_id}")
    
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Update fields if provided
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "userName" in update_data:
        db_user.user_name = update_data["userName"]
    if "externalId" in update_data:
        db_user.external_id = update_data["externalId"]
    if "displayName" in update_data:
        db_user.display_name = update_data["displayName"]
    if "active" in update_data:
        db_user.active = update_data["active"]
    
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User updated successfully: {user_id}")
    return db_user

def deactivate_user(db: Session, user_id: str) -> bool:
    """Deactivate user by setting active=False (soft delete)."""
    logger.info(f"Deactivating user: {user_id}")
    
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db_user.active = False
    db.commit()
    
    logger.info(f"User deactivated successfully: {user_id}")
    return True

def delete_user(db: Session, user_id: str) -> bool:
    """Hard delete user from database."""
    logger.info(f"Deleting user: {user_id}")
    
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    
    logger.info(f"User deleted successfully: {user_id}")
    return True

# Group CRUD operations
def create_group(db: Session, group_data: GroupCreate) -> Group:
    """Create a new group."""
    logger.info(f"Creating group: {group_data.displayName}")
    
    scim_id = str(uuid.uuid4())
    
    db_group = Group(
        scim_id=scim_id,
        display_name=group_data.displayName,
        description=group_data.description
    )
    
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    logger.info(f"Group created successfully: {scim_id}")
    return db_group

def get_group(db: Session, group_id: str) -> Optional[Group]:
    """Get group by SCIM ID."""
    return db.query(Group).filter(Group.scim_id == group_id).first()

def get_groups(db: Session, skip: int = 0, limit: int = None, filter_query: Optional[str] = None) -> List[Group]:
    """Get groups with optional filtering."""
    from .config import settings
    if limit is None:
        limit = settings.default_page_size
    query = db.query(Group)
    
    if filter_query:
        from .utils import parse_scim_filter
        filter_info = parse_scim_filter(filter_query)
        
        if filter_info:
            field = filter_info['field']
            operator = filter_info['operator']
            value = filter_info['value']
            
            if field == 'displayName':
                if operator == 'eq':
                    query = query.filter(Group.display_name == value)
                elif operator == 'co':
                    query = query.filter(Group.display_name.contains(value))
            elif field == 'description':
                if operator == 'eq':
                    query = query.filter(Group.description == value)
                elif operator == 'co':
                    query = query.filter(Group.description.contains(value))
        else:
            # Fallback to simple contains search
            query = query.filter(
                or_(
                    Group.display_name.contains(filter_query),
                    Group.description.contains(filter_query)
                )
            )
    
    return query.order_by(Group.id).offset(skip).limit(limit).all()

def update_group(db: Session, group_id: str, group_data: GroupUpdate) -> Optional[Group]:
    """Update group."""
    logger.info(f"Updating group: {group_id}")
    
    db_group = get_group(db, group_id)
    if not db_group:
        return None
    
    update_data = group_data.model_dump(exclude_unset=True)
    
    if "displayName" in update_data:
        db_group.display_name = update_data["displayName"]
    if "description" in update_data:
        db_group.description = update_data["description"]
    
    db.commit()
    db.refresh(db_group)
    
    logger.info(f"Group updated successfully: {group_id}")
    return db_group

def delete_group(db: Session, group_id: str) -> bool:
    """Delete group."""
    logger.info(f"Deleting group: {group_id}")
    
    db_group = get_group(db, group_id)
    if not db_group:
        return False
    
    db.delete(db_group)
    db.commit()
    
    logger.info(f"Group deleted successfully: {group_id}")
    return True

# Entitlement CRUD operations
def create_entitlement(db: Session, entitlement_data: EntitlementCreate) -> Entitlement:
    """Create a new entitlement."""
    logger.info(f"Creating entitlement: {entitlement_data.displayName}")
    
    scim_id = str(uuid.uuid4())
    
    db_entitlement = Entitlement(
        scim_id=scim_id,
        display_name=entitlement_data.displayName,
        type=entitlement_data.type,
        description=entitlement_data.description
    )
    
    db.add(db_entitlement)
    db.commit()
    db.refresh(db_entitlement)
    
    logger.info(f"Entitlement created successfully: {scim_id}")
    return db_entitlement

def get_entitlement(db: Session, entitlement_id: str) -> Optional[Entitlement]:
    """Get entitlement by SCIM ID."""
    return db.query(Entitlement).filter(Entitlement.scim_id == entitlement_id).first()

def get_entitlements(db: Session, skip: int = 0, limit: int = None, filter_query: Optional[str] = None) -> List[Entitlement]:
    """Get entitlements with optional filtering."""
    from .config import settings
    if limit is None:
        limit = settings.default_page_size
    query = db.query(Entitlement)
    
    if filter_query:
        from .utils import parse_scim_filter
        filter_info = parse_scim_filter(filter_query)
        
        if filter_info:
            field = filter_info['field']
            operator = filter_info['operator']
            value = filter_info['value']
            
            if field == 'displayName':
                if operator == 'eq':
                    query = query.filter(Entitlement.display_name == value)
                elif operator == 'co':
                    query = query.filter(Entitlement.display_name.contains(value))
            elif field == 'type':
                if operator == 'eq':
                    query = query.filter(Entitlement.type == value)
                elif operator == 'co':
                    query = query.filter(Entitlement.type.contains(value))
            elif field == 'description':
                if operator == 'eq':
                    query = query.filter(Entitlement.description == value)
                elif operator == 'co':
                    query = query.filter(Entitlement.description.contains(value))
        else:
            # Fallback to simple contains search
            query = query.filter(
                or_(
                    Entitlement.display_name.contains(filter_query),
                    Entitlement.type.contains(filter_query),
                    Entitlement.description.contains(filter_query)
                )
            )
    
    return query.order_by(Entitlement.id).offset(skip).limit(limit).all()

def update_entitlement(db: Session, entitlement_id: str, entitlement_data: EntitlementUpdate) -> Optional[Entitlement]:
    """Update entitlement."""
    logger.info(f"Updating entitlement: {entitlement_id}")
    
    db_entitlement = get_entitlement(db, entitlement_id)
    if not db_entitlement:
        return None
    
    update_data = entitlement_data.model_dump(exclude_unset=True)
    
    if "displayName" in update_data:
        db_entitlement.display_name = update_data["displayName"]
    if "type" in update_data:
        db_entitlement.type = update_data["type"]
    if "description" in update_data:
        db_entitlement.description = update_data["description"]
    
    db.commit()
    db.refresh(db_entitlement)
    
    logger.info(f"Entitlement updated successfully: {entitlement_id}")
    return db_entitlement

def delete_entitlement(db: Session, entitlement_id: str) -> bool:
    """Delete entitlement."""
    logger.info(f"Deleting entitlement: {entitlement_id}")
    
    db_entitlement = get_entitlement(db, entitlement_id)
    if not db_entitlement:
        return False
    
    db.delete(db_entitlement)
    db.commit()
    
    logger.info(f"Entitlement deleted successfully: {entitlement_id}")
    return True

# Role CRUD operations
def create_role(db: Session, role_data: RoleCreate) -> Role:
    """Create a new role."""
    logger.info(f"Creating role: {role_data.displayName}")
    
    scim_id = str(uuid.uuid4())
    
    db_role = Role(
        scim_id=scim_id,
        display_name=role_data.displayName,
        description=role_data.description
    )
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    logger.info(f"Role created successfully: {scim_id}")
    return db_role

def get_role(db: Session, role_id: str) -> Optional[Role]:
    """Get role by SCIM ID."""
    return db.query(Role).filter(Role.scim_id == role_id).first()

def get_roles(db: Session, skip: int = 0, limit: int = None, filter_query: Optional[str] = None) -> List[Role]:
    """Get roles with optional filtering."""
    from .config import settings
    if limit is None:
        limit = settings.default_page_size
    query = db.query(Role)
    
    if filter_query:
        from .utils import parse_scim_filter
        filter_info = parse_scim_filter(filter_query)
        
        if filter_info:
            field = filter_info['field']
            operator = filter_info['operator']
            value = filter_info['value']
            
            if field == 'displayName':
                if operator == 'eq':
                    query = query.filter(Role.display_name == value)
                elif operator == 'co':
                    query = query.filter(Role.display_name.contains(value))
            elif field == 'description':
                if operator == 'eq':
                    query = query.filter(Role.description == value)
                elif operator == 'co':
                    query = query.filter(Role.description.contains(value))
        else:
            # Fallback to simple contains search
            query = query.filter(
                or_(
                    Role.display_name.contains(filter_query),
                    Role.description.contains(filter_query)
                )
            )
    
    return query.order_by(Role.id).offset(skip).limit(limit).all()

def update_role(db: Session, role_id: str, role_data: RoleUpdate) -> Optional[Role]:
    """Update role."""
    logger.info(f"Updating role: {role_id}")
    
    db_role = get_role(db, role_id)
    if not db_role:
        return None
    
    update_data = role_data.model_dump(exclude_unset=True)
    
    if "displayName" in update_data:
        db_role.display_name = update_data["displayName"]
    if "description" in update_data:
        db_role.description = update_data["description"]
    
    db.commit()
    db.refresh(db_role)
    
    logger.info(f"Role updated successfully: {role_id}")
    return db_role

def delete_role(db: Session, role_id: str) -> bool:
    """Delete role."""
    logger.info(f"Deleting role: {role_id}")
    
    db_role = get_role(db, role_id)
    if not db_role:
        return False
    
    db.delete(db_role)
    db.commit()
    
    logger.info(f"Role deleted successfully: {role_id}")
    return True 