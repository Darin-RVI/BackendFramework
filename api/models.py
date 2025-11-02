"""
Database Models for OAuth 2.0 with Multi-Tenant Support
"""
import time
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class Tenant(db.Model):
    """Tenant/Organization model for multi-tenancy"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    domain = db.Column(db.String(255), unique=True, nullable=True, index=True)
    
    # Tenant settings
    is_active = db.Column(db.Boolean, default=True)
    plan = db.Column(db.String(50), default='free')  # free, basic, premium, enterprise
    max_users = db.Column(db.Integer, default=10)
    
    # Metadata
    settings = db.Column(db.JSON, default={})
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Tenant {self.name}>'


class User(db.Model):
    """User model for authentication with tenant support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User role within tenant
    role = db.Column(db.String(50), default='user')  # user, admin, owner
    
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    is_active = db.Column(db.Boolean, default=True)
    
    # Unique constraint: username must be unique within tenant
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'username', name='uq_tenant_username'),
        db.UniqueConstraint('tenant_id', 'email', name='uq_tenant_email'),
    )
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify user password"""
        return check_password_hash(self.password_hash, password)
    
    def get_user_id(self):
        """Required by Authlib"""
        return self.id
    
    def __repr__(self):
        return f'<User {self.username}>'


class OAuth2Client(db.Model):
    """OAuth 2.0 Client Application with tenant support"""
    __tablename__ = 'oauth2_clients'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    client_id = db.Column(db.String(48), unique=True, nullable=False, index=True)
    client_secret = db.Column(db.String(120), nullable=True)
    client_name = db.Column(db.String(100), nullable=False)
    
    # Client metadata
    redirect_uris = db.Column(db.Text, nullable=True)
    token_endpoint_auth_method = db.Column(db.String(48), default='client_secret_basic')
    grant_types = db.Column(db.Text, nullable=True)
    response_types = db.Column(db.Text, nullable=True)
    scope = db.Column(db.Text, nullable=True)
    
    # Client info
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def get_client_id(self):
        return self.client_id
    
    def get_default_redirect_uri(self):
        if self.redirect_uris:
            return self.redirect_uris.split()[0]
        return ''
    
    def get_allowed_scope(self, scope):
        if not scope:
            return ''
        allowed = set(self.scope.split())
        return ' '.join([s for s in scope.split() if s in allowed])
    
    def check_redirect_uri(self, redirect_uri):
        if self.redirect_uris:
            return redirect_uri in self.redirect_uris.split()
        return False
    
    def has_client_secret(self):
        return bool(self.client_secret)
    
    def check_client_secret(self, client_secret):
        return self.client_secret == client_secret
    
    def check_token_endpoint_auth_method(self, method):
        return self.token_endpoint_auth_method == method
    
    def check_response_type(self, response_type):
        if self.response_types:
            return response_type in self.response_types.split()
        return False
    
    def check_grant_type(self, grant_type):
        if self.grant_types:
            return grant_type in self.grant_types.split()
        return False


class OAuth2AuthorizationCode(db.Model):
    """OAuth 2.0 Authorization Code with tenant isolation"""
    __tablename__ = 'oauth2_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    code = db.Column(db.String(120), unique=True, nullable=False)
    client_id = db.Column(db.String(48), nullable=False)
    redirect_uri = db.Column(db.Text, default='')
    response_type = db.Column(db.Text, default='')
    scope = db.Column(db.Text, default='')
    nonce = db.Column(db.Text)
    auth_time = db.Column(db.Integer, nullable=False, default=lambda: int(time.time()))
    code_challenge = db.Column(db.Text)
    code_challenge_method = db.Column(db.String(48))
    
    def is_expired(self):
        return self.auth_time + 600 < time.time()
    
    def get_redirect_uri(self):
        return self.redirect_uri
    
    def get_scope(self):
        return self.scope
    
    def get_auth_time(self):
        return self.auth_time
    
    def get_nonce(self):
        return self.nonce


class OAuth2Token(db.Model):
    """OAuth 2.0 Access and Refresh Tokens with tenant isolation"""
    __tablename__ = 'oauth2_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    client_id = db.Column(db.String(48), nullable=False)
    token_type = db.Column(db.String(40), default='Bearer')
    access_token = db.Column(db.String(255), unique=True, nullable=False)
    refresh_token = db.Column(db.String(255), unique=True)
    scope = db.Column(db.Text, default='')
    revoked = db.Column(db.Boolean, default=False)
    issued_at = db.Column(db.Integer, nullable=False, default=lambda: int(time.time()))
    access_token_expires_at = db.Column(db.Integer, nullable=False)
    refresh_token_expires_at = db.Column(db.Integer)
    
    def is_expired(self):
        return self.access_token_expires_at < time.time()
    
    def is_refresh_token_expired(self):
        if self.refresh_token_expires_at:
            return self.refresh_token_expires_at < time.time()
        return True
    
    def get_client_id(self):
        return self.client_id
    
    def get_scope(self):
        return self.scope
    
    def get_expires_in(self):
        return self.access_token_expires_at - int(time.time())
    
    def is_revoked(self):
        return self.revoked
    
    def check_client(self, client):
        return self.client_id == client.get_client_id()
