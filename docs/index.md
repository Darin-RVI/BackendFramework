# Backend Framework Documentation

Welcome to the Backend Framework documentation! This comprehensive guide will help you build, deploy, and maintain applications using our Docker-based backend framework with PostgreSQL, OAuth 2.0 authentication, and multi-tenant support.

## 🚀 Features

- 🔐 **OAuth 2.0 Authentication**: Industry-standard authentication with multiple grant types
- 🏢 **Multi-Tenant Architecture**: Serve multiple organizations with complete data isolation
- 🐘 **PostgreSQL**: Robust relational database
- 🚀 **Flask API**: RESTful API with uWSGI
- 🌐 **Nginx**: High-performance reverse proxy and load balancer
- 🐳 **Docker**: Containerized architecture for easy deployment
- 📊 **PgAdmin**: Web-based database management
- 🔄 **Token Management**: Access tokens, refresh tokens, and revocation
- 👥 **Role-Based Access**: User, Admin, and Owner roles per tenant

## 📚 Documentation Structure

### Getting Started
- **[Getting Started Guide](GETTING_STARTED.md)** - Step-by-step setup and first project guide
- **[System Overview](OVERVIEW.md)** - Complete framework overview, architecture, and features

### Authentication & Security
- **[OAuth 2.0 Guide](OAUTH2.md)** - Complete OAuth 2.0 authentication with grant types and examples
- **[OAuth 2.0 Quick Reference](OAUTH2_QUICK_REFERENCE.md)** - Quick reference for OAuth 2.0 implementation
- **[Multi-Tenant Support](MULTI_TENANT.md)** - Multi-tenant architecture and implementation guide
- **[Migration Guide](MIGRATION.md)** - Migrating from JWT to OAuth 2.0

### Development Guides
- **[API Documentation](API_DOCUMENTATION.md)** - Build robust REST APIs with Flask
- **[Frontend Development](FRONTEND_DEVELOPMENT.md)** - Create web interfaces and integrate with APIs
- **[Database Guide](DATABASE.md)** - Work with PostgreSQL, migrations, and queries

### Operations
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment strategies and best practices
- **[Troubleshooting](TROUBLESHOOTING.md)** - Solutions to common issues and problems

## 🎯 Quick Start

### Prerequisites

- Docker Desktop installed
- Git installed

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd BackendFramework
   ```

2. **Configure environment:**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` with your configuration (database credentials, secret keys, etc.)

3. **Start services:**
   ```bash
   docker-compose up --build
   ```

4. **Initialize database:**
   ```bash
   docker-compose exec api flask db init
   docker-compose exec api flask db migrate -m "Initial migration"
   docker-compose exec api flask db upgrade
   ```

5. **Access services:**
   - Frontend: http://localhost:8000
   - API: http://localhost:8080
   - PgAdmin: http://localhost:5050

## 🗺️ Learning Paths

### For Beginners
1. [System Overview](OVERVIEW.md) - Understand what the framework offers
2. [Getting Started](GETTING_STARTED.md) - Get your environment running
3. [OAuth 2.0 Guide](OAUTH2.md) - Learn authentication
4. [API Documentation](API_DOCUMENTATION.md) - Learn to build APIs
5. [Database Guide](DATABASE.md) - Master database operations

### For Experienced Developers
1. [System Overview](OVERVIEW.md) - Quick architecture review
2. [OAuth 2.0 Guide](OAUTH2.md) - OAuth 2.0 implementation details
3. [Multi-Tenant Support](MULTI_TENANT.md) - Multi-tenancy patterns
4. [API Documentation](API_DOCUMENTATION.md) - Advanced patterns
5. [Deployment Guide](DEPLOYMENT.md) - Production considerations

## 🏗️ Use Cases

### Building a REST API Backend
1. [Getting Started](GETTING_STARTED.md) - Setup
2. [OAuth 2.0 Guide](OAUTH2.md) - Secure with OAuth 2.0
3. [Database Guide](DATABASE.md) - Design your schema
4. [API Documentation](API_DOCUMENTATION.md) - Implement endpoints
5. [Deployment Guide](DEPLOYMENT.md) - Go live

### Full-Stack Web Application
1. [Getting Started](GETTING_STARTED.md) - Setup
2. [OAuth 2.0 Guide](OAUTH2.md) - Authentication layer
3. [API Documentation](API_DOCUMENTATION.md) - Backend API
4. [Frontend Development](FRONTEND_DEVELOPMENT.md) - User interface
5. [Database Guide](DATABASE.md) - Data layer
6. [Deployment Guide](DEPLOYMENT.md) - Deploy

### Multi-Tenant SaaS Platform
1. [Getting Started](GETTING_STARTED.md) - Setup
2. [Multi-Tenant Support](MULTI_TENANT.md) - Multi-tenancy architecture
3. [OAuth 2.0 Guide](OAUTH2.md) - Tenant-scoped authentication
4. [API Documentation](API_DOCUMENTATION.md) - Tenant-aware APIs
5. [Deployment Guide](DEPLOYMENT.md) - Scale for production

## 🔍 Quick Reference

### Docker Commands
```powershell
# Start services
docker-compose up

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose build --no-cache
```

### Database Commands
```powershell
# Run migrations
docker-compose exec api flask db upgrade

# Create migration
docker-compose exec api flask db migrate -m "Description"

# Access database
docker-compose exec postgres psql -U postgres -d backend_db
```

### Service URLs
- Frontend: http://localhost:8000
- API: http://localhost:8080
- PgAdmin: http://localhost:5050

## 🆘 Need Help?

1. **Error or problem?** → [Troubleshooting Guide](TROUBLESHOOTING.md)
2. **Setup question?** → [Getting Started](GETTING_STARTED.md)
3. **How-to question?** → Search the relevant guide
4. **Still stuck?** → Check logs with `docker-compose logs -f`

## 📊 Architecture

The Backend Framework uses a containerized microservices architecture:

- **PostgreSQL**: Database server with persistent storage
- **API Service**: Python/Flask application with OAuth 2.0, multi-tenancy, and uWSGI
- **Nginx API Gateway**: Reverse proxy for API endpoints with caching
- **Frontend Service**: Python web application with uWSGI
- **Nginx Frontend**: Reverse proxy for frontend application
- **PgAdmin**: Web-based PostgreSQL management tool

For detailed architecture information, see the [Architecture Details](architecture.md) page.

## 🔄 Version Information

**Documentation Version**: 2.0.0  
**Framework Version**: 2.0.0  
**Authentication**: OAuth 2.0  
**Last Updated**: November 2025

## 📄 License

This documentation is part of the Backend Framework project and is available under the MIT License.

---

**Ready to get started?** Head over to the [Getting Started Guide](GETTING_STARTED.md) to begin your journey! 🎉
