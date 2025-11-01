# API Development Guide

This guide covers everything you need to build robust, scalable APIs with the Backend Framework.

## Architecture Overview

The API service is built on:
- **Flask**: Lightweight and flexible web framework
- **SQLAlchemy**: Powerful ORM for database operations
- **uWSGI**: Production-grade WSGI server
- **Nginx**: Reverse proxy and load balancer

## Project Structure

```
api/
├── Dockerfile              # Container image definition
├── requirements.txt        # Python dependencies
├── uwsgi.ini              # uWSGI server configuration
├── wsgi.py                # WSGI entry point
├── app.py                 # Flask application factory
├── routes.py              # API route definitions
├── models.py              # Database models
├── services/              # Business logic layer
│   ├── __init__.py
│   └── user_service.py
├── middleware/            # Custom middleware
│   ├── __init__.py
│   └── auth.py
├── utils/                 # Utility functions
│   ├── __init__.py
│   └── validators.py
└── tests/                 # Unit and integration tests
    ├── __init__.py
    └── test_routes.py
```

## Creating API Endpoints

### Basic Endpoint

```python
# routes.py
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api', __name__)

@api_bp.route('/items', methods=['GET'])
def get_items():
    """Retrieve all items"""
    return jsonify({
        'items': [],
        'count': 0
    }), 200
```

### Endpoint with Path Parameters

```python
@api_bp.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Retrieve a specific item"""
    # Fetch item from database
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict()), 200
```

### Endpoint with Query Parameters

```python
@api_bp.route('/items/search', methods=['GET'])
def search_items():
    """Search items with filters"""
    # Get query parameters
    query = request.args.get('q', '')
    category = request.args.get('category', None)
    limit = request.args.get('limit', 10, type=int)
    
    # Build query
    items_query = Item.query
    if query:
        items_query = items_query.filter(Item.name.ilike(f'%{query}%'))
    if category:
        items_query = items_query.filter(Item.category == category)
    
    items = items_query.limit(limit).all()
    
    return jsonify({
        'items': [item.to_dict() for item in items],
        'count': len(items)
    }), 200
```

### POST Endpoint with JSON Body

```python
from flask import request
from app import db
from models import Item

@api_bp.route('/items', methods=['POST'])
def create_item():
    """Create a new item"""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    # Create new item
    item = Item(
        name=data['name'],
        description=data.get('description', ''),
        price=data.get('price', 0.0)
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify(item.to_dict()), 201
```

### PUT/PATCH Endpoint for Updates

```python
@api_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an existing item"""
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        item.name = data['name']
    if 'description' in data:
        item.description = data['description']
    if 'price' in data:
        item.price = data['price']
    
    db.session.commit()
    
    return jsonify(item.to_dict()), 200
```

### DELETE Endpoint

```python
@api_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an item"""
    item = Item.query.get_or_404(item_id)
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Item deleted successfully'}), 200
```

## Database Models

### Creating Models

```python
# models.py
from app import db
from datetime import datetime
import uuid

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), default=0.0)
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='item', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Item {self.name}>'


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat()
        }
```

### Database Migrations

Using Flask-Migrate:

```powershell
# Initialize migrations (first time only)
docker-compose exec api flask db init

# Create a new migration
docker-compose exec api flask db migrate -m "Add items and reviews tables"

# Apply migrations
docker-compose exec api flask db upgrade

# Rollback migration
docker-compose exec api flask db downgrade
```

## Error Handling

### Custom Error Handlers

```python
# app.py
from flask import jsonify

def create_app():
    app = Flask(__name__)
    
    # ... configuration ...
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    return app
```

### Try-Except in Routes

```python
@api_bp.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Retrieve a specific item with error handling"""
    try:
        item = Item.query.get_or_404(item_id)
        return jsonify(item.to_dict()), 200
    except Exception as e:
        return jsonify({
            'error': 'Error retrieving item',
            'message': str(e)
        }), 500
```

## Authentication & Authorization

### JWT Authentication

Install required package:
```python
# requirements.txt
Flask-JWT-Extended==4.5.3
```

Configure JWT:
```python
# app.py
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)
    
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    
    jwt = JWTManager(app)
    
    return app
```

