"""
Flask Application Factory
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@postgres:5432/backend_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # OAuth 2.0 Configuration
    app.config['OAUTH2_ISSUER'] = os.getenv('OAUTH2_ISSUER', 'http://localhost:8080')
    app.config['OAUTH2_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('OAUTH2_ACCESS_TOKEN_EXPIRES', 3600))
    app.config['OAUTH2_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('OAUTH2_REFRESH_TOKEN_EXPIRES', 2592000))
    app.config['OAUTH2_AUTHORIZATION_CODE_EXPIRES'] = int(os.getenv('OAUTH2_AUTHORIZATION_CODE_EXPIRES', 600))
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize OAuth 2.0
    from oauth2 import config_oauth
    authorization_server, resource_protector = config_oauth(app)
    
    # Store OAuth instances in app context
    app.authorization_server = authorization_server
    app.resource_protector = resource_protector
    
    # Multi-tenant middleware
    @app.before_request
    def identify_tenant():
        """Identify and set current tenant before each request"""
        from tenant_context import TenantContext
        tenant = TenantContext.identify_tenant()
        if tenant:
            TenantContext.set_current_tenant(tenant)
    
    # Register blueprints
    from routes import api_bp
    from auth_routes import auth_bp
    from tenant_routes import tenant_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/oauth')
    app.register_blueprint(tenant_bp, url_prefix='/tenants')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'service': 'api'
        }), 200
    
    @app.route('/')
    def index():
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
