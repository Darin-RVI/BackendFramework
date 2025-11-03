# Backend Framework - Copilot Memory

This file contains important context and patterns that GitHub Copilot should remember when working with this project.

## AI Assistant Context

**Active Model**: Claude 3.5 Sonnet (Anthropic)
**Version**: Sonnet 4.5
**Last Updated**: November 3, 2025
**Primary User**: Developer working with multi-tenant SaaS architecture

### Interaction Guidelines

- Provide comprehensive, security-focused code suggestions
- Always consider multi-tenant data isolation in database operations
- Include OAuth 2.0 authentication in protected endpoints
- Suggest complete implementations with error handling and logging
- Reference existing patterns from this codebase
- Prioritize type safety with Python type hints
- Generate thorough documentation and docstrings

## Project Identity

**Name**: Backend Framework
**Type**: Multi-tenant Docker-based microservices backend architecture
**Primary Language**: Python 3.11
**Framework**: Flask
**Database**: PostgreSQL 15
**Authentication**: OAuth 2.0 with Authlib
**Authorization**: Multi-tenant with role-based access control
**Container Orchestration**: Docker Compose
**Web Server**: Nginx
**WSGI Server**: uWSGI

## Project Purpose

A production-ready, scalable, multi-tenant backend framework for building:
- Multi-tenant SaaS applications
- OAuth 2.0 protected REST APIs
- Full-stack web applications with tenant isolation
- Microservices architectures with shared authentication
- API-first applications with fine-grained permissions
- Enterprise-grade platforms with role-based access control

## Architecture Patterns

### Service Architecture

- **Separation of Concerns**: API and Frontend are separate services
- **Reverse Proxy Pattern**: Nginx handles all external traffic
- **Container Isolation**: Each service runs in its own container
- **Shared Database**: PostgreSQL accessed by API service only
- **Frontend-API Communication**: Frontend calls API via internal Docker network
- **Multi-Tenant Architecture**: Single application instance serves multiple tenants
- **OAuth 2.0 Authentication**: Token-based authentication with multiple grant types
- **Role-Based Authorization**: User, Admin, Owner roles within each tenant

### Multi-Tenant Patterns

#### Tenant Context Management

```python
from tenant_context import TenantContext, require_tenant

@api_bp.route('/data', methods=['GET'])
@require_tenant
def get_data(tenant):
    # Automatically has tenant context
    data = tenant_filter(MyModel).all()
    return jsonify([item.to_dict() for item in data])
```

#### Tenant Identification Strategies

```python
# Multiple strategies supported:
# 1. Header: X-Tenant-Slug: acme
# 2. Subdomain: acme.yourdomain.com
# 3. Custom domain: customdomain.com
# 4. Path parameter: /tenants/acme/...

tenant = TenantContext.identify_tenant()
```

### OAuth 2.0 Patterns

#### Protected Endpoint Pattern

```python
from oauth2 import require_oauth

@api_bp.route('/protected', methods=['GET'])
@require_oauth(scope='read')
def protected_endpoint(token):
    user = User.query.get(token.user_id)
    return jsonify(user.to_dict())
```

#### Grant Type Usage

```python
# Authorization Code Grant (recommended for web apps)
# Password Grant (for trusted first-party apps)
# Client Credentials Grant (for server-to-server)
# Refresh Token Grant (for token renewal)
```

### Code Patterns

#### Flask Application Factory

```python
def create_app():
    app = Flask(__name__)
    # Configure app
    # Initialize extensions
    # Register blueprints
    # Configure OAuth 2.0
    return app
```

#### Blueprint Pattern for Routes

```python
api_bp = Blueprint('api', __name__)

@api_bp.route('/endpoint', methods=['GET'])
def endpoint():
    return jsonify(data), 200
```

#### SQLAlchemy Model Pattern with Multi-Tenancy

```python
class Model(db.Model):
    __tablename__ = 'table_name'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    
    def to_dict(self):
        return {'id': self.id, 'tenant_id': self.tenant_id}
```

#### API Client Pattern (Frontend)

```python
class APIClient:
    def __init__(self, tenant_slug=None):
        self.base_url = os.getenv('API_URL')
        self.tenant_slug = tenant_slug
    
    def _request(self, method, endpoint, **kwargs):
        headers = kwargs.get('headers', {})
        if self.tenant_slug:
            headers['X-Tenant-Slug'] = self.tenant_slug
        kwargs['headers'] = headers
        # Request logic
        pass
```

