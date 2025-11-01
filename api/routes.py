"""
API Routes
"""
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__)


@api_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({'message': 'pong'}), 200


@api_bp.route('/status', methods=['GET'])
def status():
    """API status endpoint"""
    return jsonify({
        'status': 'running',
        'api_version': '1.0.0'
    }), 200


# Add your API routes here
# Example:
# @api_bp.route('/users', methods=['GET'])
# def get_users():
#     return jsonify({'users': []}), 200
