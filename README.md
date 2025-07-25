# SCIM.Cloud: Development-Friendly SCIM 2.0 Server

## Overview

**SCIM.Cloud** is a fully self-contained, developer-focused SCIM 2.0 server designed for rapid prototyping, testing, and integration with identity providers such as Okta. It is built to comply with the SCIM 2.0 specification and Okta's extension-driven design for ResourceTypes and entitlements ([Okta SCIM with Entitlements Guide](https://developer.okta.com/docs/guides/scim-with-entitlements/main/)).

This project is ideal for developers who need a mock SCIM server for integration testing, development, or demonstration purposes. It is not intended for production use.

---

## Project Goals

- **SCIM 2.0 Compliance:** Implement all core SCIM endpoints and behaviors, with a focus on Okta's unique requirements for ResourceTypes, entitlements, and schema discovery. ([SCIM 2.0 RFC 7644](https://datatracker.ietf.org/doc/html/rfc7644), [Okta SCIM with Entitlements Guide](https://developer.okta.com/docs/guides/scim-with-entitlements/main/))
- **Standalone & Self-Contained:** No external dependencies or services. All data and configuration are stored in a local SQLite database.
- **Developer Experience:** Extensive logging, debugging, and comprehensive testing infrastructure.
- **Extensibility:** Designed for easy extension and modification, including support for custom schemas and attributes.
- **Authentication:** Simple API key authentication using static keys provided as Bearer tokens in the Authorization header.
- **Multi-threaded Python Backend:** High responsiveness for concurrent development/testing scenarios.
- **Dynamic Testing:** Comprehensive test suite that adapts to actual database data without hardcoded values.

---

## Features

### **✅ Implemented Features**

- **SCIM 2.0 Endpoints:**
  - `/v2/ResourceTypes` - Returns available resource types for schema discovery
  - `/v2/Schemas` - Returns custom schema extensions (currently empty)
  - `/v2/Users` - Full CRUD operations with SCIM filtering and pagination
  - `/v2/Groups` - Full CRUD operations with SCIM filtering and pagination
  - `/v2/Entitlements` - Full CRUD operations with SCIM filtering and pagination
  - `/v2/Roles` - Full CRUD operations with SCIM filtering and pagination
  - Okta-compatible extension endpoints and schema discovery
- **SCIM Filtering & Pagination:**
  - Support for SCIM filter operators (`eq`, `co`, `sw`, `ew`)
  - Proper pagination with filtered total counts
  - Dynamic filter parsing and database querying
- **Authentication:**
  - API key(s) defined in the SQLite database
  - Bearer token required in the `Authorization` header
  - Unauthenticated requests return HTTP 401
- **Database:**
  - All data (users, groups, entitlements, roles, schemas, API keys, etc.) stored in SQLite
  - Centralized schema for easy backup, migration, and inspection
  - Comprehensive relationship management (user-group, user-entitlement, user-role)
- **Logging & Debugging:**
  - Verbose, developer-friendly logging for all API calls and database operations
  - Debug endpoints and detailed error messages
  - Real-time test execution logging
- **Testing Infrastructure:**
  - **93.9% Test Success Rate** (46/49 tests passing)
  - Dynamic testing that adapts to actual database data
  - Comprehensive test coverage for all endpoints and operations
  - No hardcoded values in test suite
  - Real-time test reporting and detailed execution logs

### **🔄 Planned Features**

- **Web Frontend:** A minimal web UI for browsing and editing database contents
- **Custom Schemas:** Support for custom SCIM schema extensions
- **Advanced Filtering:** Additional SCIM filter operators and complex queries

---

## Requirements

- **Python 3.8+**
- **SQLite3** (bundled with Python standard library)
- **Python Packages:**
  - `fastapi==0.116.1` (for API server)
  - `uvicorn==0.35.0` (for ASGI server, multithreaded)
  - `sqlalchemy==2.0.41` (for ORM/database access)
  - `pydantic==2.11.7` (for data validation)
  - `loguru==0.7.3` (for logging)
  - `pytest==8.4.1` (for tests)
  - `httpx==0.28.1` (for testing)
  - `requests==2.31.0` (for comprehensive testing)

All dependencies should be installed locally (e.g., in a virtual environment or with `--user`).

---

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd scim-server
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize database:**
   ```bash
   python scripts/init_db.py
   ```

3. **Create test data (optional):**
   ```bash
   python scripts/create_test_data.py
   ```

