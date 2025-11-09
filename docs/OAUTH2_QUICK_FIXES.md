# OAuth 2.0 Quick Fix Reference

This document provides quick copy-paste solutions for common OAuth 2.0 issues encountered during development.

## Issue 1: Authlib Requires HTTPS in Development

**Error:**
```json
{"error": "insecure_transport: OAuth 2 MUST utilize https."}
```

**Quick Fix - Option 1 (docker-compose.yml):**
```yaml
services:
  api:
    environment:
      AUTHLIB_INSECURE_TRANSPORT: "true"
```

**Quick Fix - Option 2 (api/app.py):**
```python
import os

def create_app():
    app = Flask(__name__)
    
    # Allow HTTP for development only
    if os.getenv('FLASK_ENV') == 'development':
        os.environ['AUTHLIB_INSECURE_TRANSPORT'] = 'true'
    
    # ... rest of configuration
```

**⚠️ Warning:** NEVER use this in production! Always use HTTPS in production.

## Issue 2: Werkzeug Version Incompatibility

**Error:**
```
AttributeError: module 'werkzeug' has no attribute '__version__'
```

**Root Cause:** Authlib 1.2.1 is incompatible with Werkzeug 3.x

**Quick Fix:**

1. **Update requirements.txt:**
```txt
Flask==2.2.5
Werkzeug==2.2.3
Authlib==1.2.1
```

2. **Create constraints.txt:**
```txt
Werkzeug==2.2.3
Flask==2.2.5
```

3. **Update Dockerfile:**
```dockerfile
COPY requirements.txt constraints.txt ./

RUN pip install --upgrade pip && \
    PIP_CONSTRAINT=constraints.txt pip install Werkzeug Flask && \
    pip install -r requirements.txt
```

## Issue 3: Missing check_endpoint_auth_method

**Error:**
```
AttributeError: 'OAuth2Client' object has no attribute 'check_endpoint_auth_method'
```

**Quick Fix (api/models.py):**

Add this method to your `OAuth2Client` class:

```python
class OAuth2Client(db.Model):
    # ... existing code ...
    
    def check_endpoint_auth_method(self, method, endpoint):
        """
        Check if authentication method is supported for specific endpoint.
        
        Args:
            method: Authentication method to check
            endpoint: Endpoint type ('token', 'introspection', 'revocation')
            
        Returns:
            bool: True if method is supported for this endpoint
        """
        if endpoint == 'token':
            return self.check_token_endpoint_auth_method(method)
        # For other endpoints, use the same auth method
        return self.token_endpoint_auth_method == method
```

## Issue 4: expires_in vs access_token_expires_at

**Error:**
```
TypeError: 'expires_in' is an invalid keyword argument for OAuth2Token
```

**Root Cause:** Authlib passes `expires_in` (seconds) but your model expects `access_token_expires_at` (Unix timestamp)

**Quick Fix (api/oauth2.py):**

Replace the default `save_token` function:

```python
# Remove this line:
# save_token = create_save_token_func(db.session, OAuth2Token)

# Add this custom function:
def save_token(token, request):
    """
    Save OAuth2Token to database with proper timestamp conversion.
    
    Converts Authlib's expires_in to our model's access_token_expires_at.
    """
    import time
    from tenant_context import TenantContext
    
    # Get user from request (may be None for client_credentials grant)
    user = request.user if hasattr(request, 'user') else None
    
    # Get tenant ID from context or user
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id and user:
        tenant_id = user.tenant_id
    
    # Convert expires_in (seconds) to expires_at (Unix timestamp)
    expires_in = token.get('expires_in', 3600)
    access_token_expires_at = int(time.time()) + expires_in
    
    # Handle refresh token expiration if present
    refresh_token_expires_at = None
    if token.get('refresh_token'):
        # Default 30 days for refresh tokens
        refresh_expires_in = 2592000
        refresh_token_expires_at = int(time.time()) + refresh_expires_in
    
    # Create token instance
    oauth_token = OAuth2Token(
        tenant_id=tenant_id,
        client_id=request.client.client_id,
        user_id=user.id if user else None,
        token_type=token.get('token_type', 'Bearer'),
        access_token=token['access_token'],
        refresh_token=token.get('refresh_token'),
        scope=token.get('scope', ''),
        access_token_expires_at=access_token_expires_at,
        refresh_token_expires_at=refresh_token_expires_at,
    )
    
    db.session.add(oauth_token)
    db.session.commit()
    return oauth_token
```

## Issue 5: ResourceProtector validate_request Signature

**Error:**
```
TypeError: ResourceProtector.validate_request() missing 1 required positional argument: 'request'
```

**Quick Fix (api/routes.py):**

Simplify the `require_oauth` decorator to use Authlib's decorator directly:

```python
def require_oauth(scope=None):
    """
    Decorator to require OAuth 2.0 authentication for routes.
    
    Args:
        scope: Optional scope string or list of scopes required
    
    Returns:
        Decorator function that validates tokens
    """
    # Return the Authlib resource_protector decorator directly
    return current_app.resource_protector(scope)
```

