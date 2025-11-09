"""
Tenant Management Routes

This module provides comprehensive tenant management endpoints for multi-tenant operations:

1. Tenant Registration: Create new tenant organizations with admin users
2. Tenant Information: Get tenant details and settings
3. User Management: CRUD operations for tenant users
4. Role Management: Update user roles within tenants
5. Statistics: Tenant usage and analytics
6. Settings Management: Configure tenant-specific settings

Role-Based Access Control:
- Public: Tenant registration and listing
- User: View own tenant information
- Admin: Manage tenant users, view statistics
- Owner: Full tenant management including settings

All endpoints enforce tenant isolation and validate user access.

Multi-Tenant Architecture:
Every endpoint respects tenant context and ensures:
- Users only access their own tenant's data
- Cross-tenant data leakage is prevented
- Tenant limits (users, resources) are enforced
- Admin operations require appropriate roles

Security Features:
- Role-based permissions (user, admin, owner)
- Tenant isolation validation
- Resource limit enforcement
- Secure password hashing
- Session-based authentication
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

# Create blueprint for tenant management routes
# All routes in this blueprint will be prefixed with /tenants (configured in app.py)
tenant_bp = Blueprint('tenant', __name__)


def validate_slug(slug):
    """
    Validate tenant slug format.
    
    Slugs must be:
    - Lowercase only
    - Alphanumeric characters and hyphens
    - No spaces or special characters
    - URL-safe
    
    Args:
        slug: Tenant slug string to validate
        
    Returns:
        bool: True if valid format, False otherwise
        
    Examples:
        Valid: "acme", "acme-corp", "company123"
        Invalid: "Acme", "acme_corp", "acme corp", "acme!"
    """
    # Slug should be lowercase, alphanumeric, hyphens only
    return bool(re.match(r'^[a-z0-9-]+$', slug))


# ==================== Tenant Registration & Discovery ====================

@tenant_bp.route('/register', methods=['POST'])
def register_tenant():
    """
    Register a new tenant organization.
    
    Creates a new tenant with an owner/admin user in a single atomic transaction.
    This is typically the first step in onboarding a new customer/organization.
    
    Public Endpoint: No authentication required (self-service registration)
    
    Request Body (JSON):
        tenant_name (str): Display name for tenant (e.g., "Acme Corporation")
        tenant_slug (str): URL-safe identifier (e.g., "acme") - must be unique
        admin_username (str): Username for tenant owner/admin
        admin_email (str): Email for tenant owner/admin
        admin_password (str): Password for tenant owner/admin (will be hashed)
        domain (str, optional): Custom domain for tenant (e.g., "acme.com")
        plan (str, optional): Subscription plan (default: "free")
                             Options: free, basic, premium, enterprise
    
    Returns:
        201: Tenant and admin user created successfully
        400: Invalid input (missing fields, invalid slug format, slug/domain exists)
        500: Server error during creation
        
    Response:
        {
            "message": "Tenant registered successfully",
            "tenant": {
                "id": 1,
                "name": "Acme Corporation",
                "slug": "acme",
                "domain": "acme.com",
                "plan": "premium"
            },
            "admin": {
                "id": 1,
                "username": "admin",
                "email": "admin@acme.com",
                "role": "owner"
            },
            "access_info": {
                "subdomain": "acme.yourdomain.com",
                "header": "X-Tenant-Slug: acme",
                "path": "/tenants/acme/..."
            }
        }
    
    Slug Format Rules:
        - Lowercase letters, numbers, and hyphens only
        - No spaces or special characters
        - Must be unique across all tenants
        - Used for subdomain and URL routing
    
    Example:
        curl -X POST http://localhost:8080/tenants/register \\
             -H "Content-Type: application/json" \\
             -d '{
                 "tenant_name": "Acme Corporation",
                 "tenant_slug": "acme",
                 "admin_username": "admin",
                 "admin_email": "admin@acme.com",
                 "admin_password": "secure123",
                 "domain": "acme.com",
                 "plan": "premium"
             }'
    """
    data = request.get_json()
    
    # Validate all required fields are present
    required = ['tenant_name', 'tenant_slug', 'admin_username', 'admin_email', 'admin_password']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields', 'required': required}), 400
    
    # Normalize and validate slug format
    slug = data['tenant_slug'].lower()
    if not validate_slug(slug):
        return jsonify({'error': 'Invalid slug format. Use lowercase letters, numbers, and hyphens only'}), 400
    
    # Check if tenant slug already exists (must be globally unique)
    if Tenant.query.filter_by(slug=slug).first():
        return jsonify({'error': 'Tenant slug already exists'}), 400
    
    # Check if custom domain is provided and validate uniqueness
    domain = data.get('domain')
    if domain:
        if Tenant.query.filter_by(domain=domain).first():
            return jsonify({'error': 'Domain already registered'}), 400
    
    try:
        # Create tenant and admin user (atomic transaction)
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
        # Rollback transaction on error
        db.session.rollback()
        return jsonify({'error': 'Failed to create tenant', 'details': str(e)}), 500


@tenant_bp.route('/list', methods=['GET'])
def list_all_tenants():
    """
    List all active tenants (public endpoint for discovery).
    
    Returns basic information about all active tenants to allow
    clients to discover available tenants for login/access.
    
    Public Endpoint: No authentication required
    
    Security Note:
        Only returns basic, non-sensitive information (name, slug, domain).
        Does not expose user counts, settings, or other private data.
    
    Returns:
        200: List of active tenants
        
    Response:
        {
            "tenants": [
                {
                    "slug": "acme",
                    "name": "Acme Corporation",
                    "domain": "acme.com"
                },
                {
                    "slug": "techcorp",
                    "name": "Tech Corp Inc",
                    "domain": null
                }
            ]
        }
    
    Example:
        curl http://localhost:8080/tenants/list
    """
    # Only return active tenants (is_active=True)
    tenants = Tenant.query.filter_by(is_active=True).all()
    
    return jsonify({
        'tenants': [{
            'slug': t.slug,
            'name': t.name,
            'domain': t.domain
        } for t in tenants]
    }), 200


# ==================== Tenant Information ====================

@tenant_bp.route('/info', methods=['GET'])
@require_tenant
def get_tenant_info(tenant):
    """
    Get current tenant information.
    
    Returns detailed information about the identified tenant.
    Authenticated users must belong to the tenant to access sensitive information.
    
    Tenant Context Required:
        Must identify tenant via header, subdomain, or path
    
    Authentication:
        Optional - If authenticated, validates user belongs to tenant
        If not authenticated, returns only public information
    
    Returns:
        200: Tenant information
        403: User doesn't belong to this tenant
        
    Response:
        {
            "id": 1,
            "name": "Acme Corporation",
            "slug": "acme",
            "domain": "acme.com",
            "plan": "premium",
            "max_users": 50,
            "is_active": true,
            "created_at": "2024-01-15T10:30:00"
        }
    
    Example:
        curl -H "X-Tenant-Slug: acme" \\
             http://localhost:8080/tenants/info
    """
    
    # Check if user is authenticated and validate tenant access
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
    """
    Get tenant usage statistics and analytics.
    
    Provides insights into tenant usage including user counts, activity metrics,
    and resource utilization. Only accessible to tenant admins and owners.
    
    Tenant Context Required: Yes
    Authentication Required: Yes (admin or owner role)
    
    Role Permissions:
        - Admin: Can view statistics for their tenant
        - Owner: Can view statistics for their tenant
        - User: Access denied (403)
    
    Returns:
        200: Statistics retrieved successfully
        401: Not authenticated
        403: User not admin/owner or not in tenant
        
    Response (from get_tenant_stats utility):
        {
            "total_users": 25,
            "active_users": 20,
            "admin_users": 3,
            "oauth_clients": 5,
            "plan": "premium",
            "max_users": 50
        }
    
    Example:
        curl -H "X-Tenant-Slug: acme" \\
             -H "Cookie: session=abc123" \\
             http://localhost:8080/tenants/stats
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
    """
    List all users in the tenant.
    
    Returns a list of users belonging to the current tenant.
    Only accessible to authenticated admins and owners.
    
    Tenant Context Required: Yes
    Authentication Required: Yes (admin or owner role)
    
    Returns:
        200: User list retrieved successfully
        401: Not authenticated
        403: User not admin/owner or not in tenant
        
    Response:
        {
            "users": [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@acme.com",
                    "role": "owner",
                    "is_active": true,
                    "created_at": "2024-01-15T10:30:00"
                },
                {
                    "id": 2,
                    "username": "user1",
                    "email": "user1@acme.com",
                    "role": "user",
                    "is_active": true,
                    "created_at": "2024-01-16T14:20:00"
                }
            ]
        }
    
    Security:
        - Only returns users from current tenant (tenant isolation)
        - Sensitive data (passwords) not included
    
    Example:
        curl -H "X-Tenant-Slug: acme" \\
             -H "Cookie: session=abc123" \\
             http://localhost:8080/tenants/users
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
    """
    Create a new user in the tenant.
    
    Creates a new user account within the current tenant.
    Only accessible to tenant admins and owners.
    Enforces tenant user limits based on subscription plan.
    
    Tenant Context Required: Yes
    Authentication Required: Yes (admin or owner role)
    
    Request Body (JSON):
        username (str): Unique username within tenant
        email (str): User email address
        password (str): User password (will be hashed)
        role (str, optional): User role (default: "user")
                             Options: user, admin
    
    Validation:
        - Checks tenant user limits (based on plan)
        - Validates username uniqueness within tenant
        - Validates email format
        - Enforces role-based creation permissions
    
    Returns:
        201: User created successfully
        400: Invalid input or user limit reached
        401: Not authenticated
        403: Insufficient permissions
        
    Response:
        {
            "message": "User created successfully",
            "user": {
                "id": 3,
                "username": "newuser",
                "email": "newuser@acme.com",
                "role": "user"
            }
        }
    
    Example:
        curl -X POST http://localhost:8080/tenants/users \\
             -H "X-Tenant-Slug: acme" \\
             -H "Cookie: session=abc123" \\
             -H "Content-Type: application/json" \\
             -d '{
                 "username": "newuser",
                 "email": "newuser@acme.com",
                 "password": "secure123",
                 "role": "user"
             }'
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    current_user = User.query.get(user_id)
    if not validate_tenant_access(current_user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    if current_user.role not in ['admin', 'owner']:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Check tenant limits (returns tuple: (bool, str))
    within_limits, error_msg = check_tenant_limits(tenant)
    if not within_limits:
        return jsonify({'error': error_msg}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists in tenant (username must be unique per tenant)
    existing = User.query.filter_by(
        tenant_id=tenant.id,
        username=data['username']
    ).first()
    
    if existing:
        return jsonify({'error': 'Username already exists in this tenant'}), 400
    
    # Create new user with hashed password
    new_user = User(
        tenant_id=tenant.id,
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user'),  # Default to 'user' role
        is_active=True
    )
    new_user.set_password(data['password'])  # Hash password
    
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
    """
    Update a user's role within the tenant.
    
    Allows tenant owners to update user roles.
    Enforces role-based permissions and prevents privilege escalation.
    
    Tenant Context Required: Yes
    Authentication Required: Yes (owner role only)
    
    Path Parameters:
        user_id (int): ID of user to update
    
    Request Body (JSON):
        role (str): New role - Options: user, admin, owner
    
    Role Update Permissions:
        - Owner: Can change any user's role (including admin ↔ user)
        - Admin: Access denied (403)
        - User: Access denied (403)
    
    Restrictions:
        - Cannot demote the last owner
        - Cannot change own role (prevents accidental lock-out)
        - Cannot modify users from other tenants
    
    Returns:
        200: User role updated successfully
        400: Invalid role or last owner protection
        401: Not authenticated
        403: Insufficient permissions (owner required)
        404: User not found in tenant
        
    Response:
        {
            "message": "User role updated",
            "user": {
                "id": 3,
                "username": "user1",
                "role": "admin"
            }
        }
    
    Example:
        curl -X PUT http://localhost:8080/tenants/users/3/role \\
             -H "X-Tenant-Slug: acme" \\
             -H "Cookie: session=abc123" \\
             -H "Content-Type: application/json" \\
             -d '{"role": "admin"}'
    """
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    current_user = User.query.get(current_user_id)
    if not validate_tenant_access(current_user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    # Only owners can change roles
    if current_user.role != 'owner':
        return jsonify({'error': 'Owner access required'}), 403
    
    # Get target user (must be in same tenant)
    target_user = User.query.filter_by(id=user_id, tenant_id=tenant.id).first()
    if not target_user:
        return jsonify({'error': 'User not found in this tenant'}), 404
    
    data = request.get_json()
    new_role = data.get('role')
    
    # Validate role value
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
    """
    Get tenant settings and configuration.
    
    Returns tenant-specific settings including plan limits and configuration.
    Only accessible to admins and owners.
    
    Tenant Context Required: Yes
    Authentication Required: Yes (admin or owner role)
    
    Returns:
        200: Settings retrieved successfully
        401: Not authenticated
        403: Insufficient permissions
        
    Response:
        {
            "settings": {
                "notifications": {
                    "email_enabled": true,
                    "webhook_url": "https://hooks.acme.com/tenant"
                },
                "features": {
                    "sso": true,
                    "custom_domain": true
                }
            },
            "plan": "premium",
            "max_users": 50
        }
    
    Example:
        curl -H "X-Tenant-Slug: acme" \\
             -H "Cookie: session=abc123" \\
             http://localhost:8080/tenants/settings
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
    """
    Update tenant settings and configuration.
    
    Allows tenant owners to modify settings within plan constraints.
    Some settings may require specific subscription plans.
    
    Tenant Context Required: Yes
    Authentication Required: Yes (owner role only)
    
    Request Body (JSON):
        settings (dict): Settings object to update
    
    Updateable Settings:
        - notifications: Email and webhook settings
        - features: Feature flags (if allowed by plan)
        - custom_domain: Custom domain (premium+ only)
    
    Plan Restrictions:
        - Free: Basic features only
        - Premium: SSO, custom domain, increased limits
        - Enterprise: All features, custom limits
    
    Returns:
        200: Settings updated successfully
        401: Not authenticated
        403: Insufficient permissions (owner required)
        
    Response:
        {
            "message": "Settings updated",
            "settings": {
                "notifications": {
                    "email_enabled": true,
                    "webhook_url": "https://hooks.acme.com/new"
                }
            }
        }
    
    Example:
        curl -X PUT http://localhost:8080/tenants/settings \\
             -H "X-Tenant-Slug: acme" \\
             -H "Cookie: session=abc123" \\
             -H "Content-Type: application/json" \\
             -d '{
                 "settings": {
                     "notifications": {
                         "email_enabled": true,
                         "webhook_url": "https://hooks.acme.com/tenant"
                     }
                 }
             }'
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    user = User.query.get(user_id)
    if not validate_tenant_access(user, tenant):
        return jsonify({'error': 'Access denied'}), 403
    
    # Only owners can update settings
    if user.role != 'owner':
        return jsonify({'error': 'Owner access required'}), 403
    
    data = request.get_json()
    
    # Update settings (replace entire settings object)
    if 'settings' in data:
        tenant.settings = data['settings']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Settings updated',
        'settings': tenant.settings
    }), 200
