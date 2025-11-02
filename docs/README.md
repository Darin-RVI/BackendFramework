# Documentation Index

Welcome to the Backend Framework documentation! This directory contains comprehensive guides to help you build, deploy, and maintain your applications.

## 📚 Documentation Files

### Getting Started
- **[OVERVIEW.md](OVERVIEW.md)** - Complete framework overview, architecture, and features
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Step-by-step setup and first project guide

### Authentication & Security
- **[OAUTH2.md](OAUTH2.md)** - OAuth 2.0 authentication guide with grant types and examples
- **[MIGRATION.md](MIGRATION.md)** - Migrating from JWT to OAuth 2.0
- **[MULTI_TENANT.md](MULTI_TENANT.md)** - Multi-tenant architecture and implementation guide

### Development Guides
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Build robust REST APIs with Flask
- **[FRONTEND_DEVELOPMENT.md](FRONTEND_DEVELOPMENT.md)** - Create web interfaces and integrate with APIs
- **[DATABASE.md](DATABASE.md)** - Work with PostgreSQL, migrations, and queries

### Operations
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment strategies and best practices
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions to common issues and problems

### Architecture
- **[architecture.drawio](architecture.drawio)** - Visual diagram of framework architecture

## 🚀 Quick Navigation

### I Want To...

**Set up my first project**
→ Start with [GETTING_STARTED.md](GETTING_STARTED.md)

**Implement multi-tenancy**
→ Read [MULTI_TENANT.md](MULTI_TENANT.md)

**Implement OAuth 2.0 authentication**
→ Read [OAUTH2.md](OAUTH2.md)

**Migrate from JWT to OAuth 2.0**
→ Follow [MIGRATION.md](MIGRATION.md)

**Build an API**
→ Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

**Create web pages**
→ Check [FRONTEND_DEVELOPMENT.md](FRONTEND_DEVELOPMENT.md)

**Work with the database**
→ See [DATABASE.md](DATABASE.md)

**Deploy to production**
→ Follow [DEPLOYMENT.md](DEPLOYMENT.md)

**Fix an error**
→ Consult [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Understand the architecture**
→ Review [OVERVIEW.md](OVERVIEW.md) or [architecture.drawio](architecture.drawio)

## 📖 Reading Order

### For Beginners
1. [OVERVIEW.md](OVERVIEW.md) - Understand what the framework offers
2. [GETTING_STARTED.md](GETTING_STARTED.md) - Get your environment running
3. [OAUTH2.md](OAUTH2.md) - Learn OAuth 2.0 authentication
4. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Learn to build APIs
5. [DATABASE.md](DATABASE.md) - Master database operations

### For Experienced Developers
1. [OVERVIEW.md](OVERVIEW.md) - Quick architecture review
2. [OAUTH2.md](OAUTH2.md) - OAuth 2.0 implementation details
3. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Advanced patterns
4. [DEPLOYMENT.md](DEPLOYMENT.md) - Production considerations
5. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common pitfalls

## 🎯 By Use Case

### Building a REST API Backend
1. [GETTING_STARTED.md](GETTING_STARTED.md) - Setup
2. [OAUTH2.md](OAUTH2.md) - Secure with OAuth 2.0
3. [DATABASE.md](DATABASE.md) - Design your schema
4. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Implement endpoints
5. [DEPLOYMENT.md](DEPLOYMENT.md) - Go live

### Full-Stack Web Application
1. [GETTING_STARTED.md](GETTING_STARTED.md) - Setup
2. [OAUTH2.md](OAUTH2.md) - Authentication layer
3. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Backend API
4. [FRONTEND_DEVELOPMENT.md](FRONTEND_DEVELOPMENT.md) - User interface
5. [DATABASE.md](DATABASE.md) - Data layer
6. [DEPLOYMENT.md](DEPLOYMENT.md) - Deploy

### Microservices Architecture
1. [OVERVIEW.md](OVERVIEW.md) - Architecture patterns
2. [OAUTH2.md](OAUTH2.md) - Service-to-service auth
3. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Service design
4. [DATABASE.md](DATABASE.md) - Database per service
5. [DEPLOYMENT.md](DEPLOYMENT.md) - Container orchestration

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

## 📝 Documentation Standards

Each documentation file follows this structure:
- **Overview** - What the document covers
- **Prerequisites** - What you need to know first
- **Main Content** - Detailed information with examples
- **Best Practices** - Recommended approaches
- **Troubleshooting** - Common issues (or link to TROUBLESHOOTING.md)
- **Next Steps** - Where to go next

## 🆘 Need Help?

1. **Error or problem?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Setup question?** → [GETTING_STARTED.md](GETTING_STARTED.md)
3. **How-to question?** → Search the relevant guide
4. **Still stuck?** → Check logs with `docker-compose logs -f`

## 🤝 Contributing to Documentation

If you find errors or want to improve the documentation:
1. Note the file and section
2. Propose changes clearly
3. Test examples before submitting
4. Follow the existing style

## 📊 Documentation Coverage

| Topic | File | Status |
|-------|------|--------|
| Framework Overview | OVERVIEW.md | ✅ Complete |
| Initial Setup | GETTING_STARTED.md | ✅ Complete |
| Multi-Tenant Architecture | MULTI_TENANT.md | ✅ Complete |
| OAuth 2.0 Authentication | OAUTH2.md | ✅ Complete |
| JWT to OAuth 2.0 Migration | MIGRATION.md | ✅ Complete |
| API Development | API_DOCUMENTATION.md | ✅ Complete |
| Frontend Development | FRONTEND_DEVELOPMENT.md | ✅ Complete |
| Database Operations | DATABASE.md | ✅ Complete |
| Production Deployment | DEPLOYMENT.md | ✅ Complete |
| Troubleshooting | TROUBLESHOOTING.md | ✅ Complete |
| Architecture Diagram | architecture.drawio | ✅ Complete |

## 🔄 Version Information

**Documentation Version**: 2.0.0  
**Framework Version**: 2.0.0  
**Authentication**: OAuth 2.0  
**Last Updated**: November 2025

## 📄 License

This documentation is part of the Backend Framework project and is available under the MIT License.

---

**Happy Building!** 🎉

Start with [GETTING_STARTED.md](GETTING_STARTED.md) to begin your journey.
