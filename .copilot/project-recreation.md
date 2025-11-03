# Backend Framework - Project Recreation Prompt

You are tasked with recreating the Backend Framework project from scratch. This is a comprehensive Docker-based backend architecture for modern web applications with **multi-tenant support** and **OAuth 2.0 authentication**.

## AI Assistant Information

This project was developed with assistance from **Claude 3.5 Sonnet (Sonnet 4.5)** by Anthropic. The AI model provides:
- Advanced code generation with security-first approach
- Multi-tenant architecture expertise
- OAuth 2.0 implementation guidance
- Comprehensive documentation generation
- Pattern recognition and consistency maintenance

When recreating this project, leverage the AI's capabilities for:
- Generating boilerplate code with proper security considerations
- Implementing complex multi-tenant database relationships
- Creating OAuth 2.0 flows with best practices
- Writing comprehensive tests and documentation
- Maintaining consistent code patterns across the codebase

## Project Overview

Create a production-ready, multi-tenant backend framework using:
- **PostgreSQL 15** for database with multi-tenant data isolation
- **Python 3.11** with Flask for API and Frontend services
- **OAuth 2.0** authentication with Authlib (Authorization Code, Password, Client Credentials, Refresh Token grants)
- **Multi-Tenant Architecture** with tenant identification via subdomain, domain, headers, or path
- **Role-Based Access Control** (User, Admin, Owner roles within tenants)
- **uWSGI** for WSGI application servers
- **Nginx** as reverse proxy for both API and frontend
- **Docker Compose** for orchestration
- **PgAdmin** for database management

## Core Architecture

The project follows a microservices architecture with these components:

1. **Database Layer**: PostgreSQL with health checks, persistent storage, and multi-tenant data isolation
2. **API Service**: Python/Flask REST API with uWSGI, OAuth 2.0 authentication, and multi-tenant support
3. **Frontend Service**: Python/Flask web application with uWSGI and tenant-aware routing
4. **API Gateway**: Nginx reverse proxy for API endpoints with tenant routing
5. **Frontend Proxy**: Nginx reverse proxy for frontend application
6. **Management**: PgAdmin for database administration

### Multi-Tenant Features

- **Tenant Identification**: Multiple strategies (subdomain, custom domain, headers, path parameters)
- **Data Isolation**: All tenant data separated by tenant_id foreign keys
- **Role-Based Access**: User, Admin, Owner roles within each tenant
- **Tenant Management**: Complete CRUD API for tenant operations
- **Subscription Plans**: Support for different pricing tiers (free, basic, premium, enterprise)
- **Usage Limits**: Configurable per-tenant limits (users, API calls, storage)

### OAuth 2.0 Features

- **Multiple Grant Types**: Authorization Code, Password, Client Credentials, Refresh Token
- **PKCE Support**: Enhanced security for public clients (mobile apps, SPAs)
- **Scope-Based Access**: Fine-grained permissions (read, write, profile, admin)
- **Token Management**: Secure token storage, expiration, and revocation
- **Client Registration**: Dynamic OAuth client registration
- **Multi-Tenant Integration**: OAuth clients and tokens isolated per tenant

## Directory Structure

```
BackendFramework/
├── .copilot/                      # Copilot configuration and prompts
│   ├── project-recreation.md
│   └── memory.md
├── docs/                          # Comprehensive documentation
│   ├── README.md
│   ├── OVERVIEW.md
│   ├── GETTING_STARTED.md
│   ├── API_DOCUMENTATION.md
│   ├── FRONTEND_DEVELOPMENT.md
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
├── api/                           # API service
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── requirements.txt
│   ├── uwsgi.ini
│   ├── uwsgi.prod.ini
│   ├── wsgi.py
│   ├── app.py
│   ├── routes.py
│   ├── models.py
│   ├── services/
│   ├── middleware/
│   ├── utils/
│   └── tests/
├── frontend/                      # Frontend service
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── requirements.txt
│   ├── uwsgi.ini
│   ├── uwsgi.prod.ini
│   ├── wsgi.py
│   ├── app.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── partials/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── utils/
├── docker/                        # Docker configurations
│   ├── nginx/
│   │   ├── api/
│   │   │   ├── nginx.conf
│   │   │   ├── nginx.prod.conf
│   │   │   └── conf.d/
│   │   │       ├── api.conf
│   │   │       └── api.prod.conf
│   │   └── frontend/
│   │       ├── nginx.conf
│   │       ├── nginx.prod.conf
│   │       └── conf.d/
│   │           ├── frontend.conf
│   │           └── frontend.prod.conf
│   └── postgres/
│       ├── init/
│       │   └── 01-init.sql
│       └── postgresql.conf
├── scripts/                       # Utility scripts
│   └── backup_db.sh
├── logs/                         # Application logs (gitignored)
├── backups/                      # Database backups (gitignored)
├── docker-compose.yml            # Development orchestration
├── docker-compose.prod.yml       # Production orchestration
├── .env.example                  # Environment template
├── .env                          # Environment variables (gitignored)
├── .gitignore
├── .dockerignore
├── Makefile                      # Helper commands
└── README.md                     # Main README
```