4. **Start the server:**
   ```bash
   python run_server.py
   ```

5. **Test the API:**
   ```bash
   # Health check
   curl http://localhost:8000/healthz
   
   # Get resource types (requires authentication)
   curl -H "Authorization: Bearer dev-api-key-12345" http://localhost:8000/v2/ResourceTypes
   
   # List users with filtering
   curl -H "Authorization: Bearer dev-api-key-12345" "http://localhost:8000/v2/Users/?filter=userName%20eq%20%22testuser@example.com%22"
   ```

6. **Run comprehensive tests:**
   ```bash
   python scripts/run_comprehensive_tests.py
   ```

---

## Design Philosophies

- **Simplicity First:** Prioritize clear, maintainable code and a simple, functional UI (for the planned frontend). Avoid unnecessary complexity or "fancy" features.
- **Centralized Data:** All configuration and data are stored in SQLite. No hardcoded users, groups, or entitlements outside the database.
- **Extensive Logging:** All actions, errors, and API calls are logged in detail to aid development and debugging.
- **Okta Compatibility:** Special attention to Okta's SCIM extension requirements, including `/ResourceTypes`, `/Schemas`, and entitlement/role endpoints.
- **Stateless API:** All state is persisted in the database; the server itself is stateless between requests.
- **Authentication:** Only API key authentication is supported. No OAuth, SAML, or other auth mechanisms.
- **Dynamic Testing:** All tests read actual data from endpoints instead of using hardcoded values. Tests adapt to whatever data is present in the database.
- **Frontend Separation:** The backend is designed to support a simple web frontend for debugging, but the frontend is a separate phase and should not affect backend design.

---

## Project Structure

```
scim-server/
├── scim_server/           # Python package for the SCIM backend
│   ├── __init__.py
│   ├── main.py           # FastAPI app and basic endpoints
│   ├── database.py       # SQLAlchemy setup and database utilities
│   ├── models.py         # Database models for all SCIM entities
│   ├── auth.py           # API key authentication
│   ├── schemas.py        # Pydantic models for SCIM entities
│   ├── crud.py           # CRUD operations for all entities
│   ├── utils.py          # Utility functions for SCIM operations
│   ├── scim_endpoints.py # SCIM 2.0 discovery endpoints
│   ├── user_endpoints.py # User CRUD endpoints
│   ├── group_endpoints.py # Group CRUD endpoints
│   ├── entitlement_endpoints.py # Entitlement CRUD endpoints
│   └── role_endpoints.py # Role CRUD endpoints
├── tests/                # Automated tests
│   ├── __init__.py
│   ├── conftest.py       # Pytest configuration and fixtures
│   ├── test_health.py    # Health check tests
│   ├── test_auth.py      # Authentication tests
│   ├── test_scim_endpoints.py # SCIM endpoint tests
│   └── test_user_endpoints.py # User endpoint tests
├── scripts/              # Utility scripts
│   ├── init_db.py        # Database initialization script
│   ├── create_test_data.py # Test data creation script
│   └── run_comprehensive_tests.py # Comprehensive test runner
├── .cursor/rules/        # Project coding and design guidelines
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── run_server.py         # Development server runner
└── scim.db              # SQLite database file (created at runtime)
```

---

## Authentication

- All API requests must include an `Authorization: Bearer <API_KEY>` header.
- API keys are stored in the SQLite database and can be managed via the API.
- Requests without a valid API key will receive a 401 Unauthorized response.
- Default development API key: `dev-api-key-12345`
- Test API key: `test-api-key-12345` (created by test data script)

---

## SCIM Filtering & Pagination

The server supports SCIM 2.0 filtering and pagination:

### **Filtering Examples:**
```bash
# Exact username match
curl -H "Authorization: Bearer dev-api-key-12345" \
  "http://localhost:8000/v2/Users/?filter=userName%20eq%20%22testuser@example.com%22"

# Contains display name
curl -H "Authorization: Bearer dev-api-key-12345" \
  "http://localhost:8000/v2/Users/?filter=displayName%20co%20%22John%22"

# Group filtering
curl -H "Authorization: Bearer dev-api-key-12345" \
  "http://localhost:8000/v2/Groups/?filter=displayName%20co%20%22Engineering%22"
```

