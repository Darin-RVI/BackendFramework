# Production Deployment Guide

This guide covers deploying the Backend Framework to production environments with best practices for security, performance, and reliability.

## Pre-Deployment Checklist

### Security
- [ ] Change all default passwords
- [ ] Generate secure secret keys
- [ ] Set `DEBUG=False`
- [ ] Configure HTTPS/SSL certificates
- [ ] Enable firewall rules
- [ ] Review CORS settings
- [ ] Implement rate limiting
- [ ] Configure authentication
- [ ] Enable security headers
- [ ] Set up SSL/TLS for database connections

### Performance
- [ ] Configure production database settings
- [ ] Set up database connection pooling
- [ ] Enable caching (Redis/Memcached)
- [ ] Configure CDN for static assets
- [ ] Optimize uWSGI worker settings
- [ ] Enable Nginx caching
- [ ] Set up database indexes
- [ ] Configure log rotation

### Monitoring
- [ ] Set up application logging
- [ ] Configure error tracking (Sentry, etc.)
- [ ] Enable health checks
- [ ] Set up uptime monitoring
- [ ] Configure alerts
- [ ] Implement metrics collection

### Backup
- [ ] Configure automated database backups
- [ ] Test backup restoration
- [ ] Set up offsite backup storage
- [ ] Document recovery procedures

## Environment Configuration

### Production Environment File

Create a production `.env` file with secure values:

```env
# PostgreSQL Configuration
POSTGRES_DB=production_db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=VERY_STRONG_PASSWORD_HERE_MIN_32_CHARS
POSTGRES_PORT=5432

# API Configuration
API_PORT=8080
FLASK_ENV=production
DEBUG=False
API_URL=https://api.yourdomain.com

# Frontend Configuration
FRONTEND_PORT=8000

# Application Secret Keys (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your_64_character_hex_secret_key_here
JWT_SECRET_KEY=your_64_character_hex_jwt_secret_here

# Database Connection Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis (for caching/sessions)
REDIS_URL=redis://redis:6379/0

# Email Configuration (if needed)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: prod_postgres
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - backend_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    # Don't expose port externally in production
    # Use only internal network communication

  redis:
    image: redis:7-alpine
    container_name: prod_redis
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - backend_network

  api:
    build:
      context: ./api
      dockerfile: Dockerfile.prod
    container_name: prod_api
    restart: always
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      FLASK_ENV: production
      DEBUG: "False"
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    volumes:
      - api_static:/app/static
      - api_media:/app/media
      - ./logs/api:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - backend_network
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: prod_frontend
    restart: always
    environment:
      API_URL: ${API_URL}
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - frontend_static:/app/static
      - ./logs/frontend:/app/logs
    depends_on:
      - api
    networks:
      - backend_network
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  nginx_api:
    image: nginx:alpine
    container_name: prod_nginx_api
    restart: always
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./docker/nginx/api/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/api/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - api_static:/var/www/api/static:ro
      - api_media:/var/www/api/media:ro
      - ./logs/nginx_api:/var/log/nginx
    depends_on:
      - api
    networks:
      - backend_network

  nginx_frontend:
    image: nginx:alpine
    container_name: prod_nginx_frontend
    restart: always
    ports:
      - "8443:443"
      - "8080:80"
    volumes:
      - ./docker/nginx/frontend/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/frontend/conf.d:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - frontend_static:/var/www/frontend/static:ro
      - ./logs/nginx_frontend:/var/log/nginx
    depends_on:
      - frontend
    networks:
      - backend_network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  api_static:
    driver: local
  api_media:
    driver: local
  frontend_static:
    driver: local

networks:
  backend_network:
    driver: bridge
```

## Production Dockerfile

### API Production Dockerfile

Create `api/Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/static /app/media /app/logs \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

EXPOSE 8080

CMD ["uwsgi", "--ini", "uwsgi.prod.ini"]
```

### Production uWSGI Configuration

Create `api/uwsgi.prod.ini`:

```ini
[uwsgi]
# Application
module = wsgi:app
callable = app

# Process Management
master = true
processes = 4
threads = 2
enable-threads = true

# Socket
socket = 0.0.0.0:8080
protocol = http
chmod-socket = 666

# Performance
vacuum = true
die-on-term = true
harakiri = 60
max-requests = 5000
max-worker-lifetime = 3600
reload-on-rss = 512
worker-reload-mercy = 60

# Buffer sizes
buffer-size = 32768
post-buffering = 8192

# Static files
static-map = /static=/app/static
static-map = /media=/app/media
static-expires-uri = /static/.* 2592000
static-expires-uri = /media/.* 604800

# Logging
logto = /app/logs/uwsgi.log
log-maxsize = 50000000
log-backupname = /app/logs/uwsgi.log.old
log-4xx = false
log-5xx = true
disable-logging = false

# Security
chmod-socket = 660
uid = appuser
gid = appuser

# No auto-reload in production
# py-autoreload = 0
```