## Environment Variables

### Required Variables

- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT signing key (if using JWT)
- `DATABASE_URL`: Full PostgreSQL connection string
- `API_URL`: API service URL for frontend
- `FLASK_ENV`: Environment (development/production)
- `DEBUG`: Debug mode flag

### OAuth 2.0 Variables

- `OAUTH2_ISSUER`: OAuth 2.0 issuer URL
- `OAUTH2_ACCESS_TOKEN_EXPIRES`: Access token lifetime (seconds)
- `OAUTH2_REFRESH_TOKEN_EXPIRES`: Refresh token lifetime (seconds)
- `OAUTH2_AUTHORIZATION_CODE_EXPIRES`: Authorization code lifetime (seconds)

### Multi-Tenant Variables

- `DEFAULT_TENANT_PLAN`: Default subscription plan for new tenants
- `MAX_TENANTS`: Maximum number of tenants (optional)
- `TENANT_ISOLATION_MODE`: Database isolation strategy

### Service Ports

- PostgreSQL: 5432 (internal), configurable external
- API: 8080 (external), 8080 (internal)
- Frontend: 8000 (external), 8000 (internal)
- PgAdmin: 5050 (external)
- Redis: 6379 (internal), optional external

## Docker Service Names

When services communicate internally, use these names:
- `postgres` - PostgreSQL database
- `api` - API service
- `frontend` - Frontend service
- `nginx_api` - API Nginx proxy
- `nginx_frontend` - Frontend Nginx proxy
- `pgadmin` - PgAdmin service
- `redis` - Redis cache (if enabled)

## Common Patterns and Conventions

### File Naming
- Python files: `snake_case.py`
- Templates: `snake_case.html`
- CSS/JS: `kebab-case.css`, `kebab-case.js`
- Markdown docs: `UPPERCASE.md`

### Code Style
- **Python**: Follow PEP 8
- **Line Length**: 100 characters for Python
- **Indentation**: 4 spaces for Python, 2 for HTML/CSS/JS
- **Imports**: Standard library → Third party → Local
- **Docstrings**: Google style for functions/classes

### API Response Format
```json
{
    "success": true/false,
    "data": {...},
    "error": "message"
}
```

### HTTP Status Codes
- 200: Successful GET, PUT, PATCH
- 201: Successful POST (created)
- 204: Successful DELETE
- 400: Bad request (validation error)
- 401: Unauthorized (not authenticated)
- 403: Forbidden (not authorized)
- 404: Not found
- 500: Internal server error

## Database Conventions

### Table Naming
- Lowercase, plural: `users`, `products`, `categories`
- Use underscores for multi-word: `order_items`

### Column Naming
- Snake_case: `user_id`, `created_at`, `is_active`
- Primary keys: `id`
- Foreign keys: `{table_singular}_id`
- Timestamps: `created_at`, `updated_at`, `deleted_at`

### Relationships
- One-to-Many: Use `db.relationship()` with `backref`
- Many-to-Many: Use association table
- Cascade: Specify cascade behavior explicitly

## Error Handling Strategy

### API Errors
- Always return JSON responses
- Include error message and status code
- Log errors for debugging
- Use try-except blocks for database operations
- Rollback database session on errors

### Frontend Errors
- Display user-friendly messages
- Flash messages for form submissions
- Graceful degradation when API unavailable
- Loading states for async operations

## Security Practices

### Implemented

- Environment-based configuration
- CORS configuration
- Security headers in Nginx
- Non-root container users
- Network isolation
- Input validation
- Prepared statements (SQLAlchemy ORM)
- OAuth 2.0 authentication with multiple grant types
- Multi-tenant data isolation at database level
- Role-based access control (User, Admin, Owner)
- Token-based authentication with proper expiration
- PKCE support for public OAuth clients

### Multi-Tenant Security

- Tenant isolation at database level (tenant_id foreign keys)
- Tenant context validation in all operations
- Cross-tenant data access prevention
- Tenant-specific OAuth clients and tokens
- Role-based permissions within tenant boundaries
- Audit logging with tenant context

### OAuth 2.0 Security

- Short-lived access tokens (1 hour default)
- Refresh token rotation on each use
- Secure client credential storage
- PKCE for public clients (mobile, SPA)
- Token revocation on logout
- Scope-based access control
- Rate limiting on token endpoints

### To Implement in Production

