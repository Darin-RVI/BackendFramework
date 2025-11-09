"""
OAuth 2.0 Server Configuration

This module configures the OAuth 2.0 authorization server using Authlib.
It implements multiple grant types for different OAuth 2.0 flows:

Supported Grant Types:
1. Authorization Code - For web applications with user authorization
2. Password (Resource Owner Password Credentials) - For trusted first-party apps
3. Refresh Token - For renewing access tokens
4. Client Credentials - For machine-to-machine communication

Features:
- PKCE support for enhanced security
- Token revocation endpoint
- Bearer token validation for protected resources
- Multi-tenant support with tenant isolation
- Scope-based access control

References:
- RFC 6749: OAuth 2.0 Authorization Framework
- RFC 7636: PKCE for OAuth Public Clients
- RFC 7009: Token Revocation
"""
import os
from authlib.integrations.flask_oauth2 import (
    AuthorizationServer,  # Main OAuth server implementation
    ResourceProtector,  # Validates tokens on protected endpoints
)
from authlib.integrations.sqla_oauth2 import (
    create_query_client_func,  # Helper to query OAuth clients from database
    create_save_token_func,  # Helper to save tokens to database
    create_revocation_endpoint,  # Creates token revocation endpoint
    create_bearer_token_validator,  # Validates Bearer tokens
)
from authlib.oauth2.rfc6749 import grants  # Grant type implementations
from authlib.oauth2.rfc7636 import CodeChallenge  # PKCE support
from werkzeug.security import gen_salt  # Generate secure random strings
from app import db
from models import User, OAuth2Client, OAuth2AuthorizationCode, OAuth2Token


# ==================== Helper Functions ====================
# Create query and save functions for Authlib integration with SQLAlchemy

# Query function: Fetches OAuth2Client from database by client_id
query_client = create_query_client_func(db.session, OAuth2Client)

