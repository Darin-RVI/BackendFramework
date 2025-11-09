"""
WSGI Entry Point for Frontend Application

This module serves as the WSGI (Web Server Gateway Interface) entry point
for the frontend Flask application. It bridges the gap between the uWSGI
server and the Flask application.

WSGI Overview:
    WSGI is a Python standard (PEP 3333) that defines how web servers
    communicate with Python web applications. It allows:
    - Production-ready deployment with uWSGI, Gunicorn, mod_wsgi
    - Concurrent request handling
    - Better performance than Flask's built-in development server
    - Process management and monitoring
    
Deployment Scenarios:

    Development (Direct Python):
        python wsgi.py
        - Uses Flask's development server
        - Single-threaded, not for production
        - Auto-reloads on code changes
        - Accessible at http://0.0.0.0:8000
    
    Production (uWSGI):
        uwsgi --ini uwsgi.ini
        - Multi-process/thread worker model
        - Production-ready performance
        - Managed by uwsgi.ini configuration
        - No auto-reload (requires restart)
    
    Docker:
        CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]
        - Containerized deployment
        - Health checks via /health endpoint
        - Orchestrated with docker-compose
        
Environment Configuration:
    This module loads environment variables from .env file (if present)
    before creating the Flask app. This allows configuration without
    hardcoding values:
    
    .env file example:
        API_URL=http://nginx_api:80
        SECRET_KEY=your-production-secret-key
        FLASK_ENV=production
        
Security Notes:
    - SECRET_KEY must be set in production (not default value)
    - Debug mode disabled in production (debug=False)
    - Environment variables should not be committed to version control
    
WSGI Application Object:
    The 'app' variable is the WSGI application object that uWSGI
    expects to find. It must be named 'app' or configured in uwsgi.ini
    via the 'callable' option.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
# This must be done BEFORE importing the Flask app to ensure
# configuration is available during app creation
load_dotenv()

# Import the Flask application factory
# create_app() returns a configured Flask application instance
from app import create_app
app = create_app()

# Development server entry point
# This block only runs when executing: python wsgi.py
# It does NOT run when loaded by uWSGI
if __name__ == "__main__":
    # Run Flask's built-in development server
    # WARNING: This is for DEVELOPMENT ONLY, not production
    # Use uWSGI (uwsgi --ini uwsgi.ini) for production deployment
    app.run(
        host='0.0.0.0',      # Listen on all network interfaces (allows external access)
        port=8000,           # Port for frontend development server
        debug=True           # Enable debug mode (auto-reload, detailed errors)
    )
    # Debug mode features:
    # - Auto-reloads on code changes
    # - Interactive debugger in browser
    # - Detailed error pages
    # NEVER use debug=True in production!
