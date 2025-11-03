# AI Model Information

## Current Model

**Name**: Claude 3.5 Sonnet (Anthropic)  
**Version**: Sonnet 4.5  
**Switched On**: November 3, 2025  
**Previous Model**: GitHub Copilot (GPT-4 based)

## Model Capabilities

### Strengths for This Project

1. **Long Context Window**
   - Can analyze entire codebase simultaneously
   - Maintains context across multiple files
   - Understands complex architectural patterns

2. **Multi-Tenant Architecture Expertise**
   - Strong understanding of data isolation patterns
   - Excellent at generating tenant-aware code
   - Can identify potential tenant leakage issues

3. **Security-First Approach**
   - Proactively identifies security vulnerabilities
   - Suggests OAuth 2.0 best practices
   - Emphasizes input validation and error handling

4. **Code Quality**
   - Generates comprehensive type hints
   - Creates thorough docstrings
   - Maintains consistent code style

5. **Database Design**
   - Expert in SQLAlchemy patterns
   - Understands complex foreign key relationships
   - Suggests proper indexing strategies

6. **Testing & Documentation**
   - Generates comprehensive test cases
   - Creates detailed API documentation
   - Writes clear, concise comments

## How to Interact Effectively

### When Asking for Code

✅ **Do This**:
```
"Create a tenant-aware endpoint to list documents with OAuth protection 
requiring 'read' scope. Include error handling and logging."
```

❌ **Not This**:
```
"Make an endpoint for documents"
```

### When Requesting Features

✅ **Do This**:
```
"Add a feature to export tenant data as JSON, ensuring:
1. Only tenant owners can export
2. Data includes all related entities
3. Sensitive fields are excluded
4. Export is logged for audit trail"
```

❌ **Not This**:
```
"Add data export"
```

### When Debugging

✅ **Do This**:
```
"I'm getting a 403 error on /api/documents when user 'john' tries to access 
documents in tenant 'acme'. User exists and is active. Here's the code and 
error trace..."
```

❌ **Not This**:
```
"Why isn't this working?"
```

## Model-Specific Guidelines

### For Multi-Tenant Features

When implementing tenant-related features:

1. **Always specify tenant context**: "Create a tenant-aware endpoint..."
2. **Mention isolation requirements**: "Ensure data isolation at database level..."
3. **Include access control**: "Require admin role within tenant..."
4. **Request validation**: "Validate tenant access before operations..."

### For OAuth 2.0 Features

When working with authentication:

1. **Specify grant type**: "Use password grant for this endpoint..."
2. **Define scopes**: "Require 'read write' scopes..."
3. **Mention token handling**: "Include token refresh logic..."
4. **Security considerations**: "Ensure client secrets are stored securely..."

### For Database Operations

When modifying models or queries:

1. **Mention relationships**: "Add a one-to-many relationship with cascade delete..."
2. **Request indexes**: "Include indexes for frequently queried columns..."
3. **Specify constraints**: "Add composite foreign key constraint for tenant isolation..."
4. **Migration awareness**: "Generate migration script for this change..."

## Context Files to Reference

When asking questions, Claude can reference:

- **memory.md**: Project context and patterns
- **instructions.md**: Coding guidelines and conventions
- **project-recreation.md**: Full architecture documentation
- **API_DOCUMENTATION.md**: API specifications
- **MULTI_TENANT.md**: Multi-tenancy guidelines
- **OAUTH2.md**: OAuth 2.0 implementation details

## Example Interactions

### Adding a New Feature

**Good Prompt**:
```
I need to add a feature for tenant administrators to view usage statistics.

Requirements:
- Endpoint: GET /tenants/stats
- Authentication: OAuth 2.0 with 'admin' scope
- Authorization: Admin or Owner role in tenant
- Response: JSON with user count, API calls, storage used
- Include: Error handling, logging, proper HTTP status codes

Use the existing tenant_routes.py pattern and follow the established 
security practices from memory.md.
```

### Debugging an Issue

**Good Prompt**:
```
I'm experiencing a data leakage issue where tenant A can see tenant B's 
documents when calling GET /api/documents.

Current implementation in api/routes.py (lines 45-60):
[paste code]

The endpoint uses @require_tenant but documents are still visible across 
tenants. What's wrong and how should I fix it?
```

### Refactoring Code

**Good Prompt**:
```
The auth_routes.py file has grown to 500+ lines. Help me refactor it by:

1. Separating OAuth client management into client_routes.py
2. Creating a services/auth_service.py for business logic
3. Keeping route handlers thin (max 20 lines)
4. Maintaining all existing functionality
5. Preserving tenant context and security

Show me the refactored structure and migration plan.
```

## Common Patterns to Request

### Tenant-Aware CRUD Endpoint

```python
"Generate a complete CRUD endpoint for 'projects' with:
- Tenant isolation via tenant_id foreign key
- OAuth 2.0 protection (read/write scopes)
- Role-based access (users can read own, admins can read all)
- Proper error handling and validation
- Comprehensive docstrings
- Unit tests"
```

### OAuth Client Registration

```python
"Create an endpoint for users to register OAuth clients within their tenant:
- Endpoint: POST /oauth/clients/register
- Require authenticated user session
- Generate secure client_id and client_secret
- Store in oauth2_clients table with tenant_id
- Return credentials once (don't expose secret again)
- Include audit logging"
```

### Database Migration

```python
"Help me create a migration to add email verification to users:
- Add email_verified boolean (default false)
- Add verification_token string (nullable)
- Add verified_at timestamp (nullable)
- Create index on verification_token
- Maintain multi-tenant isolation
- Include rollback instructions"
```

## Performance Optimization

Claude excels at optimizing code. Request optimization like:

```
"Review this endpoint for performance issues:
[paste code]

Consider:
- N+1 query problems
- Missing indexes
- Inefficient filters
- Caching opportunities
- Pagination needs

Suggest improvements with code examples."
```

## Best Practices for This Project

### 1. Always Include Type Hints

When requesting code, Claude will automatically include type hints. If missing, request:
```
"Add type hints to this function"
```

### 2. Request Comprehensive Docstrings

Claude generates excellent docstrings. Expect:
```python
def create_tenant(name: str, slug: str) -> Tuple[Tenant, User]:
    """Create a new tenant with admin user.
    
    Args:
        name: Human-readable tenant name
        slug: URL-safe tenant identifier
        
    Returns:
        Tuple of (created_tenant, admin_user)
        
    Raises:
        ValueError: If slug is invalid or already exists
        DatabaseError: If database operation fails
        
    Example:
        >>> tenant, admin = create_tenant("Acme Corp", "acme")
        >>> print(tenant.id)
        1
    """
```

### 3. Security Reviews

Request security analysis:
```
"Review this endpoint for security vulnerabilities:
[paste code]

Check for:
- SQL injection risks
- Cross-tenant data leakage
- Insufficient authentication
- Missing authorization
- Input validation gaps
- Information disclosure
```

## Updates and Maintenance

**Last Updated**: November 3, 2025  
**Next Review**: When switching AI models or major project changes

### Version History

- **November 3, 2025**: Switched to Claude Sonnet 4.5 from GitHub Copilot
- **Future**: Document any model changes or capability updates

## Notes

- Claude Sonnet 4.5 has excellent understanding of multi-tenant architectures
- Particularly strong with Python/Flask patterns used in this project
- Can generate comprehensive test suites when requested
- Excellent at maintaining consistency across large codebases
- Strong emphasis on security and best practices
