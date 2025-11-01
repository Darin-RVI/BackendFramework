"""
WSGI entry point for the Frontend application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your application
from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