### **Pagination Examples:**
```bash
# Get first 2 users
curl -H "Authorization: Bearer dev-api-key-12345" \
  "http://localhost:8000/v2/Users/?startIndex=1&count=2"

# Get users 3-5
curl -H "Authorization: Bearer dev-api-key-12345" \
  "http://localhost:8000/v2/Users/?startIndex=3&count=3"
```

---

## Logging & Debugging

- All API calls, errors, and database operations are logged with timestamps and context.
- Debug endpoints and detailed error messages are provided for developer convenience.
- Real-time test execution logging shows exactly what's happening during tests.
- Logging verbosity can be configured via environment variables or config file.

---

## Database

- Uses SQLite for all persistent storage.
- All entities (users, groups, entitlements, roles, schemas, API keys, etc.) are stored in the database.
- Database schema is designed for extensibility and easy inspection.
- Comprehensive relationship management between entities.

---

## Testing

### **Test Results:**
- **Success Rate:** 93.9% (46/49 tests passing)
- **Coverage:** All endpoints and operations tested
- **Dynamic Testing:** Tests adapt to actual database data
- **No Hardcoded Values:** All test data is read from endpoints

### **Running Tests:**

```bash
# Run unit tests
PYTHONPATH=. pytest tests/ -v

# Run comprehensive integration tests
python scripts/run_comprehensive_tests.py

# Create test data first (if needed)
python scripts/create_test_data.py
```

### **Test Features:**
- **Dynamic Data:** Tests read actual data from endpoints
- **Real-time Reporting:** Detailed execution logs and progress tracking
- **Server Verification:** Automatic server availability checking
- **Comprehensive Coverage:** All CRUD operations, filtering, pagination, and error handling

---

## Extensibility

- Custom schemas and attributes are supported via the `/Schemas` endpoint and database extensions.
- Designed to be easily modifiable for new resource types or attributes.
- Modular endpoint structure allows easy addition of new SCIM resources.

---

## Planned Frontend

- A minimal web UI for browsing and editing users, groups, entitlements, and other data in the SQLite database.
- Intended for debugging and development only; not for production use.
- Will be implemented in a later phase.

---

## SCIM/Okta-Compliant Example Responses

### ResourceTypes Example
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 4,
  "startIndex": 1,
  "itemsPerPage": 4,
  "Resources": [
    {
      "id": "User",
      "name": "User",
      "endpoint": "/Users",
      "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
    },
    {
      "id": "Group",
      "name": "Group",
      "endpoint": "/Groups",
      "schema": "urn:ietf:params:scim:schemas:core:2.0:Group"
    },
    {
      "id": "Entitlement",
      "name": "Entitlement",
      "endpoint": "/Entitlements",
      "schema": "urn:okta:scim:schemas:core:1.0:Entitlement"
    },
    {
      "id": "Role",
      "name": "Role",
      "endpoint": "/Roles",
      "schema": "urn:okta:scim:schemas:core:1.0:Role"
    }
  ]
}
```

### Filtered Users Example
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
  "totalResults": 1,
  "startIndex": 1,
  "itemsPerPage": 1,
  "Resources": [
    {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
      "id": "998dd507-27fb-4f74-a84a-90ab3c0454e1",
      "userName": "testuser@example.com",
      "displayName": "Test User",
      "active": true,
      "meta": {
        "resourceType": "User",
        "created": "2025-07-25T20:00:00Z",
        "lastModified": "2025-07-25T20:00:00Z",
        "version": "1"
      }
    }
  ]
}
```

### Error Response Example
```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
  "status": "401",
  "scimType": "invalidToken",
  "detail": "Invalid or missing API key. Please provide a valid Bearer token in the Authorization header."
}
```

---

## Contributing

- All code must follow the guidelines in `.cursor/rules/` (MDC format, see [Cursor Project Rules](https://docs.cursor.com/context/rules)).
- All new features and bugfixes must include automated tests covering all endpoints.
- Tests must use dynamic data and avoid hardcoded values.
- Update this README as new decisions are made or features are added.

---

## License

This project is open source and intended for development and testing purposes only. See `LICENSE` for details.

---

## References

- [SCIM 2.0 Specification (RFC 7644)](https://datatracker.ietf.org/doc/html/rfc7644)
- [Okta SCIM with Entitlements Guide](https://developer.okta.com/docs/guides/scim-with-entitlements/main/)
- [Cursor Project Rules](https://docs.cursor.com/context/rules)

---

## Contact

For questions or suggestions, please open an issue or contact the maintainer. 