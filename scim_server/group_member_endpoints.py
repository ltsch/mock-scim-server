"""
Group member management endpoints for SCIM compliance.

This module provides endpoints for managing group memberships, allowing SCIM clients
to add and remove users from groups.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from loguru import logger

from .database import get_db
from .auth import get_api_key, get_validated_server_id
from .crud_entities import group_crud, user_crud
from .config import settings
from .utils import validate_scim_id


def create_group_member_router() -> APIRouter:
    """Create router for group member management endpoints."""
    
    router = APIRouter(
        prefix="/scim-identifier/{server_id}/scim/v2/Groups/{group_id}/members",
        tags=["Group Members"]
    )
    
    @router.post("/{user_id}", status_code=204)
    async def add_member_to_group(
        group_id: str = Path(..., description="SCIM ID of the group"),
        user_id: str = Path(..., description="SCIM ID of the user to add"),
        server_id: str = Depends(get_validated_server_id),
        api_key: str = Depends(get_api_key),
        db: Session = Depends(get_db)
    ):
        """Add a user to a group."""
        # Validate SCIM IDs
        if not validate_scim_id(group_id):
            raise HTTPException(status_code=400, detail="Invalid group ID format")
        
        if not validate_scim_id(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        # Add member to group
        success = group_crud.add_member_to_group(db, group_id, user_id, server_id)
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="Group or user not found, or user is already a member of the group"
            )
        
        logger.info(f"Added user {user_id} to group {group_id} in server {server_id}")
        return None
    
    @router.delete("/{user_id}", status_code=204)
    async def remove_member_from_group(
        group_id: str = Path(..., description="SCIM ID of the group"),
        user_id: str = Path(..., description="SCIM ID of the user to remove"),
        server_id: str = Depends(get_validated_server_id),
        api_key: str = Depends(get_api_key),
        db: Session = Depends(get_db)
    ):
        """Remove a user from a group."""
        # Validate SCIM IDs
        if not validate_scim_id(group_id):
            raise HTTPException(status_code=400, detail="Invalid group ID format")
        
        if not validate_scim_id(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        # Remove member from group
        success = group_crud.remove_member_from_group(db, group_id, user_id, server_id)
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail="Group or user not found, or user is not a member of the group"
            )
        
        logger.info(f"Removed user {user_id} from group {group_id} in server {server_id}")
        return None
    
    @router.get("/", response_model=List[Dict[str, Any]])
    async def get_group_members(
        group_id: str = Path(..., description="SCIM ID of the group"),
        server_id: str = Depends(get_validated_server_id),
        api_key: str = Depends(get_api_key),
        db: Session = Depends(get_db)
    ):
        """Get all members of a group."""
        # Validate SCIM ID
        if not validate_scim_id(group_id):
            raise HTTPException(status_code=400, detail="Invalid group ID format")
        
        # Get group members
        members = group_crud.get_group_members(db, group_id, server_id)
        
        if not members:
            # Check if group exists
            group = group_crud.get(db, group_id, server_id)
            if not group:
                raise HTTPException(status_code=404, detail="Group not found")
        
        # Convert to SCIM format
        scim_members = []
        for member in members:
            scim_members.append({
                "value": member.scim_id,
                "display": member.display_name or member.user_name,
                "$ref": f"/scim-identifier/{server_id}/scim/v2/Users/{member.scim_id}"
            })
        
        return scim_members
    
    @router.get("/{user_id}")
    async def check_group_membership(
        group_id: str = Path(..., description="SCIM ID of the group"),
        user_id: str = Path(..., description="SCIM ID of the user to check"),
        server_id: str = Depends(get_validated_server_id),
        api_key: str = Depends(get_api_key),
        db: Session = Depends(get_db)
    ):
        """Check if a user is a member of a group."""
        # Validate SCIM IDs
        if not validate_scim_id(group_id):
            raise HTTPException(status_code=400, detail="Invalid group ID format")
        
        if not validate_scim_id(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        # Get group members
        members = group_crud.get_group_members(db, group_id, server_id)
        
        # Check if user is a member
        is_member = any(member.scim_id == user_id for member in members)
        
        if not is_member:
            # Check if group and user exist
            group = group_crud.get(db, group_id, server_id)
            if not group:
                raise HTTPException(status_code=404, detail="Group not found")
            
            user = user_crud.get(db, user_id, server_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "is_member": is_member,
            "group_id": group_id,
            "user_id": user_id
        }
    
    return router 