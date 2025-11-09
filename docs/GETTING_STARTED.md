# Getting Started with Backend Framework

This guide will walk you through setting up and running your first application with the Backend Framework.

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software
- **Docker Desktop** (version 20.10 or later)
  - Windows: [Download Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
  - macOS: [Download Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
  - Linux: [Install Docker Engine](https://docs.docker.com/engine/install/)
- **Git** (version 2.0 or later)
  - [Download Git](https://git-scm.com/downloads)

### System Requirements
- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk Space**: 5GB free space
- **CPU**: 2+ cores recommended
- **OS**: Windows 10/11, macOS 10.15+, or modern Linux distribution

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Darin-RVI/BackendFramework.git
cd BackendFramework
```

Or if starting fresh, you can use this structure in your existing directory.

### Step 2: Configure Environment Variables

1. Copy the example environment file:

```powershell
# Windows PowerShell
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

2. Edit the `.env` file with your preferred text editor:

```env
# PostgreSQL Configuration
POSTGRES_DB=backend_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here  # Change this!
POSTGRES_PORT=5432

# API Configuration
API_PORT=8080
FLASK_ENV=development
DEBUG=True

# Frontend Configuration
FRONTEND_PORT=8000

# PgAdmin Configuration
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin  # Change this!
PGADMIN_PORT=5050

# Application Secret Keys
SECRET_KEY=your_secret_key_here  # Generate a random string!
JWT_SECRET_KEY=your_jwt_secret_key_here  # Generate a random string!

# OAuth 2.0 Configuration
OAUTH2_ISSUER=http://localhost:8080
OAUTH2_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
OAUTH2_REFRESH_TOKEN_EXPIRES=2592000  # 30 days
OAUTH2_AUTHORIZATION_CODE_EXPIRES=600  # 10 minutes

# Development Only - Allow OAuth over HTTP (NEVER use in production!)
AUTHLIB_INSECURE_TRANSPORT=true
```

**⚠️ Security Note**: Always change the default passwords and generate secure secret keys!

To generate a secure secret key in Python:
```python
import secrets
print(secrets.token_hex(32))
```

### Step 3: Build and Start Services

Build the Docker images and start all services:

```powershell
docker-compose up --build
```

This command will:
1. Download required Docker images
2. Build custom images for API and Frontend
3. Create Docker volumes for data persistence
4. Start all services (PostgreSQL, API, Frontend, Nginx, PgAdmin)

**First-time setup may take 5-10 minutes** depending on your internet connection.

### Step 4: Verify Installation

Once all services are running, you should see output similar to:

```
backend_postgres    ... started
backend_api         ... started
backend_frontend    ... started
backend_nginx_api   ... started
backend_nginx_frontend ... started
backend_pgadmin     ... started
```

Access the following URLs to verify:

| Service | URL | Expected Result |
|---------|-----|-----------------|
| Frontend | http://localhost:8000 | Welcome page with status |
| API | http://localhost:8080 | JSON response with API info |
| API Health | http://localhost:8080/health | Healthy status message |
| PgAdmin | http://localhost:5050 | PgAdmin login page |

## Your First Authenticated API Request

With OAuth 2.0 and multi-tenant support, you need to authenticate to access protected endpoints.

### Step 1: Get an Access Token

```powershell
# Get access token using Password Grant
$response = Invoke-RestMethod -Uri "http://localhost:8080/oauth/token" `
  -Method POST `
  -Headers @{"X-Tenant-Slug"="acme"} `
  -Body @{
    grant_type = "password"
    username = "admin"
    password = "secure123"
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
    scope = "read write"
  }

$accessToken = $response.access_token
Write-Host "Access Token: $accessToken"
```

### Step 2: Call Protected Endpoint

```powershell
# Call protected API endpoint
Invoke-RestMethod -Uri "http://localhost:8080/api/protected" `
  -Headers @{
    "Authorization" = "Bearer $accessToken"
    "X-Tenant-Slug" = "acme"
  }

# Get user profile
Invoke-RestMethod -Uri "http://localhost:8080/oauth/userinfo" `
  -Headers @{
    "Authorization" = "Bearer $accessToken"
    "X-Tenant-Slug" = "acme"
  }
```

### Step 3: Refresh the Token

```powershell
# When access token expires, use refresh token
$refreshResponse = Invoke-RestMethod -Uri "http://localhost:8080/oauth/token" `
  -Method POST `
  -Headers @{"X-Tenant-Slug"="acme"} `
  -Body @{
    grant_type = "refresh_token"
    refresh_token = $response.refresh_token
    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"
  }

$newAccessToken = $refreshResponse.access_token
```

For more details, see [OAuth 2.0 Documentation](OAUTH2.md) and [Multi-Tenant Guide](MULTI_TENANT.md).

## Adding a Custom API Endpoint

Let's create a simple tenant-aware endpoint.

### Step 1: Edit the Routes File

Open `api/routes.py` and add a new route:

```python
from flask import jsonify
from datetime import datetime
from authlib.integrations.flask_oauth2 import current_token
from oauth2 import require_oauth
from tenant_context import get_current_tenant

@api_bp.route('/hello', methods=['GET'])
@require_oauth('read')
def hello():
    """Simple authenticated hello endpoint"""
    tenant = get_current_tenant()
    user = current_token.user
    
    return jsonify({
        'message': f'Hello, {user.username}!',
        'tenant': tenant.name,
        'timestamp': datetime.now().isoformat()
    }), 200
```

### Step 2: Test Your Endpoint

The changes are automatically reloaded (thanks to uWSGI auto-reload in development mode).

Test your new endpoint (requires authentication):

```powershell
# First, get an access token (see above)
$token = "YOUR_ACCESS_TOKEN"

# Call the protected endpoint
Invoke-RestMethod -Uri "http://localhost:8080/api/hello" `
  -Headers @{
    "Authorization" = "Bearer $token"
    "X-Tenant-Slug" = "acme"
  }
```

## Working with the Database

### Step 1: Access PgAdmin

1. Navigate to http://localhost:5050
2. Login with credentials from your `.env` file:
   - Email: `admin@admin.com`
   - Password: `admin` (or what you set)

### Step 2: Add Server Connection

1. Click "Add New Server"
2. In the "General" tab:
   - Name: `Backend Database`
3. In the "Connection" tab:
   - Host: `postgres` (the Docker service name)
   - Port: `5432`
   - Database: `backend_db` (or your POSTGRES_DB value)
   - Username: `postgres` (or your POSTGRES_USER value)
   - Password: Your POSTGRES_PASSWORD value
4. Click "Save"

### Step 3: Create Your First Table

You can create tables via SQL or using SQLAlchemy models.

**Using SQL (in PgAdmin):**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, email) VALUES
    ('john_doe', 'john@example.com'),
    ('jane_smith', 'jane@example.com');
```

**Using SQLAlchemy (recommended):**

Create or update `api/models.py`:
```python
from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure uniqueness per tenant
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'name', name='uq_tenant_product_name'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'created_at': self.created_at.isoformat()
        }
```

Create tables:
```powershell
docker-compose exec api flask db migrate -m "Add products table"
docker-compose exec api flask db upgrade
```

### Step 4: Create Tenant-Aware API Endpoints

Update `api/routes.py`:

```python
from flask import Blueprint, jsonify, request
from app import db
from models import Product
from oauth2 import require_oauth
from tenant_context import get_current_tenant, tenant_filter

api_bp = Blueprint('api', __name__)

@api_bp.route('/products', methods=['GET'])
@require_oauth('read')
def get_products():
    """Get all products for current tenant"""
    tenant = get_current_tenant()
    
    # Automatically filtered by tenant
    products = tenant_filter(Product.query).all()
    
    return jsonify({
        'products': [product.to_dict() for product in products],
        'tenant': tenant.name
    }), 200

@api_bp.route('/products', methods=['POST'])
@require_oauth('write')
def create_product():
    """Create a new product in current tenant"""
    tenant = get_current_tenant()
    data = request.get_json()
    
    product = Product(
        tenant_id=tenant.id,
        name=data.get('name'),
        description=data.get('description'),
        price=data.get('price', 0.0)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify(product.to_dict()), 201

@api_bp.route('/products/<int:product_id>', methods=['GET'])
@require_oauth('read')
def get_product(product_id):
    """Get a specific product (tenant-scoped)"""
    tenant = get_current_tenant()
    
    product = tenant_filter(Product.query).filter_by(id=product_id).first_or_404()
    return jsonify(product.to_dict()), 200
```

Test the endpoints:
```powershell
# Get all products for tenant
Invoke-RestMethod -Uri "http://localhost:8080/api/products" `
  -Headers @{
    "Authorization" = "Bearer $token"
    "X-Tenant-Slug" = "acme"
  }

# Create a new product
Invoke-RestMethod -Uri "http://localhost:8080/api/products" `
  -Method POST `
  -Headers @{
    "Authorization" = "Bearer $token"
    "X-Tenant-Slug" = "acme"
    "Content-Type" = "application/json"
  } `
  -Body (@{
    name = "Laptop"
    description = "High-performance laptop"
    price = 1299.99
  } | ConvertTo-Json)
```

## Customizing the Frontend

### Step 1: Modify the Homepage

Edit `frontend/templates/index.html` to customize your welcome page.

### Step 2: Add a New Page

Create `frontend/templates/about.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>About - Backend Framework</title>
</head>
<body>
    <h1>About Our Application</h1>
    <p>Built with Backend Framework</p>
    <a href="/">Back to Home</a>
</body>
</html>
```

Add the route in `frontend/app.py`:

```python
@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')
```

Visit: http://localhost:8000/about

## Common Commands

### Viewing Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Restarting Services

```powershell
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Stopping Services

```powershell
# Stop all services (data is preserved)
docker-compose down

# Stop and remove volumes (⚠️ deletes database data!)
docker-compose down -v
```

### Accessing Container Shell

```powershell
# API container
docker-compose exec api bash

# Frontend container
docker-compose exec frontend bash

# PostgreSQL container
docker-compose exec postgres bash
```

### Running Database Commands

```powershell
# Access PostgreSQL prompt
docker-compose exec postgres psql -U postgres -d backend_db

# Backup database
docker-compose exec postgres pg_dump -U postgres backend_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres -d backend_db < backup.sql
```

## Next Steps

Now that you have a working multi-tenant OAuth 2.0 setup:

1. 📖 Read the [OAuth 2.0 Guide](OAUTH2.md) for authentication details
2. � Check out [Multi-Tenant Guide](MULTI_TENANT.md) for advanced multi-tenancy features
3. 🎨 Review [API Documentation](API_DOCUMENTATION.md) to build robust APIs
4. 🗄️ Explore [Database Guide](DATABASE.md) for advanced PostgreSQL features
5. 🚀 Review [Deployment Guide](DEPLOYMENT.md) when ready for production
6. 🔧 Consult [Troubleshooting](TROUBLESHOOTING.md) if you encounter issues

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure Docker Desktop is running
4. Review the [Troubleshooting Guide](TROUBLESHOOTING.md)
5. Check that ports 5432, 5050, 8000, and 8080 are not in use

Happy coding! 🎉
