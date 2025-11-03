# Copilot Instructions

This file provides specific instructions to GitHub Copilot when working with the Backend Framework project.

## General Instructions

When providing code suggestions or completions:

1. **Use the established patterns** from this project
2. **Reference memory.md** for project context
3. **Follow the architecture** described in the documentation
4. **Maintain consistency** with existing code style
5. **Prioritize security** in all suggestions
6. **Include error handling** by default
7. **Add appropriate logging** for important operations
8. **Use type hints** in Python code
9. **Write self-documenting code** with clear names
10. **Add docstrings** for functions and classes

## Code Style Preferences

### Python
- Follow PEP 8 strictly
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use f-strings for string formatting
- Prefer list comprehensions over map/filter
- Use context managers (with statements)
- Add type hints to function signatures
- Use Google-style docstrings

### JavaScript
- Use modern ES6+ syntax
- Use const/let, never var
- Prefer arrow functions
- Use async/await over promises
- Use template literals for strings
- Add JSDoc comments for functions

### HTML/CSS
- Use semantic HTML5 elements
- Keep CSS modular and reusable
- Use CSS variables for theming
- Mobile-first responsive design
- Use BEM naming for CSS classes (optional)

## Framework-Specific Patterns

### Flask Routes

Always use this pattern for multi-tenant, OAuth-protected routes:

```python
from tenant_context import require_tenant
from oauth2 import require_oauth

@blueprint.route('/endpoint', methods=['GET', 'POST'])
@require_tenant
@require_oauth(scope='read write')
def endpoint_name(tenant, token):
    """Docstring explaining what this endpoint does"""
    try:
        # Validate tenant access
        user = User.query.get(token.user_id)
        if not validate_tenant_access(user, tenant):
            return jsonify({'error': 'Access denied'}), 403
        
        # Route logic with tenant context
        data = tenant_filter(Model).all()
        return jsonify({'success': True, 'data': [item.to_dict() for item in data]}), 200
    except Exception as e:
        app.logger.error(f"Error in endpoint_name: {str(e)}")
        return jsonify({'success': False, 'error': 'Error message'}), 500
```

For public endpoints (no authentication required):

```python
@blueprint.route('/public', methods=['GET'])
def public_endpoint():
    """Public endpoint - no authentication required"""
    try:
        return jsonify({'success': True, 'data': 'public data'}), 200
    except Exception as e:
        app.logger.error(f"Error in public_endpoint: {str(e)}")
        return jsonify({'success': False, 'error': 'Error message'}), 500
```

### Database Models

Always include for multi-tenant models:

- `__tablename__` attribute
- `tenant_id` foreign key to tenants table
- `__repr__` method
- `to_dict()` method for JSON serialization
- Proper relationships with cascade rules
- Indexes on frequently queried columns (including tenant_id)
- Composite foreign key constraints for tenant isolation

Example multi-tenant model:

```python
class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure user belongs to same tenant
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['tenant_id', 'user_id'],
            ['users.tenant_id', 'users.id']
        ),
        db.Index('idx_documents_tenant_created', 'tenant_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Document {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

### API Responses
Always return this structure:
```python
{
    'success': bool,
    'data': dict or list,
    'error': str (optional),
    'message': str (optional)
}
```

### Environment Variables
Always use:
```python
import os
value = os.getenv('VARIABLE_NAME', 'default_value')
```

Never hardcode sensitive information.

## Security Guidelines

When generating code:

1. **Never hardcode credentials** - use environment variables
2. **Validate all inputs** - check type, length, format
3. **Sanitize outputs** - escape HTML, validate JSON
4. **Use parameterized queries** - SQLAlchemy ORM does this
5. **Implement authentication** - JWT tokens for protected routes
6. **Add authorization checks** - verify permissions
7. **Use HTTPS in production** - configure in Nginx
8. **Implement rate limiting** - protect against abuse
9. **Log security events** - failed logins, etc.
10. **Handle errors safely** - don't expose stack traces

## Common Completions

### When I type "route" suggest:

```python
from tenant_context import require_tenant
from oauth2 import require_oauth

