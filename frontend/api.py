"""
Frontend API endpoints for SCIM Server web UI

This module provides API endpoints for reading server state and exporting server data
without interfering with the core SCIM functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger
from typing import Dict, Any, List
from datetime import datetime
import json

from scim_server.database import get_db
from scim_server.models import User, Group, Entitlement, UserGroup, UserEntitlement, AppProfile
from scim_server.auth import get_api_key
from scim_server.server_config import get_server_config_manager

# Create router for frontend API endpoints
router = APIRouter(prefix="/api", tags=["Frontend"])


def get_server_summary(server_id: str, db) -> Dict[str, Any]:
    """
    Get comprehensive summary information for a specific SCIM server.
    
    Returns detailed information including:
    - Server statistics (users, groups, entitlements, relationships)
    - Server configuration
    - App profile information
    - Last updated timestamp
    """
    try:
        # Get server configuration manager
        server_config_manager = get_server_config_manager(db)
        
        # Get basic counts
        users = db.query(User).filter(User.server_id == server_id).all()
        groups = db.query(Group).filter(Group.server_id == server_id).all()
        entitlements = db.query(Entitlement).filter(Entitlement.server_id == server_id).all()
        
        # Get user IDs for relationship counting
        user_ids = [user.id for user in users]
        
        # Count relationships
        user_group_relationships = 0
        user_entitlement_relationships = 0
        
        if user_ids:
            user_group_relationships = db.query(UserGroup).filter(UserGroup.user_id.in_(user_ids)).count()
            user_entitlement_relationships = db.query(UserEntitlement).filter(UserEntitlement.user_id.in_(user_ids)).count()
        
        # Get server configuration
        server_config = server_config_manager.get_server_config(server_id)
        
        # Get app profile from server configuration
        app_profile = None
        app_profile_name = server_config_manager.get_server_app_profile(server_id)
        
        if app_profile_name:
            logger.info(f"Server {server_id} has app profile: {app_profile_name}")
            # Get app profile configuration
            profile_config = server_config_manager.get_app_profile_config(app_profile_name)
            if profile_config:
                app_profile = {
                    "id": app_profile_name,
                    "name": profile_config.get("name", app_profile_name),
                    "description": profile_config.get("description", ""),
                    "app_type": profile_config.get("app_type", app_profile_name),
                    "configuration": profile_config.get("configuration", {}),
                    "is_active": profile_config.get("is_active", True)
                }
                logger.info(f"Created app_profile object: {app_profile}")
            else:
                app_profile = {"id": app_profile_name, "name": f"Profile {app_profile_name}"}
                logger.info(f"Profile config not found, using fallback: {app_profile}")
        else:
            logger.info(f"No app profile configured for server {server_id}")
        
        return {
            "server_id": server_id,
            "stats": {
                "users": len(users),
                "groups": len(groups),
                "entitlements": len(entitlements),
                "user_group_relationships": user_group_relationships,
                "user_entitlement_relationships": user_entitlement_relationships
            },
            "config": server_config,
            "app_profile": app_profile,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Error getting server summary for {server_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting server summary: {str(e)}")


@router.get("/list-servers")
async def list_servers(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """
    List all available SCIM servers with their summary information.
    
    Returns a JSON object containing:
    - servers: List of server summaries
    - total: Total number of servers
    - generated_at: Timestamp of when the data was generated
    """
    try:
        db = next(get_db())
        
        # Get all unique server IDs
        user_servers = [r[0] for r in db.query(User.server_id.distinct()).all()]
        group_servers = [r[0] for r in db.query(Group.server_id.distinct()).all()]
        entitlement_servers = [r[0] for r in db.query(Entitlement.server_id.distinct()).all()]
        
        # Combine and deduplicate
        all_servers = set(user_servers + group_servers + entitlement_servers)
        server_ids = sorted(list(all_servers))
        
        if not server_ids:
            return {
                "servers": [],
                "total": 0,
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
        
        # Get summary for each server
        servers = []
        for server_id in server_ids:
            try:
                summary = get_server_summary(server_id, db)
                servers.append(summary)
            except Exception as e:
                logger.warning(f"Error getting summary for server {server_id}: {e}")
                # Add basic info even if summary fails
                servers.append({
                    "server_id": server_id,
                    "error": str(e),
                    "stats": {"users": 0, "groups": 0, "entitlements": 0}
                })
        
        return {
            "servers": servers,
            "total": len(servers),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error listing servers: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing servers: {str(e)}")


@router.get("/export-server/{server_id}")
async def export_server(
    server_id: str,
    api_key: str = Depends(get_api_key),
    include_relationships: bool = Query(True, description="Include user-group and user-entitlement relationships")
) -> Dict[str, Any]:
    """
    Export complete server data including all users, groups, entitlements, and relationships.
    
    Args:
        server_id: The UUID of the server to export
        include_relationships: Whether to include relationship data (default: True)
    
    Returns a JSON object containing:
    - server_id: The server ID
    - summary: Server statistics and configuration
    - users: Complete user data with relationships
    - groups: Complete group data with members
    - entitlements: Complete entitlement data with assignments
    - metadata: Export metadata
    """
    try:
        db = next(get_db())
        
        # Verify server exists by checking if it has any data
        users = db.query(User).filter(User.server_id == server_id).all()
        groups = db.query(Group).filter(Group.server_id == server_id).all()
        entitlements = db.query(Entitlement).filter(Entitlement.server_id == server_id).all()
        
        if not users and not groups and not entitlements:
            raise HTTPException(
                status_code=404, 
                detail=f"Server '{server_id}' not found or has no data"
            )
        
        # Get server summary
        summary = get_server_summary(server_id, db)
        
        # Export users with relationships
        users_data = []
        for user in users:
            user_dict = {}
            for column in user.__table__.columns:
                value = getattr(user, column.name)
                if isinstance(value, datetime):
                    user_dict[column.name] = value.isoformat() if value else None
                else:
                    user_dict[column.name] = value
            
            if include_relationships:
                # Get user's entitlements
                user_entitlements = db.query(UserEntitlement).filter(UserEntitlement.user_id == user.id).all()
                user_dict['entitlements'] = []
                for user_entitlement in user_entitlements:
                    entitlement = db.query(Entitlement).filter(Entitlement.id == user_entitlement.entitlement_id).first()
                    if entitlement:
                        user_dict['entitlements'].append({
                            'id': entitlement.id,
                            'scim_id': entitlement.scim_id,
                            'display_name': entitlement.display_name,
                            'type': entitlement.type,
                            'description': entitlement.description,
                            'entitlement_type': entitlement.entitlement_type,
                            'multi_valued': entitlement.multi_valued
                        })
                
                # Get user's groups
                user_groups = db.query(UserGroup).filter(UserGroup.user_id == user.id).all()
                user_dict['groups'] = []
                for user_group in user_groups:
                    group = db.query(Group).filter(Group.id == user_group.group_id).first()
                    if group:
                        user_dict['groups'].append({
                            'id': group.id,
                            'scim_id': group.scim_id,
                            'display_name': group.display_name,
                            'description': group.description
                        })
            
            users_data.append(user_dict)
        
        # Export groups with members
        groups_data = []
        for group in groups:
            group_dict = {}
            for column in group.__table__.columns:
                value = getattr(group, column.name)
                if isinstance(value, datetime):
                    group_dict[column.name] = value.isoformat() if value else None
                else:
                    group_dict[column.name] = value
            
            if include_relationships:
                # Get group members
                group_dict['members'] = []
                user_groups = db.query(UserGroup).filter(UserGroup.group_id == group.id).all()
                for user_group in user_groups:
                    user = db.query(User).filter(User.id == user_group.user_id).first()
                    if user:
                        group_dict['members'].append({
                            'user_id': user.id,
                            'user_name': user.user_name,
                            'display_name': user.display_name
                        })
            
            groups_data.append(group_dict)
        
        # Export entitlements with assignments
        entitlements_data = []
        for entitlement in entitlements:
            entitlement_dict = {}
            for column in entitlement.__table__.columns:
                value = getattr(entitlement, column.name)
                if isinstance(value, datetime):
                    entitlement_dict[column.name] = value.isoformat() if value else None
                else:
                    entitlement_dict[column.name] = value
            
            if include_relationships:
                # Get entitlement assignments
                entitlement_dict['assigned_users'] = []
                user_entitlements = db.query(UserEntitlement).filter(UserEntitlement.entitlement_id == entitlement.id).all()
                for user_entitlement in user_entitlements:
                    user = db.query(User).filter(User.id == user_entitlement.user_id).first()
                    if user:
                        entitlement_dict['assigned_users'].append({
                            'user_id': user.id,
                            'user_name': user.user_name,
                            'display_name': user.display_name
                        })
            
            entitlements_data.append(entitlement_dict)
        
        # Combine all data
        export_data = {
            "server_id": server_id,
            "summary": summary,
            "users": users_data,
            "groups": groups_data,
            "entitlements": entitlements_data,
            "metadata": {
                "exported_at": datetime.utcnow().isoformat() + "Z",
                "include_relationships": include_relationships,
                "users_count": len(users_data),
                "groups_count": len(groups_data),
                "entitlements_count": len(entitlements_data)
            }
        }
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting server: {str(e)}")


@router.get("/server-stats/{server_id}")
async def get_server_stats(
    server_id: str,
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """
    Get detailed statistics for a specific server.
    
    Args:
        server_id: The UUID of the server to get stats for
    
    Returns a JSON object containing server statistics and configuration.
    """
    try:
        db = next(get_db())
        
        # Check if server exists
        users = db.query(User).filter(User.server_id == server_id).all()
        groups = db.query(Group).filter(Group.server_id == server_id).all()
        entitlements = db.query(Entitlement).filter(Entitlement.server_id == server_id).all()
        
        if not users and not groups and not entitlements:
            raise HTTPException(
                status_code=404, 
                detail=f"Server '{server_id}' not found or has no data"
            )
        
        # Get server summary
        summary = get_server_summary(server_id, db)
        
        return {
            "server_id": server_id,
            "stats": summary["stats"],
            "config": summary["config"],
            "app_profile": summary["app_profile"],
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting server stats: {str(e)}")