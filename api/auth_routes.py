"""
OAuth 2.0 Authentication Routes

This module implements OAuth 2.0 authentication endpoints following RFC 6749.
It provides complete OAuth 2.0 server functionality including:

1. User Registration & Login: Session-based authentication for authorization flow
2. Authorization Endpoint: User consent and authorization code issuance
3. Token Endpoint: Access token issuance for all grant types
4. Token Revocation: RFC 7009 token revocation
5. Client Registration: Dynamic OAuth client registration
6. UserInfo Endpoint: OpenID Connect compatible user info
7. Token Introspection: RFC 7662 token metadata

Supported OAuth 2.0 Flows:
- Authorization Code (with PKCE support)
- Resource Owner Password Credentials (Password Grant)
- Client Credentials
- Refresh Token

Security Features:
- Multi-tenant isolation (all operations scoped to tenant)
- Secure password hashing
- PKCE support for public clients
- Token revocation
- Scope-based access control
- Session management for authorization flow

All endpoints respect tenant context and ensure data isolation.
"""
import time
from flask import Blueprint, request, jsonify, session, render_template_string
from werkzeug.security import gen_salt
from app import db
from models import User, OAuth2Client
from oauth2 import create_oauth_client
from flask import current_app

# Create blueprint for authentication routes
# All routes in this blueprint will be prefixed with /oauth (configured in app.py)
auth_bp = Blueprint('auth', __name__)


# ==================== User Registration & Login ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user in a tenant.
    
    Creates a new user account within the identified tenant context.
    Requires tenant to be identified via header, subdomain, or path.
    Checks tenant limits before creating user.
    
    Required Tenant Context:
        Must provide tenant identification via:
        - X-Tenant-Slug header (e.g., "acme")
        - Subdomain (e.g., acme.example.com)
        - Path parameter (e.g., /tenants/acme/oauth/register)
    
    Request Body (JSON):
        username (str): Unique username within tenant
        password (str): User password (will be hashed)
        email (str): User email address
        role (str, optional): User role (default: 'user')
                             Options: user, admin, owner
    
    Returns:
        201: User created successfully
        400: Missing required fields or tenant not identified
        403: Tenant limits reached
        
    Example:
        curl -X POST http://localhost:8080/oauth/register \\
             -H "Content-Type: application/json" \\
             -H "X-Tenant-Slug: acme" \\
             -d '{
                 "username": "john_doe",
                 "password": "secure123",
                 "email": "john@acme.com",
                 "role": "user"
             }'
        
        # Response: {
        #     "message": "User registered successfully",
        #     "user_id": 123,
        #     "username": "john_doe",
        #     "tenant_id": 1,
        #     "tenant_slug": "acme"
        # }
    """
    from tenant_context import TenantContext, check_tenant_limits
    
    # Get current tenant from request context
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({
            'error': 'Tenant not identified',
            'message': 'Please specify tenant via X-Tenant-Slug header, subdomain, or path'
        }), 400
    
    # Check if tenant has reached user limits
    within_limits, error_msg = check_tenant_limits(tenant)
    if not within_limits:
        return jsonify({'error': error_msg}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if username already exists in this tenant
    # Usernames must be unique within tenant (not globally)
    if User.query.filter_by(tenant_id=tenant.id, username=data['username']).first():
        return jsonify({'error': 'Username already exists in this tenant'}), 400
    
    # Check if email already exists in this tenant
    if User.query.filter_by(tenant_id=tenant.id, email=data['email']).first():
        return jsonify({'error': 'Email already exists in this tenant'}), 400
    
    # Create new user with hashed password
    user = User(
        tenant_id=tenant.id,
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user')  # Default to 'user' role
    )
    user.set_password(data['password'])  # Hash password before storing
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user_id': user.id,
        'username': user.username,
        'tenant_id': tenant.id,
        'tenant_slug': tenant.slug
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint for session-based authentication.
    
    Authenticates user and creates session for OAuth authorization flow.
    The session is used when user authorizes an OAuth client via /oauth/authorize.
    
    This is NOT for getting access tokens directly - use /oauth/token for that.
    This endpoint is for web-based authorization code flow where user needs
    to be logged in before authorizing a client application.
    
    Required Tenant Context:
        Must provide tenant identification
    
    Request Body (JSON):
        username (str): User's username
        password (str): User's password
    
    Returns:
        200: Login successful, session created
        400: Missing credentials or tenant not identified
        401: Invalid credentials
        403: Account inactive or access denied
        
    Session Data Set:
        user_id: User's ID for authorization flow
        tenant_id: Tenant ID for validation
        
    Example:
        curl -X POST http://localhost:8080/oauth/login \\
             -H "Content-Type: application/json" \\
             -H "X-Tenant-Slug: acme" \\
             -c cookies.txt \\
             -d '{
                 "username": "john_doe",
                 "password": "secure123"
             }'
        
        # Use cookies.txt with subsequent /oauth/authorize requests
    """
    from tenant_context import TenantContext, validate_tenant_access
    
    # Get current tenant
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({
            'error': 'Tenant not identified',
            'message': 'Please specify tenant via X-Tenant-Slug header, subdomain, or path'
        }), 400
    
    data = request.get_json()
    
    # Validate credentials provided
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing credentials'}), 400
    
    # Find user within tenant (username is unique per tenant)
    user = User.query.filter_by(
        tenant_id=tenant.id,
        username=data['username']
    ).first()
    
    # Verify password
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check if account is active
    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403
    
    # Validate user belongs to this tenant (security check)
    if not validate_tenant_access(user, tenant):
        return jsonify({'error': 'Access denied to this tenant'}), 403
    
    # Store user in session for authorization flow
    session['user_id'] = user.id
    session['tenant_id'] = tenant.id
    
    return jsonify({
        'message': 'Login successful',
        'user_id': user.id,
        'username': user.username,
        'tenant_id': tenant.id,
        'tenant_slug': tenant.slug,
        'role': user.role
    }), 200