# Custom save token function: Converts expires_in to expires_at timestamps
def save_token(token, request):
    """
    Save OAuth2Token to database with proper timestamp conversion.
    
    Authlib passes token data with 'expires_in' (seconds from now),
    but our model uses 'access_token_expires_at' (Unix timestamp).
    This function handles the conversion.
    
    Args:
        token: Dictionary with token data from Authlib
        request: OAuth request object with user and client info
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
        # Use configured refresh token lifetime (default 30 days)
        refresh_expires_in = request.client.get_allowed_scope('refresh_token_expires_in')
        if not refresh_expires_in:
            refresh_expires_in = 2592000  # 30 days in seconds
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


# ==================== Grant Type Implementations ====================

class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    """
    Authorization Code Grant with PKCE support.
    
    This is the most secure OAuth 2.0 flow for web applications:
    1. User is redirected to authorization endpoint
    2. User logs in and authorizes the client
    3. Server issues authorization code
    4. Client exchanges code for access token
    
    PKCE (Proof Key for Code Exchange) adds extra security:
    - Client generates code_verifier (random string)
    - Client sends code_challenge (hash of verifier) with auth request
    - Client sends code_verifier when exchanging code for token
    - Server verifies the verifier matches the challenge
    
    This prevents authorization code interception attacks.
    """
    # Supported authentication methods for token endpoint
    TOKEN_ENDPOINT_AUTH_METHODS = [
        'client_secret_basic',  # Client credentials in Authorization header (recommended)
        'client_secret_post',  # Client credentials in POST body
        'none',  # Public clients without secrets (requires PKCE)
    ]
    
    def save_authorization_code(self, code, request):
        """
        Save authorization code to database with tenant isolation.
        
        Called after user authorizes client. Stores code temporarily
        for later exchange to access token.
        
        Args:
            code: Generated authorization code string
            request: Authorization request object with user, client, and parameters
            
        Returns:
            OAuth2AuthorizationCode: Saved code instance
        """
        from tenant_context import TenantContext
        
        # Extract PKCE parameters if present
        code_challenge = request.data.get('code_challenge')
        code_challenge_method = request.data.get('code_challenge_method')
        nonce = request.data.get('nonce')  # For OpenID Connect
        
        # Get tenant ID from context or user
        tenant_id = TenantContext.get_tenant_id()
        if not tenant_id:
            tenant_id = request.user.tenant_id
        
        # Create and save authorization code
        auth_code = OAuth2AuthorizationCode(
            tenant_id=tenant_id,
            code=code,
            client_id=request.client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=request.user.id,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            nonce=nonce,
        )
        db.session.add(auth_code)
        db.session.commit()
        return auth_code
    
    def query_authorization_code(self, code, client):
        """
        Query authorization code from database.
        
        Validates that:
        1. Code exists
        2. Code belongs to the requesting client
        3. Code hasn't expired (10 minute lifetime)
        
        Args:
            code: Authorization code string
            client: OAuth2Client instance
            
        Returns:
            OAuth2AuthorizationCode if valid, None otherwise
        """
        auth_code = OAuth2AuthorizationCode.query.filter_by(
            code=code,
            client_id=client.client_id
        ).first()
        
        # Verify code exists and hasn't expired
        if auth_code and not auth_code.is_expired():
            return auth_code
        return None
    
    def delete_authorization_code(self, authorization_code):
        """
        Delete authorization code after use.
        
        Authorization codes are single-use. After being exchanged
        for an access token, they must be deleted to prevent reuse.
        
        Args:
            authorization_code: OAuth2AuthorizationCode to delete
        """
        db.session.delete(authorization_code)
        db.session.commit()
    
    def authenticate_user(self, authorization_code):
        """
        Get user associated with authorization code.
        
        Args:
            authorization_code: OAuth2AuthorizationCode instance
            
        Returns:
            User: User who authorized the code
        """
        return User.query.get(authorization_code.user_id)


class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    """
    Resource Owner Password Credentials Grant with tenant isolation.
    
    This grant type allows clients to directly exchange username/password
    for an access token. Use cases:
    - First-party mobile apps
    - Command-line tools
    - Highly trusted applications
    
    WARNING: Only use for trusted first-party applications. Third-party
    apps should NEVER have access to user passwords (use Authorization Code instead).
    
    Flow:
    1. User provides username and password to client
    2. Client sends credentials to token endpoint
    3. Server validates credentials within tenant context
    4. Server issues access token
    """
    
    def authenticate_user(self, username, password):
        """
        Authenticate user with username and password within tenant context.
        
        Validates:
        1. Tenant context is set (multi-tenant requirement)
        2. User exists in tenant
        3. Password is correct
        4. User account is active
        
        Args:
            username: User's username
            password: User's password (plain text)
            
        Returns:
            User: Authenticated user if valid, None otherwise
        """
        from tenant_context import TenantContext
        
        # Get current tenant from request context
        tenant = TenantContext.get_current_tenant()
        if not tenant:
            return None
        
        # Find user within tenant (username is unique per tenant)
        user = User.query.filter_by(
            tenant_id=tenant.id,
            username=username
        ).first()
        
        # Verify password and account status
        if user and user.check_password(password) and user.is_active:
            return user
        return None


class RefreshTokenGrant(grants.RefreshTokenGrant):
    """
    Refresh Token Grant.
    
    Allows clients to obtain new access tokens without re-authenticating
    the user. Flow:
    1. Access token expires
    2. Client sends refresh token to token endpoint
    3. Server validates refresh token
    4. Server issues new access token (and optionally new refresh token)
    5. Old refresh token is revoked
    
    Refresh tokens have longer lifetime (30 days default) than access
    tokens (1 hour default) for better user experience.
    """
    
    def authenticate_refresh_token(self, refresh_token):
        """
        Authenticate refresh token.
        
        Validates:
        1. Token exists in database
        2. Token hasn't expired
        3. Token hasn't been revoked
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            OAuth2Token: Token object if valid, None otherwise
        """
        token = OAuth2Token.query.filter_by(
            refresh_token=refresh_token
        ).first()
        
        # Check validity
        if token and not token.is_refresh_token_expired() and not token.revoked:
            return token
        return None
    
    def authenticate_user(self, credential):
        """
        Get user from token credential.
        
        Args:
            credential: OAuth2Token instance
            
        Returns:
            User: User who owns the token
        """
        return User.query.get(credential.user_id)
    
    def revoke_old_credential(self, credential):
        """
        Revoke old token when issuing new one.
        
        This is a security best practice - don't allow refresh token reuse.
        When a new token pair is issued, the old refresh token must be revoked.
        
        Args:
            credential: Old OAuth2Token to revoke
        """
        credential.revoked = True
        db.session.add(credential)
        db.session.commit()


class ClientCredentialsGrant(grants.ClientCredentialsGrant):
    """
    Client Credentials Grant.
    
    For machine-to-machine authentication without a user context.
    Use cases:
    - API-to-API communication
    - Backend services
    - Cron jobs
    - Microservices
    
    Flow:
    1. Client authenticates with client_id and client_secret
    2. Server issues access token
    3. No user is associated with the token
    
    Note: Tokens issued via this grant have no user_id (they represent
    the client application itself, not a user).
    """
    # Require client authentication (confidential clients only)
    TOKEN_ENDPOINT_AUTH_METHODS = [
        'client_secret_basic',  # Client credentials in Authorization header (recommended)
        'client_secret_post',  # Client credentials in POST body
    ]


def config_oauth(app):
    """
    Configure OAuth 2.0 server with all grant types and endpoints.
    
    This function:
    1. Creates authorization server instance
    2. Registers all supported grant types
    3. Creates token revocation endpoint
    4. Creates resource protector for validating tokens
    
    Args:
        app: Flask application instance
        
    Returns:
        tuple: (authorization_server, resource_protector)
    """
    
    # Create authorization server instance
    authorization_server = AuthorizationServer()
    
    # Initialize authorization server with Flask app and helper functions
    # query_client: How to find OAuth clients in database
    # save_token: How to save issued tokens to database
    authorization_server.init_app(app, query_client=query_client, save_token=save_token)
    
    # Register supported grant types
    # Each grant type handles a different OAuth 2.0 flow
    
    # Authorization Code flow (with optional PKCE)
    # Most secure flow for web/mobile apps
    authorization_server.register_grant(AuthorizationCodeGrant, [CodeChallenge(required=False)])
    
    # Password flow (for trusted first-party apps)
    authorization_server.register_grant(PasswordGrant)
    
    # Refresh Token flow (for renewing access tokens)
    authorization_server.register_grant(RefreshTokenGrant)
    
    # Client Credentials flow (for machine-to-machine)
    authorization_server.register_grant(ClientCredentialsGrant)
    
    # Create and register token revocation endpoint
    # Allows clients to revoke access/refresh tokens
    # Endpoint: POST /oauth/revoke
    revocation_cls = create_revocation_endpoint(db.session, OAuth2Token)
    authorization_server.register_endpoint(revocation_cls)
    
    # Create resource protector for validating Bearer tokens
    # This is used by @require_oauth() decorator in routes
    bearer_cls = create_bearer_token_validator(db.session, OAuth2Token)
    resource_protector = ResourceProtector()
    resource_protector.register_token_validator(bearer_cls())
    
    return authorization_server, resource_protector


def create_oauth_client(tenant_id, user_id, client_name, redirect_uris, grant_types, scope):
    """
    Helper function to create OAuth 2.0 client with tenant support.
    
    Generates secure random client_id and client_secret, then creates
    a new OAuth2Client in the database.
    
    Args:
        tenant_id: ID of tenant this client belongs to
        user_id: ID of user who owns this client
        client_name: Human-readable name for the client
        redirect_uris: List of allowed redirect URIs (for auth code flow)
        grant_types: List of allowed grant types (e.g., ['password', 'refresh_token'])
        scope: Space-separated string of allowed scopes
        
    Returns:
        OAuth2Client: Newly created client with credentials
    """
    # Generate secure random credentials
    client_id = gen_salt(24)  # 24-byte random string
    client_secret = gen_salt(48)  # 48-byte random string
    
    # Create client instance
    client = OAuth2Client(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        client_name=client_name,
        user_id=user_id,
        # Convert lists to space-separated strings (OAuth 2.0 convention)
        redirect_uris=' '.join(redirect_uris) if isinstance(redirect_uris, list) else redirect_uris,
        grant_types=' '.join(grant_types) if isinstance(grant_types, list) else grant_types,
        response_types='code',  # Support authorization code flow
        scope=scope,
        token_endpoint_auth_method='client_secret_basic',  # Use HTTP Basic Auth
    )
    
    # Save to database
    db.session.add(client)
    db.session.commit()
    
    return client
