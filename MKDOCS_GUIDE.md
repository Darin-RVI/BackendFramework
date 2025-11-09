# MkDocs Documentation Guide

This guide explains how to work with the project documentation using MkDocs with Material theme.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

Install MkDocs and all required dependencies:

```bash
pip install -r docs-requirements.txt
```

This installs:
- MkDocs (static site generator)
- Material for MkDocs (theme)
- Various plugins (search, lightbox, etc.)
- Markdown extensions

## Local Development

### Serve Documentation Locally

Start the built-in development server:

```bash
mkdocs serve
```

This will:
- Build the documentation
- Start a local server at http://127.0.0.1:8000
- Auto-reload when you make changes to documentation files
- Show any build errors or warnings

### Preview Options

You can customize the server:

```bash
# Use a different port
mkdocs serve -a localhost:8080

# Strict mode (warnings treated as errors)
mkdocs serve --strict

# Dirty reload (only rebuild changed files)
mkdocs serve --dirtyreload
```

## Building Documentation

### Build Static Site

Generate the static HTML documentation:

```bash
mkdocs build
```

This creates a `site/` directory with all HTML, CSS, JavaScript, and assets. The `site/` directory is ignored by git (see `.gitignore`).

### Clean Build

Remove the existing site and rebuild:

```bash
mkdocs build --clean
```

### Strict Build

Fail the build on warnings:

```bash
mkdocs build --strict
```

## Documentation Structure

### File Organization

```
BackendFramework/
├── mkdocs.yml              # MkDocs configuration
├── docs-requirements.txt   # Python dependencies for docs
└── docs/                   # Documentation source files
    ├── index.md           # Homepage
    ├── GETTING_STARTED.md
    ├── OVERVIEW.md
    ├── OAUTH2.md
    ├── MULTI_TENANT.md
    └── ...                # Other documentation files
```

### Navigation Structure

The navigation is defined in `mkdocs.yml`:

```yaml
nav:
  - Home: 
    - Overview: index.md
    - Getting Started: GETTING_STARTED.md
  - Architecture:
    - System Overview: OVERVIEW.md
  # ... more sections
```

## Writing Documentation

### Markdown Format

All documentation is written in Markdown (`.md` files). MkDocs supports:

- Standard Markdown
- GitHub Flavored Markdown
- Additional extensions (see `mkdocs.yml`)

### Code Blocks

Use fenced code blocks with syntax highlighting:

````markdown
```python
def hello():
    print("Hello, World!")
```

```bash
docker-compose up
```
````

### Admonitions

Create callout boxes:

```markdown
!!! note
    This is a note.

!!! warning
    This is a warning.

!!! tip
    This is a tip.

!!! danger
    This is a danger warning.
```

### Tabs

Create tabbed content:

```markdown
=== "Tab 1"
    Content for tab 1

=== "Tab 2"
    Content for tab 2
```

### Task Lists

```markdown
- [x] Completed task
- [ ] Incomplete task
```

### Internal Links

Link to other documentation pages:

```markdown
See the [Getting Started Guide](GETTING_STARTED.md) for setup instructions.
```

## Theme Configuration

### Colors

The Material theme uses color schemes defined in `mkdocs.yml`:

- **Light mode**: Default scheme with indigo primary color
- **Dark mode**: Slate scheme with indigo primary color

Users can toggle between modes using the icon in the header.

### Features Enabled

- **Navigation tabs**: Top-level sections as tabs
- **Navigation sections**: Expandable sections
- **Search**: Full-text search with suggestions
- **Code copy**: Copy button for code blocks
- **Table of contents**: Auto-generated TOC
- **Dark mode toggle**: User-selectable theme

## Adding New Pages

1. **Create the Markdown file** in the `docs/` directory:
   ```bash
   # Create new file
   touch docs/NEW_FEATURE.md
   ```

2. **Add content** to the file using Markdown

3. **Update navigation** in `mkdocs.yml`:
   ```yaml
   nav:
     - Features:
       - New Feature: NEW_FEATURE.md
   ```

4. **Preview changes**:
   ```bash
   mkdocs serve
   ```

## Deployment Options

### GitHub Pages

Deploy to GitHub Pages:

```bash
mkdocs gh-deploy
```

This builds the site and pushes it to the `gh-pages` branch.

### Static Hosting

Deploy the `site/` directory to any static hosting service:

- Netlify
- Vercel
- AWS S3 + CloudFront
- Azure Static Web Apps
- Google Cloud Storage

### Docker Container

You can also serve the documentation using a simple Docker container:

```dockerfile
FROM nginx:alpine
COPY site/ /usr/share/nginx/html/
```

## Customization

### Changing Theme Colors

Edit `mkdocs.yml`:

```yaml
theme:
  palette:
    primary: blue  # Change primary color
    accent: cyan   # Change accent color
```

Available colors: red, pink, purple, deep purple, indigo, blue, light blue, cyan, teal, green, light green, lime, yellow, amber, orange, deep orange

### Adding Plugins

1. **Install the plugin**:
   ```bash
   pip install mkdocs-plugin-name
   ```

2. **Add to docs-requirements.txt**:
   ```
   mkdocs-plugin-name>=1.0.0
   ```

3. **Enable in mkdocs.yml**:
   ```yaml
   plugins:
     - plugin-name
   ```

### Custom CSS

Add custom styles:

1. Create `docs/stylesheets/extra.css`
2. Add to `mkdocs.yml`:
   ```yaml
   extra_css:
     - stylesheets/extra.css
   ```

## Troubleshooting

### Build Errors

**Issue**: `Config file 'mkdocs.yml' does not exist`

**Solution**: Run `mkdocs` commands from the project root directory (where `mkdocs.yml` is located).

---

**Issue**: `No module named 'material'`

**Solution**: Install dependencies:
```bash
pip install -r docs-requirements.txt
```

---

**Issue**: Navigation not updating

**Solution**: 
1. Stop the server (Ctrl+C)
2. Clear cache: `mkdocs build --clean`
3. Restart: `mkdocs serve`

---

**Issue**: Search not working

**Solution**: The search plugin requires a full build. Run `mkdocs build` then `mkdocs serve`.

### Performance Issues

If the site is slow to build:

1. Use dirty reload: `mkdocs serve --dirtyreload`
2. Disable unnecessary plugins temporarily
3. Check for large files or images

## Best Practices

1. **Keep files organized**: Use clear file names and directory structure
2. **Use relative links**: Link to other docs with relative paths
3. **Test locally**: Always preview changes before committing
4. **Write clear headings**: Good headings improve navigation and SEO
5. **Use code examples**: Include practical examples in documentation
6. **Keep navigation simple**: Don't create too many nesting levels
7. **Update regularly**: Keep documentation in sync with code changes

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)

## Quick Reference

### Common Commands

```bash
# Install dependencies
pip install -r docs-requirements.txt

# Serve locally
mkdocs serve

# Build site
mkdocs build

# Clean build
mkdocs build --clean

# Deploy to GitHub Pages
mkdocs gh-deploy

# Create new project (not needed, already set up)
mkdocs new my-project
```

### File Locations

- **Configuration**: `mkdocs.yml`
- **Dependencies**: `docs-requirements.txt`
- **Source files**: `docs/` directory
- **Built site**: `site/` directory (auto-generated, git-ignored)

---

For questions about the documentation system, refer to the [MkDocs documentation](https://www.mkdocs.org/) or the [Material theme documentation](https://squidfunk.github.io/mkdocs-material/).
