"""
Flask Application Factory

This module implements the application factory pattern for creating Flask instances.
It configures the database, OAuth 2.0 server, multi-tenant support, and registers
all application blueprints.

Key Features:
- Application factory pattern for flexibility and testing
- OAuth 2.0 authentication with multiple grant types
- Multi-tenant request handling via middleware
- Database migrations with Flask-Migrate
- CORS support for frontend integration
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize Flask extensions as global objects
# These will be attached to the app in create_app()
db = SQLAlchemy()  # Database ORM for model management
migrate = Migrate()  # Database migration management


def create_app():
    """
    Create and configure the Flask application.
    
    This factory function creates a new Flask application instance with all
    necessary configuration, extensions, and blueprints registered. Using
    the factory pattern allows for multiple app instances with different
    configurations (e.g., testing, production).
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask application instance
    app = Flask(__name__)
    
    # ==================== Database Configuration ====================
    # Configure PostgreSQL database connection
    # Defaults to Docker service name 'postgres' for containerized deployment
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@postgres:5432/backend_db'
    )
    # Disable modification tracking to save resources (Flask-SQLAlchemy 3.0+ default)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Secret key for session management and CSRF protection
    # IMPORTANT: Use a strong random key in production via environment variable
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # ==================== OAuth 2.0 Configuration ====================
    # Issuer URL - identifies this OAuth server to clients
    # Should be the public-facing URL in production (e.g., https://api.yourdomain.com)
    app.config['OAUTH2_ISSUER'] = os.getenv('OAUTH2_ISSUER', 'http://localhost:8080')
    
    # Access token lifetime in seconds (default: 1 hour = 3600 seconds)
    # Access tokens are short-lived for security
    app.config['OAUTH2_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('OAUTH2_ACCESS_TOKEN_EXPIRES', 3600))
    
    # Refresh token lifetime in seconds (default: 30 days = 2592000 seconds)
    # Refresh tokens are long-lived to allow seamless token renewal
    app.config['OAUTH2_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('OAUTH2_REFRESH_TOKEN_EXPIRES', 2592000))
    
    # Authorization code lifetime in seconds (default: 10 minutes = 600 seconds)
    # Authorization codes are very short-lived for the authorization code flow
    app.config['OAUTH2_AUTHORIZATION_CODE_EXPIRES'] = int(os.getenv('OAUTH2_AUTHORIZATION_CODE_EXPIRES', 600))
    
    # Allow insecure HTTP transport for development
    # WARNING: Only use in development! Always use HTTPS in production
    if os.getenv('FLASK_ENV') == 'development' or os.getenv('AUTHLIB_INSECURE_TRANSPORT') == 'true':
        os.environ['AUTHLIB_INSECURE_TRANSPORT'] = 'true'
    
    # ==================== Initialize Extensions ====================
    # Enable Cross-Origin Resource Sharing (CORS) for frontend access
    # Allows frontend app on different port/domain to access API
    CORS(app)
    
    # Bind SQLAlchemy to this Flask app instance
    db.init_app(app)
    
    # Bind Flask-Migrate to app and db for database migrations
    migrate.init_app(app, db)
    
    # ==================== Initialize OAuth 2.0 Server ====================
    # Import and configure OAuth 2.0 authorization server
    from oauth2 import config_oauth
    authorization_server, resource_protector = config_oauth(app)
    
    # Store OAuth instances in app context for access in routes
    # authorization_server: handles token generation and authorization
    # resource_protector: validates tokens on protected endpoints
    app.authorization_server = authorization_server
    app.resource_protector = resource_protector
    
    # ==================== Multi-Tenant Middleware ====================
    @app.before_request
    def identify_tenant():
        """
        Identify and set current tenant before each request.
        
        This middleware runs before every request to:
        1. Extract tenant identification from request (subdomain, header, or path)
        2. Load the tenant from database
        3. Set tenant in thread-local context for request duration
        4. All subsequent database queries will be tenant-scoped
        
        Tenant isolation ensures data security in multi-tenant architecture.
        """
        from tenant_context import TenantContext
        
        # Identify tenant from request (subdomain, X-Tenant-Slug header, etc.)
        tenant = TenantContext.identify_tenant()
        
        # Set tenant in thread-local storage for this request
        if tenant:
            TenantContext.set_current_tenant(tenant)
    
    # ==================== Register Blueprints ====================
    # Import route blueprints (late import to avoid circular dependencies)
    from routes import api_bp  # Protected API endpoints
    from auth_routes import auth_bp  # OAuth 2.0 authentication routes
    from tenant_routes import tenant_bp  # Tenant management routes
    
    # Register blueprints with URL prefixes
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/oauth')
    app.register_blueprint(tenant_bp, url_prefix='/tenants')
    
    # ==================== Health Check Endpoint ====================
    @app.route('/health')
    def health():
        """
        Health check endpoint for monitoring.
        
        Returns service status for load balancers and monitoring tools.
        Use this endpoint to verify the API service is running.
        
        Returns:
            JSON response with status 200
        """
        return jsonify({
            'status': 'healthy',
            'service': 'api'
        }), 200
    
    # ==================== API Root Endpoint ====================
    @app.route('/')
    def index():
        """
        API root endpoint with service information.
        
        Provides overview of the API including version, authentication type,
        and available endpoints. Useful for API discovery and documentation.
        
        Returns:
            JSON response with API metadata and endpoint URLs
        """
        return jsonify({
            'message': 'Backend API with OAuth 2.0 and Multi-Tenant Support',
            'version': '2.0.0',
            'auth_type': 'OAuth 2.0',
            'multi_tenant': True,
            'endpoints': {
                'authorization': '/oauth/authorize',
                'token': '/oauth/token',
                'revoke': '/oauth/revoke',
                'register': '/oauth/register',
                'login': '/oauth/login',
                'tenant_register': '/tenants/register',
                'tenant_info': '/tenants/info'
            }
        }), 200
    
    return app