## Step-by-Step Recreation Instructions

### Phase 1: Core Infrastructure Files

1. **Create docker-compose.yml** with services:
   - postgres (PostgreSQL 15 Alpine)
   - api (Python/Flask with uWSGI)
   - frontend (Python/Flask with uWSGI)
   - nginx_api (Nginx for API)
   - nginx_frontend (Nginx for frontend)
   - pgadmin (Database management)
   - redis (Optional caching layer)

2. **Create .env.example** with:
   - PostgreSQL credentials
   - API and frontend ports
   - Secret keys
   - PgAdmin credentials
   - Environment flags (DEBUG, FLASK_ENV)

3. **Create .gitignore** excluding:
   - .env files
   - Python cache (__pycache__, *.pyc)
   - Logs
   - Virtual environments
   - Database files
   - Static/media files

### Phase 2: API Service

1. **Create api/Dockerfile**:
   - Base: python:3.11-slim
   - Install system deps (gcc, postgresql-client, libpq-dev)
   - Copy requirements.txt and install
   - Copy application code
   - Create directories for static/media/logs
   - Run as non-root user
   - Expose port 8080
   - CMD: uwsgi --ini uwsgi.ini

3. **Create api/requirements.txt**:
   - Flask (3.0.0)
   - Flask-CORS
   - Flask-SQLAlchemy
   - Flask-Migrate
   - Authlib (OAuth 2.0 library)
   - psycopg2-binary
   - SQLAlchemy
   - uWSGI
   - python-dotenv
   - requests
   - cryptography (for secure token generation)

3. **Create api/uwsgi.ini**:
   - Master process with 4 workers, 2 threads
   - HTTP socket on 0.0.0.0:8080
   - Harakiri timeout, max requests
   - Static file mappings
   - Logging configuration
   - Auto-reload for development

4. **Create api/wsgi.py**:
   - Load environment variables
   - Import create_app from app.py
   - Create application instance
   - Main block for direct execution

5. **Create api/app.py**:
   - Flask application factory pattern
   - SQLAlchemy configuration
   - Flask-Migrate setup
   - CORS configuration
   - Blueprint registration
   - Health check endpoint
   - Error handlers (404, 500, etc.)
   - Logging setup

6. **Create api/routes.py**:
   - Flask Blueprint for API routes
   - CRUD endpoints examples
   - /ping endpoint
   - /status endpoint
   - Error handling

7. **Create api/models.py**:
   - SQLAlchemy models with multi-tenant support
   - Tenant model (base tenant entity)
   - User model (with tenant_id foreign key)
   - OAuth2Client model (tenant-aware OAuth clients)
   - OAuth2Token model (access/refresh tokens)
   - OAuth2AuthorizationCode model (authorization codes)
   - Relationships examples
   - to_dict() methods
   - Proper indexes for tenant isolation

8. **Create api/tenant_context.py**:
   - TenantContext class for tenant identification
   - Tenant identification strategies (subdomain, domain, header, path)
   - require_tenant decorator
   - tenant_filter utility function
   - Helper functions for tenant management

9. **Create api/tenant_routes.py**:
   - Tenant registration endpoint
   - Tenant management endpoints
   - User management within tenants
   - Tenant statistics and settings

10. **Create api/oauth2.py**:
    - OAuth 2.0 server configuration with Authlib
    - Grant type implementations (Authorization Code, Password, etc.)
    - Token validation and introspection
    - Client credential management

11. **Create api/auth_routes.py**:
    - OAuth 2.0 endpoints (/authorize, /token, /revoke, etc.)
    - User registration and login
    - Client registration and management
    - Token introspection and user info endpoints

### Phase 3: Frontend Service

1. **Create frontend/Dockerfile**:
   - Base: python:3.11-slim
   - Install system dependencies
   - Copy requirements and install
   - Copy application code
   - Create static directories
   - Expose port 8000
   - CMD: uwsgi --ini uwsgi.ini

2. **Create frontend/requirements.txt**:
   - Flask
   - Flask-CORS
   - Jinja2
   - uWSGI
   - python-dotenv
   - requests

3. **Create frontend/uwsgi.ini**:
   - Similar to API but on port 8000
   - Static file mappings
   - Auto-reload for development

4. **Create frontend/wsgi.py**:
   - Load environment
   - Import create_app
   - Create app instance

5. **Create frontend/app.py**:
   - Flask application factory
   - Context processors
   - Route definitions
   - API client integration
   - Health check endpoint

