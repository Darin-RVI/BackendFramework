# Migrating from JWT to OAuth 2.0

This guide will help you migrate your application from JWT (Flask-JWT-Extended) to OAuth 2.0 (Authlib).

## Why OAuth 2.0?

OAuth 2.0 offers several advantages over simple JWT authentication:

- **Standardized Protocol**: Industry-standard with broad ecosystem support
- **Multiple Grant Types**: Support for various authentication flows
- **Token Revocation**: Ability to invalidate tokens server-side
- **Scope-based Authorization**: Fine-grained access control
- **Refresh Token Rotation**: Enhanced security with automatic rotation
- **Client Management**: Support for multiple client applications
- **OpenID Connect Compatible**: Easy extension to OIDC for identity layer

## Changes Overview

### Dependencies

**Before (JWT):**
```txt
Flask-JWT-Extended==4.5.3
```

**After (OAuth 2.0):**
```txt
Authlib==1.2.1
cryptography==41.0.7
```

### Environment Variables

**Before:**
```bash
JWT_SECRET_KEY=your_jwt_secret_key_here
```

**After:**
```bash
OAUTH2_ISSUER=http://localhost:8080
OAUTH2_ACCESS_TOKEN_EXPIRES=3600
OAUTH2_REFRESH_TOKEN_EXPIRES=2592000
OAUTH2_AUTHORIZATION_CODE_EXPIRES=600
```

## Step-by-Step Migration

### Step 1: Update Dependencies

Edit `api/requirements.txt`:

```bash
# Remove
- Flask-JWT-Extended==4.5.3

# Add
+ Authlib==1.2.1
+ cryptography==41.0.7
```

Rebuild containers:

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### Step 2: Create Database Models

The framework now includes these models in `models.py`:

- `User`: User accounts with password hashing
- `OAuth2Client`: OAuth 2.0 client applications
- `OAuth2AuthorizationCode`: Authorization codes
- `OAuth2Token`: Access and refresh tokens

### Step 3: Run Database Migrations

```bash
# Create migration
docker-compose exec api flask db migrate -m "Migrate to OAuth 2.0"

# Apply migration
docker-compose exec api flask db upgrade
```

This creates the following tables:
- `users`
- `oauth2_clients`
- `oauth2_codes`
- `oauth2_tokens`

### Step 4: Update Application Configuration

The `app.py` file now includes OAuth 2.0 initialization:

```python
# OAuth 2.0 Configuration
app.config['OAUTH2_ISSUER'] = os.getenv('OAUTH2_ISSUER', 'http://localhost:8080')
app.config['OAUTH2_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('OAUTH2_ACCESS_TOKEN_EXPIRES', 3600))

# Initialize OAuth 2.0
from oauth2 import config_oauth
authorization_server, resource_protector = config_oauth(app)
```

### Step 5: Update Protected Endpoints

**Before (JWT):**

```python
from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/protected')
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'user': current_user})
```

**After (OAuth 2.0):**

```python
from flask import current_app

def require_oauth(scope=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = current_app.resource_protector.validate_request(scopes=scope)
            kwargs['token'] = token
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/protected')
@require_oauth()
def protected(token):
    user = User.query.get(token.user_id)
    return jsonify({'user': user.username})
```

### Step 6: Update Authentication Endpoints

**Before (JWT):**

```python
from flask_jwt_extended import create_access_token

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # Verify user...
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)
```

**After (OAuth 2.0):**

```python
@app.route('/oauth/token', methods=['POST'])
def issue_token():
    # Supports multiple grant types
    return current_app.authorization_server.create_token_response()

# Client uses password grant:
# POST /oauth/token
# grant_type=password&username=user&password=pass&client_id=...
```

### Step 7: Register OAuth Clients

Before clients can authenticate, they need to be registered:

```bash
# 1. Register user
curl -X POST http://localhost:8080/oauth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "secure123"}'

# 2. Login to create session
curl -X POST http://localhost:8080/oauth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username": "admin", "password": "secure123"}'

# 3. Register OAuth client
curl -X POST http://localhost:8080/oauth/client/register \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "client_name": "My App",
    "redirect_uris": ["http://localhost:3000/callback"],
    "grant_types": ["password", "refresh_token"],
    "scope": "read write profile"
  }'

# Save the client_id and client_secret returned!
```

### Step 8: Update Client Code

**Before (JWT):**

```python
# Login to get token
response = requests.post('http://localhost:8080/login', json={
    'username': 'user',
    'password': 'pass'
})
access_token = response.json()['access_token']

# Use token
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://localhost:8080/protected', headers=headers)
```

**After (OAuth 2.0):**

```python
# Get token using password grant
response = requests.post('http://localhost:8080/oauth/token', data={
    'grant_type': 'password',
    'username': 'user',
    'password': 'pass',
    'client_id': 'YOUR_CLIENT_ID',
    'client_secret': 'YOUR_CLIENT_SECRET',
    'scope': 'read write'
})
token_data = response.json()
access_token = token_data['access_token']
refresh_token = token_data['refresh_token']

# Use token (same as before)
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://localhost:8080/api/protected', headers=headers)

# Refresh token when expired
response = requests.post('http://localhost:8080/oauth/token', data={
    'grant_type': 'refresh_token',
    'refresh_token': refresh_token,
    'client_id': 'YOUR_CLIENT_ID',
    'client_secret': 'YOUR_CLIENT_SECRET'
})
new_token_data = response.json()
```

