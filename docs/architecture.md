# Architecture Details

## System Architecture

The Backend Framework uses a modern, containerized microservices architecture designed for scalability, security, and maintainability. All services run in Docker containers orchestrated by Docker Compose.

## Architecture Diagram

For a visual representation of the system architecture, see the [architecture.drawio](architecture.drawio) file. You can open this file with [draw.io](https://app.diagrams.net/) or any compatible diagram viewer.

## Component Overview

### 1. PostgreSQL Database
- **Purpose**: Primary data store for all application data
- **Port**: 5432
- **Features**:
  - Persistent data storage with Docker volumes
  - Multi-tenant data isolation
  - ACID compliance
  - Full-text search capabilities
  - JSON/JSONB support for flexible schemas

### 2. API Service (Flask + uWSGI)
- **Purpose**: RESTful API backend with OAuth 2.0 authentication
- **Port**: 8080 (via Nginx)
- **Technology Stack**:
  - Python 3.11+
  - Flask web framework
  - uWSGI application server
  - Flask-SQLAlchemy ORM
  - Authlib for OAuth 2.0
  - Flask-Migrate for database migrations
- **Key Features**:
  - OAuth 2.0 token-based authentication
  - Multi-tenant request routing
  - RESTful API endpoints
  - Role-based access control (RBAC)
  - Token management and revocation

### 3. Nginx API Gateway
- **Purpose**: Reverse proxy and load balancer for API service
- **Port**: 8080 (external)
- **Features**:
  - Request routing to API service
  - SSL/TLS termination (production)
  - Response caching
  - Rate limiting
  - Load balancing (when scaled)
  - Static file serving

### 4. Frontend Service (Flask + uWSGI)
- **Purpose**: Web application UI
- **Port**: 8000 (via Nginx)
- **Technology Stack**:
  - Python 3.11+
  - Flask web framework
  - uWSGI application server
  - Jinja2 templating
- **Features**:
  - Server-side rendering
  - Template-based UI
  - Session management
  - API integration

### 5. Nginx Frontend Proxy
- **Purpose**: Reverse proxy for frontend service
- **Port**: 8000 (external)
- **Features**:
  - Request routing to frontend service
  - SSL/TLS termination (production)
  - Static asset serving
  - Compression (gzip)
  - Caching for static files

### 6. PgAdmin
- **Purpose**: Web-based PostgreSQL administration
- **Port**: 5050
- **Features**:
  - Database management interface
  - Query execution
  - Schema visualization
  - Data import/export
  - Backup management

## Data Flow

### Authentication Flow

1. **User Registration/Login** (Multi-Tenant)
   ```
   Client → Nginx → API → Database
   ```
   - Client sends credentials with tenant identifier
   - API validates tenant context
   - User authenticated within tenant scope
   - OAuth tokens issued for tenant

2. **Token-Based API Request**
   ```
   Client → Nginx → API → Database → API → Nginx → Client
   ```
   - Client includes Bearer token in Authorization header
   - Nginx forwards to API service
   - API validates token and tenant scope
   - API queries database (tenant-isolated)
   - Response returned through Nginx

3. **Frontend Page Request**
   ```
   Browser → Nginx → Frontend → API → Database
   ```
   - Browser requests page
   - Nginx routes to frontend service
   - Frontend renders template
   - May call API for data (with token)
   - HTML returned to browser

### Multi-Tenant Request Flow

```
Client Request → Tenant Identification → Context Injection → Data Isolation
```

1. **Tenant Identification**: Via subdomain, header, or path
2. **Context Injection**: Tenant context added to request
3. **Query Filtering**: All database queries scoped to tenant
4. **Response**: Data returned only for authenticated tenant

## Security Architecture

### Authentication Layers

1. **OAuth 2.0 Token Authentication**
   - Access tokens (short-lived, 1 hour default)
   - Refresh tokens (long-lived, 30 days default)
   - Token revocation support
   - Multiple grant types (password, authorization code, client credentials)

2. **Tenant-Scoped Access**
   - All tokens are tenant-specific
   - Cross-tenant access prevented at API level
   - Tenant validation on every request

3. **Role-Based Access Control (RBAC)**
   - Owner: Full tenant management
   - Admin: User and resource management
   - User: Standard resource access
   - Scope-based permission model

### Network Security

- **Internal Network**: Services communicate on Docker network
- **External Access**: Only through Nginx reverse proxies
- **SSL/TLS**: Enforced in production
- **Database**: Not directly exposed externally

## Scalability Considerations

### Horizontal Scaling

- **API Service**: Can run multiple instances behind Nginx load balancer
- **Frontend Service**: Can run multiple instances
- **Database**: Can use read replicas for scaling reads
- **Nginx**: Can distribute load across multiple API/Frontend instances

### Performance Optimization

- **Nginx Caching**: Reduces backend load for cacheable responses
- **Database Indexing**: Optimized queries with proper indexes
- **Connection Pooling**: Efficient database connection management
- **Static Asset CDN**: Offload static files (production)

## Deployment Topology

### Development Environment
```
Docker Compose → All services on single host
```

### Production Environment
```
Load Balancer → Multiple Nginx instances
              → Multiple API instances
              → Multiple Frontend instances
              → PostgreSQL (with replication)
              → Redis (for session/cache)
```

## Technology Stack Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.11+ | Application logic |
| Web Framework | Flask | API and frontend |
| Application Server | uWSGI | Production WSGI server |
| Database | PostgreSQL 15 | Data persistence |
| ORM | SQLAlchemy | Database abstraction |
| Migrations | Flask-Migrate/Alembic | Schema versioning |
| Authentication | Authlib | OAuth 2.0 implementation |
| Reverse Proxy | Nginx | Load balancing & routing |
| Containerization | Docker | Service isolation |
| Orchestration | Docker Compose | Multi-container management |
| Admin Tool | PgAdmin | Database management |

## Design Patterns

### Architectural Patterns

- **Microservices**: Separate services with clear responsibilities
- **API Gateway**: Single entry point for all API requests
- **Multi-Tenancy**: Shared infrastructure with data isolation
- **Repository Pattern**: Data access abstraction
- **Factory Pattern**: Application instance creation

### Security Patterns

- **OAuth 2.0**: Token-based authentication
- **Bearer Token**: Stateless authentication
- **RBAC**: Role-based access control
- **Data Isolation**: Tenant-scoped queries
- **Defense in Depth**: Multiple security layers

## Configuration Management

- **Environment Variables**: Sensitive configuration (passwords, keys)
- **Configuration Files**: Service-specific settings (Nginx, uWSGI)
- **Docker Compose**: Service orchestration and networking
- **Database Migrations**: Schema version control

## Monitoring and Logging

### Logging
- **Application Logs**: Flask application logging
- **Access Logs**: Nginx access and error logs
- **Database Logs**: PostgreSQL query and error logs
- **Container Logs**: Docker container output

### Monitoring Points
- Service health checks
- API response times
- Database connection pool status
- Error rates and types
- Token usage patterns

## Backup and Recovery

### Database Backups
- Regular PostgreSQL dumps
- Point-in-time recovery capability
- Volume snapshots

### Application State
- Configuration files in version control
- Container images in registry
- Database migration history

## Next Steps

- **[Getting Started](GETTING_STARTED.md)**: Set up the development environment
- **[API Documentation](API_DOCUMENTATION.md)**: Learn to build APIs
- **[Deployment Guide](DEPLOYMENT.md)**: Deploy to production
- **[Multi-Tenant Guide](MULTI_TENANT.md)**: Implement multi-tenancy

For questions or issues, refer to the [Troubleshooting Guide](TROUBLESHOOTING.md).
