"""
Simplified User endpoints using base endpoint classes.
This module eliminates massive code duplication by using the BaseEntityEndpoint class.
"""

from fastapi import APIRouter
from .endpoint_base import BaseEntityEndpoint
from .crud_entities import user_crud
from .response_converter import user_converter
from .schemas import UserCreate, UserUpdate, UserResponse, UserListResponse

# Create router
router = APIRouter(prefix="/v2/Users", tags=["Users"])

# Create endpoint handler using base class
# This single line replaces 253 lines of duplicated code!
user_endpoints = BaseEntityEndpoint(
    entity_type="User",
    router=router,
    crud_operations=user_crud,
    response_converter=user_converter,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    response_schema=UserResponse,
    list_response_schema=UserListResponse,
    schema_uri="urn:ietf:params:scim:schemas:core:2.0:User",
    supports_multi_server=True
) 