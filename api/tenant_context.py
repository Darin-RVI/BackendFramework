"""
Multi-Tenant Context and Utilities

This module provides utilities for managing multi-tenant context throughout
the application. It handles:

1. Tenant Identification: Extracts tenant from requests via multiple strategies
2. Context Management: Stores current tenant in thread-local request context
3. Access Control: Validates users belong to correct tenants
4. Tenant Operations: CRUD operations for tenants and users
5. Limit Checking: Enforces tenant-specific resource quotas

Tenant Identification Strategies (in priority order):
1. X-Tenant-Slug HTTP header (e.g., "X-Tenant-Slug: acme")
2. X-Tenant-ID HTTP header (e.g., "X-Tenant-ID: 123")
3. Subdomain (e.g., "acme.example.com")
4. Custom domain (e.g., "customdomain.com")
5. Path parameter (e.g., "/tenants/acme/api/...")

Thread Safety:
Uses Flask's 'g' object which is thread-local, ensuring tenant context
is isolated per request even in multi-threaded environments.
"""
from flask import g, request, abort
from functools import wraps
from models import Tenant, User
from app import db


class TenantContext:
    """
    Context manager for multi-tenant operations.
    
    This class provides static methods to manage tenant context throughout
    the request lifecycle. The current tenant is stored in Flask's 'g' object,
    which is request-scoped and thread-safe.
    
    Usage:
        # Get current tenant in any route or function
        tenant = TenantContext.get_current_tenant()
        
        # Query users for current tenant
        tenant_id = TenantContext.get_tenant_id()
        users = User.query.filter_by(tenant_id=tenant_id).all()
    """
    
    @staticmethod
    def get_current_tenant():
        """
        Get the current tenant from request context.
        
        Returns the tenant that was identified and set by the
        before_request middleware in app.py.
        
        Returns:
            Tenant: Current tenant object or None if not identified
        """
        return getattr(g, 'current_tenant', None)
    
    @staticmethod
    def get_tenant_id():
        """
        Get the current tenant ID.
        
        Convenience method to get just the ID without the full object.
        Useful for database queries.
        
        Returns:
            int: Current tenant ID or None if no tenant set
        """
        tenant = TenantContext.get_current_tenant()
        return tenant.id if tenant else None
    
    @staticmethod
    def set_current_tenant(tenant):
        """
        Set the current tenant in request context.
        
        Called by the before_request middleware after identifying tenant.
        Stores tenant in Flask's 'g' object for request duration.
        
        Args:
            tenant: Tenant object to set as current
        """
        g.current_tenant = tenant
    
    @staticmethod
    def identify_tenant():
        """
        Identify tenant from the current request.
        
        Tries multiple identification strategies in priority order:
        1. X-Tenant-Slug header - Most explicit, recommended for APIs
        2. X-Tenant-ID header - Alternative explicit identification
        3. Subdomain - Useful for web applications (e.g., acme.example.com)
        4. Custom domain - For white-label deployments (e.g., customdomain.com)
        5. Path parameter - RESTful approach (e.g., /tenants/acme/api/...)
        
        Only active tenants (is_active=True) are returned.
        
        Returns:
            Tenant: Identified tenant object or None if no tenant found
            
        Examples:
            # Using header (recommended)
            curl -H "X-Tenant-Slug: acme" http://api.example.com/api/data
            
            # Using subdomain
            curl http://acme.example.com/api/data
            
            # Using custom domain
            curl http://acme-corp.com/api/data
            
            # Using path parameter
            curl http://api.example.com/tenants/acme/api/data
        """
        tenant = None
        
        # ===== Strategy 1: Check X-Tenant-Slug header =====
        # Most explicit and recommended for API calls
        # Example: X-Tenant-Slug: acme
        tenant_slug = request.headers.get('X-Tenant-Slug')
        if tenant_slug:
            tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True).first()
            if tenant:
                return tenant
        
        # ===== Strategy 2: Check X-Tenant-ID header =====
        # Alternative explicit identification using numeric ID
        # Example: X-Tenant-ID: 123
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                tenant = Tenant.query.filter_by(id=int(tenant_id), is_active=True).first()
                if tenant:
                    return tenant
            except (ValueError, TypeError):
                # Invalid ID format, continue to next strategy
                pass
        
        # ===== Strategy 3: Check subdomain =====
        # Extract subdomain from hostname (e.g., acme.example.com -> acme)
        # Useful for web applications with tenant-specific subdomains
        host = request.host.split(':')[0]  # Remove port number if present
        parts = host.split('.')
        
        if len(parts) >= 3:  # Needs at least subdomain.domain.tld
            subdomain = parts[0]
            # Ignore common non-tenant subdomains
            if subdomain not in ['www', 'api', 'admin']:
                tenant = Tenant.query.filter_by(slug=subdomain, is_active=True).first()
                if tenant:
                    return tenant
        
        # ===== Strategy 4: Check custom domain =====
        # For white-label deployments where tenant has their own domain
        # Example: acme-corp.com points to this application
        tenant = Tenant.query.filter_by(domain=host, is_active=True).first()
        if tenant:
            return tenant
        
        # ===== Strategy 5: Check path parameter =====
        # RESTful approach with tenant slug in URL path
        # Example: /tenants/acme/api/... -> acme
        path_parts = request.path.split('/')
        if len(path_parts) >= 3 and path_parts[1] == 'tenants':
            tenant_slug = path_parts[2]
            tenant = Tenant.query.filter_by(slug=tenant_slug, is_active=True).first()
            if tenant:
                return tenant
        
        # No tenant identified by any strategy
        return None


