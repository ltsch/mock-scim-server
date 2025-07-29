# SCIM Server API & URLs Reference

## Overview

This document provides a comprehensive reference for all SCIM Server endpoints, URLs, and API usage. The server includes both **SCIM 2.0 endpoints** for identity provider integration and **Frontend API endpoints** for web-based management.

## Base URL

```
http://localhost:7001
```

## Authentication

All API endpoints require **API key authentication** using Bearer token format:

### API Keys
- **Default API Key**: `api-key-12345` (for normal operations)
- **Test API Key**: `test-api-key-12345` (for testing operations)

### Authentication Header
```
Authorization: Bearer api-key-12345
```

### Caddy Proxy Setup (Recommended)

For production use, configure Caddy to automatically inject the API key:

```caddyfile
localhost:7001 {
    env SCIM_API_KEY
    
    reverse_proxy localhost:7001 {
        header_up Authorization "Bearer {env.SCIM_API_KEY}"
    }
}
```

Then set the environment variable:
```bash
export SCIM_API_KEY="api-key-12345"
```

---

## Frontend API

The Frontend API provides web UI endpoints for reading server state and exporting server data. These endpoints are separate from the core SCIM functionality and are designed to support a web-based management interface.

### Base API Path
```
http://localhost:7001/api/
```

### 1. List All Servers

**GET** `/api/list-servers`

Returns a summary of all available SCIM servers with their statistics.

#### Response Format
```json
{
  "servers": [
    {
      "server_id": "test-hr-server",
      "stats": {
        "users": 3,
        "groups": 2,
        "entitlements": 3,
        "user_group_relationships": 5,
        "user_entitlement_relationships": 6
      },
      "config": {
        "server_id": "test-hr-server",
        "name": "SCIM Server test-hr-server",
        "description": "Dynamic SCIM server with ID test-hr-server",
        "app_profile": "hr",
        "enabled_resource_types": ["User", "Group", "Entitlement"]
      },
      "app_profile": "hr",
      "last_updated": "2025-07-28T23:15:16.197154Z"
    }
  ],
  "total": 45,
  "generated_at": "2025-07-28T23:15:16.197173Z"
}
```

#### Example Request
```bash
curl -H "Authorization: Bearer api-key-12345" \
     http://localhost:7001/api/list-servers
```

### 2. Export Server Data

**GET** `/api/export-server/{server_id}`

Exports complete server data including all users, groups, entitlements, and relationships.

#### Path Parameters
- `server_id` (string): The UUID of the server to export

#### Query Parameters
- `include_relationships` (boolean, default: `true`): Whether to include user-group and user-entitlement relationships

#### Response Format
```json
{
  "server_id": "test-hr-server",
  "summary": {
    "server_id": "test-hr-server",
    "stats": {
      "users": 3,
      "groups": 2,
      "entitlements": 3,
      "user_group_relationships": 5,
      "user_entitlement_relationships": 6
    },
    "config": { /* server configuration */ },
    "app_profile": "hr",
    "last_updated": "2025-07-28T23:15:16.197154Z"
  },
  "users": [
    {
      "id": 1,
      "scim_id": "user-123",
      "user_name": "john.doe",
      "display_name": "John Doe",
      "email": "john.doe@example.com",
      "active": true,
      "server_id": "test-hr-server",
      "entitlements": [
        {
          "id": 1,
          "scim_id": "entitlement-123",
          "display_name": "Office 365 License",
          "type": "application_access"
        }
      ],
      "groups": [
        {
          "id": 1,
          "scim_id": "group-123",
          "display_name": "Engineering Team",
          "description": "Engineering department"
        }
      ]
    }
  ],
  "groups": [
    {
      "id": 1,
      "scim_id": "group-123",
      "display_name": "Engineering Team",
      "description": "Engineering department",
      "server_id": "test-hr-server",
      "members": [
        {
          "user_id": 1,
          "user_name": "john.doe",
          "display_name": "John Doe"
        }
      ]
    }
  ],
  "entitlements": [
    {
      "id": 1,
      "scim_id": "entitlement-123",
      "display_name": "Office 365 License",
      "type": "application_access",
      "description": "Microsoft Office 365 license type",
      "server_id": "test-hr-server",
      "assigned_users": [
        {
          "user_id": 1,
          "user_name": "john.doe",
          "display_name": "John Doe"
        }
      ]
    }
  ],
  "metadata": {
    "exported_at": "2025-07-28T23:15:16.197173Z",
    "include_relationships": true,
    "users_count": 3,
    "groups_count": 2,
    "entitlements_count": 3
  }
}
```