- HTTPS/SSL enforcement
- Secrets management (HashiCorp Vault, AWS Secrets Manager)
- Advanced rate limiting per tenant
- CSRF protection for web endpoints
- SQL injection prevention (already handled by SQLAlchemy ORM)
- XSS protection with proper output encoding
- Content Security Policy (CSP) headers
- Database encryption at rest
- Audit logging with tamper protection

## Testing Strategy

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Use pytest fixtures

### Integration Tests
- Test API endpoints
- Test database operations
- Use test database

### Test Location
- API tests: `api/tests/`
- Frontend tests: `frontend/tests/`

## Common Development Tasks

### Adding a New API Endpoint

1. Define route in `api/routes.py` or appropriate blueprint
2. Create/update model in `api/models.py` if needed (include tenant_id)
3. Add business logic in `api/services/` if complex
4. Add tenant context validation with `@require_tenant`
5. Add OAuth 2.0 protection with `@require_oauth(scope='...')`
6. Test endpoint manually or with tests
7. Document in API_DOCUMENTATION.md

### Adding a New Multi-Tenant Feature

1. Add tenant_id to relevant database models
2. Create database migration for new columns/tables
3. Use `tenant_filter()` for all data queries
4. Add tenant context validation in endpoints
5. Test with multiple tenants for data isolation
6. Update tenant management endpoints if needed

### Setting Up OAuth 2.0 Client

1. Login to create session: `POST /oauth/login`
2. Register OAuth client: `POST /oauth/client/register`
3. Store client credentials securely
4. Implement appropriate grant flow in your application
5. Test token generation and API access

### Adding a New Frontend Page

1. Create route in `frontend/app.py`
2. Create template in `frontend/templates/`
3. Add styles in `frontend/static/css/`
4. Add JavaScript if needed in `frontend/static/js/`
5. Add tenant context handling if needed
6. Update navigation in base template

### Database Migration

1. Create/update model in `api/models.py`
2. Generate migration: `flask db migrate -m "description"`
3. Review migration file for tenant isolation
4. Apply: `flask db upgrade`
5. Test changes with multiple tenants

### Creating a New Tenant

1. Use tenant registration API: `POST /tenants/register`
2. Or use tenant context helper: `create_tenant()`
3. Verify tenant isolation works correctly
4. Set up initial OAuth clients if needed
5. Configure tenant-specific settings

## Performance Optimization

### Database
- Add indexes to frequently queried columns
- Use eager loading for relationships
- Implement pagination for large datasets
- Use database connection pooling (configured)

### API
- Enable caching for static data
- Use Redis for session storage
- Optimize query complexity
- Implement response compression (Nginx)

### Frontend
- Minimize API calls
- Cache API responses
- Lazy load images
- Minify CSS/JS in production

## Logging Standards

### Log Levels
- DEBUG: Detailed development info
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### What to Log
- API requests/responses (in development)
- Database errors
- Authentication failures
- Validation errors
- Performance metrics
- Security events

### Where Logs Are Stored
- Development: Container stdout/stderr
- Production: `logs/` directory with rotation

## Deployment Checklist

Before deploying to production:
- [ ] Set `DEBUG=False`
- [ ] Set `FLASK_ENV=production`
- [ ] Use strong passwords
- [ ] Generate secure secret keys
- [ ] Configure SSL/TLS
- [ ] Set up database backups
- [ ] Configure logging to files
- [ ] Remove auto-reload from uWSGI
- [ ] Set resource limits
- [ ] Configure monitoring
- [ ] Test all endpoints
- [ ] Review security headers
- [ ] Update dependencies
- [ ] Document deployment process

## Common Commands

### Docker

```powershell
# Start services
docker-compose up

# Rebuild and start
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service]

# Access container shell
docker-compose exec [service] bash

# Clean up
docker-compose down -v
docker system prune -a
```

### Database

```powershell
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d backend_db

# Run migrations
docker-compose exec api flask db upgrade

# Create migration
docker-compose exec api flask db migrate -m "message"

# Backup
docker-compose exec postgres pg_dump -U postgres backend_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres backend_db < backup.sql
```

### Multi-Tenant Operations

```powershell
# Create a new tenant via API
curl -X POST http://localhost:8080/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Acme Corp",
    "tenant_slug": "acme",
    "admin_username": "admin",
    "admin_email": "admin@acme.com",
    "admin_password": "secure123"
  }'

# Get tenant info
curl -H "X-Tenant-Slug: acme" http://localhost:8080/tenants/info

# List all tenants
curl http://localhost:8080/tenants/list
```

