"""
Tenant Management Routes
"""
from flask import Blueprint, request, jsonify, session
from app import db
from models import Tenant, User
from tenant_context import (
    create_tenant, 
    TenantContext, 
    require_tenant,
    check_tenant_limits,
    get_tenant_stats,
    validate_tenant_access
)
import re

tenant_bp = Blueprint('tenant', __name__)


def validate_slug(slug):
    """Validate tenant slug format"""
    # Slug should be lowercase, alphanumeric, hyphens only
    return bool(re.match(r'^[a-z0-9-]+$', slug))


@tenant_bp.route('/register', methods=['POST'])
def register_tenant():
    """Register a new tenant organization
    
    Creates a new tenant and its owner/admin user
    """
    data = request.get_json()
    
    # Validate required fields
    required = ['tenant_name', 'tenant_slug', 'admin_username', 'admin_email', 'admin_password']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields', 'required': required}), 400
    
    # Validate slug format
    slug = data['tenant_slug'].lower()
    if not validate_slug(slug):
        return jsonify({'error': 'Invalid slug format. Use lowercase letters, numbers, and hyphens only'}), 400
    
    # Check if tenant slug already exists
    if Tenant.query.filter_by(slug=slug).first():
        return jsonify({'error': 'Tenant slug already exists'}), 400
    
    # Check if domain is provided and unique
    domain = data.get('domain')
    if domain:
        if Tenant.query.filter_by(domain=domain).first():
            return jsonify({'error': 'Domain already registered'}), 400
    
    try:
        # Create tenant and admin user
        tenant, admin_user = create_tenant(
            name=data['tenant_name'],
            slug=slug,
            admin_username=data['admin_username'],
            admin_email=data['admin_email'],
            admin_password=data['admin_password'],
            domain=domain,
            plan=data.get('plan', 'free')
        )
        
        return jsonify({
            'message': 'Tenant registered successfully',
            'tenant': {
                'id': tenant.id,
                'name': tenant.name,
                'slug': tenant.slug,
                'domain': tenant.domain,
                'plan': tenant.plan
            },
            'admin': {
                'id': admin_user.id,
                'username': admin_user.username,
                'email': admin_user.email,
                'role': admin_user.role
            },
            'access_info': {
                'subdomain': f'{slug}.yourdomain.com',
                'header': f'X-Tenant-Slug: {slug}',
                'path': f'/tenants/{slug}/...'
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create tenant', 'details': str(e)}), 500


@tenant_bp.route('/info', methods=['GET'])
@require_tenant
def get_tenant_info(tenant):
    """Get current tenant information"""
    
    # Check if user is authenticated and belongs to tenant
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if not validate_tenant_access(user, tenant):
            return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': tenant.id,
        'name': tenant.name,
        'slug': tenant.slug,
        'domain': tenant.domain,
        'plan': tenant.plan,
        'max_users': tenant.max_users,
        'is_active': tenant.is_active,
        'created_at': tenant.created_at.isoformat() if tenant.created_at else None
    }), 200


@tenant_bp.route('/stats', methods=['GET'])
@require_tenant
def get_tenant_statistics(tenant):
    """Get tenant usage statistics
    
    Requires admin role
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not validate_tenant_access(user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    if user.role not in ['admin', 'owner']:
        return jsonify({'error': 'Admin access required'}), 403
    
    stats = get_tenant_stats(tenant)
    
    return jsonify(stats), 200


@tenant_bp.route('/users', methods=['GET'])
@require_tenant
def list_tenant_users(tenant):
    """List users in the current tenant
    
    Requires admin role
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not validate_tenant_access(user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    if user.role not in ['admin', 'owner']:
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.filter_by(tenant_id=tenant.id).all()
    
    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'is_active': u.is_active,
            'created_at': u.created_at.isoformat() if u.created_at else None
        } for u in users]
    }), 200


@tenant_bp.route('/users', methods=['POST'])
@require_tenant
def create_tenant_user(tenant):
    """Create a new user in the current tenant
    
    Requires admin role
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    current_user = User.query.get(user_id)
    if not validate_tenant_access(current_user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    if current_user.role not in ['admin', 'owner']:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Check tenant limits
    within_limits, error_msg = check_tenant_limits(tenant)
    if not within_limits:
        return jsonify({'error': error_msg}), 403
    
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists in tenant
    existing = User.query.filter_by(
        tenant_id=tenant.id,
        username=data['username']
    ).first()
    
    if existing:
        return jsonify({'error': 'Username already exists in this tenant'}), 400
    
    # Create new user
    new_user = User(
        tenant_id=tenant.id,
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user'),
        is_active=True
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'role': new_user.role
        }
    }), 201


@tenant_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@require_tenant
def update_user_role(tenant, user_id):
    """Update a user's role within the tenant
    
    Requires owner role
    """
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    current_user = User.query.get(current_user_id)
    if not validate_tenant_access(current_user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    if current_user.role != 'owner':
        return jsonify({'error': 'Owner access required'}), 403
    
    target_user = User.query.filter_by(id=user_id, tenant_id=tenant.id).first()
    if not target_user:
        return jsonify({'error': 'User not found in this tenant'}), 404
    
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['user', 'admin', 'owner']:
        return jsonify({'error': 'Invalid role'}), 400
    
    target_user.role = new_role
    db.session.commit()
    
    return jsonify({
        'message': 'User role updated',
        'user': {
            'id': target_user.id,
            'username': target_user.username,
            'role': target_user.role
        }
    }), 200


@tenant_bp.route('/settings', methods=['GET'])
@require_tenant
def get_tenant_settings(tenant):
    """Get tenant settings
    
    Requires admin role
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not validate_tenant_access(user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    if user.role not in ['admin', 'owner']:
        return jsonify({'error': 'Admin access required'}), 403
    
    return jsonify({
        'settings': tenant.settings or {},
        'plan': tenant.plan,
        'max_users': tenant.max_users
    }), 200


@tenant_bp.route('/settings', methods=['PUT'])
@require_tenant
def update_tenant_settings(tenant):
    """Update tenant settings
    
    Requires owner role
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not validate_tenant_access(user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    if user.role != 'owner':
        return jsonify({'error': 'Owner access required'}), 403
    
    data = request.get_json()
    
    # Update allowed settings
    if 'settings' in data:
        tenant.settings = data['settings']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Settings updated',
        'settings': tenant.settings
    }), 200


@tenant_bp.route('/list', methods=['GET'])
def list_all_tenants():
    """List all tenants (public endpoint for discovery)
    
    Returns basic tenant information only
    """
    tenants = Tenant.query.filter_by(is_active=True).all()
    
    return jsonify({
        'tenants': [{
            'slug': t.slug,
            'name': t.name,
            'domain': t.domain
        } for t in tenants]
    }), 200
