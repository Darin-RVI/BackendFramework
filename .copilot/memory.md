# Backend Framework - Copilot Memory

This file contains important context and patterns that GitHub Copilot should remember when working with this project.

## Project Identity

**Name**: Backend Framework
**Type**: Docker-based microservices backend architecture
**Primary Language**: Python 3.11
**Framework**: Flask
**Database**: PostgreSQL 15
**Container Orchestration**: Docker Compose
**Web Server**: Nginx
**WSGI Server**: uWSGI

## Project Purpose

A production-ready, scalable backend framework for building:
- REST APIs
- Full-stack web applications
- Microservices architectures
- API-first applications
- Multi-tenant platforms

## Architecture Patterns

### Service Architecture
- **Separation of Concerns**: API and Frontend are separate services
- **Reverse Proxy Pattern**: Nginx handles all external traffic
- **Container Isolation**: Each service runs in its own container
- **Shared Database**: PostgreSQL accessed by API service only
- **Frontend-API Communication**: Frontend calls API via internal Docker network

### Code Patterns

#### Flask Application Factory
```python
def create_app():
    app = Flask(__name__)
    # Configure app
    # Initialize extensions
    # Register blueprints
    return app
```

#### Blueprint Pattern for Routes
```python
api_bp = Blueprint('api', __name__)

@api_bp.route('/endpoint', methods=['GET'])
def endpoint():
    return jsonify(data), 200
```

#### SQLAlchemy Model Pattern
```python
class Model(db.Model):
    __tablename__ = 'table_name'
    id = db.Column(db.Integer, primary_key=True)
    
    def to_dict(self):
        return {'id': self.id}
```

#### API Client Pattern (Frontend)
```python
class APIClient:
    def __init__(self):
        self.base_url = os.getenv('API_URL')
    
    def _request(self, method, endpoint, **kwargs):
        # Request logic
        pass
```

## Environment Variables

### Required Variables
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT signing key
- `DATABASE_URL`: Full PostgreSQL connection string
- `API_URL`: API service URL for frontend
- `FLASK_ENV`: Environment (development/production)
- `DEBUG`: Debug mode flag

### Service Ports
- PostgreSQL: 5432 (internal), configurable external
- API: 8080 (external), 8080 (internal)
- Frontend: 8000 (external), 8000 (internal)
- PgAdmin: 5050 (external)

## Docker Service Names

When services communicate internally, use these names:
- `postgres` - PostgreSQL database
- `api` - API service
- `frontend` - Frontend service
- `nginx_api` - API Nginx proxy
- `nginx_frontend` - Frontend Nginx proxy
- `pgadmin` - PgAdmin service
- `redis` - Redis cache (if enabled)

## Common Patterns and Conventions

### File Naming
- Python files: `snake_case.py`
- Templates: `snake_case.html`
- CSS/JS: `kebab-case.css`, `kebab-case.js`
- Markdown docs: `UPPERCASE.md`

### Code Style
- **Python**: Follow PEP 8
- **Line Length**: 100 characters for Python
- **Indentation**: 4 spaces for Python, 2 for HTML/CSS/JS
- **Imports**: Standard library → Third party → Local
- **Docstrings**: Google style for functions/classes

### API Response Format
```json
{
    "success": true/false,
    "data": {...},
    "error": "message"
}
```

### HTTP Status Codes
- 200: Successful GET, PUT, PATCH
- 201: Successful POST (created)
- 204: Successful DELETE
- 400: Bad request (validation error)
- 401: Unauthorized (not authenticated)
- 403: Forbidden (not authorized)
- 404: Not found
- 500: Internal server error

## Database Conventions

### Table Naming
- Lowercase, plural: `users`, `products`, `categories`
- Use underscores for multi-word: `order_items`

### Column Naming
- Snake_case: `user_id`, `created_at`, `is_active`
- Primary keys: `id`
- Foreign keys: `{table_singular}_id`
- Timestamps: `created_at`, `updated_at`, `deleted_at`

### Relationships
- One-to-Many: Use `db.relationship()` with `backref`
- Many-to-Many: Use association table
- Cascade: Specify cascade behavior explicitly

## Error Handling Strategy

### API Errors
- Always return JSON responses
- Include error message and status code
- Log errors for debugging
- Use try-except blocks for database operations
- Rollback database session on errors

### Frontend Errors
- Display user-friendly messages
- Flash messages for form submissions
- Graceful degradation when API unavailable
- Loading states for async operations

## Security Practices

### Implemented
- Environment-based configuration
- CORS configuration
- Security headers in Nginx
- Non-root container users
- Network isolation
- Input validation
- Prepared statements (SQLAlchemy ORM)

### To Implement in Production
- JWT authentication
- Rate limiting
- HTTPS/SSL
- Secrets management
- Input sanitization
- CSRF protection
- SQL injection prevention
- XSS protection

## Testing Strategy

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Use pytest fixtures

### Integration Tests
- Test API endpoints
- Test database operations
- Use test database

### Test Location
- API tests: `api/tests/`
- Frontend tests: `frontend/tests/`

## Common Development Tasks