Usage remains the same:
```python
@api_bp.route('/protected', methods=['GET'])
@require_oauth()
def protected_route(token):
    return jsonify({'message': 'Access granted'})

@api_bp.route('/admin', methods=['GET'])
@require_oauth(scope='admin')
def admin_route(token):
    return jsonify({'message': 'Admin access'})
```

## Issue 6: Frontend Can't Reach API

**Error:**
```
Connection refused to http://localhost:8080
```

**Root Cause:** Services inside Docker should use service names, not localhost

**Quick Fix (docker-compose.yml):**
```yaml
services:
  frontend:
    environment:
      # Use Docker service name, not localhost!
      API_URL: http://nginx_api:80  # ✅ Correct
      # API_URL: http://localhost:8080  # ❌ Wrong
```

## Complete Working Configuration

**requirements.txt:**
```txt
Flask==2.2.5
Werkzeug==2.2.3
Authlib==1.2.1
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
Flask-CORS==4.0.0
psycopg2-binary==2.9.9
uwsgi==2.0.23
cryptography==41.0.7
```

**constraints.txt:**
```txt
Werkzeug==2.2.3
Flask==2.2.5
```

**.env (development):**
```env
FLASK_ENV=development
DEBUG=True
AUTHLIB_INSECURE_TRANSPORT=true
SECRET_KEY=your-secret-key-here
OAUTH2_ISSUER=http://localhost:8080
POSTGRES_DB=backend_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
```

**docker-compose.yml (key sections):**
```yaml
services:
  api:
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/backend_db
      FLASK_ENV: development
      DEBUG: "True"
      AUTHLIB_INSECURE_TRANSPORT: "true"
  
  frontend:
    environment:
      API_URL: http://nginx_api:80  # Use service name!
```

## Testing OAuth Flow (PowerShell)

**Complete working example:**

```powershell
# Step 1: Login
$loginBody = @{
    username = "admin"
    password = "password123"
} | ConvertTo-Json

$loginResponse = Invoke-WebRequest `
    -Uri "http://localhost:8080/oauth/login" `
    -Method POST `
    -Body $loginBody `
    -ContentType "application/json" `
    -SessionVariable session

# Step 2: Get authorization code
$authUrl = "http://localhost:8080/oauth/authorize?" +
    "client_id=$CLIENT_ID&" +
    "redirect_uri=http://localhost:3000/callback&" +
    "response_type=code&" +
    "scope=profile email&" +
    "state=random123"

$authResponse = Invoke-WebRequest `
    -Uri $authUrl `
    -Method POST `
    -Body @{ confirm = "yes" } `
    -WebSession $session `
    -MaximumRedirection 0 `
    -ErrorAction SilentlyContinue

# Step 3: Extract code from redirect
$location = $authResponse.Headers['Location']
$code = ([System.Uri]$location).Query -replace '.*code=([^&]+).*', '$1'

# Step 4: Exchange for token (use HTTP Basic Auth)
$authBytes = [System.Text.Encoding]::ASCII.GetBytes("${CLIENT_ID}:${CLIENT_SECRET}")
$authBase64 = [Convert]::ToBase64String($authBytes)

$tokenResponse = Invoke-RestMethod `
    -Uri "http://localhost:8080/oauth/token" `
    -Method POST `
    -Headers @{ Authorization = "Basic $authBase64" } `
    -Body @{
        grant_type = "authorization_code"
        code = $code
        redirect_uri = "http://localhost:3000/callback"
    } `
    -ContentType "application/x-www-form-urlencoded"

$ACCESS_TOKEN = $tokenResponse.access_token

# Step 5: Use the token
$data = Invoke-RestMethod `
    -Uri "http://localhost:8080/api/protected" `
    -Headers @{ Authorization = "Bearer $ACCESS_TOKEN" }

Write-Host ($data | ConvertTo-Json)
```

## Quick Troubleshooting Checklist

- [ ] Is `AUTHLIB_INSECURE_TRANSPORT=true` set in development?
- [ ] Are you using Flask 2.2.5 and Werkzeug 2.2.3?
- [ ] Does OAuth2Client have `check_endpoint_auth_method()` method?
- [ ] Is your custom `save_token` function handling `expires_in` conversion?
- [ ] Are you using HTTP Basic Auth for client authentication at token endpoint?
- [ ] Is frontend using Docker service names (not localhost)?
- [ ] Are all containers on the same Docker network?
- [ ] Have you run `flask db upgrade` to create tables?

## Additional Resources

- [Full Testing Results](TESTING_RESULTS.md)
- [Complete OAuth 2.0 Guide](OAUTH2.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Architecture Documentation](OVERVIEW.md)

---

**Last Updated:** November 9, 2025  
**Tested With:** Python 3.11, Flask 2.2.5, Authlib 1.2.1, PostgreSQL 15