### OAuth 2.0 Operations

```powershell
# Register OAuth client
curl -X POST http://localhost:8080/oauth/client/register \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: acme" \
  -b cookies.txt \
  -d '{
    "client_name": "My App",
    "grant_types": ["password", "refresh_token"],
    "scope": "read write profile"
  }'

# Get access token (password grant)
curl -X POST http://localhost:8080/oauth/token \
  -H "X-Tenant-Slug: acme" \
  -d "grant_type=password" \
  -d "username=user" \
  -d "password=pass" \
  -d "client_id=CLIENT_ID" \
  -d "client_secret=CLIENT_SECRET"

# Test protected endpoint
curl -H "Authorization: Bearer ACCESS_TOKEN" \
     -H "X-Tenant-Slug: acme" \
     http://localhost:8080/api/protected
```

### Python Shell

```powershell
# API Python shell
docker-compose exec api python

# Frontend Python shell
docker-compose exec frontend python

# Flask shell (with app context)
docker-compose exec api flask shell
```

## Directory Purpose

- **api/**: Backend API service code
- **frontend/**: Frontend web application code
- **docker/**: Docker and Nginx configurations
- **docs/**: Comprehensive documentation
- **scripts/**: Utility scripts (backup, deploy, etc.)
- **logs/**: Application logs (gitignored)
- **backups/**: Database backups (gitignored)
- **.copilot/**: Copilot configuration and memory

## Dependencies Management

### When Adding Dependencies
1. Add to appropriate `requirements.txt`
2. Rebuild Docker image
3. Document if it's a major dependency
4. Pin versions for reproducibility

### When Updating Dependencies
1. Test in development first
2. Check for breaking changes
3. Update requirements.txt
4. Rebuild images
5. Test thoroughly

## Code Review Guidelines

When reviewing or writing code:
- ✅ Follow established patterns
- ✅ Add error handling
- ✅ Include docstrings
- ✅ Validate user input
- ✅ Use type hints where appropriate
- ✅ Write clear variable names
- ✅ Keep functions small and focused
- ✅ Add comments for complex logic
- ✅ Test edge cases
- ✅ Check for security issues

## Known Limitations

- Frontend and API must be on same Docker network
- PostgreSQL port should not be exposed in production
- Static files served by Nginx for performance
- Session storage is in-memory (use Redis for production)
- No built-in rate limiting (implement in production)

## Future Enhancements

Potential improvements to consider:
- Kubernetes deployment configurations
- GraphQL API option
- WebSocket support
- Celery for background tasks
- ElasticSearch for search
- Prometheus/Grafana for monitoring
- CI/CD pipeline configurations
- Multi-stage Docker builds
- Health check endpoints with detailed status

## Important Notes for Copilot

When generating code for this project:

1. **Always use service names** in Docker network (not localhost)
2. **Use environment variables** for configuration
3. **Follow Flask application factory pattern**
4. **Use SQLAlchemy ORM** for database operations
5. **Return JSON** from API endpoints
6. **Use Jinja2** for frontend templates
7. **Include error handling** in all routes
8. **Use try-except** for database operations
9. **Log errors** appropriately
10. **Follow existing code style** and patterns

### Multi-Tenant Specific

11. **Always include tenant_id** in database models
12. **Use tenant_filter()** for all data queries
13. **Add @require_tenant decorator** to tenant-aware endpoints
14. **Validate tenant access** with validate_tenant_access()
15. **Use TenantContext** for tenant identification
16. **Never query across tenants** without explicit permission
17. **Include tenant context** in all logging and audit trails

### OAuth 2.0 Specific

18. **Use @require_oauth() decorator** for protected endpoints
19. **Specify appropriate scopes** for API endpoints
20. **Include tenant context** in OAuth operations
21. **Store client secrets securely** (environment variables)
22. **Implement proper token validation** and error handling
23. **Use appropriate grant types** for different client types
24. **Include PKCE support** for public clients
25. **Log authentication events** for security auditing

## Version Information

- Python: 3.11
- Flask: 3.0.0
- PostgreSQL: 15 (Alpine)
- SQLAlchemy: 2.0.23
- uWSGI: 2.0.23
- Nginx: Alpine (latest)
- Docker Compose: 3.8

This memory file helps Copilot understand the project context and generate code that follows established patterns and best practices.