### Adding a New API Endpoint
1. Define route in `api/routes.py`
2. Create/update model in `api/models.py` if needed
3. Add business logic in `api/services/` if complex
4. Test endpoint manually or with tests
5. Document in API_DOCUMENTATION.md

### Adding a New Frontend Page
1. Create route in `frontend/app.py`
2. Create template in `frontend/templates/`
3. Add styles in `frontend/static/css/`
4. Add JavaScript if needed in `frontend/static/js/`
5. Update navigation in base template

### Database Migration
1. Create/update model in `api/models.py`
2. Generate migration: `flask db migrate -m "description"`
3. Review migration file
4. Apply: `flask db upgrade`
5. Test changes

## Performance Optimization

### Database
- Add indexes to frequently queried columns
- Use eager loading for relationships
- Implement pagination for large datasets
- Use database connection pooling (configured)

### API
- Enable caching for static data
- Use Redis for session storage
- Optimize query complexity
- Implement response compression (Nginx)

### Frontend
- Minimize API calls
- Cache API responses
- Lazy load images
- Minify CSS/JS in production

## Logging Standards

### Log Levels
- DEBUG: Detailed development info
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### What to Log
- API requests/responses (in development)
- Database errors
- Authentication failures
- Validation errors
- Performance metrics
- Security events

### Where Logs Are Stored
- Development: Container stdout/stderr
- Production: `logs/` directory with rotation

## Deployment Checklist

Before deploying to production:
- [ ] Set `DEBUG=False`
- [ ] Set `FLASK_ENV=production`
- [ ] Use strong passwords
- [ ] Generate secure secret keys
- [ ] Configure SSL/TLS
- [ ] Set up database backups
- [ ] Configure logging to files
- [ ] Remove auto-reload from uWSGI
- [ ] Set resource limits
- [ ] Configure monitoring
- [ ] Test all endpoints
- [ ] Review security headers
- [ ] Update dependencies
- [ ] Document deployment process

## Common Commands

### Docker
```powershell
# Start services
docker-compose up

# Rebuild and start
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service]

# Access container shell
docker-compose exec [service] bash

# Clean up
docker-compose down -v
docker system prune -a
```

### Database
```powershell
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d backend_db

# Run migrations
docker-compose exec api flask db upgrade

# Create migration
docker-compose exec api flask db migrate -m "message"

# Backup
docker-compose exec postgres pg_dump -U postgres backend_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres backend_db < backup.sql
```

### Python Shell
```powershell
# API Python shell
docker-compose exec api python

# Frontend Python shell
docker-compose exec frontend python

# Flask shell (with app context)
docker-compose exec api flask shell
```

## Directory Purpose

- **api/**: Backend API service code
- **frontend/**: Frontend web application code
- **docker/**: Docker and Nginx configurations
- **docs/**: Comprehensive documentation
- **scripts/**: Utility scripts (backup, deploy, etc.)
- **logs/**: Application logs (gitignored)
- **backups/**: Database backups (gitignored)
- **.copilot/**: Copilot configuration and memory

## Dependencies Management

### When Adding Dependencies
1. Add to appropriate `requirements.txt`
2. Rebuild Docker image
3. Document if it's a major dependency
4. Pin versions for reproducibility

### When Updating Dependencies
1. Test in development first
2. Check for breaking changes
3. Update requirements.txt
4. Rebuild images
5. Test thoroughly

## Code Review Guidelines

When reviewing or writing code:
- ✅ Follow established patterns
- ✅ Add error handling
- ✅ Include docstrings
- ✅ Validate user input
- ✅ Use type hints where appropriate
- ✅ Write clear variable names
- ✅ Keep functions small and focused
- ✅ Add comments for complex logic
- ✅ Test edge cases
- ✅ Check for security issues

## Known Limitations

- Frontend and API must be on same Docker network
- PostgreSQL port should not be exposed in production
- Static files served by Nginx for performance
- Session storage is in-memory (use Redis for production)
- No built-in rate limiting (implement in production)

## Future Enhancements

Potential improvements to consider:
- Kubernetes deployment configurations
- GraphQL API option
- WebSocket support
- Celery for background tasks
- ElasticSearch for search
- Prometheus/Grafana for monitoring
- CI/CD pipeline configurations
- Multi-stage Docker builds
- Health check endpoints with detailed status

## Important Notes for Copilot

When generating code for this project:
1. **Always use service names** in Docker network (not localhost)
2. **Use environment variables** for configuration
3. **Follow Flask application factory pattern**
4. **Use SQLAlchemy ORM** for database operations
5. **Return JSON** from API endpoints
6. **Use Jinja2** for frontend templates
7. **Include error handling** in all routes
8. **Use try-except** for database operations
9. **Log errors** appropriately
10. **Follow existing code style** and patterns

## Version Information

- Python: 3.11
- Flask: 3.0.0
- PostgreSQL: 15 (Alpine)
- SQLAlchemy: 2.0.23
- uWSGI: 2.0.23
- Nginx: Alpine (latest)
- Docker Compose: 3.8

This memory file helps Copilot understand the project context and generate code that follows established patterns and best practices.