def require_tenant(f):
    """
    Decorator to require tenant context for a route.
    
    Use this decorator on routes that need a tenant to be identified.
    If no tenant is found, returns 400 error with helpful message.
    
    The tenant object is passed as a keyword argument to the decorated function.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function that includes tenant parameter
        
    Example:
        @app.route('/api/data')
        @require_tenant
        def get_data(tenant):
            # tenant object is available here
            users = User.query.filter_by(tenant_id=tenant.id).all()
            return jsonify({'users': [...]})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = TenantContext.get_current_tenant()
        if not tenant:
            return {
                'error': 'Tenant not identified',
                'message': 'Please specify tenant via header, subdomain, or path'
            }, 400
        
        # Add tenant to kwargs so route function can access it
        kwargs['tenant'] = tenant
        return f(*args, **kwargs)
    return decorated_function


def tenant_filter(query_class):
    """
    Apply tenant filter to a database query.
    
    Convenience function to automatically scope queries to current tenant.
    Only returns records that belong to the current tenant.
    
    Args:
        query_class: SQLAlchemy model class to query
        
    Returns:
        Query: Filtered query object
        
    Usage:
        # Instead of:
        users = User.query.filter_by(tenant_id=tenant.id).all()
        
        # Use:
        users = tenant_filter(User).all()
        
        # Also supports chaining:
        active_users = tenant_filter(User).filter_by(is_active=True).all()
    """
    tenant_id = TenantContext.get_tenant_id()
    if tenant_id:
        return query_class.query.filter_by(tenant_id=tenant_id)
    return query_class.query


def create_tenant(name, slug, admin_username, admin_email, admin_password, domain=None, plan='free'):
    """
    Helper function to create a new tenant with admin user.
    
    This is an atomic operation - if either tenant or admin creation fails,
    the entire transaction is rolled back.
    
    Args:
        name: Tenant display name (e.g., "Acme Corporation")
        slug: URL-safe tenant identifier (e.g., "acme")
        admin_username: Username for tenant owner/admin
        admin_email: Email for tenant owner/admin
        admin_password: Password for tenant owner/admin (will be hashed)
        domain: Optional custom domain for tenant
        plan: Subscription plan (free, basic, premium, enterprise)
    
    Returns:
        tuple: (tenant, admin_user) - Both newly created objects
        
    Raises:
        Exception: If tenant or user creation fails
        
    Example:
        tenant, admin = create_tenant(
            name="Acme Corp",
            slug="acme",
            admin_username="admin",
            admin_email="admin@acme.com",
            admin_password="secure123",
            plan="premium"
        )
    """
    # Create tenant record
    tenant = Tenant(
        name=name,
        slug=slug,
        domain=domain,
        plan=plan,
        is_active=True
    )
    db.session.add(tenant)
    db.session.flush()  # Flush to get tenant.id without committing
    
    # Create owner/admin user for the tenant
    admin_user = User(
        tenant_id=tenant.id,
        username=admin_username,
        email=admin_email,
        role='owner',  # Highest permission level
        is_active=True
    )
    admin_user.set_password(admin_password)  # Hash the password
    
    db.session.add(admin_user)
    db.session.commit()  # Commit both tenant and user
    
    return tenant, admin_user


def validate_tenant_access(user, tenant):
    """
    Validate that a user belongs to a specific tenant.
    
    Security check to prevent users from accessing resources
    in other tenants (cross-tenant access).
    
    Args:
        user: User object to validate
        tenant: Tenant object to check against
        
    Returns:
        bool: True if user belongs to tenant, False otherwise
        
    Example:
        if not validate_tenant_access(user, tenant):
            return jsonify({'error': 'Access denied'}), 403
    """
    if not user or not tenant:
        return False
    return user.tenant_id == tenant.id


def check_tenant_limits(tenant):
    """
    Check if tenant has reached usage limits.
    
    Validates tenant against their subscription plan limits:
    - Active status
    - User count limits
    - (Can be extended for API rate limits, storage, etc.)
    
    Args:
        tenant: Tenant object to check
        
    Returns:
        tuple: (is_within_limits: bool, error_message: str or None)
        
    Example:
        within_limits, error = check_tenant_limits(tenant)
        if not within_limits:
            return jsonify({'error': error}), 403
    """
    # Check if tenant account is active
    if not tenant.is_active:
        return False, "Tenant account is inactive"
    
    # Check user limit based on subscription plan
    user_count = User.query.filter_by(tenant_id=tenant.id, is_active=True).count()
    if user_count >= tenant.max_users:
        return False, f"User limit reached ({tenant.max_users} users)"
    
    # Add more limit checks as needed:
    # - API request rate limits
    # - Storage limits
    # - Feature access based on plan
    # - Concurrent connection limits
    
    return True, None


def get_tenant_stats(tenant):
    """
    Get usage statistics for a tenant.
    
    Provides overview of tenant's resource usage including:
    - User counts (total and active)
    - OAuth client count
    - Active token count
    - Plan and limits
    
    Useful for admin dashboards and usage monitoring.
    
    Args:
        tenant: Tenant object to get stats for
        
    Returns:
        dict: Dictionary with tenant statistics
        
    Example:
        stats = get_tenant_stats(tenant)
        # {
        #     'total_users': 15,
        #     'active_users': 12,
        #     'total_clients': 3,
        #     'active_tokens': 8,
        #     'plan': 'premium',
        #     'max_users': 50
        # }
    """
    # Count total and active users
    total_users = User.query.filter_by(tenant_id=tenant.id).count()
    active_users = User.query.filter_by(tenant_id=tenant.id, is_active=True).count()
    
    # Import models here to avoid circular imports
    from models import OAuth2Client, OAuth2Token
    import time
    
    # Count OAuth clients
    total_clients = OAuth2Client.query.filter_by(tenant_id=tenant.id).count()
    
    # Count active (non-expired, non-revoked) tokens
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
