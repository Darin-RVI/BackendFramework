"""
Flask Frontend Application
"""
import os
import requests
from flask import Flask, render_template, jsonify

API_URL = os.getenv('API_URL', 'http://nginx_api:80')


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    @app.route('/')
    def index():
        """Homepage"""
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'frontend'
        }), 200
    
    @app.route('/api-status')
    def api_status():
        """Check API status"""
        try:
            response = requests.get(f'{API_URL}/health', timeout=5)
            return jsonify({
                'api_reachable': True,
                'api_status': response.json()
            }), 200
        except Exception as e:
            return jsonify({
                'api_reachable': False,
                'error': str(e)
            }), 503
    
    return app
