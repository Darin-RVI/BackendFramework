# Backend Framework

A comprehensive Docker-based backend framework with PostgreSQL, Nginx API Gateway, OAuth 2.0 authentication, Multi-Tenant support, and Nginx WSGI Frontend.

## Features

- 🔐 **OAuth 2.0 Authentication**: Industry-standard authentication with multiple grant types
- 🏢 **Multi-Tenant Architecture**: Serve multiple organizations with complete data isolation
- 🐘 **PostgreSQL**: Robust relational database
- 🚀 **Flask API**: RESTful API with uWSGI
- 🌐 **Nginx**: High-performance reverse proxy and load balancer
- 🐳 **Docker**: Containerized architecture for easy deployment
- 📊 **PgAdmin**: Web-based database management
- 🔄 **Token Management**: Access tokens, refresh tokens, and revocation
- 👥 **Role-Based Access**: User, Admin, and Owner roles per tenant

## Architecture

- **PostgreSQL**: Database server with persistent storage
- **API Service**: Python/Flask application with OAuth 2.0, multi-tenancy, and uWSGI
- **Nginx API Gateway**: Reverse proxy for API endpoints with caching
- **Frontend Service**: Python web application with uWSGI
- **Nginx Frontend**: Reverse proxy for frontend application
- **PgAdmin**: Web-based PostgreSQL management tool

## Multi-Tenant Support

The framework supports **multi-tenancy** out of the box:

- **Complete Data Isolation**: Each tenant's data is fully separated
- **Flexible Identification**: Subdomain, custom domain, header, or path-based
- **Tenant Management**: Full CRUD API for managing tenants and users
- **Subscription Plans**: Free, Basic, Premium, and Enterprise tiers
- **Per-Tenant Limits**: Configurable user limits and resource quotas
- **Role-Based Access**: Owner, Admin, and User roles within each tenant

See [docs/MULTI_TENANT.md](docs/MULTI_TENANT.md) for complete multi-tenant documentation.

## Authentication

This framework uses **OAuth 2.0** for authentication and authorization:

- **Multiple Grant Types**: Authorization Code, Password, Refresh Token, Client Credentials
- **PKCE Support**: Enhanced security for public clients
- **Token Revocation**: Server-side token invalidation
- **Scope-based Access Control**: Fine-grained permissions
- **OpenID Connect Compatible**: UserInfo endpoint included
- **Tenant-Aware**: All authentication is tenant-scoped

See [docs/OAUTH2.md](docs/OAUTH2.md) for complete authentication documentation.

## Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8080 | Backend API endpoints |
| Frontend | 8000 | Web frontend application |
| PostgreSQL | 5432 | Database server |
| PgAdmin | 5050 | Database management UI |

## Quick Start

### Prerequisites

- Docker Desktop installed
- Git installed

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd BackendFramework
```

2. Copy the environment file and configure:
```bash
copy .env.example .env
```

Edit `.env` with your configuration (database credentials, secret keys, etc.)

3. Build and start the services:
```bash
docker-compose up --build
```

4. Initialize the database:
```bash
# Create migration
docker-compose exec api flask db init
docker-compose exec api flask db migrate -m "Initial migration"
docker-compose exec api flask db upgrade
```

5. Create your first tenant and OAuth client:
```bash
# Register a tenant
curl -X POST http://localhost:8080/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Acme Corporation",
    "tenant_slug": "acme",
    "admin_username": "admin",
    "admin_email": "admin@acme.com",
    "admin_password": "secure123",
    "plan": "free"
  }'

# Login to tenant
curl -X POST http://localhost:8080/oauth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: acme" \
  -c cookies.txt \
  -d '{"username": "admin", "password": "secure123"}'

# Register OAuth client for tenant
curl -X POST http://localhost:8080/oauth/client/register \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: acme" \
  -b cookies.txt \
  -d '{
    "client_name": "My Application",
    "grant_types": ["password", "refresh_token"],
    "scope": "read write profile"
  }'

# Save the client_id and client_secret returned!
```

6. Access the services:
- Frontend: http://localhost:8000
- API: http://localhost:8080
- PgAdmin: http://localhost:5050

## Development

### Project Structure

```
BackendFramework/
├── api/                    # API application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── uwsgi.ini
│   ├── wsgi.py
│   ├── app.py
│   └── routes.py
├── frontend/              # Frontend application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── uwsgi.ini
│   ├── wsgi.py
│   ├── app.py
│   └── templates/
│       └── index.html
├── docker/
│   ├── nginx/
│   │   ├── api/          # Nginx config for API
│   │   │   ├── nginx.conf
│   │   │   └── conf.d/
│   │   │       └── api.conf
│   │   └── frontend/     # Nginx config for frontend
│   │       ├── nginx.conf
│   │       └── conf.d/
│   │           └── frontend.conf
│   └── postgres/
│       └── init/         # Database initialization scripts
│           └── 01-init.sql
├── docker-compose.yml
├── .env.example
└── README.md
```

### Running Commands

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f postgres
```

**Restart services:**
```bash
docker-compose restart
```

**Stop services:**
```bash
docker-compose down
```

**Stop and remove volumes (WARNING: deletes database data):**
```bash
docker-compose down -v
```