# ==================== OAuth 2.0 Authorization Endpoint ====================

@auth_bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """
    OAuth 2.0 Authorization Endpoint (RFC 6749 Section 3.1).
    
    This endpoint handles the authorization code flow where:
    1. Client redirects user here with authorization request
    2. User must be logged in (via /oauth/login)
    3. User is shown consent screen (in production)
    4. User approves/denies access
    5. Authorization code is generated and sent to redirect_uri
    
    GET: Display authorization request details (consent screen)
    POST: Process user's authorization decision
    
    Query Parameters (GET):
        response_type: Must be 'code' for authorization code flow
        client_id: OAuth client identifier
        redirect_uri: Where to send authorization code
        scope: Requested scopes (space-separated)
        state: Client state for CSRF protection (recommended)
        code_challenge: PKCE code challenge (optional but recommended)
        code_challenge_method: PKCE method (S256 or plain)
    
    Form Data (POST):
        confirm: 'yes' to approve, 'no' to deny
        
    Returns:
        GET 200: Authorization request details
        GET 401: User not logged in
        POST 302: Redirect to client with code or error
        POST 401: User not logged in
        POST 403: User denied access
        
    Example Authorization Request:
        # User visits (or is redirected to):
        http://localhost:8080/oauth/authorize?
            response_type=code&
            client_id=abc123&
            redirect_uri=http://localhost:3000/callback&
            scope=read%20write&
            state=random_state_string&
            code_challenge=BASE64URL(SHA256(code_verifier))&
            code_challenge_method=S256
        
        # After approval, user is redirected to:
        http://localhost:3000/callback?
            code=AUTHORIZATION_CODE&
            state=random_state_string
    """
    
    # Get current user from session (set by /oauth/login)
    user_id = session.get('user_id')
    
    if request.method == 'GET':
        # ===== GET: Display authorization request details =====
        # Check if user is logged in
        if not user_id:
            return jsonify({
                'error': 'unauthorized',
                'error_description': 'User must be logged in'
            }), 401
        
        # Get authorization request details
        try:
            grant = current_app.authorization_server.get_consent_grant(end_user=User.query.get(user_id))
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
        # In production: Show consent screen with client details
        # For demo: Auto-approve or return details for client to display
        return jsonify({
            'client_name': grant.client.client_name,
            'scope': grant.request.scope,
            'redirect_uri': grant.request.redirect_uri,
            'state': grant.request.state
        }), 200
    
    # ===== POST: User approved/denied the authorization =====
    if not user_id:
        return jsonify({'error': 'unauthorized'}), 401
    
    user = User.query.get(user_id)
    
    # Check if user denied permission
    if request.form.get('confirm') == 'no':
        return jsonify({'error': 'access_denied'}), 403
    
    # Generate authorization code and redirect
    return current_app.authorization_server.create_authorization_response(grant_user=user)


