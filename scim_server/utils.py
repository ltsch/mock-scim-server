from typing import Dict, Any, List, Optional
from datetime import datetime
from .models import User, Group, Entitlement, Role
from .schemas import ScimMeta, ScimName, ScimEmail, UserResponse, GroupResponse, EntitlementResponse, RoleResponse

def create_scim_meta(resource_type: str, resource_id: str, created: datetime = None, modified: datetime = None) -> ScimMeta:
    """Create SCIM meta information."""
    return ScimMeta(
        resourceType=resource_type,
        created=created or datetime.utcnow(),
        lastModified=modified or datetime.utcnow(),
        version="W/\"1\"",
        location=f"/v2/{resource_type}s/{resource_id}"
    )

def user_to_scim_response(user: User) -> Dict[str, Any]:
    """Convert User database model to SCIM response format."""
    # Build name object
    name = None
    if user.given_name or user.family_name:
        name = ScimName(
            givenName=user.given_name,
            familyName=user.family_name,
            formatted=f"{user.given_name or ''} {user.family_name or ''}".strip() if (user.given_name or user.family_name) else None
        )
    
    # Build emails array
    emails = []
    if user.email:
        emails.append(ScimEmail(value=user.email, primary=True))
    
    # Build meta information
    meta = create_scim_meta("User", user.scim_id, user.created_at, user.updated_at)
    
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user.scim_id,
        "externalId": user.external_id,
        "userName": user.user_name,
        "displayName": user.display_name,
        "name": name.model_dump() if name else None,
        "emails": [email.model_dump() for email in emails],
        "active": user.active,
        "meta": meta.model_dump()
    }

def group_to_scim_response(group: Group) -> Dict[str, Any]:
    """Convert Group database model to SCIM response format."""
    meta = create_scim_meta("Group", group.scim_id, group.created_at, group.updated_at)
    
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "id": group.scim_id,
        "displayName": group.display_name,
        "description": group.description,
        "members": [],  # TODO: Implement member relationships
        "meta": meta.model_dump()
    }

def entitlement_to_scim_response(entitlement: Entitlement) -> Dict[str, Any]:
    """Convert Entitlement database model to SCIM response format."""
    meta = create_scim_meta("Entitlement", entitlement.scim_id, entitlement.created_at, entitlement.updated_at)
    
    return {
        "schemas": ["urn:okta:scim:schemas:core:1.0:Entitlement"],
        "id": entitlement.scim_id,
        "displayName": entitlement.display_name,
        "type": entitlement.type,
        "description": entitlement.description,
        "meta": meta.model_dump()
    }

def role_to_scim_response(role: Role) -> Dict[str, Any]:
    """Convert Role database model to SCIM response format."""
    meta = create_scim_meta("Role", role.scim_id, role.created_at, role.updated_at)
    
    return {
        "schemas": ["urn:okta:scim:schemas:core:1.0:Role"],
        "id": role.scim_id,
        "displayName": role.display_name,
        "description": role.description,
        "meta": meta.model_dump()
    }

def create_scim_list_response(resources: List[Dict[str, Any]], total_results: int, start_index: int = 1, items_per_page: int = None) -> Dict[str, Any]:
    """Create a SCIM list response."""
    if items_per_page is None:
        items_per_page = len(resources)
    
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": total_results,
        "startIndex": start_index,
        "itemsPerPage": items_per_page,
        "Resources": resources
    }

# Allowed filter fields and operators for security
ALLOWED_FILTER_FIELDS = {
    'userName', 'displayName', 'email', 'givenName', 'familyName',
    'active', 'externalId'
}

ALLOWED_OPERATORS = {'eq', 'co', 'sw', 'ew'}

def parse_scim_filter(filter_query: str) -> Optional[Dict[str, Any]]:
    """
    Parse SCIM filter query and return structured filter information.
    Returns a dict with 'field', 'operator', and 'value' keys.
    Validates against allowed fields and operators for security.
    """
    if not filter_query:
        return None
    
    # Remove 'filter=' prefix if present
    if filter_query.startswith('filter='):
        filter_query = filter_query[7:]
    
    # Parse common SCIM filter patterns
    import re
    
    # Pattern for: field operator "value"
    pattern = r'(\w+)\s+(eq|co|sw|ew)\s+"([^"]*)"'
    match = re.search(pattern, filter_query)
    
    if match:
        field = match.group(1)
        operator = match.group(2)
        value = match.group(3)
        
        # Validate field and operator against whitelist
        if field not in ALLOWED_FILTER_FIELDS:
            return None
        
        if operator not in ALLOWED_OPERATORS:
            return None
        
        return {
            'field': field,
            'operator': operator,
            'value': value
        }
    
    # If no pattern found, return None
    return None

def validate_scim_id(scim_id: str) -> bool:
    """Validate SCIM ID format (UUID)."""
    import uuid
    try:
        uuid.UUID(scim_id)
        return True
    except ValueError:
        return False

def create_error_response(status: str, detail: str, scim_type: Optional[str] = None) -> Dict[str, Any]:
    """Create a SCIM error response."""
    error = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "status": status,
        "detail": detail
    }
    
    if scim_type:
        error["scimType"] = scim_type
    
    return error 