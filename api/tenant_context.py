"""
Multi-Tenant Context and Utilities
"""
from flask import g, request, abort
from functools import wraps
from models import Tenant, User
from app import db


class TenantContext:
    """Context manager for tenant operations"""
    
    @staticmethod
    def get_current_tenant():
        """Get the current tenant from request context"""
        return getattr(g, 'current_tenant', None)
    
    @staticmethod
    def get_tenant_id():
        """Get the current tenant ID"""
        tenant = TenantContext.get_current_tenant()
        return tenant.id if tenant else None
    
    @staticmethod
    def set_current_tenant(tenant):
        """Set the current tenant in request context"""
        g.current_tenant = tenant
    
    @staticmethod
    def identify_tenant():
        """Identify tenant from request
        
        Supports multiple identification strategies:
        1. Subdomain (tenant.example.com)
        2. Custom domain (customdomain.com)
        3. Header (X-Tenant-ID or X-Tenant-Slug)
        4. Path parameter (/tenants/{slug}/...)
        """
        tenant = None
        
        # Strategy 1: Check X-Tenant-Slug header
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if tenant_slug:
            tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True).first()
            if tenant:
                return tenant
        
        # Strategy 2: Check X-Tenant-ID header
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                tenant = Tenant.query.filter_by(id=int(tenant_id), is_active=True).first()
                if tenant:
                    return tenant
            except (ValueError, TypeError):
                pass
        
        # Strategy 3: Check subdomain
        host = request.host.split(':')[0]  # Remove port
        parts = host.split('.')
        
        if len(parts) >= 3:  # e.g., tenant.example.com
            subdomain = parts[0]
            if subdomain not in ['www', 'api', 'admin']:  # Ignore common subdomains
                tenant = Tenant.query.filter_by(slug=subdomain, is_active=True).first()
                if tenant:
                    return tenant
        
        # Strategy 4: Check custom domain
        tenant = Tenant.query.filter_by(domain=host, is_active=True).first()
        if tenant:
            return tenant
        
        # Strategy 5: Check path parameter (e.g., /tenants/acme/api/...)
        path_parts = request.path.split('/')
        if len(path_parts) >= 3 and path_parts[1] == 'tenants':
            tenant_slug = path_parts[2]
            tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True).first()
            if tenant:
                return tenant
        
        return None


def require_tenant(f):
    """Decorator to require tenant context"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = TenantContext.get_current_tenant()
        if not tenant:
            return {'error': 'Tenant not identified', 'message': 'Please specify tenant via header, subdomain, or path'}, 400
        
        kwargs['tenant'] = tenant
        return f(*args, **kwargs)
    return decorated_function


def tenant_filter(query_class):
    """Apply tenant filter to query
    
    Usage:
        users = tenant_filter(User).all()
    """
    tenant_id = TenantContext.get_tenant_id()
    if tenant_id:
        return query_class.query.filter_by(tenant_id=tenant_id)
    return query_class.query


def create_tenant(name, slug, admin_username, admin_email, admin_password, domain=None, plan='free'):
    """Helper function to create a new tenant with admin user
    
    Args:
        name: Tenant name
        slug: Tenant slug (URL-safe identifier)
        admin_username: Admin username
        admin_email: Admin email
        admin_password: Admin password
        domain: Optional custom domain
        plan: Subscription plan
    
    Returns:
        Tuple of (tenant, admin_user)
    """
    # Create tenant
    tenant = Tenant(
        name=name,
        slug=slug,
        domain=domain,
        plan=plan,
        is_active=True
    )
    db.session.add(tenant)
    db.session.flush()  # Get tenant ID
    
    # Create admin user
    admin_user = User(
        tenant_id=tenant.id,
        username=admin_username,
        email=admin_email,
        role='owner',
        is_active=True
    )
    admin_user.set_password(admin_password)
    
    db.session.add(admin_user)
    db.session.commit()
    
    return tenant, admin_user


def validate_tenant_access(user, tenant):
    """Validate that user belongs to tenant"""
    if not user or not tenant:
        return False
    return user.tenant_id == tenant.id


def check_tenant_limits(tenant):
    """Check if tenant has reached usage limits
    
    Returns:
        Tuple of (is_within_limits, error_message)
    """
    if not tenant.is_active:
        return False, "Tenant account is inactive"
    
    # Check user limit
    user_count = User.query.filter_by(tenant_id=tenant.id, is_active=True).count()
    if user_count >= tenant.max_users:
        return False, f"User limit reached ({tenant.max_users} users)"
    
    # Add more limit checks as needed (API calls, storage, etc.)
    
    return True, None


def get_tenant_stats(tenant):
    """Get statistics for a tenant
    
    Returns:
        Dictionary with tenant statistics
    """
    total_users = User.query.filter_by(tenant_id=tenant.id).count()
    active_users = User.query.filter_by(tenant_id=tenant.id, is_active=True).count()
    
    from models import OAuth2Client, OAuth2Token
    total_clients = OAuth2Client.query.filter_by(tenant_id=tenant.id).count()
    active_tokens = OAuth2Token.query.filter_by(
        tenant_id=tenant.id, 
        revoked=False
    ).filter(OAuth2Token.access_token_expires_at > int(time.time())).count()
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'total_clients': total_clients,
        'active_tokens': active_tokens,
        'plan': tenant.plan,
        'max_users': tenant.max_users
    }


import time