#### Example Request
```bash
# Export with relationships
curl -H "Authorization: Bearer api-key-12345" \
     "http://localhost:7001/api/export-server/test-hr-server?include_relationships=true"

# Export without relationships
curl -H "Authorization: Bearer api-key-12345" \
     "http://localhost:7001/api/export-server/test-hr-server?include_relationships=false"
```

### 3. Get Server Statistics

**GET** `/api/server-stats/{server_id}`

Returns detailed statistics for a specific server.

#### Path Parameters
- `server_id` (string): The UUID of the server to get stats for

#### Response Format
```json
{
  "server_id": "test-hr-server",
  "stats": {
    "users": 3,
    "groups": 2,
    "entitlements": 3,
    "user_group_relationships": 5,
    "user_entitlement_relationships": 6
  },
  "config": {
    "server_id": "test-hr-server",
    "name": "SCIM Server test-hr-server",
    "description": "Dynamic SCIM server with ID test-hr-server",
    "app_profile": "hr",
    "enabled_resource_types": ["User", "Group", "Entitlement"]
  },
  "app_profile": "hr",
  "generated_at": "2025-07-28T23:15:16.197154Z"
}
```

#### Example Request
```bash
curl -H "Authorization: Bearer api-key-12345" \
     http://localhost:7001/api/server-stats/test-hr-server
```

---

## SCIM API

The SCIM API implements RFC 7644 compliant endpoints for identity provider integration.

### Base SCIM Path Pattern
```
/scim-identifier/{server_id}/scim/v2
```

### Example Server URLs
- **Test HR Server**: `http://localhost:7001/scim-identifier/test-hr-server/scim/v2/`
- **Test IT Server**: `http://localhost:7001/scim-identifier/test-it-server/scim/v2/`

### SCIM Endpoints

#### Users
- **URL**: `/Users`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: User management operations

#### Groups
- **URL**: `/Groups`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Group management operations

#### Entitlements
- **URL**: `/Entitlements`
- **Methods**: GET, POST, PUT, PATCH, DELETE
- **Description**: Entitlement management operations

#### Resource Types
- **URL**: `/ResourceTypes`
- **Methods**: GET
- **Description**: Schema discovery for available resource types

#### Schemas
- **URL**: `/Schemas`
- **Methods**: GET
- **Description**: Schema discovery for all available schemas

### Complete Example URLs
```
http://localhost:7001/scim-identifier/test-hr-server/scim/v2/Users
http://localhost:7001/scim-identifier/test-hr-server/scim/v2/Groups
http://localhost:7001/scim-identifier/test-hr-server/scim/v2/Entitlements
http://localhost:7001/scim-identifier/test-hr-server/scim/v2/ResourceTypes
http://localhost:7001/scim-identifier/test-hr-server/scim/v2/Schemas
```

### SCIM Example Requests

#### List Users
```bash
curl -H "Authorization: Bearer api-key-12345" \
     "http://localhost:7001/scim-identifier/test-hr-server/scim/v2/Users"
```

#### Get Specific User
```bash
curl -H "Authorization: Bearer api-key-12345" \
     "http://localhost:7001/scim-identifier/test-hr-server/scim/v2/Users/user-123"
```