6. **Create frontend/templates/base.html**:
   - HTML5 boilerplate
   - Header, main, footer structure
   - Jinja2 blocks for content
   - Flash message handling
   - Static file loading with url_for

7. **Create frontend/templates/index.html**:
   - Extends base.html
   - Welcome page with status check
   - Modern responsive design

8. **Create frontend/static/css/style.css**:
   - Modern CSS with CSS variables
   - Responsive grid layouts
   - Component styles (cards, buttons, forms, tables)
   - Mobile-first approach

9. **Create frontend/static/js/app.js**:
   - API client class
   - DOM ready handlers
   - Form validation
   - Flash message auto-hide
   - Utility functions

### Phase 4: Nginx Configuration

1. **Create docker/nginx/api/nginx.conf**:
   - Worker processes auto
   - Events block with epoll
   - HTTP block with gzip, logging, mime types

2. **Create docker/nginx/api/conf.d/api.conf**:
   - Upstream definition for api:8080
   - Server block on port 80
   - Proxy settings for API
   - Static file serving
   - Security headers
   - Caching configuration

3. **Create docker/nginx/frontend/nginx.conf**:
   - Similar structure to API nginx.conf

4. **Create docker/nginx/frontend/conf.d/frontend.conf**:
   - Upstream for frontend:8000
   - Proxy configuration
   - Static file serving

### Phase 5: Database Configuration

1. **Create docker/postgres/init/01-init.sql**:
   - Enable extensions (uuid-ossp, pg_trgm)
   - Sample table creation (commented)
   - Initial data (commented)

### Phase 6: Documentation

Create comprehensive markdown documentation in docs/:

1. **README.md** - Documentation index
2. **OVERVIEW.md** - Architecture and features
3. **GETTING_STARTED.md** - Setup guide
4. **API_DOCUMENTATION.md** - API development guide
5. **FRONTEND_DEVELOPMENT.md** - Frontend guide
6. **DATABASE.md** - Database operations
7. **DEPLOYMENT.md** - Production deployment
8. **TROUBLESHOOTING.md** - Common issues

### Phase 7: Additional Files

1. **Create README.md** (main):
   - Project introduction
   - Quick start instructions
   - Architecture diagram (text)
   - Service URLs table
   - Common commands
   - Links to documentation

2. **Create Makefile**:
   - Helper commands for common operations
   - build, up, down, restart, logs
   - shell access commands
   - Database commands

3. **Create .dockerignore**:
   - Exclude git, docs, tests
   - Python cache files
   - Logs and temporary files

## Key Configuration Details

### Environment Variables
```env
POSTGRES_DB=backend_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_PORT=5432
API_PORT=8080
FRONTEND_PORT=8000
FLASK_ENV=development
DEBUG=True
SECRET_KEY=generate_secure_key
JWT_SECRET_KEY=generate_secure_key
```

### Docker Network
- All services on bridge network: `backend_network`
- Services communicate via service names (postgres, api, frontend)

### Volumes
- postgres_data: Database persistence
- api_static, api_media: API assets
- frontend_static: Frontend assets
- nginx logs: Nginx access/error logs

### Ports Exposed
- 5432: PostgreSQL
- 5050: PgAdmin
- 8080: API (via Nginx)
- 8000: Frontend (via Nginx)

## Production Considerations

For production deployment (docker-compose.prod.yml):

1. **Remove auto-reload** from uWSGI configs
2. **Set DEBUG=False**
3. **Use strong passwords** and secret keys
4. **Add SSL/TLS** certificates
5. **Configure resource limits**
6. **Set up logging** to files
7. **Add Redis** for caching/sessions
8. **Increase worker counts**
9. **Don't expose** PostgreSQL port
10. **Use secrets management**

## Testing the Setup

After recreation, verify with:

```powershell
# Build and start
docker-compose up --build

# Check services
docker-compose ps

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8000/health

# View logs
docker-compose logs -f

# Access database
docker-compose exec postgres psql -U postgres -d backend_db
```

## Success Criteria

The project is successfully recreated when:

✅ All services start without errors
✅ API health check returns 200
✅ Frontend loads in browser
✅ Database is accessible
✅ Nginx proxies requests correctly
✅ Static files load properly
✅ PgAdmin can connect to database
✅ Logs are viewable
✅ All documentation is complete

## Additional Notes

- Use Alpine-based images for smaller size
- Implement health checks for all services
- Follow Flask application factory pattern
- Use SQLAlchemy ORM for database operations
- Implement proper error handling
- Add request validation
- Use environment-based configuration
- Follow security best practices
- Implement comprehensive logging
- Write clear, well-documented code
- Include code comments where needed
- Follow PEP 8 for Python code
- Use semantic versioning
- Keep dependencies updated

This prompt provides everything needed to recreate the Backend Framework project from scratch while maintaining the same architecture, structure, and functionality.
