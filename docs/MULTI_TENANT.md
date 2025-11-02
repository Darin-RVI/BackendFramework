# Multi-Tenant Architecture Guide

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Tenant Identification](#tenant-identification)
- [Setup Guide](#setup-guide)
- [API Reference](#api-reference)
- [Data Isolation](#data-isolation)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)
- [Scaling Considerations](#scaling-considerations)

## Overview

This framework now supports **multi-tenancy**, allowing you to serve multiple organizations (tenants) from a single application instance while ensuring complete data isolation between tenants.

### What is Multi-Tenancy?

Multi-tenancy is an architecture where a single instance of the application serves multiple customers (tenants). Each tenant's data is isolated and invisible to other tenants.

### Key Features

- ✅ **Complete Data Isolation**: Each tenant's data is separated at the database level
- ✅ **Tenant Identification**: Multiple strategies (subdomain, domain, header, path)
- ✅ **OAuth 2.0 Integration**: Tenant-aware authentication and authorization
- ✅ **Role-Based Access**: User, Admin, and Owner roles within each tenant
- ✅ **Flexible Limits**: Configurable per-tenant limits (users, API calls, storage)
- ✅ **Subscription Plans**: Support for different pricing tiers
- ✅ **Tenant Management API**: Complete CRUD operations for tenants

## Architecture

### Database Schema

```
┌─────────────────┐
│    Tenants      │
│  - id           │
│  - name         │
│  - slug         │
│  - domain       │
│  - plan         │
│  - max_users    │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────┴────────────────────────┐
    │                             │
┌───▼─────────┐        ┌─────────▼────────┐
│   Users     │        │  OAuth2Clients   │
│ - tenant_id │        │  - tenant_id     │
│ - username  │        │  - client_id     │
│ - role      │        │  - client_secret │
└─────────────┘        └──────────────────┘
         │
         │ 1:N
         │
┌────────┴───────────┐
│  OAuth2Tokens      │
│  - tenant_id       │
│  - user_id         │
│  - access_token    │
└────────────────────┘
```

### Tenant Roles

| Role | Permissions |
|------|-------------|
| `user` | Read/write own data |
| `admin` | Manage users, view tenant stats |
| `owner` | Full control, manage settings, billing |

### Subscription Plans

| Plan | Max Users | Features |
|------|-----------|----------|
| `free` | 10 | Basic features |
| `basic` | 50 | Standard features |
| `premium` | 200 | Advanced features |
| `enterprise` | Unlimited | All features + support |

## Tenant Identification

The framework supports multiple tenant identification strategies:

### 1. Subdomain (Recommended)

```
https://acme.yourdomain.com/api/...
```

Tenant is identified by subdomain (`acme`)

### 2. Custom Domain

```
https://customdomain.com/api/...
```

Tenant registers custom domain

### 3. HTTP Header

```http
GET /api/users
X-Tenant-Slug: acme
```

Or:

```http
GET /api/users
X-Tenant-ID: 123
```

### 4. Path Parameter

```
https://api.yourdomain.com/tenants/acme/api/...
```

Tenant is in the URL path

### Priority Order

1. X-Tenant-Slug header
2. X-Tenant-ID header
3. Subdomain
4. Custom domain
5. Path parameter

## Setup Guide

### 1. Run Database Migrations

```bash
docker-compose exec api flask db migrate -m "Add multi-tenant support"
docker-compose exec api flask db upgrade
```

### 2. Create Your First Tenant

```bash
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
```

Response:

```json
{
  "message": "Tenant registered successfully",
  "tenant": {
    "id": 1,
    "name": "Acme Corporation",
    "slug": "acme",
    "domain": null,
    "plan": "free"
  },
  "admin": {
    "id": 1,
    "username": "admin",
    "email": "admin@acme.com",
    "role": "owner"
  },
  "access_info": {
    "subdomain": "acme.yourdomain.com",
    "header": "X-Tenant-Slug: acme",
    "path": "/tenants/acme/..."
  }
}
```

### 3. Register Additional Users

```bash
curl -X POST http://localhost:8080/oauth/register \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: acme" \
  -d '{
    "username": "john_doe",
    "email": "john@acme.com",
    "password": "password123"
  }'
```

### 4. Login and Get OAuth Client

```bash
# Login
curl -X POST http://localhost:8080/oauth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: acme" \
  -c cookies.txt \
  -d '{
    "username": "admin",
    "password": "secure123"
  }'

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
```

### 5. Get Access Token

```bash
curl -X POST http://localhost:8080/oauth/token \
  -H "X-Tenant-Slug: acme" \
  -d "grant_type=password" \
  -d "username=john_doe" \
  -d "password=password123" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=read write"
```

## API Reference

### Tenant Management Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/tenants/register` | POST | None | Register new tenant |
| `/tenants/list` | GET | None | List all tenants (public) |
| `/tenants/info` | GET | Tenant Context | Get current tenant info |
| `/tenants/stats` | GET | Admin | Get tenant statistics |
| `/tenants/users` | GET | Admin | List tenant users |
| `/tenants/users` | POST | Admin | Create user in tenant |
| `/tenants/users/<id>/role` | PUT | Owner | Update user role |
| `/tenants/settings` | GET | Admin | Get tenant settings |
| `/tenants/settings` | PUT | Owner | Update tenant settings |

### Modified OAuth Endpoints

All OAuth endpoints now require tenant context:

```bash
# User registration (tenant-aware)
POST /oauth/register
Header: X-Tenant-Slug: acme

# User login (tenant-aware)
POST /oauth/login
Header: X-Tenant-Slug: acme

# Client registration (tenant-aware)
POST /oauth/client/register
Header: X-Tenant-Slug: acme
```

## Data Isolation

### Database Level

All tenant-specific tables include `tenant_id`:

- `users.tenant_id`
- `oauth2_clients.tenant_id`
- `oauth2_tokens.tenant_id`
- `oauth2_codes.tenant_id`

### Query Filtering

Use the `tenant_filter` utility:

```python
from tenant_context import tenant_filter

# Automatically filters by current tenant
users = tenant_filter(User).all()
```

### Manual Filtering

```python
from tenant_context import TenantContext

tenant_id = TenantContext.get_tenant_id()
users = User.query.filter_by(tenant_id=tenant_id).all()
```

## Code Examples

### Creating a Tenant-Aware Endpoint

```python
from flask import Blueprint, jsonify
from tenant_context import require_tenant, tenant_filter
from models import User

api_bp = Blueprint('api', __name__)

@api_bp.route('/users', methods=['GET'])
@require_tenant
def get_users(tenant):
    """Get all users in current tenant"""
    users = tenant_filter(User).all()
    
    return jsonify({
        'tenant': tenant.name,
        'users': [{
            'id': u.id,
            'username': u.username,
            'role': u.role
        } for u in users]
    })
```

### Checking Tenant Limits

```python
from tenant_context import check_tenant_limits, TenantContext

@api_bp.route('/data', methods=['POST'])
@require_tenant
def create_data(tenant):
    # Check if tenant can create more resources
    within_limits, error = check_tenant_limits(tenant)
    if not within_limits:
        return jsonify({'error': error}), 403
    
    # Create resource...
    pass
```

### Getting Tenant Statistics

```python
from tenant_context import get_tenant_stats

@api_bp.route('/admin/stats', methods=['GET'])
@require_tenant
def get_stats(tenant):
    stats = get_tenant_stats(tenant)
    return jsonify(stats)
```

## Best Practices

### 1. Always Use Tenant Context

```python
# ✅ Good
from tenant_context import tenant_filter
users = tenant_filter(User).all()

# ❌ Bad - Could leak data across tenants
users = User.query.all()
```

### 2. Validate Tenant Access

```python
from tenant_context import validate_tenant_access

user = User.query.get(user_id)
tenant = TenantContext.get_current_tenant()

if not validate_tenant_access(user, tenant):
    abort(403)
```

### 3. Use Tenant-Aware Foreign Keys

```python
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Composite constraint ensures user belongs to tenant
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['tenant_id', 'user_id'],
            ['users.tenant_id', 'users.id']
        ),
    )
```

### 4. Implement Tenant-Specific Settings

```python
# Store tenant-specific config in settings JSON field
tenant.settings = {
    'branding': {
        'logo_url': 'https://...',
        'primary_color': '#007bff'
    },
    'features': {
        'api_enabled': True,
        'max_api_calls_per_day': 10000
    }
}
db.session.commit()
```

### 5. Monitor Tenant Usage

```python
import time

class APICall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    endpoint = db.Column(db.String(255))
    timestamp = db.Column(db.Integer, default=lambda: int(time.time()))

# Track usage
@app.before_request
def track_api_call():
    tenant = TenantContext.get_current_tenant()
    if tenant and request.path.startswith('/api/'):
        call = APICall(tenant_id=tenant.id, endpoint=request.path)
        db.session.add(call)
        db.session.commit()
```

## Scaling Considerations

### Database Sharding

For large-scale deployments, consider database sharding by tenant:

```python
# Different database per tenant group
TENANT_DATABASES = {
    'shard1': ['tenant1', 'tenant2'],
    'shard2': ['tenant3', 'tenant4']
}

def get_tenant_database(tenant):
    for shard, tenants in TENANT_DATABASES.items():
        if tenant.slug in tenants:
            return shard
    return 'default'
```

### Caching Strategy

Use tenant-aware cache keys:

```python
from flask_caching import Cache

cache = Cache()

def get_cached_data(key):
    tenant_id = TenantContext.get_tenant_id()
    cache_key = f'tenant:{tenant_id}:{key}'
    return cache.get(cache_key)

def set_cached_data(key, value, timeout=300):
    tenant_id = TenantContext.get_tenant_id()
    cache_key = f'tenant:{tenant_id}:{key}'
    cache.set(cache_key, value, timeout=timeout)
```

### Background Jobs

Ensure background jobs include tenant context:

```python
from celery import Task

class TenantTask(Task):
    def __call__(self, *args, **kwargs):
        tenant_id = kwargs.pop('tenant_id', None)
        if tenant_id:
            tenant = Tenant.query.get(tenant_id)
            TenantContext.set_current_tenant(tenant)
        return super().__call__(*args, **kwargs)

@celery.task(base=TenantTask)
def process_tenant_data(data, tenant_id):
    # Task automatically has tenant context
    users = tenant_filter(User).all()
    # Process...
```

### Resource Limits

Implement per-tenant rate limiting:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=lambda: f"{TenantContext.get_tenant_id()}:{get_remote_address()}"
)

@api_bp.route('/data')
@limiter.limit("100 per hour")
def get_data():
    pass
```

## Migration from Single-Tenant

If you have an existing single-tenant application:

### 1. Create Default Tenant

```python
default_tenant = Tenant(
    name="Default Organization",
    slug="default",
    plan="enterprise",
    max_users=1000
)
db.session.add(default_tenant)
db.session.commit()
```

### 2. Migrate Existing Users

```python
# Add tenant_id to all existing users
User.query.update({User.tenant_id: default_tenant.id})
db.session.commit()
```

### 3. Update Application Code

Add `@require_tenant` decorators and use `tenant_filter()` for queries.

## Security Considerations

### 1. Prevent Tenant Leakage

```python
# Always validate tenant access
@api_bp.route('/users/<int:user_id>')
def get_user(user_id):
    tenant_id = TenantContext.get_tenant_id()
    user = User.query.filter_by(
        id=user_id,
        tenant_id=tenant_id  # Critical!
    ).first_or_404()
    return jsonify(user.to_dict())
```

### 2. Secure Tenant Identification

```python
# Don't trust client-provided tenant IDs for critical operations
# Always verify from session or token
```

### 3. Audit Logging

```python
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100))
    resource = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=db.func.now())
```

### 4. Data Encryption

Encrypt sensitive tenant data at rest:

```python
from cryptography.fernet import Fernet

class Tenant(db.Model):
    # ...
    encrypted_api_key = db.Column(db.LargeBinary)
    
    def set_api_key(self, key):
        cipher = Fernet(app.config['ENCRYPTION_KEY'])
        self.encrypted_api_key = cipher.encrypt(key.encode())
    
    def get_api_key(self):
        cipher = Fernet(app.config['ENCRYPTION_KEY'])
        return cipher.decrypt(self.encrypted_api_key).decode()
```

## Testing Multi-Tenant Features

### Unit Tests

```python
import unittest
from app import create_app, db
from models import Tenant, User
from tenant_context import TenantContext, create_tenant

class MultiTenantTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test tenants
            self.tenant1, self.user1 = create_tenant(
                'Tenant 1', 'tenant1', 'admin1', 
                'admin1@test.com', 'pass123'
            )
            self.tenant2, self.user2 = create_tenant(
                'Tenant 2', 'tenant2', 'admin2',
                'admin2@test.com', 'pass123'
            )
    
    def test_data_isolation(self):
        """Test that tenant data is isolated"""
        with self.app.app_context():
            # Set tenant context to tenant1
            TenantContext.set_current_tenant(self.tenant1)
            
            from tenant_context import tenant_filter
            users = tenant_filter(User).all()
            
            # Should only see tenant1 users
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0].tenant_id, self.tenant1.id)
```

## Troubleshooting

### Tenant Not Identified

**Problem**: Getting "Tenant not identified" errors

**Solutions**:
- Ensure X-Tenant-Slug header is set
- Check subdomain configuration
- Verify tenant exists and is active

### Data Leakage Between Tenants

**Problem**: Seeing data from other tenants

**Solutions**:
- Use `tenant_filter()` for all queries
- Add `tenant_id` to WHERE clauses
- Enable query logging to debug

### Performance Issues

**Problem**: Slow queries with many tenants

**Solutions**:
- Add indexes on `tenant_id` columns
- Implement caching strategy
- Consider database sharding

## Next Steps

- See [OAUTH2.md](OAUTH2.md) for OAuth 2.0 authentication details
- See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for building tenant-aware APIs
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment considerations
