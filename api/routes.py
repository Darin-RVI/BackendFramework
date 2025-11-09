"""
API Routes with OAuth 2.0 Protection

This module defines protected API endpoints that require OAuth 2.0 authentication.
All routes in this blueprint demonstrate different levels of access control:

1. Public endpoints - No authentication required
2. Protected endpoints - Valid access token required
3. Scope-protected endpoints - Specific scopes required (e.g., admin, profile)

Authentication Flow:
1. Client obtains access token from /oauth/token
2. Client includes token in Authorization header: "Bearer <token>"
3. @require_oauth() decorator validates token before allowing access
4. Token object (with user_id, client_id, scope) passed to route function

Scope-Based Access Control:
- No scope: Any valid token grants access
- Specific scope (e.g., 'admin'): Token must include that scope
- Multiple scopes: Can check for multiple required scopes

Best Practices:
- Always use HTTPS in production to protect Bearer tokens
- Use specific scopes for different resource access levels
- Set appropriate token expiration times
- Log access attempts for security auditing
"""
from flask import Blueprint, jsonify, request, current_app
from functools import wraps

# Create blueprint for API routes
# All routes in this blueprint will be prefixed with /api (configured in app.py)
api_bp = Blueprint('api', __name__)


def require_oauth(scope=None):
    """
    Decorator to require OAuth 2.0 authentication for routes.
    
    This decorator validates the Bearer token in the Authorization header
    and optionally checks if required scopes are present.
    
    Args:
        scope: Optional scope string or list of scopes required
               - None: Any valid token is accepted
               - 'read': Token must have 'read' scope
               - ['read', 'write']: Token must have both scopes
    
    Returns:
        Decorator function that validates tokens
        
    Usage:
        # Any valid token
        @require_oauth()
        def protected_route(token):
            pass
        
        # Specific scope required
        @require_oauth(scope='admin')
        def admin_only(token):
            pass
        
        # Multiple scopes required
        @require_oauth(scope=['read', 'write'])
        def full_access(token):
            pass
    
    Error Responses:
        401: Missing or invalid token
        403: Valid token but insufficient scope
    """
    # Return the Authlib resource_protector decorator directly
    # It handles token validation and scope checking
    return current_app.resource_protector(scope)


# ==================== Public Endpoints ====================
# These endpoints don't require authentication

@api_bp.route('/ping', methods=['GET'])
def ping():
    """
    Simple ping endpoint for health checks.
    
    Public endpoint - no authentication required.
    Useful for monitoring tools and load balancers to check if API is responsive.
    
    Returns:
        JSON: Simple pong message with 200 status
        
    Example:
        curl http://localhost:8080/api/ping
        # Response: {"message": "pong"}
    """
    return jsonify({'message': 'pong'}), 200


@api_bp.route('/status', methods=['GET'])
def status():
    """
    API status endpoint with version information.
    
    Public endpoint - no authentication required.
    Returns API health status and metadata for monitoring and discovery.
    
    Returns:
        JSON: Status information including version and auth type
        
    Example:
        curl http://localhost:8080/api/status
        # Response: {
        #     "status": "running",
        #     "api_version": "2.0.0",
        #     "auth_type": "OAuth 2.0"
        # }
    """
    return jsonify({
        'status': 'running',
        'api_version': '2.0.0',
        'auth_type': 'OAuth 2.0'
    }), 200


# ==================== Protected Endpoints ====================
# These endpoints require valid OAuth 2.0 access tokens

@api_bp.route('/protected', methods=['GET'])
@require_oauth()
def protected(token):
    """
    Protected endpoint requiring valid access token.
    
    Demonstrates basic OAuth 2.0 protection. Any valid access token
    grants access regardless of scope.
    
    Args:
        token: OAuth2Token object injected by @require_oauth() decorator
    
    Returns:
        JSON: Access granted message with user and token details
        
    Example:
        curl -H "Authorization: Bearer <your_access_token>" \\
             http://localhost:8080/api/protected
        
        # Response: {
        #     "message": "Access granted to protected resource",
        #     "user": "john_doe",
        #     "client_id": "abc123",
        #     "scope": "read write"
        # }
    """
    from models import User
    
    # Get user associated with token (may be None for client_credentials grant)
    user = User.query.get(token.user_id) if token.user_id else None
    
    return jsonify({
        'message': 'Access granted to protected resource',
        'user': user.username if user else None,
        'client_id': token.client_id,
        'scope': token.scope
    }), 200


@api_bp.route('/admin', methods=['GET'])
@require_oauth(scope='admin')
def admin_only(token):
    """
    Admin-only endpoint requiring 'admin' scope.
    
    Demonstrates scope-based access control. Token must explicitly
    include 'admin' scope to access this endpoint.
    
    Use Cases:
    - Administrative operations
    - Sensitive data access
    - System configuration endpoints
    
    Args:
        token: OAuth2Token object with validated 'admin' scope
    
    Returns:
        JSON: Access granted message for admin resource
        
    Error Responses:
        403: Token is valid but lacks 'admin' scope
        
    Example:
        # Get token with admin scope
        curl -X POST http://localhost:8080/oauth/token \\
             -d "grant_type=password" \\
             -d "username=admin" \\
             -d "password=secret" \\
             -d "scope=read write admin" \\
             -d "client_id=..." \\
             -d "client_secret=..."
        
        # Use token to access admin endpoint
        curl -H "Authorization: Bearer <admin_token>" \\
             http://localhost:8080/api/admin
    """
    from models import User
    
    user = User.query.get(token.user_id) if token.user_id else None
    
    return jsonify({
        'message': 'Access granted to admin resource',
        'user': user.username if user else None,
        'scope': token.scope
    }), 200


@api_bp.route('/users/me', methods=['GET'])
@require_oauth(scope='profile')
def get_current_user(token):
    """
    Get current authenticated user's profile.
    
    Requires 'profile' scope to access user information.
    Returns profile data for the user associated with the access token.
    
    Args:
        token: OAuth2Token object with 'profile' scope
    
    Returns:
        JSON: User profile information
        
    Error Responses:
        404: User not found (shouldn't happen with valid token)
        403: Token lacks 'profile' scope
        
    Example:
        curl -H "Authorization: Bearer <token_with_profile_scope>" \\
             http://localhost:8080/api/users/me
        
        # Response: {
        #     "id": 123,
        #     "username": "john_doe",
        #     "email": "john@example.com",
        #     "created_at": "2024-01-15T10:30:00",
        #     "is_active": true
        # }
    """
    from models import User
    
    user = User.query.get(token.user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'is_active': user.is_active
    }), 200


# ==================== Add Your Custom API Routes Below ====================
# Template for adding new protected endpoints:
#
# @api_bp.route('/your-endpoint', methods=['GET', 'POST'])
# @require_oauth(scope='your_scope')  # Optional: specify required scope
# def your_endpoint(token):
#     """
#     Your endpoint description.
#     
#     Args:
#         token: OAuth2Token object with validated access
#     
#     Returns:
#         JSON: Your response data
#     """
#     from models import User
#     
#     # Get user if needed
#     user = User.query.get(token.user_id) if token.user_id else None
#     
#     # Your business logic here
#     data = {'result': 'success'}
#     
#     return jsonify(data), 200

# Example: Protected data endpoint
# @api_bp.route('/data', methods=['GET'])
# @require_oauth(scope='read')
# def get_data(token):
#     """Get data that requires 'read' scope"""
#     return jsonify({'data': []}), 200
