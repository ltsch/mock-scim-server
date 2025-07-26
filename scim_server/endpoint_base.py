"""
Base endpoint classes for all SCIM entities.
This module eliminates massive code duplication by providing generic endpoint patterns.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, TypeVar, Generic, Type
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import get_db
from .auth import get_api_key
from .models import ApiKey
from .config import settings
from .server_context import get_server_id
from .utils import validate_scim_id, create_scim_list_response

# Generic types for entities
T = TypeVar('T')
CreateSchema = TypeVar('CreateSchema')
UpdateSchema = TypeVar('UpdateSchema')
ResponseSchema = TypeVar('ResponseSchema')
ListResponseSchema = TypeVar('ListResponseSchema')

class BaseEntityEndpoint(Generic[T, CreateSchema, UpdateSchema, ResponseSchema, ListResponseSchema]):
    """
    Base class for all entity endpoints that eliminates massive code duplication.
    
    This class provides generic CRUD endpoint patterns that can be used by any entity type.
    It handles all common patterns: validation, error handling, logging, and response conversion.
    """
    
    def __init__(
        self,
        entity_type: str,
        router: APIRouter,
        crud_operations,
        response_converter,
        create_schema: Type[CreateSchema],
        update_schema: Type[UpdateSchema],
        response_schema: Type[ResponseSchema],
        list_response_schema: Type[ListResponseSchema],
        schema_uri: str,
        supports_multi_server: bool = True
    ):
        self.entity_type = entity_type
        self.router = router
        self.crud = crud_operations
        self.converter = response_converter
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.list_response_schema = list_response_schema
        self.schema_uri = schema_uri
        self.supports_multi_server = supports_multi_server
        
        # Initialize rate limiter
        self.limiter = Limiter(key_func=get_remote_address)
        
        # Register all endpoints
        self._register_endpoints()
    
    def _register_endpoints(self):
        """Register all CRUD endpoints with the router."""
        
        # Create endpoint
        @self.router.post("/", response_model=self.response_schema, status_code=201)
        @self.limiter.limit(f"{settings.rate_limit_create}/{settings.rate_limit_window}minute")
        async def create_entity_endpoint(
            request: Request,
            entity_data: self.create_schema,
            server_id: str = Depends(get_server_id) if self.supports_multi_server else None,
            api_key: ApiKey = Depends(get_api_key),
            db: Session = Depends(get_db)
        ):
            return await self._create_entity(entity_data, server_id, db)
        
        # List endpoint
        @self.router.get("/", response_model=self.list_response_schema)
        @self.limiter.limit(f"{settings.rate_limit_read}/{settings.rate_limit_window}minute")
        async def get_entities_endpoint(
            request: Request,
            start_index: int = Query(1, ge=1, alias="startIndex", description="1-based index of the first result"),
            count: int = Query(settings.default_page_size, ge=1, le=settings.max_results_per_page, description="Number of results to return"),
            filter: Optional[str] = Query(None, alias="filter", description="SCIM filter query"),
            server_id: str = Depends(get_server_id) if self.supports_multi_server else None,
            api_key: ApiKey = Depends(get_api_key),
            db: Session = Depends(get_db)
        ):
            return await self._get_entities(start_index, count, filter, server_id, db)
        
        # Get by ID endpoint
        @self.router.get("/{entity_id}", response_model=self.response_schema)
        async def get_entity_endpoint(
            entity_id: str,
            request: Request,
            server_id: str = Depends(get_server_id) if self.supports_multi_server else None,
            api_key: ApiKey = Depends(get_api_key),
            db: Session = Depends(get_db)
        ):
            return await self._get_entity(entity_id, server_id, db)
        
        # Update endpoint
        @self.router.put("/{entity_id}", response_model=self.response_schema)
        async def update_entity_endpoint(
            entity_id: str,
            entity_data: self.update_schema,
            request: Request,
            server_id: str = Depends(get_server_id) if self.supports_multi_server else None,
            api_key: ApiKey = Depends(get_api_key),
            db: Session = Depends(get_db)
        ):
            return await self._update_entity(entity_id, entity_data, server_id, db)
        
        # Patch endpoint
        @self.router.patch("/{entity_id}", response_model=self.response_schema)
        async def patch_entity_endpoint(
            entity_id: str,
            entity_data: self.update_schema,
            request: Request,
            server_id: str = Depends(get_server_id) if self.supports_multi_server else None,
            api_key: ApiKey = Depends(get_api_key),
            db: Session = Depends(get_db)
        ):
            return await self._patch_entity(entity_id, entity_data, server_id, db)
        
        # Delete endpoint
        @self.router.delete("/{entity_id}", status_code=204)
        async def delete_entity_endpoint(
            entity_id: str,
            server_id: str = Depends(get_server_id) if self.supports_multi_server else None,
            api_key: ApiKey = Depends(get_api_key),
            db: Session = Depends(get_db)
        ):
            return await self._delete_entity(entity_id, server_id, db)
    
    async def _create_entity(self, entity_data: CreateSchema, server_id: str, db: Session) -> ResponseSchema:
        """Generic create entity endpoint."""
        logger.info(f"Creating {self.entity_type}: {getattr(entity_data, 'displayName', 'unknown')} in server: {server_id}")
        
        # Check for duplicates if applicable
        if hasattr(self.crud, 'get_by_field'):
            # For users, check userName uniqueness; for others, check displayName
            if self.entity_type == "User" and hasattr(entity_data, 'userName'):
                existing = self.crud.get_by_field(db, 'user_name', entity_data.userName, server_id)
                if existing:
                    logger.warning(f"{self.entity_type} with userName {entity_data.userName} already exists in server: {server_id}")
                    raise HTTPException(
                        status_code=409,
                        detail=f"{self.entity_type} with userName '{entity_data.userName}' already exists"
                    )
            elif hasattr(entity_data, 'displayName'):
                existing = self.crud.get_by_field(db, 'display_name', entity_data.displayName, server_id)
                if existing:
                    logger.warning(f"{self.entity_type} with displayName {entity_data.displayName} already exists in server: {server_id}")
                    raise HTTPException(
                        status_code=409,
                        detail=f"{self.entity_type} with displayName '{entity_data.displayName}' already exists"
                    )
        
        # Create entity using the appropriate method
        if self.entity_type == "User":
            db_entity = self.crud.create_user(db, entity_data, server_id)
        elif self.entity_type == "Group":
            db_entity = self.crud.create_group(db, entity_data, server_id)
        elif self.entity_type == "Entitlement":
            db_entity = self.crud.create_entitlement(db, entity_data, server_id)
        elif self.entity_type == "Role":
            db_entity = self.crud.create_role(db, entity_data, server_id)
        else:
            raise ValueError(f"Unsupported entity type: {self.entity_type}")
        
        # Convert to SCIM response format
        response = self.converter.to_scim_response(db_entity)
        
        logger.info(f"{self.entity_type} created successfully: {db_entity.scim_id} in server: {server_id}")
        return response
    
    async def _get_entities(
        self, 
        start_index: int, 
        count: int, 
        filter_query: Optional[str], 
        server_id: str, 
        db: Session
    ) -> ListResponseSchema:
        """Generic get entities endpoint."""
        logger.info(f"Getting {self.entity_type}s in server: {server_id}, startIndex={start_index}, count={count}, filter={filter_query}")
        
        # Calculate skip value (convert from 1-based to 0-based)
        skip = start_index - 1
        
        # Get entities from database with filter
        entities = self.crud.get_list(db, skip=skip, limit=count, filter_query=filter_query, server_id=server_id)
        
        # Get total count for pagination
        if filter_query:
            # Get total count of filtered results
            filtered_entities = self.crud.get_list(db, skip=0, limit=settings.max_count_limit, filter_query=filter_query, server_id=server_id)
            total_count = len(filtered_entities)
        else:
            # Get total count of all entities in this server
            total_count = self.crud.count(db, server_id)
        
        # Convert to SCIM response format
        resources = [self.converter.to_scim_response(entity) for entity in entities]
        
        response = create_scim_list_response(
            resources=resources,
            total_results=total_count,
            start_index=start_index,
            items_per_page=len(resources)
        )
        
        logger.info(f"Returning {len(resources)} {self.entity_type}s from server: {server_id}")
        return response
    
    async def _get_entity(self, entity_id: str, server_id: str, db: Session) -> ResponseSchema:
        """Generic get entity by ID endpoint."""
        logger.info(f"Getting {self.entity_type}: {entity_id} in server: {server_id}")
        
        # Validate SCIM ID format
        if not validate_scim_id(entity_id):
            logger.warning(f"Invalid SCIM ID format: {entity_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid SCIM ID format"
            )
        
        # Get entity from database
        entity = self.crud.get_by_id(db, entity_id, server_id)
        if not entity:
            logger.warning(f"{self.entity_type} not found: {entity_id}")
            raise HTTPException(
                status_code=404,
                detail=f"{self.entity_type} not found"
            )
        
        # Convert to SCIM response format
        response = self.converter.to_scim_response(entity)
        
        logger.info(f"{self.entity_type} retrieved successfully: {entity_id} from server: {server_id}")
        return response
    
    async def _update_entity(self, entity_id: str, entity_data: UpdateSchema, server_id: str, db: Session) -> ResponseSchema:
        """Generic update entity endpoint."""
        logger.info(f"Updating {self.entity_type}: {entity_id} in server: {server_id}")
        
        # Validate SCIM ID format
        if not validate_scim_id(entity_id):
            logger.warning(f"Invalid SCIM ID format: {entity_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid SCIM ID format"
            )
        
        # Check if entity exists
        existing_entity = self.crud.get_by_id(db, entity_id, server_id)
        if not existing_entity:
            logger.warning(f"{self.entity_type} not found: {entity_id}")
            raise HTTPException(
                status_code=404,
                detail=f"{self.entity_type} not found"
            )
        
        # Update entity using the appropriate method
        if self.entity_type == "User":
            updated_entity = self.crud.update_user(db, entity_id, entity_data, server_id)
        elif self.entity_type == "Group":
            updated_entity = self.crud.update_group(db, entity_id, entity_data, server_id)
        elif self.entity_type == "Entitlement":
            updated_entity = self.crud.update_entitlement(db, entity_id, entity_data, server_id)
        elif self.entity_type == "Role":
            updated_entity = self.crud.update_role(db, entity_id, entity_data, server_id)
        else:
            raise ValueError(f"Unsupported entity type: {self.entity_type}")
            
        if not updated_entity:
            logger.error(f"Failed to update {self.entity_type}: {entity_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update {self.entity_type}"
            )
        
        # Convert to SCIM response format
        response = self.converter.to_scim_response(updated_entity)
        
        logger.info(f"{self.entity_type} updated successfully: {entity_id} in server: {server_id}")
        return response
    
    async def _patch_entity(self, entity_id: str, entity_data: UpdateSchema, server_id: str, db: Session) -> ResponseSchema:
        """Generic patch entity endpoint."""
        logger.info(f"Patching {self.entity_type}: {entity_id} in server: {server_id}")
        
        # Validate SCIM ID format
        if not validate_scim_id(entity_id):
            logger.warning(f"Invalid SCIM ID format: {entity_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid SCIM ID format"
            )
        
        # Check if entity exists
        existing_entity = self.crud.get_by_id(db, entity_id, server_id)
        if not existing_entity:
            logger.warning(f"{self.entity_type} not found: {entity_id}")
            raise HTTPException(
                status_code=404,
                detail=f"{self.entity_type} not found"
            )
        
        # Update entity using the appropriate method
        if self.entity_type == "User":
            updated_entity = self.crud.update_user(db, entity_id, entity_data, server_id)
        elif self.entity_type == "Group":
            updated_entity = self.crud.update_group(db, entity_id, entity_data, server_id)
        elif self.entity_type == "Entitlement":
            updated_entity = self.crud.update_entitlement(db, entity_id, entity_data, server_id)
        elif self.entity_type == "Role":
            updated_entity = self.crud.update_role(db, entity_id, entity_data, server_id)
        else:
            raise ValueError(f"Unsupported entity type: {self.entity_type}")
            
        if not updated_entity:
            logger.error(f"Failed to patch {self.entity_type}: {entity_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to patch {self.entity_type}"
            )
        
        # Convert to SCIM response format
        response = self.converter.to_scim_response(updated_entity)
        
        logger.info(f"{self.entity_type} patched successfully: {entity_id} in server: {server_id}")
        return response
    
    async def _delete_entity(self, entity_id: str, server_id: str, db: Session) -> None:
        """Generic delete entity endpoint."""
        logger.info(f"Deleting {self.entity_type}: {entity_id} in server: {server_id}")
        
        # Validate SCIM ID format
        if not validate_scim_id(entity_id):
            logger.warning(f"Invalid SCIM ID format: {entity_id}")
            raise HTTPException(
                status_code=400,
                detail="Invalid SCIM ID format"
            )
        
        # Check if entity exists
        existing_entity = self.crud.get_by_id(db, entity_id, server_id)
        if not existing_entity:
            logger.warning(f"{self.entity_type} not found: {entity_id}")
            raise HTTPException(
                status_code=404,
                detail=f"{self.entity_type} not found"
            )
        
        # Delete entity using the appropriate method
        if self.entity_type == "User":
            success = self.crud.deactivate_user(db, entity_id, server_id)
        else:
            success = self.crud.delete(db, entity_id, server_id)
            
        if not success:
            logger.error(f"Failed to delete {self.entity_type}: {entity_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete {self.entity_type}"
            )
        
        logger.info(f"{self.entity_type} deleted successfully: {entity_id} in server: {server_id}")
        return None 