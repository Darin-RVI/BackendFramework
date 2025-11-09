"""
Database Models for OAuth 2.0 with Multi-Tenant Support

This module defines all database models for the application:
- Tenant: Organization/customer for multi-tenancy
- User: User accounts with tenant isolation
- OAuth2Client: OAuth 2.0 client applications
- OAuth2AuthorizationCode: Authorization codes for auth code flow
- OAuth2Token: Access and refresh tokens

All models support multi-tenancy with tenant_id foreign keys and proper isolation.
"""
import time
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Tenant(db.Model):
    """
    Tenant/Organization model for multi-tenancy.
    
    Represents a customer organization in the system. Each tenant has:
    - Isolated data and users
    - Unique identifier (slug) for routing
    - Optional custom domain
    - Subscription plan and limits
    - Settings for customization
    
    All other models reference tenant_id to ensure data isolation.
    """
    __tablename__ = 'tenants'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Tenant identification
    name = db.Column(db.String(100), nullable=False)  # Display name (e.g., "Acme Corporation")
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)  # URL-safe identifier (e.g., "acme")
    domain = db.Column(db.String(255), unique=True, nullable=True, index=True)  # Optional custom domain (e.g., "acme.com")
    
    # Tenant settings and limits
    is_active = db.Column(db.Boolean, default=True)  # Enable/disable tenant access
    plan = db.Column(db.String(50), default='free')  # Subscription tier: free, basic, premium, enterprise
    max_users = db.Column(db.Integer, default=10)  # Maximum users allowed based on plan
    
    # Metadata and customization
    settings = db.Column(db.JSON, default={})  # JSON field for flexible tenant-specific settings
    created_at = db.Column(db.DateTime, default=db.func.now())  # Tenant creation timestamp
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())  # Last update timestamp
    
    # Relationships
    # One-to-many: A tenant has many users
    # cascade='all, delete-orphan' ensures users are deleted when tenant is deleted
    users = db.relationship('User', backref='tenant', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        """String representation of Tenant for debugging"""
        return f'<Tenant {self.name}>'


class User(db.Model):
    """
    User model for authentication with tenant support.
    
    Represents individual users within a tenant. Features:
    - Username and email must be unique WITHIN each tenant
    - Password hashing with Werkzeug for security
    - Role-based permissions (user, admin, owner)
    - Active status flag for enabling/disabling accounts
    
    Users are always scoped to a specific tenant for data isolation.
    """
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Tenant association (foreign key with cascade delete)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # User identification (unique within tenant, not globally)
    username = db.Column(db.String(80), nullable=False, index=True)  # Username for login
    email = db.Column(db.String(120), nullable=False, index=True)  # Email address
    password_hash = db.Column(db.String(255), nullable=False)  # Hashed password (never store plain text!)
    
    # User role within tenant (determines permissions)
    # - user: Standard user with basic access
    # - admin: Can manage users and resources
    # - owner: Full tenant management including billing
    role = db.Column(db.String(50), default='user')
    
    # Timestamps and status
    created_at = db.Column(db.DateTime, default=db.func.now())  # Account creation date
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())  # Last update
    is_active = db.Column(db.Boolean, default=True)  # Enable/disable user account
    
    # Unique constraints: username and email are unique PER TENANT (not globally)
    # This allows different tenants to have users with same username/email
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'username', name='uq_tenant_username'),
        db.UniqueConstraint('tenant_id', 'email', name='uq_tenant_email'),
    )
    
    def set_password(self, password):
        """
        Hash and set user password.
        
        Uses Werkzeug's secure password hashing (pbkdf2:sha256 by default).
        Never stores passwords in plain text.
        
        Args:
            password: Plain text password to hash
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify user password against stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def get_user_id(self):
        """
        Get user ID (required by Authlib OAuth implementation).
        
        Returns:
            int: User's primary key ID
        """
        return self.id
    
    def __repr__(self):
        """String representation of User for debugging"""
        return f'<User {self.username}>'


class OAuth2Client(db.Model):
    """
    OAuth 2.0 Client Application with tenant support.
    
    Represents an application that can authenticate users via OAuth 2.0.
    Each client belongs to a tenant and has:
    - Unique client_id and client_secret for authentication
    - Allowed grant types (authorization_code, password, refresh_token, etc.)
    - Allowed redirect URIs for authorization code flow
    - Allowed scopes for access control
    
    Clients are tenant-isolated to prevent cross-tenant authentication.
    """
    __tablename__ = 'oauth2_clients'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Tenant association (clients belong to specific tenants)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Client credentials
    client_id = db.Column(db.String(48), unique=True, nullable=False, index=True)  # Public client identifier
    client_secret = db.Column(db.String(120), nullable=True)  # Secret key (optional for public clients)
    client_name = db.Column(db.String(100), nullable=False)  # Human-readable client name
    
    # Client OAuth 2.0 configuration
    redirect_uris = db.Column(db.Text, nullable=True)  # Space-separated list of allowed redirect URIs
    token_endpoint_auth_method = db.Column(db.String(48), default='client_secret_basic')  # How client authenticates
    grant_types = db.Column(db.Text, nullable=True)  # Space-separated grant types (authorization_code, password, etc.)
    response_types = db.Column(db.Text, nullable=True)  # Space-separated response types (code, token)
    scope = db.Column(db.Text, nullable=True)  # Space-separated list of allowed scopes
    
    # Client ownership and metadata
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  # User who created this client
    created_at = db.Column(db.DateTime, default=db.func.now())  # Client registration date
    
    def get_client_id(self):
        """Get client ID (required by Authlib)"""
        return self.client_id
    
    def get_default_redirect_uri(self):
        """
        Get default redirect URI (first in list).
        
        Returns:
            str: Default redirect URI or empty string if none configured
        """
        if self.redirect_uris:
            return self.redirect_uris.split()[0]
        return ''
    
    def get_allowed_scope(self, scope):
        """
        Filter requested scopes to only those allowed for this client.
        
        Args:
            scope: Space-separated string of requested scopes
            
        Returns:
            str: Space-separated string of allowed scopes
        """
        if not scope:
            return ''
        allowed = set(self.scope.split())
        return ' '.join([s for s in scope.split() if s in allowed])
    
    def check_redirect_uri(self, redirect_uri):
        """
        Validate redirect URI is in client's allowed list.
        
        Args:
            redirect_uri: URI to validate
            
        Returns:
            bool: True if URI is allowed, False otherwise
        """
        if self.redirect_uris:
            return redirect_uri in self.redirect_uris.split()
        return False
    
    def has_client_secret(self):
        """Check if client has a secret (confidential client)"""
        return bool(self.client_secret)
    
    def check_client_secret(self, client_secret):
        """
        Verify client secret.
        
        Args:
            client_secret: Secret to verify
            
        Returns:
            bool: True if secret matches, False otherwise
        """
        return self.client_secret == client_secret
    
    def check_token_endpoint_auth_method(self, method):
        """Check if authentication method is supported"""
        return self.token_endpoint_auth_method == method
    
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
    
    def check_response_type(self, response_type):
        """Check if response type is allowed for this client"""
        if self.response_types:
            return response_type in self.response_types.split()
        return False
    
    def check_grant_type(self, grant_type):
        """Check if grant type is allowed for this client"""
        if self.grant_types:
            return grant_type in self.grant_types.split()
        return False


class OAuth2AuthorizationCode(db.Model):
    """
    OAuth 2.0 Authorization Code with tenant isolation.
    
    Represents temporary authorization codes issued during the authorization
    code flow. Features:
    - Short-lived (10 minutes default)
    - One-time use (deleted after token exchange)
    - PKCE support for enhanced security
    - Tenant-scoped for isolation
    
    Flow: User authorizes -> Code issued -> Client exchanges code for token
    """
    __tablename__ = 'oauth2_codes'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Tenant association
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Authorization code details
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  # User who authorized
    code = db.Column(db.String(120), unique=True, nullable=False)  # The authorization code itself
    client_id = db.Column(db.String(48), nullable=False)  # Client requesting authorization
    
    # OAuth 2.0 parameters
    redirect_uri = db.Column(db.Text, default='')  # Where to redirect after authorization
    response_type = db.Column(db.Text, default='')  # Response type from request
    scope = db.Column(db.Text, default='')  # Requested scopes
    nonce = db.Column(db.Text)  # Nonce for OpenID Connect
    auth_time = db.Column(db.Integer, nullable=False, default=lambda: int(time.time()))  # When code was issued
    
    # PKCE (Proof Key for Code Exchange) for enhanced security
    code_challenge = db.Column(db.Text)  # Hashed code verifier
    code_challenge_method = db.Column(db.String(48))  # Hash method (plain or S256)
    
    def is_expired(self):
        """
        Check if authorization code has expired.
        
        Codes expire after 10 minutes (600 seconds) by default.
        
        Returns:
            bool: True if expired, False if still valid
        """
        return self.auth_time + 600 < time.time()
    
    def get_redirect_uri(self):
        """Get redirect URI (required by Authlib)"""
        return self.redirect_uri
    
    def get_scope(self):
        """Get authorized scopes (required by Authlib)"""
        return self.scope
    
    def get_auth_time(self):
        """Get authorization timestamp (required by Authlib)"""
        return self.auth_time
    
    def get_nonce(self):
        """Get nonce for OpenID Connect (required by Authlib)"""
        return self.nonce


class OAuth2Token(db.Model):
    """
    OAuth 2.0 Access and Refresh Tokens with tenant isolation.
    
    Represents issued access tokens and refresh tokens. Features:
    - Access tokens: Short-lived (1 hour default), used for API access
    - Refresh tokens: Long-lived (30 days default), used to get new access tokens
    - Token revocation support
    - Tenant-scoped for isolation
    - Scope-based access control
    
    Tokens are the primary authentication mechanism for API requests.
    """
    __tablename__ = 'oauth2_tokens'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Tenant association
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Token ownership
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  # User who owns token
    client_id = db.Column(db.String(48), nullable=False)  # Client that requested token
    
    # Token details
    token_type = db.Column(db.String(40), default='Bearer')  # Token type (always Bearer for this implementation)
    access_token = db.Column(db.String(255), unique=True, nullable=False)  # The access token itself
    refresh_token = db.Column(db.String(255), unique=True)  # Optional refresh token
    scope = db.Column(db.Text, default='')  # Granted scopes
    revoked = db.Column(db.Boolean, default=False)  # Whether token has been revoked
    
    # Token timestamps
    issued_at = db.Column(db.Integer, nullable=False, default=lambda: int(time.time()))  # When token was issued
    access_token_expires_at = db.Column(db.Integer, nullable=False)  # Access token expiration (Unix timestamp)
    refresh_token_expires_at = db.Column(db.Integer)  # Refresh token expiration (Unix timestamp)
    
    def is_expired(self):
        """
        Check if access token has expired.
        
        Returns:
            bool: True if access token is expired, False otherwise
        """
        return self.access_token_expires_at < time.time()
    
    def is_refresh_token_expired(self):
        """
        Check if refresh token has expired.
        
        Returns:
            bool: True if refresh token is expired or doesn't exist, False otherwise
        """
        if self.refresh_token_expires_at:
            return self.refresh_token_expires_at < time.time()
        return True
    
    def get_client_id(self):
        """Get client ID (required by Authlib)"""
        return self.client_id
    
    def get_scope(self):
        """Get token scopes (required by Authlib)"""
        return self.scope
    
    def get_expires_in(self):
        """
        Get seconds until access token expires.
        
        Returns:
            int: Seconds remaining until expiration
        """
        return self.access_token_expires_at - int(time.time())
    
    def is_revoked(self):
        """Check if token has been revoked"""
        return self.revoked
    
    def check_client(self, client):
        """
        Verify token belongs to specified client.
        
        Args:
            client: OAuth2Client instance
            
        Returns:
            bool: True if token belongs to client, False otherwise
        """
        return self.client_id == client.get_client_id()
