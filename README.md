# Backend Framework

A comprehensive Docker-based backend framework with PostgreSQL, Nginx API Gateway, and Nginx WSGI Frontend.

## Architecture

- **PostgreSQL**: Database server
- **API Service**: Python application (Flask/FastAPI/Django) with uWSGI
- **Nginx API Gateway**: Reverse proxy for API endpoints
- **Frontend Service**: Python web application with uWSGI
- **Nginx Frontend**: Reverse proxy for frontend application
- **PgAdmin**: Web-based PostgreSQL management tool (optional)

## Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8080 | Backend API endpoints |
| Frontend | 8000 | Web frontend application |
| PostgreSQL | 5432 | Database server |
| PgAdmin | 5050 | Database management UI |

## Quick Start

### Prerequisites

- Docker Desktop installed
- Git installed

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd BackendFramework
```

2. Copy the environment file and configure:
```bash
copy .env.example .env
```

Edit `.env` with your configuration (database credentials, secret keys, etc.)

3. Build and start the services:
```bash
docker-compose up --build
```

4. Access the services:
- Frontend: http://localhost:8000
- API: http://localhost:8080
- PgAdmin: http://localhost:5050

## Development

### Project Structure

```
BackendFramework/
├── api/                    # API application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── uwsgi.ini
│   ├── wsgi.py
│   ├── app.py
│   └── routes.py
├── frontend/              # Frontend application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── uwsgi.ini
│   ├── wsgi.py
│   ├── app.py
│   └── templates/
│       └── index.html
├── docker/
│   ├── nginx/
│   │   ├── api/          # Nginx config for API
│   │   │   ├── nginx.conf
│   │   │   └── conf.d/
│   │   │       └── api.conf
│   │   └── frontend/     # Nginx config for frontend
│   │       ├── nginx.conf
│   │       └── conf.d/
│   │           └── frontend.conf
│   └── postgres/
│       └── init/         # Database initialization scripts
│           └── 01-init.sql
├── docker-compose.yml
├── .env.example
└── README.md
```

### Running Commands

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f postgres
```

**Restart services:**
```bash
docker-compose restart
```

**Stop services:**
```bash
docker-compose down
```

**Stop and remove volumes (WARNING: deletes database data):**
```bash
docker-compose down -v
```

**Execute commands in containers:**
```bash
# Access API container shell
docker-compose exec api bash

# Access database
docker-compose exec postgres psql -U postgres -d backend_db

# Run database migrations (if using Flask-Migrate)
docker-compose exec api flask db upgrade
```

### Database Management

**Using PgAdmin:**
1. Access http://localhost:5050
2. Login with credentials from `.env`
3. Add new server:
   - Host: `postgres`
   - Port: `5432`
   - Database: Value from `POSTGRES_DB`
   - Username: Value from `POSTGRES_USER`
   - Password: Value from `POSTGRES_PASSWORD`

**Using command line:**
```bash
docker-compose exec postgres psql -U postgres -d backend_db
```

### API Development

The API is built with Flask (you can switch to FastAPI or Django). Key files:

- `api/app.py`: Application factory and configuration
- `api/routes.py`: API endpoints
- `api/wsgi.py`: WSGI entry point
- `api/uwsgi.ini`: uWSGI configuration

**Adding new endpoints:**
Edit `api/routes.py` and add your routes to the `api_bp` blueprint.

**Database models:**
Add your SQLAlchemy models in a new `models.py` file.

### Frontend Development

The frontend uses Flask with Jinja2 templates. Key files:

- `frontend/app.py`: Flask application
- `frontend/templates/`: HTML templates
- `frontend/static/`: Static files (CSS, JS, images)

**Adding pages:**
Add new routes in `frontend/app.py` and corresponding templates in `templates/`.

## Production Deployment

For production deployment:

1. Update environment variables in `.env`:
   - Set strong passwords
   - Change `FLASK_ENV` to `production`
   - Set `DEBUG=False`
   - Generate secure secret keys

2. Remove auto-reload from uWSGI configs:
   - Delete `py-autoreload = 1` from `api/uwsgi.ini` and `frontend/uwsgi.ini`

3. Enable HTTPS:
   - Add SSL certificates
   - Update Nginx configurations for SSL
   - Consider using Let's Encrypt with Certbot

4. Adjust resource limits in `docker-compose.yml`

5. Set up proper logging and monitoring

6. Configure backups for PostgreSQL data

## Troubleshooting

**Container fails to start:**
```bash
docker-compose logs <service-name>
```

**Database connection issues:**
- Verify environment variables in `.env`
- Check if PostgreSQL is healthy: `docker-compose ps`
- Ensure services are on the same network

**Port already in use:**
- Change port mappings in `.env` or `docker-compose.yml`

**Permission issues:**
```bash
# Reset permissions
docker-compose down
docker-compose up --build
```

## License

This project is open source and available under the MIT License.
