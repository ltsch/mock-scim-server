"""
Generic SCIM response converter for all entities.
This module eliminates response conversion duplication by providing a single converter.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .models import User, Group, Entitlement
from .schemas import ScimMeta, ScimName, ScimEmail

class ScimResponseConverter:
    """
    Generic SCIM response converter that eliminates duplication across all entity types.
    
    This class provides a single, configurable way to convert any database entity
    to SCIM response format, eliminating the need for separate conversion functions.
    """
    
    def __init__(self, schema_uri: str, field_mapping: Dict[str, str], entity_type: str):
        """
        Initialize the converter with entity-specific configuration.
        
        Args:
            schema_uri: The SCIM schema URI for this entity type
            field_mapping: Mapping from SCIM field names to database field names
            entity_type: The entity type name for meta information
        """
        self.schema_uri = schema_uri
        self.field_mapping = field_mapping
        self.entity_type = entity_type
    
    def to_scim_response(self, entity) -> Dict[str, Any]:
        """
        Convert any entity to SCIM response format.
        
        Args:
            entity: Database entity (User, Group, Entitlement)
            
        Returns:
            Dict containing SCIM response format
        """
        # Create meta information
        meta = self._create_scim_meta(entity)
        
        # Build base response
        response = {
            "schemas": [self.schema_uri],
            "id": entity.scim_id,
            "meta": meta.model_dump()
        }
        
        # Add entity-specific fields
        response.update(self._extract_entity_fields(entity))
        
        return response
    
    def _create_scim_meta(self, entity) -> ScimMeta:
        """Create SCIM meta information for the entity."""
        return ScimMeta(
            resourceType=self.entity_type,
            created=entity.created_at or datetime.utcnow(),
            lastModified=entity.updated_at or datetime.utcnow(),
            version="W/\"1\"",
            location=f"/v2/{self.entity_type}s/{entity.scim_id}"
        )
    
    def _extract_entity_fields(self, entity) -> Dict[str, Any]:
        """Extract entity-specific fields based on entity type."""
        if isinstance(entity, User):
            return self._extract_user_fields(entity)
        elif isinstance(entity, Group):
            return self._extract_group_fields(entity)
        elif isinstance(entity, Entitlement):
            return self._extract_entitlement_fields(entity)

        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")
    
    def _extract_user_fields(self, user: User) -> Dict[str, Any]:
        """Extract User-specific fields."""
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
        
        return {
            "externalId": user.external_id,
            "userName": user.user_name,
            "displayName": user.display_name,
            "name": name.model_dump() if name else None,
            "emails": [email.model_dump() for email in emails],
            "active": user.active,
        }
    
    def _extract_group_fields(self, group: Group) -> Dict[str, Any]:
        """Extract Group-specific fields."""
        return {
            "displayName": group.display_name,
            "description": group.description,
            "members": [],  # TODO: Implement member relationships
        }
    
    def _extract_entitlement_fields(self, entitlement: Entitlement) -> Dict[str, Any]:
        """Extract Entitlement-specific fields."""
        return {
            "displayName": entitlement.display_name,
            "type": entitlement.type,
            "description": entitlement.description,
            "entitlementType": entitlement.entitlement_type,
            "multiValued": entitlement.multi_valued,
        }
    


# Pre-configured converters for each entity type
class UserResponseConverter(ScimResponseConverter):
    """User-specific response converter."""
    
    def __init__(self):
        super().__init__(
            schema_uri="urn:ietf:params:scim:schemas:core:2.0:User",
            field_mapping={
                'userName': 'user_name',
                'displayName': 'display_name',
                'givenName': 'given_name',
                'familyName': 'family_name',
                'email': 'email',
            },
            entity_type="User"
        )

class GroupResponseConverter(ScimResponseConverter):
    """Group-specific response converter."""
    
    def __init__(self):
        super().__init__(
            schema_uri="urn:ietf:params:scim:schemas:core:2.0:Group",
            field_mapping={
                'displayName': 'display_name',
                'description': 'description',
            },
            entity_type="Group"
        )

class EntitlementResponseConverter(ScimResponseConverter):
    """Entitlement-specific response converter."""
    
    def __init__(self):
        super().__init__(
            schema_uri="urn:okta:scim:schemas:core:1.0:Entitlement",
            field_mapping={
                'displayName': 'display_name',
                'type': 'type',
                'description': 'description',
                'entitlementType': 'entitlement_type',
                'multiValued': 'multi_valued',
            },
            entity_type="Entitlement"
        )

# Create instances for easy import
user_converter = UserResponseConverter()
group_converter = GroupResponseConverter()
entitlement_converter = EntitlementResponseConverter() 