# Troubleshooting Guide

This guide covers common issues you may encounter when working with the Backend Framework and their solutions.

## Table of Contents

- [Docker Issues](#docker-issues)
- [Database Issues](#database-issues)
- [API Issues](#api-issues)
- [Frontend Issues](#frontend-issues)
- [Network Issues](#network-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)

## Docker Issues

### Docker Desktop Not Starting

**Problem**: Docker Desktop fails to start or shows "Docker Desktop is starting..." indefinitely.

**Solutions**:

1. **Restart Docker Desktop**:
   ```powershell
   # Windows: Restart Docker Desktop from the system tray
   # Or restart the service
   Restart-Service docker
   ```

2. **Check Windows Features**:
   - Open "Turn Windows features on or off"
   - Ensure "Hyper-V" and "Windows Subsystem for Linux" are enabled
   - Restart your computer

3. **Check WSL 2**:
   ```powershell
   wsl --update
   wsl --set-default-version 2
   ```

4. **Reset Docker Desktop**:
   - Go to Docker Desktop Settings → Troubleshoot → Reset to factory defaults

### Containers Won't Start

**Problem**: `docker-compose up` fails or containers exit immediately.

**Diagnosis**:
```powershell
# Check container status
docker-compose ps

# View logs
docker-compose logs

# View specific service logs
docker-compose logs api
```

**Solutions**:

1. **Port Already in Use**:
   ```powershell
   # Find process using port 8080
   netstat -ano | findstr :8080
   
   # Kill the process (use PID from above command)
   taskkill /PID <PID> /F
   ```

2. **Build Issues**:
   ```powershell
   # Rebuild containers
   docker-compose build --no-cache
   docker-compose up
   ```

3. **Volume Issues**:
   ```powershell
   # Remove volumes and restart
   docker-compose down -v
   docker-compose up
   ```

### "Cannot connect to Docker daemon"

**Problem**: Error message "Cannot connect to the Docker daemon..."

**Solutions**:

1. **Ensure Docker is Running**:
   - Check if Docker Desktop is running
   - Look for Docker icon in system tray

2. **Reset Docker**:
   ```powershell
   # Windows
   Restart-Service docker
   
   # Linux
   sudo systemctl restart docker
   ```

### Out of Disk Space

**Problem**: Docker fills up disk space.

**Solutions**:

```powershell
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a

# Remove unused volumes
docker volume prune

# Remove specific stopped containers
docker container prune
```

## Database Issues

### Cannot Connect to Database

**Problem**: Application cannot connect to PostgreSQL.

**Diagnosis**:
```powershell
# Check if PostgreSQL container is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U postgres
```

**Solutions**:

1. **Wait for Database to Be Ready**:
   - PostgreSQL takes time to initialize on first startup
   - Check logs for "database system is ready to accept connections"

2. **Verify Environment Variables**:
   - Check `.env` file for correct credentials
   - Ensure `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` match

3. **Check DATABASE_URL**:
   ```python
   # In Python
   import os
   print(os.getenv('DATABASE_URL'))
   ```

4. **Network Issues**:
   ```powershell
   # Verify services are on same network
   docker network ls
   docker network inspect backend_backendnetwork
   ```

### Database Migration Errors

**Problem**: `flask db upgrade` fails.

**Solutions**:

1. **Check Migration Files**:
   ```powershell
   # List migrations
   docker-compose exec api flask db current
   docker-compose exec api flask db history
   ```

2. **Reset Migrations** (⚠️ Development only):
   ```powershell
   # Backup database first!
   docker-compose exec api rm -rf migrations/
   docker-compose exec api flask db init
   docker-compose exec api flask db migrate -m "Initial migration"
   docker-compose exec api flask db upgrade
   ```

3. **Manual Migration Fix**:
   ```powershell
   # Access database
   docker-compose exec postgres psql -U postgres -d backend_db
   
   # Check alembic_version table
   SELECT * FROM alembic_version;
   
   # Manually set version if needed
   UPDATE alembic_version SET version_num = 'revision_id';
   ```

### "Too Many Connections"

**Problem**: PostgreSQL rejects connections with "too many connections" error.

**Solutions**:

1. **Increase max_connections**:
   Create `docker/postgres/postgresql.conf`:
   ```conf
   max_connections = 200
   ```

2. **Fix Connection Pool**:
   ```python
   # api/app.py
   app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
       'pool_size': 10,
       'max_overflow': 5,
       'pool_pre_ping': True
   }
   ```

3. **Close Idle Connections**:
   ```sql
   -- Find idle connections
   SELECT * FROM pg_stat_activity WHERE state = 'idle';
   
   -- Terminate idle connections
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
   WHERE state = 'idle' AND state_change < NOW() - INTERVAL '1 hour';
   ```

### Slow Queries

**Problem**: Database queries are slow.

**Diagnosis**:
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1s
SELECT pg_reload_conf();

-- View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

**Solutions**:

1. **Add Indexes**:
   ```sql
   -- Create index
   CREATE INDEX idx_users_email ON users(email);
   CREATE INDEX idx_products_category ON products(category_id);
   ```

2. **Analyze Tables**:
   ```sql
   ANALYZE users;
   ANALYZE products;
   ```

3. **Optimize Queries**:
   ```python
   # Use eager loading
   users = User.query.options(db.joinedload(User.orders)).all()
   
   # Select only needed columns
   users = db.session.query(User.id, User.username).all()
   ```

## API Issues

### API Returns 500 Internal Server Error

**Diagnosis**:
```powershell
# Check API logs
docker-compose logs api

# Access API container
docker-compose exec api bash

# Check Python errors
docker-compose exec api python wsgi.py
```

**Solutions**:

1. **Check Application Logs**:
   - Look in `logs/api/` directory
   - Check uWSGI logs

2. **Debug Mode**:
   ```python
   # Temporarily enable debug in app.py
   app.config['DEBUG'] = True
   ```

3. **Dependency Issues**:
   ```powershell
   # Rebuild with clean install
   docker-compose build --no-cache api
   docker-compose up api
   ```

### API Endpoints Not Found (404)

**Problem**: Requests to API endpoints return 404.

**Solutions**:

1. **Check Routes**:
   ```python
   # In api/app.py
   from routes import api_bp
   app.register_blueprint(api_bp, url_prefix='/api')
   ```

2. **Verify Blueprint Registration**:
   ```powershell
   # Test routes
   docker-compose exec api python -c "from app import create_app; app = create_app(); print(app.url_map)"
   ```

3. **Check Nginx Configuration**:
   ```nginx
   # Ensure proxy_pass is correct
   location / {
       proxy_pass http://api:8080;
   }
   ```

### CORS Errors

**Problem**: Browser shows CORS policy errors.

**Solutions**:

```python
# api/app.py
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Development: Allow all origins
    CORS(app)
    
    # Production: Specify origins
    CORS(app, resources={
        r"/api/*": {
            "origins": ["https://yourdomain.com"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    return app
```

### OAuth Authentication Issues

**Problem**: OAuth 2.0 authentication not working.

**Common Issues & Solutions**:

1. **"insecure_transport" Error**:
   - **Problem**: Authlib requires HTTPS by default
   - **Solution**: For development, enable insecure transport:
   ```yaml
   # docker-compose.yml
   services:
     api:
       environment:
         AUTHLIB_INSECURE_TRANSPORT: "true"
   ```
   
   ```python
   # api/app.py - Alternative approach
   if os.getenv('FLASK_ENV') == 'development':
       os.environ['AUTHLIB_INSECURE_TRANSPORT'] = 'true'
   ```

2. **"invalid_client" Error**:
   - **Problem**: Client authentication failing at token endpoint
   - **Solution**: Use HTTP Basic Auth with client credentials:
   ```powershell
   # Correct format
   $auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${client_id}:${client_secret}"))
   $headers = @{ Authorization = "Basic $auth" }
   Invoke-RestMethod -Uri "http://localhost:8080/oauth/token" -Method POST -Headers $headers
   ```

3. **"AttributeError: check_endpoint_auth_method"**:
   - **Problem**: OAuth2Client model missing required method
   - **Solution**: Add method to models.py:
   ```python
   def check_endpoint_auth_method(self, method, endpoint):
       """Check if authentication method is supported for endpoint."""
       if endpoint == 'token':
           return self.check_token_endpoint_auth_method(method)
       return self.token_endpoint_auth_method == method
   ```

4. **"TypeError: 'expires_in' is an invalid keyword"**:
   - **Problem**: Authlib passes `expires_in` but model expects `access_token_expires_at`
   - **Solution**: Create custom save_token function in oauth2.py:
   ```python
   def save_token(token, request):
       import time
       expires_in = token.get('expires_in', 3600)
       access_token_expires_at = int(time.time()) + expires_in
       
       oauth_token = OAuth2Token(
           tenant_id=tenant_id,
           access_token=token['access_token'],
           access_token_expires_at=access_token_expires_at,
           # ... other fields
       )
       db.session.add(oauth_token)
       db.session.commit()
   ```

5. **Werkzeug Version Compatibility**:
   - **Problem**: Authlib 1.2.1 incompatible with Werkzeug 3.x
   - **Solution**: Pin compatible versions:
   ```txt
   # requirements.txt
   Flask==2.2.5
   Werkzeug==2.2.3
   Authlib==1.2.1
   ```
   
   ```txt
   # constraints.txt (new file)
   Werkzeug==2.2.3
   Flask==2.2.5
   ```
   
   ```dockerfile
   # Dockerfile - Use constraints during install
   RUN pip install --upgrade pip && \
       PIP_CONSTRAINT=constraints.txt pip install Werkzeug Flask && \
       pip install -r requirements.txt
   ```

6. **Token Validation in Protected Routes**:
   - **Problem**: `resource_protector.validate_request()` signature issues
   - **Solution**: Use Authlib's decorator directly:
   ```python
   def require_oauth(scope=None):
       """Decorator for OAuth-protected routes."""
       return current_app.resource_protector(scope)
   ```

7. **Testing OAuth Flow**:
   ```powershell
   # Step 1: Login to get session
   $loginBody = @{ username = "admin"; password = "password" } | ConvertTo-Json
   $session = @{}
   Invoke-WebRequest -Uri "http://localhost:8080/oauth/login" -Method POST `
       -Body $loginBody -ContentType "application/json" -SessionVariable session
   
   # Step 2: Get authorization code
   $authUrl = "http://localhost:8080/oauth/authorize?client_id=$client_id&redirect_uri=http://localhost:3000/callback&response_type=code&scope=profile email&state=random123"
   $response = Invoke-WebRequest -Uri $authUrl -Method POST -Body @{confirm="yes"} `
       -WebSession $session -MaximumRedirection 0 -ErrorAction SilentlyContinue
   $code = ([System.Uri]$response.Headers['Location']).Query -replace '.*code=([^&]+).*', '$1'
   
   # Step 3: Exchange code for token
   $auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${client_id}:${client_secret}"))
   $headers = @{ Authorization = "Basic $auth" }
   $tokenBody = @{ grant_type = "authorization_code"; code = $code; redirect_uri = "http://localhost:3000/callback" }
   $token = Invoke-RestMethod -Uri "http://localhost:8080/oauth/token" -Method POST `
       -Body $tokenBody -ContentType "application/x-www-form-urlencoded" -Headers $headers
   
   # Step 4: Use access token
   $authHeaders = @{ Authorization = "Bearer $($token.access_token)" }
   Invoke-RestMethod -Uri "http://localhost:8080/api/protected" -Headers $authHeaders
   ```

## Frontend Issues

### Frontend Shows Blank Page

**Diagnosis**:
```powershell
# Check frontend logs
docker-compose logs frontend

# Check browser console for errors
# Press F12 in browser and check Console tab
```

**Solutions**:

1. **Template Not Found**:
   - Verify template path in `templates/` directory
   - Check template name in route matches file name

2. **Static Files Not Loading**:
   ```python
   # Verify static folder configuration
   app = Flask(__name__, static_folder='static', static_url_path='/static')
   ```

3. **Check uWSGI**:
   ```powershell
   # Restart frontend service
   docker-compose restart frontend
   ```

### Cannot Reach API from Frontend

**Problem**: Frontend can't communicate with API.

**Solutions**:

1. **Check API_URL**:
   ```env
   # In .env
   API_URL=http://nginx_api:80  # Use service name, not localhost
   ```

2. **Network Configuration**:
   ```powershell
   # Verify both services are on same network
   docker network inspect backend_backendnetwork
   ```

3. **Test API Connection**:
   ```python
   # In frontend container
   docker-compose exec frontend python -c "import requests; print(requests.get('http://nginx_api:80/health').json())"
   ```

### Static Files Return 404

**Problem**: CSS, JS, or images not loading.

**Solutions**:

1. **Check Static Path**:
   ```html
   <!-- Use url_for for static files -->
   <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
   ```

2. **Verify Nginx Configuration**:
   ```nginx
   location /static/ {
       alias /var/www/frontend/static/;
   }
   ```

3. **Check Volume Mounts**:
   ```yaml
   # docker-compose.yml
   volumes:
     - frontend_static:/app/static
   ```

## Network Issues

### Cannot Access Services from Host

**Problem**: Cannot access `localhost:8080` or `localhost:8000`.

**Solutions**:

1. **Check Port Mappings**:
   ```powershell
   # Verify ports are mapped
   docker-compose ps
   ```

2. **Use 127.0.0.1 Instead of localhost**:
   - Try `http://127.0.0.1:8080` instead of `http://localhost:8080`

3. **Check Windows Firewall**:
   - Temporarily disable to test
   - Add exception for Docker ports

4. **Verify Port Not in Use**:
   ```powershell
   netstat -ano | findstr :8080
   ```

### Services Cannot Communicate

**Problem**: Services within Docker can't reach each other.

**Solutions**:

1. **Use Service Names**:
   ```python
   # Use 'postgres' not 'localhost'
   DATABASE_URL = 'postgresql://user:pass@postgres:5432/db'
   ```

2. **Check Docker Network**:
   ```powershell
   docker network ls
   docker network inspect backend_backendnetwork
   ```

3. **Restart Network**:
   ```powershell
   docker-compose down
   docker-compose up
   ```

## Performance Issues

### Slow API Responses

**Solutions**:

1. **Enable Query Logging**:
   ```python
   # Log slow database queries
   app.config['SQLALCHEMY_ECHO'] = True
   ```

2. **Add Caching**:
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'redis'})
   
   @cache.cached(timeout=300)
   def get_data():
       return expensive_operation()
   ```

3. **Optimize uWSGI**:
   ```ini
   # Increase workers
   processes = 4
   threads = 2
   ```

### High Memory Usage

**Solutions**:

1. **Limit Docker Resources**:
   ```yaml
   # docker-compose.yml
   services:
     api:
       deploy:
         resources:
           limits:
             memory: 512M
   ```

2. **Optimize Queries**:
   ```python
   # Use pagination
   items = Item.query.paginate(page=1, per_page=20)
   
   # Select only needed columns
   items = db.session.query(Item.id, Item.name).all()
   ```

3. **Clear Cache**:
   ```powershell
   docker system prune -a
   ```

### Database Growing Too Large

**Solutions**:

```powershell
# Vacuum database
docker-compose exec postgres psql -U postgres -d backend_db -c "VACUUM FULL;"

# Check table sizes
docker-compose exec postgres psql -U postgres -d backend_db -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## Deployment Issues

### Build Fails in CI/CD

**Solutions**:

1. **Check Docker Credentials**:
   - Verify Docker Hub or registry credentials
   - Ensure CI/CD has access to secrets

2. **Build Timeout**:
   - Increase build timeout in CI/CD settings
   - Optimize Dockerfile (use smaller base images)

3. **Cache Issues**:
   ```yaml
   # Use build cache
   - docker-compose build --pull
   ```

### SSL Certificate Errors

**Problem**: HTTPS not working or certificate errors.

**Solutions**:

1. **Check Certificate Path**:
   ```nginx
   ssl_certificate /etc/nginx/ssl/certificate.crt;
   ssl_certificate_key /etc/nginx/ssl/private.key;
   ```

2. **Renew Let's Encrypt**:
   ```bash
   certbot renew --force-renewal
   ```

3. **Test SSL Configuration**:
   ```bash
   openssl s_client -connect yourdomain.com:443
   ```

### Environment Variables Not Loading

**Problem**: Application can't read environment variables.

**Solutions**:

1. **Check .env File Location**:
   - Must be in same directory as `docker-compose.yml`

2. **Verify docker-compose Configuration**:
   ```yaml
   services:
     api:
       env_file:
         - .env
       # Or explicit environment
       environment:
         - DATABASE_URL=${DATABASE_URL}
   ```

3. **Test Inside Container**:
   ```powershell
   docker-compose exec api env | grep DATABASE_URL
   ```

## Getting Help

If you're still experiencing issues:

1. **Check Logs**:
   ```powershell
   docker-compose logs -f
   ```

2. **Verify Configuration**:
   - Double-check `.env` file
   - Verify `docker-compose.yml` syntax

3. **Test Components Individually**:
   ```powershell
   # Test database only
   docker-compose up postgres
   
   # Test API only
   docker-compose up postgres api
   ```

4. **Clean Slate**:
   ```powershell
   # Complete reset (⚠️ Deletes all data!)
   docker-compose down -v
   docker system prune -a
   docker-compose build --no-cache
   docker-compose up
   ```

5. **Check Docker Version**:
   ```powershell
   docker --version
   docker-compose --version
   ```

## Common Error Messages

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| "port is already allocated" | Port in use by another process | Kill process or change port in .env |
| "Cannot connect to Docker daemon" | Docker not running | Start Docker Desktop |
| "no space left on device" | Disk full | Run `docker system prune -a` |
| "network not found" | Network deleted/corrupted | Run `docker-compose up` to recreate |
| "permission denied" | File permissions | Check file ownership |
| "connection refused" | Service not ready | Wait for service to start, check logs |
| "exec format error" | Wrong architecture | Rebuild image for correct platform |
| "OCI runtime create failed" | Resource limits | Increase Docker resources |

## Debug Mode

Enable debug mode for more detailed error messages:

```python
# api/app.py
def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True  # Only for development!
    app.config['SQLALCHEMY_ECHO'] = True  # Log all SQL queries
    return app
```

```ini
# api/uwsgi.ini
# Enable Python autoreload
py-autoreload = 1
```

Remember to disable debug mode in production!

---

**Still need help?** Check the other documentation files or review the logs carefully for specific error messages.