# ==================== OAuth 2.0 Token Endpoint ====================

@auth_bp.route('/token', methods=['POST'])
def issue_token():
    """
    OAuth 2.0 Token Endpoint (RFC 6749 Section 3.2).
    
    This is the main token issuance endpoint supporting multiple grant types:
    - authorization_code: Exchange auth code for tokens
    - password: Exchange username/password for tokens (trusted apps only)
    - refresh_token: Exchange refresh token for new access token
    - client_credentials: Client authentication for machine-to-machine
    
    Request Format:
        Content-Type: application/x-www-form-urlencoded
        
    Common Parameters:
        grant_type (str): Type of grant (required)
        client_id (str): OAuth client identifier
        client_secret (str): OAuth client secret (for confidential clients)
        
    Grant-Specific Parameters:
        authorization_code:
            - code: Authorization code from /authorize
            - redirect_uri: Must match original request
            - code_verifier: For PKCE (if code_challenge was used)
            
        password:
            - username: User's username
            - password: User's password
            - scope: Requested scopes (optional)
            
        refresh_token:
            - refresh_token: Valid refresh token
            
        client_credentials:
            - scope: Requested scopes (optional)
    
    Returns:
        200: Token issued successfully
        400: Invalid request (missing parameters, invalid grant, etc.)
        401: Invalid client credentials
        
    Response Format:
        {
            "access_token": "...",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "..." (if applicable),
            "scope": "read write"
        }
    
    Examples:
        # Authorization Code Grant
        curl -X POST http://localhost:8080/oauth/token \\
             -H "Content-Type: application/x-www-form-urlencoded" \\
             -d "grant_type=authorization_code" \\
             -d "code=AUTH_CODE_HERE" \\
             -d "redirect_uri=http://localhost:3000/callback" \\
             -d "client_id=YOUR_CLIENT_ID" \\
             -d "client_secret=YOUR_CLIENT_SECRET"
        
        # Password Grant
        curl -X POST http://localhost:8080/oauth/token \\
             -H "X-Tenant-Slug: acme" \\
             -d "grant_type=password" \\
             -d "username=john_doe" \\
             -d "password=secure123" \\
             -d "client_id=YOUR_CLIENT_ID" \\
             -d "client_secret=YOUR_CLIENT_SECRET" \\
             -d "scope=read write"
        
        # Refresh Token Grant
        curl -X POST http://localhost:8080/oauth/token \\
             -d "grant_type=refresh_token" \\
             -d "refresh_token=YOUR_REFRESH_TOKEN" \\
             -d "client_id=YOUR_CLIENT_ID" \\
             -d "client_secret=YOUR_CLIENT_SECRET"
        
        # Client Credentials Grant
        curl -X POST http://localhost:8080/oauth/token \\
             -d "grant_type=client_credentials" \\
             -d "client_id=YOUR_CLIENT_ID" \\
             -d "client_secret=YOUR_CLIENT_SECRET" \\
             -d "scope=read"
    """
    return current_app.authorization_server.create_token_response()


@auth_bp.route('/revoke', methods=['POST'])
def revoke_token():
    """
    OAuth 2.0 Token Revocation Endpoint (RFC 7009).
    
    Allows clients to revoke access tokens or refresh tokens.
    Revoked tokens can no longer be used for authentication.
    
    Use Cases:
    - User logs out
    - Token compromised
    - Client deauthorization
    - Security cleanup
    
    Request Format:
        Content-Type: application/x-www-form-urlencoded
        
    Parameters:
        token (str): The token to revoke (access or refresh token)
        token_type_hint (str, optional): 'access_token' or 'refresh_token'
        client_id (str): OAuth client identifier
        client_secret (str): OAuth client secret
    
    Returns:
        200: Token revoked successfully (or token was already invalid)
        
    Note: Returns 200 even if token doesn't exist (security best practice
    to not leak information about token validity)
    
    Example:
        curl -X POST http://localhost:8080/oauth/revoke \\
             -d "token=YOUR_ACCESS_TOKEN" \\
             -d "token_type_hint=access_token" \\
             -d "client_id=YOUR_CLIENT_ID" \\
             -d "client_secret=YOUR_CLIENT_SECRET"
    """
    return current_app.authorization_server.create_endpoint_response('revocation')


