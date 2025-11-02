# Changelog

All notable changes to the Backend Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-11-02

### Added

#### OAuth 2.0 Authentication
- Complete OAuth 2.0 implementation using Authlib 1.2.1
- Multiple grant types support:
  - Authorization Code with PKCE
  - Password Grant
  - Refresh Token
  - Client Credentials
- Token management endpoints:
  - `/oauth/token` - Token generation and refresh
  - `/oauth/revoke` - Token revocation
  - `/oauth/introspect` - Token introspection
  - `/oauth/userinfo` - User information (OpenID Connect compatible)
- OAuth client management:
  - `/oauth/client/register` - Register new OAuth clients
  - `/oauth/client/list` - List user's OAuth clients
- Scope-based access control (read, write, admin, profile)
- PKCE support for enhanced security in public clients
- Automatic token expiration and refresh

#### Multi-Tenant Architecture
- Complete tenant isolation at database level
- Tenant model with subscription plans (free, basic, premium, enterprise)
- Flexible tenant identification strategies:
  - Subdomain-based (e.g., `acme.example.com`)
  - Custom domain (e.g., `acme-corp.com`)
  - HTTP header (`X-Tenant-Slug`, `X-Tenant-ID`)
  - Path parameter
- Tenant management API:
  - `/tenants/register` - Register new tenant
  - `/tenants/info` - Get tenant information
  - `/tenants/stats` - Tenant statistics
  - `/tenants/users` - User management
  - `/tenants/settings` - Tenant settings
  - `/tenants/list` - List all tenants
- Role-based access control per tenant:
  - User - Basic access
  - Admin - User management and statistics
  - Owner - Full tenant control
- Tenant context management with automatic filtering
- Per-tenant resource limits and usage tracking
- Tenant-aware database models with composite unique constraints

#### Documentation
- `docs/OAUTH2.md` - Comprehensive OAuth 2.0 guide (600+ lines)
- `docs/MULTI_TENANT.md` - Multi-tenant architecture guide (650+ lines)
- `docs/MIGRATION.md` - JWT to OAuth 2.0 migration guide (400+ lines)
- `docs/OAUTH2_QUICK_REFERENCE.md` - Quick reference guide
- `docs/architecture.drawio` - Visual architecture diagram
- Updated all existing documentation for OAuth 2.0 and multi-tenancy

### Changed

#### Database Models
- Added `Tenant` model with subscription plan support
- Added `tenant_id` foreign key to all domain models
- Replaced global unique constraints with tenant-scoped constraints
  - `(tenant_id, username)` unique on User
  - `(tenant_id, email)` unique on User
- OAuth models (User, OAuth2Client, OAuth2AuthorizationCode, OAuth2Token)
- Support for JSON metadata fields

#### API Endpoints
- All authentication endpoints now tenant-aware
- Protected endpoints require OAuth 2.0 access tokens
- Automatic tenant filtering on all queries
- Tenant context injected into request lifecycle

#### Application Structure
- New `api/tenant_context.py` - Tenant management utilities
- New `api/tenant_routes.py` - Tenant API endpoints
- Updated `api/oauth2.py` - OAuth 2.0 server configuration
- Updated `api/auth_routes.py` - Authentication endpoints
- Updated `api/models.py` - Database models with multi-tenancy
- Updated `api/app.py` - Application factory with OAuth and tenant middleware

### Removed
- Flask-JWT-Extended dependency (replaced with Authlib)
- Single-tenant assumptions from all models and endpoints
- Global uniqueness constraints on username and email

### Security
- Token-based authentication with automatic expiration
- Tenant-scoped authorization preventing cross-tenant access
- PKCE support for public OAuth clients
- Enhanced security headers in Nginx configuration
- Audit logging support for tenant operations

### Migration Notes
For users upgrading from v1.x:

1. **Backup your database** before upgrading
2. Install new dependencies: `docker-compose build`
3. Run database migrations:
   ```bash
   docker-compose exec api flask db migrate -m "Add OAuth 2.0 and multi-tenant support"
   docker-compose exec api flask db upgrade
   ```
4. Create your first tenant using `/tenants/register`
5. Register OAuth clients for each application
6. Update API clients to use OAuth 2.0 tokens instead of JWT
7. Add tenant identification to all API requests

See `docs/MIGRATION.md` for detailed migration instructions.

### Dependencies
- Added: `Authlib==1.2.1`
- Added: `cryptography==41.0.7`
- Removed: `Flask-JWT-Extended==4.5.3`

### Breaking Changes
- **Authentication**: JWT authentication replaced with OAuth 2.0
  - Old: `Authorization: Bearer <jwt_token>`
  - New: `Authorization: Bearer <oauth_access_token>` + tenant context
- **API Endpoints**: All endpoints now require tenant context
  - Must include `X-Tenant-Slug` or `X-Tenant-ID` header
  - Or use subdomain/domain-based tenant identification
- **User Registration**: Now requires tenant context
  - Users are created within a tenant
  - Username/email must be unique per tenant (not globally)
- **Database Schema**: New `tenant_id` columns on all tables
  - Requires database migration
  - Data migration required for existing installations

## [1.0.0] - 2025-10-01

### Added
- Initial release of Backend Framework
- Docker Compose orchestration with 6 services
- PostgreSQL 15 database with persistent storage
- Flask 3.0.0 API service with uWSGI
- Nginx reverse proxy for API and frontend
- PgAdmin for database management
- SQLAlchemy 2.0.23 ORM
- Flask-Migrate for database migrations
- Basic JWT authentication
- Comprehensive documentation
- Development environment with hot reload

---

## Version History

- **2.0.0** (2025-11-02): OAuth 2.0 + Multi-Tenant Architecture
- **1.0.0** (2025-10-01): Initial Release
