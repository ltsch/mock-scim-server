from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

# Base SCIM schemas
class ScimMeta(BaseModel):
    """SCIM meta information."""
    resourceType: str
    created: Optional[datetime] = None
    lastModified: Optional[datetime] = None
    version: Optional[str] = None
    location: Optional[str] = None

class ScimName(BaseModel):
    """SCIM name object."""
    formatted: Optional[str] = None
    familyName: Optional[str] = None
    givenName: Optional[str] = None
    middleName: Optional[str] = None
    honorificPrefix: Optional[str] = None
    honorificSuffix: Optional[str] = None

class ScimEmail(BaseModel):
    """SCIM email object."""
    value: EmailStr
    type: Optional[str] = "work"
    primary: Optional[bool] = False

class ScimPhoneNumber(BaseModel):
    """SCIM phone number object."""
    value: str
    type: Optional[str] = "work"
    primary: Optional[bool] = False

class ScimAddress(BaseModel):
    """SCIM address object."""
    type: Optional[str] = "work"
    streetAddress: Optional[str] = None
    locality: Optional[str] = None
    region: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None
    formatted: Optional[str] = None
    primary: Optional[bool] = False

# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    userName: str = Field(..., description="Unique identifier for the user")
    externalId: Optional[str] = None
    displayName: Optional[str] = None
    name: Optional[ScimName] = None
    emails: Optional[List[ScimEmail]] = None
    phoneNumbers: Optional[List[ScimPhoneNumber]] = None
    addresses: Optional[List[ScimAddress]] = None
    userType: Optional[str] = None
    title: Optional[str] = None
    preferredLanguage: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    active: Optional[bool] = True

class UserCreate(UserBase):
    """Schema for creating a user."""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    userName: Optional[str] = None
    externalId: Optional[str] = None
    displayName: Optional[str] = None
    name: Optional[ScimName] = None
    emails: Optional[List[ScimEmail]] = None
    phoneNumbers: Optional[List[ScimPhoneNumber]] = None
    addresses: Optional[List[ScimAddress]] = None
    userType: Optional[str] = None
    title: Optional[str] = None
    preferredLanguage: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    active: Optional[bool] = None

class UserResponse(UserBase):
    """Schema for user responses."""
    id: str
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:User"]
    meta: ScimMeta
    groups: Optional[List[Dict[str, str]]] = None
    entitlements: Optional[List[Dict[str, str]]] = None


# Group schemas
class GroupBase(BaseModel):
    """Base group schema."""
    displayName: str = Field(..., description="Human-readable name for the group")
    description: Optional[str] = None

class GroupCreate(GroupBase):
    """Schema for creating a group."""
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:Group"]

class GroupUpdate(BaseModel):
    """Schema for updating a group."""
    displayName: Optional[str] = None
    description: Optional[str] = None

class GroupResponse(GroupBase):
    """Schema for group responses."""
    id: str
    schemas: List[str] = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
    meta: ScimMeta
    members: Optional[List[Dict[str, str]]] = None

# Entitlement schemas
class EntitlementBase(BaseModel):
    """Base entitlement schema."""
    displayName: str = Field(..., description="Human-readable name for the entitlement")
    type: str = Field(..., description="Type of entitlement (e.g., 'License', 'Profile')")
    description: Optional[str] = None
    entitlementType: Optional[str] = Field(None, description="Category of entitlement (e.g., 'application_access', 'role_based')")
    multiValued: Optional[bool] = Field(False, description="Whether this entitlement supports multiple values")

class EntitlementCreate(EntitlementBase):
    """Schema for creating an entitlement."""
    schemas: List[str] = ["urn:okta:scim:schemas:core:1.0:Entitlement"]

class EntitlementUpdate(BaseModel):
    """Schema for updating an entitlement."""
    displayName: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    entitlementType: Optional[str] = None
    multiValued: Optional[bool] = None

class EntitlementResponse(EntitlementBase):
    """Schema for entitlement responses."""
    id: str
    schemas: List[str] = ["urn:okta:scim:schemas:core:1.0:Entitlement"]
    meta: ScimMeta



# List response schemas
class ScimListResponse(BaseModel):
    """Base SCIM list response schema."""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:ListResponse"]
    totalResults: int
    startIndex: int = 1
    itemsPerPage: int
    Resources: List[Dict[str, Any]]

class UserListResponse(ScimListResponse):
    """User list response schema."""
    Resources: List[UserResponse]

class GroupListResponse(ScimListResponse):
    """Group list response schema."""
    Resources: List[GroupResponse]

class EntitlementListResponse(ScimListResponse):
    """Entitlement list response schema."""
    Resources: List[EntitlementResponse]



# Error response schema
class ScimError(BaseModel):
    """SCIM error response schema."""
    schemas: List[str] = ["urn:ietf:params:scim:api:messages:2.0:Error"]
    status: str
    scimType: Optional[str] = None
    detail: str 