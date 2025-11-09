"""
Flask Frontend Application

This module implements the frontend web server for the multi-tenant OAuth 2.0 system.
It serves the user interface and acts as a proxy/gateway to the backend API.

Architecture:
    Frontend (this app) ↔ Nginx ↔ Backend API
    
    - Frontend: Renders HTML templates, handles user interactions
    - Nginx: Load balancing, SSL termination, routing
    - Backend API: OAuth 2.0 server, database operations, business logic

Deployment:
    - Runs as a separate uWSGI process in Docker container
    - Communicates with backend via internal Docker network
    - Exposed to users through Nginx reverse proxy
    
Environment Variables:
    API_URL: Backend API base URL (default: http://nginx_api:80)
    SECRET_KEY: Flask session secret (MUST be set in production)
    
Security:
    - Does NOT handle authentication directly (uses backend OAuth API)
    - Sessions managed by Flask (encrypted with SECRET_KEY)
    - CSRF protection should be enabled for production
    
Example Usage:
    # Development
    export API_URL=http://localhost:8080
    export SECRET_KEY=your-secret-key
    python app.py
    
    # Production (via uWSGI)
    uwsgi --ini uwsgi.ini
"""
import os
import requests
from flask import Flask, render_template, jsonify

# Backend API URL - configure based on deployment environment
# Docker: http://nginx_api:80 (internal Docker network)
# Local Dev: http://localhost:8080
API_URL = os.getenv('API_URL', 'http://nginx_api:80')


def create_app():
    """
    Create and configure the Flask frontend application.
    
    Application Factory Pattern:
        Returns a configured Flask app instance instead of creating
        a global app object. This allows:
        - Multiple app instances for testing
        - Different configurations per environment
        - Better separation of concerns
    
    Configuration:
        - SECRET_KEY: Used for session encryption and CSRF tokens
                     CRITICAL: Must be strong random value in production
    
    Registered Routes:
        /           - Homepage (renders index.html template)
        /health     - Health check for container orchestration
        /api-status - Backend API connectivity check
    
    Returns:
        Flask: Configured Flask application instance
        
    Example:
        app = create_app()
        app.run(host='0.0.0.0', port=5000)
    """
    app = Flask(__name__)
    
    # Configuration
    # WARNING: SECRET_KEY must be set via environment variable in production
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    @app.route('/')
    def index():
        """
        Homepage route - serves the main user interface.
        
        Renders the index.html template which provides:
        - Login/registration interface
        - OAuth client management UI
        - Tenant selection
        - API documentation links
        
        Returns:
            HTML: Rendered index.html template
            
        Template Context:
            Currently no context variables passed to template.
            In production, you might pass:
            - Available tenants
            - OAuth clients
            - User session info
        
        Example:
            GET http://localhost:3000/
        """
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        """
        Health check endpoint for monitoring and orchestration.
        
        Used by:
        - Docker health checks (HEALTHCHECK in Dockerfile)
        - Kubernetes liveness/readiness probes
        - Load balancers for routing decisions
        - Monitoring systems (Prometheus, Datadog, etc.)
        
        Returns:
            JSON: Health status object
            Status Code: 200 (always healthy if app is running)
            
        Response:
            {
                "status": "healthy",
                "service": "frontend"
            }
        
        Note:
            This only checks if the frontend process is running.
            Use /api-status to verify backend connectivity.
        
        Example:
            curl http://localhost:3000/health
        """
        return jsonify({
            'status': 'healthy',
            'service': 'frontend'
        }), 200
    
    @app.route('/api-status')
    def api_status():
        """
        Check backend API connectivity and health.
        
        Verifies that the frontend can reach the backend API service.
        Useful for diagnosing network issues, container startup sequencing,
        and overall system health.
        
        Process:
            1. Makes HTTP request to backend /health endpoint
            2. Returns success if backend responds
            3. Returns error if backend unreachable or timeout
        
        Returns:
            JSON: API connectivity status
            Status Code: 200 if API reachable, 503 if not
            
        Success Response (200):
            {
                "api_reachable": true,
                "api_status": {
                    "status": "healthy",
                    "service": "api",
                    "database": "connected"
                }
            }
        
        Error Response (503):
            {
                "api_reachable": false,
                "error": "Connection refused" | "Timeout" | etc.
            }
        
        Common Issues:
            - "Connection refused": Backend not started yet
            - "Timeout": Network connectivity issues
            - "Name resolution failed": DNS/hostname issues
        
        Example:
            curl http://localhost:3000/api-status
        """
        try:
            # Make request to backend health endpoint with 5 second timeout
            response = requests.get(f'{API_URL}/health', timeout=5)
            return jsonify({
                'api_reachable': True,
                'api_status': response.json()
            }), 200
        except requests.exceptions.Timeout:
            return jsonify({
                'api_reachable': False,
                'error': 'Backend API timeout (>5s)'
            }), 503
        except requests.exceptions.ConnectionError as e:
            return jsonify({
                'api_reachable': False,
                'error': f'Connection error: {str(e)}'
            }), 503
        except Exception as e:
            return jsonify({
                'api_reachable': False,
                'error': str(e)
            }), 503
    
    return app
