"""
WSGI Entry Point for the API Application

This module serves as the entry point for WSGI servers (uWSGI, Gunicorn, etc.)
to run the Flask application in production.

WSGI (Web Server Gateway Interface):
    A specification that describes how web servers communicate with Python web
    applications. This file creates the 'app' object that WSGI servers expect.

Production Deployment:
    - uWSGI: Configured in uwsgi.ini to import this module
    - Gunicorn: Run with 'gunicorn wsgi:app'
    - Other WSGI servers: Point to 'wsgi:app'

Environment Variables:
    Loads .env file for configuration. Required variables:
    - DATABASE_URL: PostgreSQL connection string
    - SECRET_KEY: Flask secret key for sessions
    - OAUTH2_ISSUER: OAuth issuer URL
    - (See .env.example for complete list)

Development vs Production:
    - Development: Run directly with 'python wsgi.py' (uses Flask dev server)
    - Production: Use uWSGI or Gunicorn (never use Flask dev server)
"""
import os
from dotenv import load_dotenv

# ==================== Load Environment Variables ====================
# Load environment variables from .env file
# This must happen BEFORE importing the app to ensure configuration is available
load_dotenv()

# ==================== Import and Create Application ====================
# Import the Flask application factory and create app instance
from app import create_app

# Create the Flask application
# This is the WSGI application object that web servers will use
app = create_app()

# ==================== Alternative Framework Examples ====================
# Examples for other Python web frameworks (commented out):

# For FastAPI:
# from app.main import app

# For Django:
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# django.setup()
# from django.core.wsgi import get_wsgi_application
# app = get_wsgi_application()

# ==================== Development Server ====================
# Only runs when script is executed directly (not via WSGI server)
# WARNING: Do NOT use Flask's development server in production!
# It's single-threaded and not secure.
if __name__ == "__main__":
    # Run Flask's built-in development server
    # - host='0.0.0.0': Listen on all network interfaces (accessible from other machines)
    # - port=8080: Listen on port 8080 (matches uwsgi configuration)
    # - debug=True: Enable debug mode with auto-reload and detailed error pages
    #
    # For development only! In production, use uWSGI or Gunicorn:
    #   uwsgi --ini uwsgi.ini
    #   gunicorn -w 4 -b 0.0.0.0:8080 wsgi:app
    app.run(host='0.0.0.0', port=8080, debug=True)