Login endpoint:
```python
# routes.py
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200
```

Protected endpoint:
```python
@api_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile (requires authentication)"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    
    return jsonify(user.to_dict()), 200
```

## Request Validation

### Using Marshmallow

```python
# Install marshmallow
# requirements.txt: marshmallow==3.20.1

from marshmallow import Schema, fields, validate, ValidationError

class ItemSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str()
    price = fields.Float(validate=validate.Range(min=0))
    category = fields.Str(validate=validate.Length(max=100))

@api_bp.route('/items', methods=['POST'])
def create_item():
    """Create item with validation"""
    schema = ItemSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    
    item = Item(**data)
    db.session.add(item)
    db.session.commit()
    
    return jsonify(schema.dump(item)), 201
```

## Pagination

```python
@api_bp.route('/items', methods=['GET'])
def get_items():
    """Get paginated items"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Limit per_page to reasonable maximum
    per_page = min(per_page, 100)
    
    pagination = Item.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }), 200
```

## CORS Configuration

```python
# app.py
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Allow all origins (development only)
    CORS(app)
    
    # Or configure specific origins (production)
    CORS(app, resources={
        r"/api/*": {
            "origins": ["https://yourdomain.com", "https://www.yourdomain.com"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    return app
```

## API Versioning

```python
# Create versioned blueprints
# routes_v1.py
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

@api_v1.route('/items', methods=['GET'])
def get_items_v1():
    # Version 1 implementation
    pass

# routes_v2.py
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

@api_v2.route('/items', methods=['GET'])
def get_items_v2():
    # Version 2 implementation with enhanced features
    pass

# app.py
from routes_v1 import api_v1
from routes_v2 import api_v2

def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_v1)
    app.register_blueprint(api_v2)
    return app
```

## Testing APIs

### Unit Tests

```python
# tests/test_routes.py
import pytest
from app import create_app, db
from models import Item

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_get_items(client):
    """Test GET /api/items"""
    response = client.get('/api/items')
    assert response.status_code == 200
    data = response.get_json()
    assert 'items' in data

def test_create_item(client):
    """Test POST /api/items"""
    response = client.post('/api/items', json={
        'name': 'Test Item',
        'price': 19.99
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Test Item'
```

Run tests:
```powershell
docker-compose exec api pytest
```

## Best Practices

### 1. Use HTTP Status Codes Correctly
- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### 2. Consistent Response Format

```python
def success_response(data, status_code=200):
    return jsonify({
        'success': True,
        'data': data
    }), status_code

def error_response(message, status_code=400):
    return jsonify({
        'success': False,
        'error': message
    }), status_code
```

### 3. Use Environment Variables
Never hardcode sensitive information:

```python
import os

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
API_KEY = os.getenv('API_KEY')
```

### 4. Implement Rate Limiting

```python
# requirements.txt: Flask-Limiter==3.5.0

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@api_bp.route('/items', methods=['POST'])
@limiter.limit("10 per minute")
def create_item():
    # Rate-limited endpoint
    pass
```

### 5. Log Important Events

```python
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/items', methods=['POST'])
def create_item():
    logger.info(f"Creating new item: {request.get_json()}")
    try:
        # Create item logic
        logger.info(f"Item created successfully: {item.id}")
    except Exception as e:
        logger.error(f"Error creating item: {str(e)}")
        raise
```

## Performance Optimization

### 1. Database Query Optimization

```python
# Eager loading to avoid N+1 queries
from sqlalchemy.orm import joinedload

items = Item.query.options(joinedload(Item.reviews)).all()

# Selective column loading
items = Item.query.with_entities(Item.id, Item.name).all()
```

### 2. Caching

```python
# requirements.txt: Flask-Caching==2.1.0

from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@api_bp.route('/items', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_items():
    # Cached for 5 minutes
    return jsonify(items)
```

### 3. Response Compression

Nginx handles this automatically with the configuration provided.

## Next Steps

- Review [Database Guide](DATABASE.md) for advanced queries
- Check [Deployment Guide](DEPLOYMENT.md) for production setup
- See [Troubleshooting](TROUBLESHOOTING.md) for common issues