## Feature Comparison

| Feature | JWT (Flask-JWT-Extended) | OAuth 2.0 (Authlib) |
|---------|--------------------------|---------------------|
| Access Tokens | ✅ | ✅ |
| Refresh Tokens | ✅ | ✅ |
| Token Revocation | ❌ (stateless) | ✅ |
| Multiple Grant Types | ❌ | ✅ |
| Client Management | ❌ | ✅ |
| Scope-based Access | Limited | ✅ |
| Token Introspection | ❌ | ✅ |
| PKCE Support | ❌ | ✅ |
| OpenID Connect | ❌ | Compatible |

## Authentication Flow Changes

### JWT Flow (Before)

```
1. User sends username/password to /login
2. Server validates and returns JWT
3. Client stores JWT
4. Client sends JWT in Authorization header
5. Server validates JWT signature (stateless)
```

### OAuth 2.0 Flow (After)

```
1. Client registered with client_id/client_secret
2. User sends credentials + client credentials to /oauth/token
3. Server validates and returns access_token + refresh_token
4. Client stores both tokens
5. Client sends access_token in Authorization header
6. Server validates token from database
7. When token expires, client uses refresh_token
```

## Testing the Migration

### Test User Registration and Login

```bash
# Register user
curl -X POST http://localhost:8080/oauth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "test123"}'
```

### Test Token Generation

```bash
# Get access token (requires registered client)
curl -X POST http://localhost:8080/oauth/token \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=test123" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=read write"
```

### Test Protected Endpoint

```bash
# Call protected endpoint
curl -X GET http://localhost:8080/api/protected \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test Token Refresh

```bash
# Refresh token
curl -X POST http://localhost:8080/oauth/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

## Common Migration Issues

### Issue 1: Missing Client Credentials

**Error:** `invalid_client`

**Solution:** Ensure you've registered an OAuth client before attempting authentication.

```bash
# Register client first
curl -X POST http://localhost:8080/oauth/client/register \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"client_name": "Test App", "grant_types": ["password", "refresh_token"]}'
```

### Issue 2: Invalid Grant Type

**Error:** `unsupported_grant_type`

**Solution:** Ensure the client is registered with the grant type you're trying to use.

```python
# When registering client, specify grant_types
{
    "grant_types": ["authorization_code", "password", "refresh_token"]
}
```

### Issue 3: Token Validation Failures

**Error:** `invalid_token` or `token_expired`

**Solution:** 

1. Check token hasn't expired
2. Verify token exists in database
3. Use refresh token to get new access token

### Issue 4: Scope Errors

**Error:** `insufficient_scope`

**Solution:** Request appropriate scopes when getting token:

```bash
curl -X POST http://localhost:8080/oauth/token \
  -d "scope=read write profile admin"
  # ... other parameters
```

## Rollback Plan

If you need to rollback to JWT:

1. **Restore dependencies:**
   ```bash
   # In requirements.txt, restore:
   Flask-JWT-Extended==4.5.3
   # Remove:
   # Authlib==1.2.1
   # cryptography==41.0.7
   ```

2. **Restore previous code:**
   ```bash
   git checkout HEAD~1 api/app.py api/routes.py
   # Remove new files
   rm api/oauth2.py api/auth_routes.py api/models.py
   ```

3. **Rollback migrations:**
   ```bash
   docker-compose exec api flask db downgrade
   ```

4. **Rebuild:**
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

## Performance Considerations

### JWT (Stateless)
- ✅ No database lookup for validation
- ❌ Cannot revoke tokens
- ❌ Larger token size (claims in token)

### OAuth 2.0 (Stateful)
- ❌ Database lookup for validation
- ✅ Can revoke tokens immediately
- ✅ Smaller token size (random string)
- ✅ Better for microservices with shared token store

**Optimization Tips:**

1. **Use caching**: Cache valid tokens in Redis
2. **Connection pooling**: Optimize database connections
3. **Token cleanup**: Periodically remove expired tokens

```python
# Add to cron job or background task
def cleanup_expired_tokens():
    now = int(time.time())
    OAuth2Token.query.filter(
        OAuth2Token.access_token_expires_at < now
    ).delete()
    db.session.commit()
```

## Security Improvements

The OAuth 2.0 implementation provides:

1. **Client Authentication**: Prevents unauthorized token requests
2. **Token Revocation**: Immediately invalidate compromised tokens
3. **Refresh Token Rotation**: New refresh token issued on each use
4. **PKCE Support**: Protection for public clients
5. **Scope Limitation**: Restrict token capabilities
6. **Audit Trail**: Track all authentication events

## Next Steps

After migration:

1. **Update documentation**: Document OAuth 2.0 flows for your team
2. **Update clients**: Migrate all client applications
3. **Implement PKCE**: For mobile and SPA clients
4. **Add monitoring**: Track token usage and failures
5. **Consider OIDC**: Add OpenID Connect for identity management

## Support

For issues during migration:

- See [OAUTH2.md](OAUTH2.md) for complete OAuth 2.0 documentation
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common problems
- Review Authlib docs: https://docs.authlib.org/

## Checklist

- [ ] Updated dependencies
- [ ] Created database migrations
- [ ] Updated application configuration
- [ ] Registered OAuth clients
- [ ] Updated protected endpoints
- [ ] Updated client applications
- [ ] Tested all authentication flows
- [ ] Updated documentation
- [ ] Trained team on OAuth 2.0
- [ ] Deployed to production