#### Create User
```bash
curl -X POST \
     -H "Authorization: Bearer api-key-12345" \
     -H "Content-Type: application/scim+json" \
     -d '{
       "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
       "userName": "john.doe",
       "displayName": "John Doe",
       "emails": [{"value": "john.doe@example.com", "primary": true}],
       "active": true
     }' \
     "http://localhost:7001/scim-identifier/test-hr-server/scim/v2/Users"
```

#### List Groups
```bash
curl -H "Authorization: Bearer api-key-12345" \
     "http://localhost:7001/scim-identifier/test-hr-server/scim/v2/Groups"
```

#### Get Resource Types
```bash
curl -H "Authorization: Bearer api-key-12345" \
     "http://localhost:7001/scim-identifier/test-hr-server/scim/v2/ResourceTypes"
```

---

## Web Interface

### Main Web UI
- **URL**: `http://localhost:7001/`
- **Description**: Modern web interface for managing SCIM servers
- **Features**: Server listing, data export, statistics visualization

### Static Files
- **URL**: `http://localhost:7001/static/`
- **Description**: Static assets for the web interface

---

## System URLs

### Health Check
- **URL**: `http://localhost:7001/healthz`
- **Description**: Health check endpoint for readiness/liveness probes
- **Authentication**: Not required

### API Information
- **URL**: `http://localhost:7001/api`
- **Description**: API information and endpoint documentation
- **Authentication**: Not required

### Routing Information
- **URL**: `http://localhost:7001/routing`
- **Description**: Routing configuration and SCIM client compatibility info
- **Authentication**: Not required

---

## Error Responses

### Authentication Errors (401)
```json
{
  "detail": "Authorization header required"
}
```

```json
{
  "detail": "Authorization header must start with 'Bearer '"
}
```

```json
{
  "detail": "Invalid or inactive API key"
}
```

### Validation Errors (400)
```json
{
  "detail": "Server ID is required"
}
```

```json
{
  "detail": "Server ID must contain only alphanumeric characters, hyphens, and underscores"
}
```

### Not Found Errors (404)
```json
{
  "detail": "Server 'invalid-server-id' not found or has no data"
}
```

### Server Errors (500)
```json
{
  "detail": "Error listing servers: Database connection failed"
}
```

---

## Rate Limiting

All API endpoints are subject to rate limiting:
- **Read operations**: 500 requests per 30 minutes
- **Write operations**: 500 requests per 30 minutes

---

## CORS Support

Both Frontend API and SCIM API endpoints support CORS for cross-origin requests from web applications.

---

## Development Notes

- All endpoints return JSON responses
- Timestamps are in ISO 8601 format with UTC timezone
- Server IDs must be alphanumeric with hyphens and underscores only
- Relationships are included by default but can be disabled for performance
- The web interface automatically hides API key input when using Caddy proxy setup
- SCIM endpoints follow RFC 7644 specification exactly
- Frontend API endpoints are designed for web UI consumption

---

## Quick Reference

### Frontend API Endpoints
- `GET /api/list-servers` - List all servers
- `GET /api/export-server/{server_id}` - Export server data
- `GET /api/server-stats/{server_id}` - Get server statistics

### SCIM API Endpoints
- `GET /scim-identifier/{server_id}/scim/v2/Users` - List users
- `GET /scim-identifier/{server_id}/scim/v2/Groups` - List groups
- `GET /scim-identifier/{server_id}/scim/v2/Entitlements` - List entitlements
- `GET /scim-identifier/{server_id}/scim/v2/ResourceTypes` - Get resource types
- `GET /scim-identifier/{server_id}/scim/v2/Schemas` - Get schemas

### System Endpoints
- `GET /healthz` - Health check
- `GET /api/info` - API information
- `GET /api/protected` - Authentication test endpoint
- `GET /api/routing` - Routing information
- `GET /frontend/index.html` - Web interface
- `GET /` - 404 Not Found (no root endpoint)

### Frontend Routes
- `GET /frontend/index.html` - Web UI for managing SCIM servers
- `GET /frontend/static/*` - Static assets for the web interface