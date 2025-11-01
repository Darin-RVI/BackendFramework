# Frontend Development Guide

This guide covers building frontend applications with the Backend Framework, including server-side rendering, static file management, and integration with the API service.

## Architecture

The frontend service is built with:

- **Flask**: Web framework for serving pages
- **Jinja2**: Template engine for HTML rendering
- **uWSGI**: Production WSGI server
- **Nginx**: Reverse proxy for static file serving

## Project Structure

```
frontend/
├── Dockerfile
├── requirements.txt
├── uwsgi.ini
├── wsgi.py
├── app.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── about.html
│   └── partials/
│       ├── header.html
│       └── footer.html
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
└── utils/
    └── api_client.py
```

## Templates

### Base Template

Create `templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{% block meta_description %}Backend Framework Application{% endblock %}">
    <title>{% block title %}Backend Framework{% endblock %}</title>
    
    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% include 'partials/header.html' %}
    
    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </main>
    
    {% include 'partials/footer.html' %}
    
    <!-- JavaScript -->
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Header Partial

Create `templates/partials/header.html`:

```html
<header class="site-header">
    <nav class="navbar">
        <div class="container">
            <a href="{{ url_for('index') }}" class="logo">
                <h1>Backend Framework</h1>
            </a>
            <ul class="nav-menu">
                <li><a href="{{ url_for('index') }}">Home</a></li>
                <li><a href="{{ url_for('about') }}">About</a></li>
                {% if current_user.is_authenticated %}
                    <li><a href="{{ url_for('dashboard') }}">Dashboard</a></li>
                    <li><a href="{{ url_for('logout') }}">Logout</a></li>
                {% else %}
                    <li><a href="{{ url_for('login') }}">Login</a></li>
                {% endif %}
            </ul>
        </div>
    </nav>
</header>
```

### Footer Partial

Create `templates/partials/footer.html`:

```html
<footer class="site-footer">
    <div class="container">
        <p>&copy; {{ current_year }} Backend Framework. All rights reserved.</p>
        <p>
            <a href="{{ url_for('privacy') }}">Privacy Policy</a> |
            <a href="{{ url_for('terms') }}">Terms of Service</a>
        </p>
    </div>
</footer>
```

### Content Pages

Create `templates/dashboard.html`:

```html
{% extends "base.html" %}

{% block title %}Dashboard - Backend Framework{% endblock %}

{% block content %}
<div class="dashboard">
    <h1>Welcome, {{ user.username }}!</h1>
    
    <div class="stats-grid">
        <div class="stat-card">
            <h3>Total Items</h3>
            <p class="stat-number">{{ stats.total_items }}</p>
        </div>
        <div class="stat-card">
            <h3>Active Users</h3>
            <p class="stat-number">{{ stats.active_users }}</p>
        </div>
        <div class="stat-card">
            <h3>Recent Activity</h3>
            <p class="stat-number">{{ stats.recent_activity }}</p>
        </div>
    </div>
    
    <div class="recent-items">
        <h2>Recent Items</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Date</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td>{{ item.name }}</td>
                    <td>{{ item.category }}</td>
                    <td>${{ item.price }}</td>
                    <td>{{ item.created_at.strftime('%Y-%m-%d') }}</td>
                    <td>
                        <a href="{{ url_for('edit_item', id=item.id) }}">Edit</a>
                        <a href="{{ url_for('delete_item', id=item.id) }}" onclick="return confirm('Are you sure?')">Delete</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

## Static Files

### CSS Styling

Create `static/css/style.css`:

```css
/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #4caf50;
    --danger-color: #f44336;
    --warning-color: #ff9800;
    --text-color: #333;
    --bg-color: #f5f5f5;
    --white: #ffffff;
    --shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
.site-header {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: var(--white);
    padding: 1rem 0;
    box-shadow: var(--shadow);
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo h1 {
    font-size: 1.5rem;
    color: var(--white);
}

.nav-menu {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-menu a {
    color: var(--white);
    text-decoration: none;
    transition: opacity 0.3s;
}

.nav-menu a:hover {
    opacity: 0.8;
}

/* Main Content */
main {
    min-height: calc(100vh - 200px);
    padding: 2rem 0;
}

/* Cards */
.card {
    background: var(--white);
    border-radius: 8px;
    padding: 2rem;
    box-shadow: var(--shadow);
    margin-bottom: 1.5rem;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    text-decoration: none;
    transition: all 0.3s;
}

.btn-primary {
    background: var(--primary-color);
    color: var(--white);
}

.btn-primary:hover {
    background: #5568d3;
}

.btn-success {
    background: var(--success-color);
    color: var(--white);
}

.btn-danger {
    background: var(--danger-color);
    color: var(--white);
}

/* Forms */
.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.form-control {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

.form-control:focus {
    outline: none;
    border-color: var(--primary-color);
}

/* Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--white);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow);
}

.data-table th,
.data-table td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

.data-table th {
    background: var(--primary-color);
    color: var(--white);
    font-weight: 600;
}

.data-table tr:hover {
    background: #f9f9f9;
}

/* Alerts */
.flash-messages {
    margin-bottom: 1.5rem;
}

.alert {
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
}

.alert-success {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.alert-error {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.alert-warning {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: var(--white);
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: var(--shadow);
    text-align: center;
}

.stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    color: var(--primary-color);
    margin-top: 0.5rem;
}

/* Footer */
.site-footer {
    background: #333;
    color: var(--white);
    text-align: center;
    padding: 2rem 0;
    margin-top: 3rem;
}

.site-footer a {
    color: var(--white);
    text-decoration: none;
}

/* Responsive */
@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 1rem;
    }
    
    .nav-menu {
        flex-direction: column;
        gap: 0.5rem;
        text-align: center;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
}
```