# ==================== OAuth Client Management ====================

@auth_bp.route('/client/register', methods=['POST'])
def register_client():
    """
    Register a new OAuth 2.0 client application.
    
    Allows authenticated users to register OAuth clients for their applications.
    Creates client with random client_id and client_secret.
    
    Authentication:
        Requires user to be logged in (session-based)
        
    Tenant Context:
        Requires tenant identification
        User must belong to the tenant
    
    Request Body (JSON):
        client_name (str): Human-readable client name (required)
        redirect_uris (list): Allowed redirect URIs (default: ['http://localhost:3000/callback'])
        grant_types (list): Allowed grant types (default: ['authorization_code', 'refresh_token'])
        scope (str): Allowed scopes (default: 'read write')
    
    Returns:
        201: Client created successfully with credentials
        400: Missing required fields or tenant not identified
        401: Authentication required
        403: Access denied to tenant
        404: User not found
        
    Response:
        {
            "client_id": "randomly_generated_id",
            "client_secret": "randomly_generated_secret",
            "client_name": "My App",
            "redirect_uris": ["http://localhost:3000/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "scope": "read write",
            "tenant_id": 1,
            "tenant_slug": "acme",
            "message": "Client registered successfully. Store client_secret securely!"
        }
    
    Security Notes:
        - Store client_secret securely - it's shown only once
        - Use HTTPS in production to protect credentials
        - Rotate secrets periodically for security
    
    Example:
        # Login first
        curl -X POST http://localhost:8080/oauth/login \\
             -H "X-Tenant-Slug: acme" \\
             -H "Content-Type: application/json" \\
             -c cookies.txt \\
             -d '{"username": "admin", "password": "secret"}'
        
        # Register client
        curl -X POST http://localhost:8080/oauth/client/register \\
             -H "X-Tenant-Slug: acme" \\
             -H "Content-Type: application/json" \\
             -b cookies.txt \\
             -d '{
                 "client_name": "My Mobile App",
                 "redirect_uris": ["myapp://callback"],
                 "grant_types": ["authorization_code", "refresh_token"],
                 "scope": "read write profile"
             }'
    """
    from tenant_context import TenantContext, validate_tenant_access
    
    # Require authentication
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({'error': 'Tenant not identified'}), 400
    
    # Validate user belongs to tenant
    if not validate_tenant_access(user, tenant):
        return jsonify({'error': 'Access denied to this tenant'}), 403
    
    data = request.get_json()
    
    if not data or not data.get('client_name'):
        return jsonify({'error': 'client_name is required'}), 400
    
    # Default values for optional fields
    redirect_uris = data.get('redirect_uris', ['http://localhost:3000/callback'])
    grant_types = data.get('grant_types', ['authorization_code', 'refresh_token'])
    scope = data.get('scope', 'read write')
    
    # Create OAuth client
    client = create_oauth_client(
        tenant_id=tenant.id,
        user_id=user_id,
        client_name=data['client_name'],
        redirect_uris=redirect_uris,
        grant_types=grant_types,
        scope=scope
    )
    
    return jsonify({
        'client_id': client.client_id,
        'client_secret': client.client_secret,
        'client_name': client.client_name,
        'redirect_uris': client.redirect_uris.split(),
        'grant_types': client.grant_types.split(),
        'scope': client.scope,
        'tenant_id': tenant.id,
        'tenant_slug': tenant.slug,
        'message': 'Client registered successfully. Store client_secret securely!'
    }), 201