@api_bp.route('/endpoint', methods=['GET'])
@require_tenant
@require_oauth(scope='read')
def get_endpoint(tenant, token):
    """Description"""
    try:
        # Validate tenant access
        user = User.query.get(token.user_id)
        if not validate_tenant_access(user, tenant):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Logic here with tenant context
        data = tenant_filter(Model).all()
        return jsonify({'success': True, 'data': [item.to_dict() for item in data]}), 200
    except Exception as e:
        app.logger.error(f"Error in get_endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

### When I type "model" suggest:

```python
class ModelName(db.Model):
    __tablename__ = 'table_name'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes for multi-tenant queries
    __table_args__ = (
        db.Index('idx_table_name_tenant', 'tenant_id'),
    )
    
    def __repr__(self):
        return f'<ModelName {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

### When I type "oauth-client" suggest:

```python
from oauth2 import create_oauth_client

# Create OAuth client for tenant
client = create_oauth_client(
    tenant_id=tenant.id,
    user_id=current_user.id,
    client_name="My Application",
    redirect_uris=["http://localhost:3000/callback"],
    grant_types=["authorization_code", "refresh_token"],
    scope="read write profile"
)
```

### When I type "tenant-query" suggest:

```python
from tenant_context import tenant_filter, TenantContext

# Use tenant_filter for automatic filtering
items = tenant_filter(MyModel).filter_by(active=True).all()

# Or manual tenant filtering
tenant_id = TenantContext.get_tenant_id()
items = MyModel.query.filter_by(tenant_id=tenant_id, active=True).all()
```

### When I type "template" suggest:
```html
{% extends "base.html" %}

{% block title %}Page Title{% endblock %}

{% block content %}
<div class="container">
    <h1>{{ title }}</h1>
    <!-- Content here -->
</div>
{% endblock %}
```

### When I type "api-call" suggest:
```javascript
async function fetchData() {
    try {
        const response = await api.get('/endpoint');
        // Handle response
    } catch (error) {
        console.error('Error:', error);
        showMessage(error.message, 'error');
    }
}
```

## Docker-Specific Instructions

### Service Communication
When connecting services:
- Use service names from docker-compose.yml
- Never use "localhost" between containers
- Use internal ports (not exposed ports)

Example:
```python
# Correct
DATABASE_URL = 'postgresql://user:pass@postgres:5432/db'

# Wrong
DATABASE_URL = 'postgresql://user:pass@localhost:5432/db'
```

### Environment Variables in Docker
Always reference from .env file:
```yaml
environment:
  - VARIABLE=${VARIABLE}
```

## Testing Instructions

When generating tests:

1. Use pytest framework
2. Create fixtures for common setup
3. Test happy path and error cases
4. Mock external dependencies
5. Test database operations with test database
6. Include docstrings explaining test purpose

Example:
```python
def test_endpoint_success(client):
    """Test successful API call to endpoint"""
    response = client.get('/api/endpoint')
    assert response.status_code == 200
    assert 'data' in response.json()
```

## Documentation Instructions

When suggesting documentation:

1. Use Markdown format
2. Include code examples
3. Add clear step-by-step instructions
4. Include troubleshooting tips
5. Use tables for structured data
6. Add command examples with syntax highlighting
7. Cross-reference related documentation

## Error Handling Preferences

Always include:
- Try-except blocks for risky operations
- Specific exception types when possible
- Logging of errors
- User-friendly error messages
- Appropriate HTTP status codes
- Database rollback on errors

Example:
```python
try:
    user = User.query.get_or_404(user_id)
    # Operations
    db.session.commit()
    return jsonify({'success': True}), 200
except SQLAlchemyError as e:
    db.session.rollback()
    app.logger.error(f"Database error: {str(e)}")
    return jsonify({'success': False, 'error': 'Database error'}), 500
except Exception as e:
    app.logger.error(f"Unexpected error: {str(e)}")
    return jsonify({'success': False, 'error': 'Internal error'}), 500
```

## Performance Considerations

When suggesting code:

1. **Use pagination** for large datasets
2. **Eager load** relationships to avoid N+1 queries
3. **Index** frequently queried columns
4. **Cache** expensive operations
5. **Minimize** database queries
6. **Use bulk operations** for multiple inserts/updates
7. **Optimize** SQL queries
8. **Compress** responses in Nginx
9. **Lazy load** images and assets
10. **Minify** CSS/JS in production

## Logging Preferences

Use this logging pattern:
```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: Detailed information
logger.debug(f"Processing item {item_id}")

# INFO: General information
logger.info(f"User {user_id} logged in")

# WARNING: Warning messages
logger.warning(f"Low stock for product {product_id}")

# ERROR: Error messages
logger.error(f"Failed to process order: {str(e)}")

# CRITICAL: Critical errors
logger.critical(f"Database connection lost")
```

## Comments and Documentation

Add comments for:
- Complex algorithms or logic
- Non-obvious code decisions
- Workarounds for bugs or limitations
- Configuration values
- Regular expressions
- Business logic rules

Don't add comments for:
- Self-explanatory code
- Restating what the code does
- Obvious operations

## Git Commit Message Style

When suggesting commit messages:
- Use imperative mood ("Add feature" not "Added feature")
- Start with capital letter
- No period at the end
- First line: brief summary (50 chars)
- Blank line
- Detailed description if needed

Example:
```
Add user authentication with JWT

- Implement login/logout endpoints
- Add JWT token generation and validation
- Protect sensitive routes with @jwt_required
- Update API documentation
```

## Code Organization

When adding new code:

1. **API**: Group related endpoints in same blueprint
2. **Models**: One model per class, related models in same file
3. **Services**: Business logic separate from routes
4. **Utils**: Reusable helper functions
5. **Middleware**: Custom middleware in separate files
6. **Templates**: Organize by feature/section
7. **Static**: Separate CSS, JS, images by purpose

## Accessibility Considerations

When generating HTML/CSS:
- Use semantic HTML elements
- Add ARIA labels where needed
- Ensure keyboard navigation works
- Provide alt text for images
- Use sufficient color contrast
- Support screen readers
- Make forms accessible

## Mobile Responsiveness

When suggesting CSS:
- Use relative units (rem, em, %)
- Implement mobile-first design
- Use CSS Grid/Flexbox for layouts
- Add media queries for breakpoints
- Test on multiple screen sizes
- Ensure touch targets are large enough

## Internationalization

While not currently implemented, keep in mind:
- Use template variables for user-facing text
- Don't hardcode strings in code
- Use date/time formatting functions
- Consider RTL languages in CSS

## Remember

This is a **production-ready framework** designed for:
- Scalability
- Security
- Maintainability
- Performance
- Developer experience

All suggestions should align with these goals and the established architecture.
