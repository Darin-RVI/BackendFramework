"""
API Routes with OAuth 2.0 Protection
"""
from flask import Blueprint, jsonify, request, current_app
from functools import wraps

api_bp = Blueprint('api', __name__)


def require_oauth(scope=None):
    """Decorator to require OAuth 2.0 authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Validate access token
            token = current_app.resource_protector.validate_request(scopes=scope)
            # Add token to kwargs for use in route
            kwargs['token'] = token
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@api_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint (public)"""
    return jsonify({'message': 'pong'}), 200


@api_bp.route('/status', methods=['GET'])
def status():
    """API status endpoint (public)"""
    return jsonify({
        'status': 'running',
        'api_version': '2.0.0',
        'auth_type': 'OAuth 2.0'
    }), 200


@api_bp.route('/protected', methods=['GET'])
@require_oauth()
def protected(token):
    """Protected endpoint - requires valid access token"""
    from models import User
    
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
    """Admin-only endpoint - requires 'admin' scope"""
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
    """Get current user profile - requires 'profile' scope"""
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


# Add your API routes here
# Example protected endpoint:
# @api_bp.route('/data', methods=['GET'])
# @require_oauth(scope='read')
# def get_data(token):
#     return jsonify({'data': []}), 200
