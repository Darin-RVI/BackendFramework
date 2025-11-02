"""
OAuth 2.0 Authentication Routes
"""
import time
from flask import Blueprint, request, jsonify, session, render_template_string
from werkzeug.security import gen_salt
from app import db
from models import User, OAuth2Client
from oauth2 import create_oauth_client
from flask import current_app

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user in a tenant
    
    Requires tenant context (header, subdomain, or path)
    """
    from tenant_context import TenantContext, check_tenant_limits
    
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({
            'error': 'Tenant not identified',
            'message': 'Please specify tenant via X-Tenant-Slug header, subdomain, or path'
        }), 400
    
    # Check tenant limits
    within_limits, error_msg = check_tenant_limits(tenant)
    if not within_limits:
        return jsonify({'error': error_msg}), 403
    
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists in this tenant
    if User.query.filter_by(tenant_id=tenant.id, username=data['username']).first():
        return jsonify({'error': 'Username already exists in this tenant'}), 400
    
    if User.query.filter_by(tenant_id=tenant.id, email=data['email']).first():
        return jsonify({'error': 'Email already exists in this tenant'}), 400
    
    # Create new user
    user = User(
        tenant_id=tenant.id,
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user')
    )
    user.set_password(data['password'])
    
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
    """User login endpoint (for session-based auth)
    
    Requires tenant context
    """
    from tenant_context import TenantContext, validate_tenant_access
    
    tenant = TenantContext.get_current_tenant()
    if not tenant:
        return jsonify({
            'error': 'Tenant not identified',
            'message': 'Please specify tenant via X-Tenant-Slug header, subdomain, or path'
        }), 400
    
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing credentials'}), 400
    
    # Find user in tenant
    user = User.query.filter_by(
        tenant_id=tenant.id,
        username=data['username']
    ).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403
    
    # Validate tenant access
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


@auth_bp.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """OAuth 2.0 Authorization Endpoint"""
    
    # Get current user from session
    user_id = session.get('user_id')
    
    if request.method == 'GET':
        # Check if user is logged in
        if not user_id:
            return jsonify({
                'error': 'unauthorized',
                'error_description': 'User must be logged in'
            }), 401
        
        # Get authorization request
        try:
            grant = current_app.authorization_server.get_consent_grant(end_user=User.query.get(user_id))
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
        # For demo purposes, auto-approve (in production, show consent screen)
        return jsonify({
            'client_name': grant.client.client_name,
            'scope': grant.request.scope,
            'redirect_uri': grant.request.redirect_uri,
            'state': grant.request.state
        }), 200
    
    # POST - User approved the authorization
    if not user_id:
        return jsonify({'error': 'unauthorized'}), 401
    
    user = User.query.get(user_id)
    
    # Check if user granted permission
    if request.form.get('confirm') == 'no':
        return jsonify({'error': 'access_denied'}), 403
    
    return current_app.authorization_server.create_authorization_response(grant_user=user)


@auth_bp.route('/token', methods=['POST'])
def issue_token():
    """OAuth 2.0 Token Endpoint
    
    Supports multiple grant types:
    - authorization_code
    - password (Resource Owner Password Credentials)
    - refresh_token
    - client_credentials
    """
    return current_app.authorization_server.create_token_response()


@auth_bp.route('/revoke', methods=['POST'])
def revoke_token():
    """OAuth 2.0 Token Revocation Endpoint"""
    return current_app.authorization_server.create_endpoint_response('revocation')


@auth_bp.route('/client/register', methods=['POST'])
def register_client():
    """Register a new OAuth 2.0 client application
    
    Requires authentication and tenant context
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
    
    # Validate tenant access
    if not validate_tenant_access(user, tenant):
        return jsonify({'error': 'Access denied to this tenant'}), 403
    
    data = request.get_json()
    
    if not data or not data.get('client_name'):
        return jsonify({'error': 'client_name is required'}), 400
    
    # Default values
    redirect_uris = data.get('redirect_uris', ['http://localhost:3000/callback'])
    grant_types = data.get('grant_types', ['authorization_code', 'refresh_token'])
    scope = data.get('scope', 'read write')
    
    # Create client
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
    """List OAuth 2.0 clients for authenticated user"""
    
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


@auth_bp.route('/userinfo', methods=['GET'])
def userinfo():
    """OAuth 2.0 UserInfo Endpoint (OpenID Connect compatible)
    
    Requires valid access token in Authorization header
    """
    # Validate access token
    token = current_app.resource_protector.validate_request(scopes=None)
    
    user = User.query.get(token.user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Return user information based on scope
    userinfo = {
        'sub': str(user.id),
        'username': user.username,
    }
    
    # Include email if scope permits
    if token.scope and 'email' in token.scope:
        userinfo['email'] = user.email
    
    # Include profile info if scope permits
    if token.scope and 'profile' in token.scope:
        userinfo['created_at'] = user.created_at.isoformat() if user.created_at else None
    
    return jsonify(userinfo), 200


@auth_bp.route('/introspect', methods=['POST'])
def introspect_token():
    """Token Introspection Endpoint (RFC 7662)
    
    Allows clients to check token validity and metadata
    """
    from models import OAuth2Token
    
    token_string = request.form.get('token')
    if not token_string:
        return jsonify({'active': False}), 200
    
    token = OAuth2Token.query.filter_by(access_token=token_string).first()
    
    if not token or token.is_expired() or token.revoked:
        return jsonify({'active': False}), 200
    
    return jsonify({
        'active': True,
        'client_id': token.client_id,
        'username': User.query.get(token.user_id).username if token.user_id else None,
        'scope': token.scope,
        'exp': token.access_token_expires_at,
        'iat': token.issued_at,
        'token_type': token.token_type
    }), 200