**Execute commands in containers:**
```bash
# Access API container shell
docker-compose exec api bash

# Access database
docker-compose exec postgres psql -U postgres -d backend_db

# Run database migrations (if using Flask-Migrate)
docker-compose exec api flask db upgrade
```

### Database Management

**Using PgAdmin:**
1. Access http://localhost:5050
2. Login with credentials from `.env`
3. Add new server:
   - Host: `postgres`
   - Port: `5432`
   - Database: Value from `POSTGRES_DB`
   - Username: Value from `POSTGRES_USER`
   - Password: Value from `POSTGRES_PASSWORD`

**Using command line:**
```bash
docker-compose exec postgres psql -U postgres -d backend_db
```

### API Development

The API is built with Flask and uses OAuth 2.0 for authentication. Key files:

- `api/app.py`: Application factory and OAuth configuration
- `api/routes.py`: Protected API endpoints
- `api/auth_routes.py`: OAuth 2.0 authentication endpoints
- `api/models.py`: Database models (User, OAuth2Client, OAuth2Token)
- `api/oauth2.py`: OAuth 2.0 server configuration
- `api/wsgi.py`: WSGI entry point
- `api/uwsgi.ini`: uWSGI configuration

**OAuth 2.0 Endpoints:**
- `POST /tenants/register` - Register new tenant organization
- `POST /tenants/info` - Get tenant information
- `POST /oauth/register` - Register new user (requires tenant context)
- `POST /oauth/login` - User login (requires tenant context)
- `POST /oauth/token` - Get access token (supports multiple grant types)
- `POST /oauth/revoke` - Revoke token
- `GET /oauth/userinfo` - Get user information (requires token)
- `POST /oauth/client/register` - Register OAuth client (requires tenant context)

**Protected API Endpoints:**
- `GET /api/protected` - Requires valid access token
- `GET /api/admin` - Requires 'admin' scope
- `GET /api/users/me` - Requires 'profile' scope

**Tenant Management Endpoints:**
- `GET /tenants/list` - List all tenants
- `GET /tenants/users` - List tenant users (requires admin role)
- `POST /tenants/users` - Create user in tenant (requires admin role)
- `GET /tenants/stats` - Get tenant statistics (requires admin role)

**Example: Get Access Token (Multi-Tenant)**
```bash
curl -X POST http://localhost:8080/oauth/token \
  -H "X-Tenant-Slug: acme" \
  -d "grant_type=password" \
  -d "username=admin" \
  -d "password=secure123" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=read write"
```

**Example: Call Protected Endpoint**
```bash
curl -X GET http://localhost:8080/api/protected \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Adding new protected endpoints:**
```python
@api_bp.route('/data', methods=['GET'])
@require_oauth(scope='read')
def get_data(token):
    user = User.query.get(token.user_id)
    return jsonify({'data': [...], 'user': user.username})
```

See [docs/OAUTH2.md](docs/OAUTH2.md) for complete OAuth 2.0 documentation.

### Frontend Development

The frontend uses Flask with Jinja2 templates. Key files:

- `frontend/app.py`: Flask application
- `frontend/templates/`: HTML templates
- `frontend/static/`: Static files (CSS, JS, images)

**Adding pages:**
Add new routes in `frontend/app.py` and corresponding templates in `templates/`.

## Production Deployment

For production deployment:

1. Update environment variables in `.env`:
   - Set strong passwords
   - Change `FLASK_ENV` to `production`
   - Set `DEBUG=False`
   - Generate secure secret keys
   - Update `OAUTH2_ISSUER` to your production domain

2. Remove auto-reload from uWSGI configs:
   - Delete `py-autoreload = 1` from `api/uwsgi.ini` and `frontend/uwsgi.ini`

3. Enable HTTPS:
   - Add SSL certificates
   - Update Nginx configurations for SSL
   - Consider using Let's Encrypt with Certbot

4. Adjust resource limits in `docker-compose.yml`

5. Set up proper logging and monitoring

6. Configure backups for PostgreSQL data

7. Implement token cleanup:
   - Add cron job to remove expired tokens
   - Consider Redis for token caching

8. Secure OAuth 2.0:
   - Use HTTPS for all OAuth endpoints
   - Implement rate limiting on `/oauth/token`
   - Monitor failed authentication attempts
   - Rotate client secrets periodically

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guide.

## Documentation

- **[Multi-Tenant Guide](docs/MULTI_TENANT.md)** - Complete multi-tenancy documentation
- **[OAuth 2.0 Guide](docs/OAUTH2.md)** - Complete OAuth 2.0 authentication documentation
- **[Migration Guide](docs/MIGRATION.md)** - Migrating from JWT to OAuth 2.0
- **[API Documentation](docs/API_DOCUMENTATION.md)** - API development guide
- **[Getting Started](docs/GETTING_STARTED.md)** - Detailed setup instructions
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment guide
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Architecture Diagram](docs/architecture.drawio)** - Visual architecture overview

## Troubleshooting

**Container fails to start:**
```bash
docker-compose logs <service-name>
```

**Database connection issues:**
- Verify environment variables in `.env`
- Check if PostgreSQL is healthy: `docker-compose ps`
- Ensure services are on the same network

**Port already in use:**
- Change port mappings in `.env` or `docker-compose.yml`

**Permission issues:**
```bash
# Reset permissions
docker-compose down
docker-compose up --build
```

## License

This project is open source and available under the MIT License.