@auth_bp.route('/client/list', methods=['GET'])
def list_clients():
    """
    List OAuth 2.0 clients for authenticated user.
    
    Returns all OAuth clients created by the current user.
    Client secrets are NOT included in response for security.
    
    Authentication:
        Requires user to be logged in (session-based)
    
    Returns:
        200: List of client applications
        401: Authentication required
        
    Response:
        {
            "clients": [
                {
                    "client_id": "abc123",
                    "client_name": "My App",
                    "redirect_uris": ["http://localhost:3000/callback"],
                    "grant_types": ["authorization_code", "refresh_token"],
                    "scope": "read write",
                    "created_at": "2024-01-15T10:30:00"
                }
            ]
        }
    
    Example:
        curl -X GET http://localhost:8080/oauth/client/list \\
             -b cookies.txt
    """
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    clients = OAuth2Client.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'clients': [{
            'client_id': c.client_id,
            'client_name': c.client_name,
            'redirect_uris': c.redirect_uris.split() if c.redirect_uris else [],
            'grant_types': c.grant_types.split() if c.grant_types else [],
            'scope': c.scope,
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in clients]
    }), 200


# ==================== OpenID Connect & Token Info ====================

@auth_bp.route('/userinfo', methods=['GET'])
def userinfo():
    """
    OAuth 2.0 UserInfo Endpoint (OpenID Connect compatible).
    
    Returns information about the authenticated user based on access token.
    Information returned depends on token scopes.
    
    Authentication:
        Requires valid access token in Authorization header
        Format: Authorization: Bearer <access_token>
    
    Scopes:
        - No specific scope: Returns basic user info (sub, username)
        - 'email' scope: Includes email address
        - 'profile' scope: Includes profile information (created_at)
    
    Returns:
        200: User information
        401: Invalid or missing token
        404: User not found
        
    Response Format:
        {
            "sub": "123",              // User ID (always included)
            "username": "john_doe",    // Username (always included)
            "email": "john@example.com",  // If 'email' scope
            "created_at": "2024-01-15T10:30:00"  // If 'profile' scope
        }
    
    Example:
        curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
             http://localhost:8080/oauth/userinfo
    """
    # Validate access token from Authorization header
    token = current_app.resource_protector.validate_request(scopes=None)
    
    user = User.query.get(token.user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Build userinfo response based on scopes
    userinfo = {
        'sub': str(user.id),  # Subject (user ID) - always included
        'username': user.username,  # Username - always included
    }
    
    # Include email if 'email' scope is present
    if token.scope and 'email' in token.scope:
        userinfo['email'] = user.email
    
    # Include profile info if 'profile' scope is present
    if token.scope and 'profile' in token.scope:
        userinfo['created_at'] = user.created_at.isoformat() if user.created_at else None
    
    return jsonify(userinfo), 200


@auth_bp.route('/introspect', methods=['POST'])
def introspect_token():
    """
    Token Introspection Endpoint (RFC 7662).
    
    Allows clients to check if a token is valid and get metadata.
    Useful for resource servers to validate tokens.
    
    Request Format:
        Content-Type: application/x-www-form-urlencoded
        
    Parameters:
        token (str): The access token to introspect
        token_type_hint (str, optional): 'access_token' or 'refresh_token'
    
    Returns:
        200: Token introspection result
        
    Response (Active Token):
        {
            "active": true,
            "client_id": "abc123",
            "username": "john_doe",
            "scope": "read write",
            "exp": 1640000000,  // Expiration timestamp
            "iat": 1639996400,  // Issued at timestamp
            "token_type": "Bearer"
        }
    
    Response (Inactive Token):
        {
            "active": false
        }
    
    Note: Returns "active": false for:
    - Expired tokens
    - Revoked tokens
    - Non-existent tokens
    - Invalid tokens
    
    Example:
        curl -X POST http://localhost:8080/oauth/introspect \\
             -d "token=YOUR_ACCESS_TOKEN" \\
             -d "token_type_hint=access_token"
    """
    from models import OAuth2Token
    
    token_string = request.form.get('token')
    if not token_string:
        return jsonify({'active': False}), 200
    
    # Look up token in database
    token = OAuth2Token.query.filter_by(access_token=token_string).first()
    
    # Return inactive if token doesn't exist, is expired, or is revoked
    if not token or token.is_expired() or token.revoked:
        return jsonify({'active': False}), 200
    
    # Return token metadata
    return jsonify({
        'active': True,
        'client_id': token.client_id,
        'username': User.query.get(token.user_id).username if token.user_id else None,
        'scope': token.scope,
        'exp': token.access_token_expires_at,  # Expiration time (Unix timestamp)
        'iat': token.issued_at,  # Issued at time (Unix timestamp)
        'token_type': token.token_type
    }), 200
