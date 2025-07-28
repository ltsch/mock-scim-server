"""
Base CRUD operations for multi-server SCIM entities.
This module provides generic CRUD functions that can be used across all entity types.
"""

from sqlalchemy.orm import Session, Query
from sqlalchemy import and_
from typing import List, Optional, TypeVar, Generic, Type, Any
from loguru import logger

# Generic type for SQLAlchemy models
T = TypeVar('T')

class BaseCRUD(Generic[T]):
    """Base CRUD operations for any SCIM entity."""
    
    def __init__(self, model: Type[T]):
        self.model = model
    
    def create(self, db: Session, data: dict, server_id: str) -> T:
        """Create a new entity with server_id."""
        logger.info(f"Creating {self.model.__name__} in server: {server_id}")
        
        # Add server_id to the data
        data['server_id'] = server_id
        
        # Create the entity
        db_entity = self.model(**data)
        db.add(db_entity)
        db.commit()
        db.refresh(db_entity)
        
        logger.info(f"{self.model.__name__} created successfully: {getattr(db_entity, 'scim_id', 'unknown')} in server: {server_id}")
        return db_entity
    
    def get_by_id(self, db: Session, entity_id: str, server_id: str) -> Optional[T]:
        """Get entity by SCIM ID within a specific server."""
        return db.query(self.model).filter(
            getattr(self.model, 'scim_id') == entity_id,
            getattr(self.model, 'server_id') == server_id
        ).first()
    
    def get_by_field(self, db: Session, field_name: str, field_value: Any, server_id: str) -> Optional[T]:
        """Get entity by a specific field within a specific server."""
        return db.query(self.model).filter(
            getattr(self.model, field_name) == field_value,
            getattr(self.model, 'server_id') == server_id
        ).first()
    
    def get_list(self, db: Session, server_id: str, skip: int = 0, limit: Optional[int] = None, 
                 filter_query: Optional[str] = None) -> List[T]:
        """Get list of entities with optional filtering within a specific server."""
        from .config import settings
        if limit is None:
            limit = settings.default_page_size
        
        query = db.query(self.model).filter(getattr(self.model, 'server_id') == server_id)
        
        # Apply custom filtering if provided
        if filter_query:
            query = self._apply_filter(query, filter_query)
        
        result = query.order_by(getattr(self.model, 'id')).offset(skip).limit(limit).all()
        logger.info(f"Query returned {len(result)} {self.model.__name__}s")
        return result
    
    def update(self, db: Session, entity_id: str, update_data: dict, server_id: str) -> Optional[T]:
        """Update entity within a specific server."""
        logger.info(f"Updating {self.model.__name__}: {entity_id} in server: {server_id}")
        
        db_entity = self.get_by_id(db, entity_id, server_id)
        if not db_entity:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(db_entity, field):
                setattr(db_entity, field, value)
        
        db.commit()
        db.refresh(db_entity)
        
        logger.info(f"{self.model.__name__} updated successfully: {entity_id}")
        return db_entity
    
    def delete(self, db: Session, entity_id: str, server_id: str) -> bool:
        """Delete entity within a specific server."""
        logger.info(f"Deleting {self.model.__name__}: {entity_id} in server: {server_id}")
        
        db_entity = self.get_by_id(db, entity_id, server_id)
        if not db_entity:
            return False
        
        db.delete(db_entity)
        db.commit()
        
        logger.info(f"{self.model.__name__} deleted successfully: {entity_id}")
        return True
    
    def count(self, db: Session, server_id: str) -> int:
        """Count entities in a specific server."""
        return db.query(self.model).filter(getattr(self.model, 'server_id') == server_id).count()
    
    def _apply_filter(self, query: Query, filter_query: str) -> Query:
        """Apply SCIM filter to query. Override in subclasses for entity-specific filtering."""
        from .utils import parse_scim_filter
        filter_info = parse_scim_filter(filter_query)
        
        if filter_info:
            field = filter_info['field']
            operator = filter_info['operator']
            value = filter_info['value']
            
            # Get the actual database column name
            db_field = self._get_db_field_name(field)
            if db_field:
                if operator == 'eq':
                    query = query.filter(getattr(self.model, db_field) == value)
                elif operator == 'co':
                    query = query.filter(getattr(self.model, db_field).contains(value))
        
        return query
    
    def _get_db_field_name(self, scim_field: str) -> Optional[str]:
        """Map SCIM field names to database column names. Override in subclasses."""
        # Default mapping - subclasses should override this
        field_mapping = {
            'userName': 'user_name',
            'displayName': 'display_name',
            'givenName': 'given_name',
            'familyName': 'family_name',
            'email': 'email',
        }
        return field_mapping.get(scim_field, scim_field) 