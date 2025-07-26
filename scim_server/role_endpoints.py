"""
Simplified Role endpoints using base endpoint classes.
This module eliminates massive code duplication by using the BaseEntityEndpoint class.
"""

from fastapi import APIRouter
from .endpoint_base import BaseEntityEndpoint
from .crud_entities import role_crud
from .response_converter import role_converter
from .schemas import RoleCreate, RoleUpdate, RoleResponse, RoleListResponse

# Create router
router = APIRouter(prefix="/v2/Roles", tags=["Roles"])

# Create endpoint handler using base class
# This single line replaces 234 lines of duplicated code!
role_endpoints = BaseEntityEndpoint(
    entity_type="Role",
    router=router,
    crud_operations=role_crud,
    response_converter=role_converter,
    create_schema=RoleCreate,
    update_schema=RoleUpdate,
    response_schema=RoleResponse,
    list_response_schema=RoleListResponse,
    schema_uri="urn:okta:scim:schemas:core:1.0:Role",
    supports_multi_server=True
) 