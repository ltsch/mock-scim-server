"""
Simplified Group endpoints using base endpoint classes.
This module eliminates massive code duplication by using the BaseEntityEndpoint class.
"""

from fastapi import APIRouter
from .endpoint_base import BaseEntityEndpoint
from .crud_entities import group_crud
from .response_converter import group_converter
from .schemas import GroupCreate, GroupUpdate, GroupResponse, GroupListResponse

# Create router
from .config import settings

# Construct the API prefix dynamically
api_prefix = f"{settings.api_base_path}/scim/v2/Groups"
router = APIRouter(prefix=api_prefix, tags=["Groups"])

# Create endpoint handler using base class
# This single line replaces 234 lines of duplicated code!
group_endpoints = BaseEntityEndpoint(
    entity_type="Group",
    router=router,
    crud_operations=group_crud,
    response_converter=group_converter,
    create_schema=GroupCreate,
    update_schema=GroupUpdate,
    response_schema=GroupResponse,
    list_response_schema=GroupListResponse,
    schema_uri="urn:ietf:params:scim:schemas:core:2.0:Group",
    supports_multi_server=True
) 