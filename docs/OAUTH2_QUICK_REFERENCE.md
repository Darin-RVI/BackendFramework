# OAuth 2.0 Quick Reference

## Quick Start Commands

### 1. Register a User
```bash
curl -X POST http://localhost:8080/oauth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "email": "user@example.com", "password": "password123"}'
```

### 2. Login (Create Session)
```bash
curl -X POST http://localhost:8080/oauth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username": "myuser", "password": "password123"}'
```

### 3. Register OAuth Client
```bash
curl -X POST http://localhost:8080/oauth/client/register \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "client_name": "My App",
    "grant_types": ["password", "refresh_token"],
    "scope": "read write profile"
  }'
```

**Save the client_id and client_secret!**

### 4. Get Access Token (Password Grant)
```bash
curl -X POST http://localhost:8080/oauth/token \
  -d "grant_type=password" \
  -d "username=myuser" \
  -d "password=password123" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=read write"
```

### 5. Call Protected Endpoint
```bash
curl -X GET http://localhost:8080/api/protected \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Refresh Token
```bash
curl -X POST http://localhost:8080/oauth/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

## Grant Types

### Password Grant
```http
POST /oauth/token
grant_type=password&username=USER&password=PASS&client_id=ID&client_secret=SECRET
```

### Authorization Code Grant
```http
GET /oauth/authorize?response_type=code&client_id=ID&redirect_uri=URI
POST /oauth/token
grant_type=authorization_code&code=CODE&redirect_uri=URI&client_id=ID&client_secret=SECRET
```

### Refresh Token Grant
```http
POST /oauth/token
grant_type=refresh_token&refresh_token=TOKEN&client_id=ID&client_secret=SECRET
```

### Client Credentials Grant
```http
POST /oauth/token
grant_type=client_credentials&client_id=ID&client_secret=SECRET&scope=SCOPE
```

## Available Scopes

| Scope | Purpose |
|-------|---------|
| `read` | Read access to resources |
| `write` | Write access to resources |
| `profile` | Access to user profile information |
| `email` | Access to user email address |
| `admin` | Administrative privileges |

## Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/oauth/register` | POST | None | Register new user |
| `/oauth/login` | POST | None | User login |
| `/oauth/authorize` | GET/POST | Session | Authorization endpoint |
| `/oauth/token` | POST | Client | Token endpoint |
| `/oauth/revoke` | POST | Client | Revoke token |
| `/oauth/userinfo` | GET | Bearer | Get user info |
| `/oauth/introspect` | POST | Client | Check token validity |
| `/oauth/client/register` | POST | Session | Register OAuth client |
| `/api/protected` | GET | Bearer | Example protected endpoint |
| `/api/admin` | GET | Bearer (admin) | Admin-only endpoint |
| `/api/users/me` | GET | Bearer (profile) | Current user profile |

## Token Lifetimes

| Token Type | Default Lifetime | Configurable |
|------------|------------------|--------------|
| Access Token | 3600s (1 hour) | `OAUTH2_ACCESS_TOKEN_EXPIRES` |
| Refresh Token | 2592000s (30 days) | `OAUTH2_REFRESH_TOKEN_EXPIRES` |
| Authorization Code | 600s (10 minutes) | `OAUTH2_AUTHORIZATION_CODE_EXPIRES` |

## Python Example

```python
import requests

# Configuration
TOKEN_URL = 'http://localhost:8080/oauth/token'
API_URL = 'http://localhost:8080/api'
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'

# Get token
response = requests.post(TOKEN_URL, data={
    'grant_type': 'password',
    'username': 'user',
    'password': 'pass',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'scope': 'read write'
})
token_data = response.json()

# Use token
headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
response = requests.get(f'{API_URL}/protected', headers=headers)
print(response.json())
```

## JavaScript Example

```javascript
// Get token
const tokenResponse = await fetch('http://localhost:8080/oauth/token', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: new URLSearchParams({
    grant_type: 'password',
    username: 'user',
    password: 'pass',
    client_id: 'CLIENT_ID',
    client_secret: 'CLIENT_SECRET',
    scope: 'read write'
  })
});
const tokenData = await tokenResponse.json();

// Use token
const apiResponse = await fetch('http://localhost:8080/api/protected', {
  headers: {'Authorization': `Bearer ${tokenData.access_token}`}
});
const data = await apiResponse.json();
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_client` | Wrong client credentials | Verify client_id and client_secret |
| `invalid_grant` | Invalid authorization code | Check code hasn't expired |
| `invalid_token` | Token expired or invalid | Refresh token or re-authenticate |
| `insufficient_scope` | Missing required scope | Request appropriate scopes |
| `unauthorized` | Not logged in | Login first for session-based endpoints |

## Environment Variables

```bash
# .env file
OAUTH2_ISSUER=http://localhost:8080
OAUTH2_ACCESS_TOKEN_EXPIRES=3600
OAUTH2_REFRESH_TOKEN_EXPIRES=2592000
OAUTH2_AUTHORIZATION_CODE_EXPIRES=600
```

## Protected Endpoint Decorator

```python
from flask import current_app
from functools import wraps

def require_oauth(scope=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = current_app.resource_protector.validate_request(scopes=scope)
            kwargs['token'] = token
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/data')
@require_oauth(scope='read')
def get_data(token):
    return jsonify({'data': [...]})
```

## Database Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts |
| `oauth2_clients` | OAuth client applications |
| `oauth2_codes` | Authorization codes |
| `oauth2_tokens` | Access and refresh tokens |

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Store client_secret securely
- [ ] Implement rate limiting on `/oauth/token`
- [ ] Short-lived access tokens (1 hour)
- [ ] Rotate refresh tokens
- [ ] Validate redirect URIs
- [ ] Use PKCE for public clients
- [ ] Monitor failed authentication attempts
- [ ] Implement token cleanup for expired tokens
- [ ] Use strong passwords
- [ ] Enable CORS properly
- [ ] Audit log authentication events

## For More Information

See [OAUTH2.md](OAUTH2.md) for complete documentation.