## SSL/TLS Configuration

### Generate SSL Certificates

#### Option 1: Let's Encrypt (Recommended for production)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (add to crontab)
0 0 * * * certbot renew --quiet
```

#### Option 2: Self-Signed (Development/Testing only)

```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/private.key \
    -out ssl/certificate.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

### Nginx SSL Configuration

Create `docker/nginx/api/conf.d/api.prod.conf`:

```nginx
upstream api_backend {
    server api:8080;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Logging
    access_log /var/log/nginx/api_access.log;
    error_log /var/log/nginx/api_error.log;
    
    # Client upload size
    client_max_body_size 20M;
    
    # API endpoints
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files with caching
    location /static/ {
        alias /var/www/api/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Media files
    location /media/ {
        alias /var/www/api/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

## Database Optimization

### PostgreSQL Configuration

Create `docker/postgres/postgresql.conf`:

```conf
# Connection Settings
max_connections = 100
shared_buffers = 256MB

# Performance
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2MB
min_wal_size = 1GB
max_wal_size = 4GB

# Logging
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000  # Log queries > 1 second
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

### Database Backup Script

Create `scripts/backup_db.sh`:

```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"
RETENTION_DAYS=7

# Create backup
docker-compose exec -T postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_FILE

# Remove old backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE"
```

Make it executable and add to crontab:
```bash
chmod +x scripts/backup_db.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/scripts/backup_db.sh
```

## Monitoring & Logging

### Application Logging

Update `api/app.py`:

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app():
    app = Flask(__name__)
    
    # Configure logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    
    return app
```

### Error Tracking with Sentry

```python
# requirements.txt
sentry-sdk[flask]==1.38.0

# app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

def create_app():
    app = Flask(__name__)
    
    if os.getenv('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            environment=os.getenv('FLASK_ENV', 'production')
        )
    
    return app
```

## Deployment Strategies

### Cloud Platform Deployment

#### AWS (Elastic Container Service)
1. Push images to Amazon ECR
2. Create ECS task definitions
3. Set up Application Load Balancer
4. Configure RDS for PostgreSQL
5. Use ElastiCache for Redis
6. Set up CloudWatch for logging

#### Google Cloud Platform
1. Push images to Google Container Registry
2. Deploy to Google Kubernetes Engine (GKE)
3. Use Cloud SQL for PostgreSQL
4. Configure Cloud Load Balancing
5. Use Memorystore for Redis

#### DigitalOcean
1. Use DigitalOcean Container Registry
2. Deploy to DigitalOcean Kubernetes
3. Use Managed PostgreSQL Database
4. Configure Load Balancer
5. Set up Managed Redis

### VPS Deployment

```bash
# On your VPS (Ubuntu/Debian)

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone your-repo-url
cd BackendFramework

# Set up environment
cp .env.example .env
nano .env  # Edit with production values

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Set up automatic updates
cat > update.sh << 'EOF'
#!/bin/bash
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
EOF
chmod +x update.sh
```

## Performance Tuning

### uWSGI Optimization

Adjust workers based on CPU cores:
```ini
# processes = (2 x number_of_cores) + 1
processes = 5  # For 2 CPU cores
threads = 2
```

### Nginx Caching

Add to Nginx configuration:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 10m;
    proxy_cache_bypass $http_cache_control;
    add_header X-Cache-Status $upstream_cache_status;
    
    # ... other proxy settings ...
}
```

## Security Hardening

### 1. Use Secrets Management
- AWS Secrets Manager
- HashiCorp Vault
- Docker Secrets (Swarm mode)

### 2. Regular Updates
```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Update system packages
sudo apt-get update && sudo apt-get upgrade
```

### 3. Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 4. Fail2Ban
```bash
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 4  # Run 4 instances
```

### Load Balancing
Configure Nginx upstream with multiple backends:
```nginx
upstream api_backend {
    least_conn;
    server api_1:8080;
    server api_2:8080;
    server api_3:8080;
    server api_4:8080;
}
```

## Post-Deployment

### Health Checks
```bash
# API health
curl https://api.yourdomain.com/health

# Database connection
docker-compose exec postgres pg_isready

# Check logs
docker-compose logs -f --tail=100
```

### Monitoring
- Set up uptime monitoring (UptimeRobot, Pingdom)
- Configure application performance monitoring (New Relic, Datadog)
- Set up log aggregation (ELK Stack, Graylog)

## Rollback Procedure

```bash
# Tag current version
git tag -a v1.0.1 -m "Production release 1.0.1"

# If issues occur, rollback
git checkout v1.0.0
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## Maintenance Windows

Plan for:
- Database migrations
- Security updates
- Feature deployments
- Backup verification

Use blue-green deployment or rolling updates to minimize downtime.

---

**Remember**: Test everything in a staging environment before deploying to production!
