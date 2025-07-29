from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class ApiKey(Base):
    """API keys for authentication."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

class AppProfile(Base):
    """App Profile entity for defining different application layouts and configurations."""
    __tablename__ = "app_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    app_type = Column(String(100), nullable=False)  # e.g., "hr", "it", "sales", "marketing"
    configuration = Column(JSON, nullable=True)  # JSON configuration for the profile
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    """SCIM User entity."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    scim_id = Column(String(255), unique=True, index=True, nullable=False)
    external_id = Column(String(255), index=True, nullable=True)
    user_name = Column(String(255), nullable=False)  # Remove global unique constraint
    display_name = Column(String(255), nullable=True)
    given_name = Column(String(100), nullable=True)
    family_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)  # Remove global unique constraint
    active = Column(Boolean, default=True)
    server_id = Column(String(255), index=True, nullable=False)
    app_profile_id = Column(String(255), ForeignKey("app_profiles.profile_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Add composite unique constraints for server-specific uniqueness
    __table_args__ = (
        UniqueConstraint('user_name', 'server_id', name='uq_user_name_server'),
        UniqueConstraint('email', 'server_id', name='uq_user_email_server'),
    )

class Group(Base):
    """SCIM Group entity."""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    scim_id = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    server_id = Column(String(255), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Entitlement(Base):
    """SCIM Entitlement entity for Okta compatibility."""
    __tablename__ = "entitlements"
    
    id = Column(Integer, primary_key=True, index=True)
    scim_id = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)  # e.g., "License", "Profile"
    description = Column(Text, nullable=True)
    entitlement_type = Column(String(100), nullable=True)  # e.g., "application_access", "role_based"
    multi_valued = Column(Boolean, default=False)  # Whether this entitlement supports multiple values
    server_id = Column(String(255), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())



class Schema(Base):
    """SCIM Schema definitions for custom extensions."""
    __tablename__ = "schemas"
    
    id = Column(Integer, primary_key=True, index=True)
    urn = Column(String(500), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    schema_definition = Column(Text, nullable=False)  # JSON schema definition
    server_id = Column(String(255), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Association tables for many-to-many relationships
class UserGroup(Base):
    """Association table for User-Group relationships."""
    __tablename__ = "user_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)

class UserEntitlement(Base):
    """Association table for User-Entitlement relationships."""
    __tablename__ = "user_entitlements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entitlement_id = Column(Integer, ForeignKey("entitlements.id"), nullable=False)

 