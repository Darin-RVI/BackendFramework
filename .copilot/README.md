# .copilot Folder

This folder contains configuration and context files for AI-assisted development of the Backend Framework project.

## Current AI Model

**Active**: Claude 3.5 Sonnet (Sonnet 4.5) by Anthropic  
**Switched**: November 3, 2025  
**Previous**: GitHub Copilot (GPT-4 based)

## Files in This Folder

### 📋 [ai-model-info.md](ai-model-info.md)
**Purpose**: Information about the AI model being used  
**Contains**:
- Current model capabilities and strengths
- Best practices for interaction
- Example prompts for common tasks
- Model-specific guidelines for multi-tenant and OAuth development

**Use when**:
- Starting a new coding session
- Switching AI models
- Need guidance on how to ask for help effectively

---

### 🧠 [memory.md](memory.md)
**Purpose**: Project context and patterns for the AI to remember  
**Contains**:
- Project identity and architecture
- Multi-tenant patterns
- OAuth 2.0 patterns
- Database conventions
- Common development tasks
- Environment variables
- Security practices

**Use when**:
- AI needs context about the project
- Implementing new features following existing patterns
- Understanding project architecture
- Setting up development environment

---

### 📐 [instructions.md](instructions.md)
**Purpose**: Coding guidelines and code generation rules  
**Contains**:
- Code style preferences (Python, JavaScript, HTML/CSS)
- Framework-specific patterns (Flask, OAuth, Multi-tenant)
- Common code completions
- Security guidelines
- Testing instructions
- Error handling preferences

**Use when**:
- Generating new code
- Refactoring existing code
- Need code snippets for common patterns
- Ensuring code style consistency

---

### 🏗️ [project-recreation.md](project-recreation.md)
**Purpose**: Complete guide to recreate the project from scratch  
**Contains**:
- Step-by-step recreation instructions
- Directory structure
- Complete file-by-file setup guide
- Configuration details
- Production considerations
- Testing and validation steps

**Use when**:
- Setting up a new development environment
- Onboarding new developers
- Understanding complete project structure
- Deploying to new infrastructure
- Creating similar projects

---

## How to Use These Files

### For AI Assistants

When helping with this project:

1. **Read memory.md first** - Get project context
2. **Reference instructions.md** - Follow coding patterns
3. **Check ai-model-info.md** - Understand interaction guidelines
4. **Use project-recreation.md** - For complete architecture understanding

### For Developers

When working on the project:

1. **Review ai-model-info.md** - Learn how to ask the AI for help effectively
2. **Keep memory.md updated** - Add new patterns and conventions
3. **Update instructions.md** - When code style or patterns change
4. **Maintain project-recreation.md** - When architecture changes

## Quick Reference

### Ask for Multi-Tenant Code
```
"Create a tenant-aware endpoint to [feature] with OAuth protection 
requiring '[scope]' scope. Include error handling and logging."
```

### Ask for OAuth Implementation
```
"Implement [grant type] OAuth flow for [purpose]. Include token 
validation, scope checking, and security best practices."
```

### Ask for Database Changes
```
"Add a [model name] model with tenant isolation. Include proper 
relationships, indexes, and migration script."
```

### Ask for Security Review
```
"Review [file/endpoint] for security issues. Check for tenant 
leakage, authentication gaps, and authorization problems."
```

## Maintenance

### When to Update

- **ai-model-info.md**: When switching AI models or major capability changes
- **memory.md**: When adding new patterns, features, or architectural changes
- **instructions.md**: When code style or conventions change
- **project-recreation.md**: When project structure or setup process changes

### Update Checklist

When making significant project changes:

- [ ] Update memory.md with new patterns
- [ ] Update instructions.md if coding style changed
- [ ] Update project-recreation.md if structure changed
- [ ] Update ai-model-info.md if AI interaction patterns changed
- [ ] Add date to "Last Updated" sections
- [ ] Test AI assistance with updated context

## File Structure

```
.copilot/
├── README.md                    # This file - navigation guide
├── ai-model-info.md            # Current AI model information
├── memory.md                   # Project context and patterns
├── instructions.md             # Coding guidelines
└── project-recreation.md       # Complete project setup guide
```

## Important Notes

### Security
- Keep sensitive information out of these files
- No API keys, passwords, or tokens
- Use placeholders (e.g., `YOUR_SECRET_KEY`)

### Version Control
- All files in `.copilot` should be committed to git
- These files help AI assistants and developers alike
- Keep them up-to-date with project evolution

### Multi-Tenant Focus
- All code suggestions should consider tenant isolation
- Always include tenant context validation
- Security is paramount - never compromise tenant boundaries

### OAuth 2.0 Standards
- Follow RFC specifications for OAuth flows
- Use appropriate grant types for each use case
- Implement proper token validation and scopes

## Getting Started

### New to This Project?

1. Read [project-recreation.md](project-recreation.md) for architecture overview
2. Review [memory.md](memory.md) for patterns and conventions
3. Check [instructions.md](instructions.md) for code style
4. Read [ai-model-info.md](ai-model-info.md) for effective AI interaction

### Need to Add a Feature?

1. Check [memory.md](memory.md) for similar existing patterns
2. Review [instructions.md](instructions.md) for code style
3. Use examples from [ai-model-info.md](ai-model-info.md) to ask AI for help
4. Update documentation after implementation

### Debugging an Issue?

1. Reference [memory.md](memory.md) for architectural patterns
2. Check [instructions.md](instructions.md) for error handling patterns
3. Use debugging examples from [ai-model-info.md](ai-model-info.md)
4. Review relevant docs/ files for detailed information

## Related Documentation

This `.copilot` folder supplements the main documentation in `/docs`:

- [OVERVIEW.md](../docs/OVERVIEW.md) - High-level architecture
- [MULTI_TENANT.md](../docs/MULTI_TENANT.md) - Multi-tenancy details
- [OAUTH2.md](../docs/OAUTH2.md) - OAuth 2.0 implementation
- [API_DOCUMENTATION.md](../docs/API_DOCUMENTATION.md) - API reference
- [GETTING_STARTED.md](../docs/GETTING_STARTED.md) - Setup guide

## Last Updated

**Date**: November 3, 2025  
**Updated By**: Switching to Claude Sonnet 4.5  
**Changes**: Added ai-model-info.md and this README
