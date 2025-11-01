"""
WSGI entry point for the API application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your application
# For Flask:
from app import create_app
app = create_app()

# For FastAPI:
# from app.main import app

# For Django:
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# django.setup()
# from django.core.wsgi import get_wsgi_application
# app = get_wsgi_application()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
