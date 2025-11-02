"""
OAuth 2.0 Server Configuration
"""
import os
from authlib.integrations.flask_oauth2 import (
    AuthorizationServer,
    ResourceProtector,
)
from authlib.integrations.sqla_oauth2 import (
    create_query_client_func,
    create_save_token_func,
    create_revocation_endpoint,
    create_bearer_token_validator,
)
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7636 import CodeChallenge
from werkzeug.security import gen_salt
from app import db
from models import User, OAuth2Client, OAuth2AuthorizationCode, OAuth2Token


# Query functions
query_client = create_query_client_func(db.session, OAuth2Client)
save_token = create_save_token_func(db.session, OAuth2Token)


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    """Authorization Code Grant with PKCE support"""
    TOKEN_ENDPOINT_AUTH_METHODS = [
        'client_secret_basic',
        'client_secret_post',
        'none',
    ]
    
    def save_authorization_code(self, code, request):
        """Save authorization code to database with tenant isolation"""
        from tenant_context import TenantContext
        
        code_challenge = request.data.get('code_challenge')
        code_challenge_method = request.data.get('code_challenge_method')
        nonce = request.data.get('nonce')
        
        tenant_id = TenantContext.get_tenant_id()
        if not tenant_id:
            tenant_id = request.user.tenant_id
        
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
        """Query authorization code from database"""
        auth_code = OAuth2AuthorizationCode.query.filter_by(
            code=code,
            client_id=client.client_id
        ).first()
        if auth_code and not auth_code.is_expired():
            return auth_code
        return None
    
    def delete_authorization_code(self, authorization_code):
        """Delete authorization code after use"""
        db.session.delete(authorization_code)
        db.session.commit()
    
    def authenticate_user(self, authorization_code):
        """Get user associated with authorization code"""
        return User.query.get(authorization_code.user_id)


class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    """Resource Owner Password Credentials Grant with tenant isolation"""
    
    def authenticate_user(self, username, password):
        """Authenticate user with username and password within tenant context"""
        from tenant_context import TenantContext
        
        tenant = TenantContext.get_current_tenant()
        if not tenant:
            return None
        
        user = User.query.filter_by(
            tenant_id=tenant.id,
            username=username
        ).first()
        
        if user and user.check_password(password) and user.is_active:
            return user
        return None


class RefreshTokenGrant(grants.RefreshTokenGrant):
    """Refresh Token Grant"""
    
    def authenticate_refresh_token(self, refresh_token):
        """Authenticate refresh token"""
        token = OAuth2Token.query.filter_by(
            refresh_token=refresh_token
        ).first()
        if token and not token.is_refresh_token_expired() and not token.revoked:
            return token
        return None
    
    def authenticate_user(self, credential):
        """Get user from token"""
        return User.query.get(credential.user_id)
    
    def revoke_old_credential(self, credential):
        """Revoke old token when issuing new one"""
        credential.revoked = True
        db.session.add(credential)
        db.session.commit()


class ClientCredentialsGrant(grants.ClientCredentialsGrant):
    """Client Credentials Grant"""
    TOKEN_ENDPOINT_AUTH_METHODS = [
        'client_secret_basic',
        'client_secret_post',
    ]


def config_oauth(app):
    """Configure OAuth 2.0 server"""
    
    # Create authorization server
    authorization_server = AuthorizationServer()
    
    # Initialize authorization server
    authorization_server.init_app(app, query_client=query_client, save_token=save_token)
    
    # Register supported grant types
    authorization_server.register_grant(AuthorizationCodeGrant, [CodeChallenge(required=False)])
    authorization_server.register_grant(PasswordGrant)
    authorization_server.register_grant(RefreshTokenGrant)
    authorization_server.register_grant(ClientCredentialsGrant)
    
    # Create revocation endpoint
    revocation_cls = create_revocation_endpoint(db.session, OAuth2Token)
    authorization_server.register_endpoint(revocation_cls)
    
    # Create resource protector
    bearer_cls = create_bearer_token_validator(db.session, OAuth2Token)
    resource_protector = ResourceProtector()
    resource_protector.register_token_validator(bearer_cls())
    
    return authorization_server, resource_protector


def create_oauth_client(tenant_id, user_id, client_name, redirect_uris, grant_types, scope):
    """Helper function to create OAuth 2.0 client with tenant support"""
    client_id = gen_salt(24)
    client_secret = gen_salt(48)
    
    client = OAuth2Client(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        client_name=client_name,
        user_id=user_id,
        redirect_uris=' '.join(redirect_uris) if isinstance(redirect_uris, list) else redirect_uris,
        grant_types=' '.join(grant_types) if isinstance(grant_types, list) else grant_types,
        response_types='code',
        scope=scope,
        token_endpoint_auth_method='client_secret_basic',
    )
    
    db.session.add(client)
    db.session.commit()
    
    return client