### JavaScript

Create `static/js/app.js`:

```javascript
// API Client
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL || 'http://localhost:8080/api';
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint);
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Initialize API client
const api = new APIClient();

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application loaded');
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
    
    // Form validation
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
});

// Form submission handler
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    try {
        const response = await api.post(form.action, data);
        showMessage('Success!', 'success');
        form.reset();
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// Show message
function showMessage(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.flash-messages') || 
                     document.querySelector('main');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

// Utility functions
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}
```

## API Integration

### API Client Module

Create `utils/api_client.py`:

```python
import os
import requests
from typing import Optional, Dict, Any
from flask import current_app

class APIClient:
    """Client for making requests to the API service"""
    
    def __init__(self):
        self.base_url = os.getenv('API_URL', 'http://nginx_api:80')
        self.timeout = 30
        
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Frontend-Client/1.0'
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=default_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"API request failed: {str(e)}")
            raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET request"""
        return self._request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        """POST request"""
        return self._request('POST', endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict) -> Dict:
        """PUT request"""
        return self._request('PUT', endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict:
        """DELETE request"""
        return self._request('DELETE', endpoint)
```

### Using the API Client

Update `frontend/app.py`:

```python
import os
from flask import Flask, render_template, request, flash, redirect, url_for
from datetime import datetime
from utils.api_client import APIClient

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    api_client = APIClient()
    
    @app.context_processor
    def inject_globals():
        """Inject global variables into templates"""
        return {
            'current_year': datetime.now().year
        }
    
    @app.route('/')
    def index():
        """Homepage"""
        try:
            # Fetch data from API
            data = api_client.get('/api/items', params={'limit': 10})
            items = data.get('items', [])
        except Exception as e:
            app.logger.error(f"Failed to fetch items: {str(e)}")
            items = []
            flash('Unable to load data from API', 'error')
        
        return render_template('index.html', items=items)
    
    @app.route('/dashboard')
    def dashboard():
        """User dashboard"""
        try:
            stats = api_client.get('/api/stats')
            items = api_client.get('/api/items', params={'limit': 20})
            
            return render_template(
                'dashboard.html',
                stats=stats,
                items=items.get('items', [])
            )
        except Exception as e:
            app.logger.error(f"Dashboard error: {str(e)}")
            flash('Error loading dashboard', 'error')
            return redirect(url_for('index'))
    
    @app.route('/items/create', methods=['GET', 'POST'])
    def create_item():
        """Create new item"""
        if request.method == 'POST':
            try:
                data = {
                    'name': request.form.get('name'),
                    'description': request.form.get('description'),
                    'price': float(request.form.get('price', 0))
                }
                
                result = api_client.post('/api/items', data)
                flash('Item created successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                app.logger.error(f"Create item error: {str(e)}")
                flash('Error creating item', 'error')
        
        return render_template('items/create.html')
    
    @app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
    def edit_item(item_id):
        """Edit existing item"""
        try:
            if request.method == 'POST':
                data = {
                    'name': request.form.get('name'),
                    'description': request.form.get('description'),
                    'price': float(request.form.get('price', 0))
                }
                
                api_client.put(f'/api/items/{item_id}', data)
                flash('Item updated successfully!', 'success')
                return redirect(url_for('dashboard'))
            
            # GET request - fetch item data
            item = api_client.get(f'/api/items/{item_id}')
            return render_template('items/edit.html', item=item)
        except Exception as e:
            app.logger.error(f"Edit item error: {str(e)}")
            flash('Error processing request', 'error')
            return redirect(url_for('dashboard'))
    
    @app.route('/items/<int:item_id>/delete', methods=['POST'])
    def delete_item(item_id):
        """Delete item"""
        try:
            api_client.delete(f'/api/items/{item_id}')
            flash('Item deleted successfully!', 'success')
        except Exception as e:
            app.logger.error(f"Delete item error: {str(e)}")
            flash('Error deleting item', 'error')
        
        return redirect(url_for('dashboard'))
    
    @app.route('/health')
    def health():
        """Health check"""
        return {'status': 'healthy', 'service': 'frontend'}, 200
    
    return app
```

## Forms

Create `templates/items/create.html`:

```html
{% extends "base.html" %}

{% block title %}Create Item{% endblock %}

{% block content %}
<div class="card">
    <h1>Create New Item</h1>
    
    <form method="POST" action="{{ url_for('create_item') }}">
        <div class="form-group">
            <label for="name">Name *</label>
            <input type="text" id="name" name="name" class="form-control" required>
        </div>
        
        <div class="form-group">
            <label for="description">Description</label>
            <textarea id="description" name="description" class="form-control" rows="4"></textarea>
        </div>
        
        <div class="form-group">
            <label for="price">Price *</label>
            <input type="number" id="price" name="price" class="form-control" step="0.01" required>
        </div>
        
        <div class="form-group">
            <button type="submit" class="btn btn-primary">Create Item</button>
            <a href="{{ url_for('dashboard') }}" class="btn">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
```

## Best Practices

### 1. Error Handling
Always handle API errors gracefully and provide user feedback.

### 2. Loading States
Show loading indicators for async operations.

### 3. Caching
Cache API responses where appropriate to reduce load.

### 4. Security
- Validate all user input
- Use CSRF protection
- Sanitize output in templates

### 5. Performance
- Minimize API calls
- Optimize images
- Use CDN for static assets in production

## Next Steps

- Review [API Documentation](API_DOCUMENTATION.md) for available endpoints
- Check [Database Guide](DATABASE.md) for data structure
- See [Deployment Guide](DEPLOYMENT.md) for production setup
