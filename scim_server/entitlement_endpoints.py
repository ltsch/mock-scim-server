"""
Simplified Entitlement endpoints using base endpoint classes.
This module eliminates massive code duplication by using the BaseEntityEndpoint class.
"""

from fastapi import APIRouter
from .endpoint_base import BaseEntityEndpoint
from .crud_entities import entitlement_crud
from .response_converter import entitlement_converter
from .schemas import EntitlementCreate, EntitlementUpdate, EntitlementResponse, EntitlementListResponse

# Create router
from .config import settings

# Construct the API prefix dynamically
api_prefix = f"{settings.api_base_path}/scim/v2/Entitlements"
router = APIRouter(prefix=api_prefix, tags=["Entitlements"])

# Create endpoint handler using base class
# This single line replaces 234 lines of duplicated code!
entitlement_endpoints = BaseEntityEndpoint(
    entity_type="Entitlement",
    router=router,
    crud_operations=entitlement_crud,
    response_converter=entitlement_converter,
    create_schema=EntitlementCreate,
    update_schema=EntitlementUpdate,
    response_schema=EntitlementResponse,
    list_response_schema=EntitlementListResponse,
    schema_uri="urn:okta:scim:schemas:core:1.0:Entitlement",
    supports_multi_server=True
) 