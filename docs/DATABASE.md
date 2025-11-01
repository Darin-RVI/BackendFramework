# Database Guide

Comprehensive guide to working with PostgreSQL in the Backend Framework.

## Overview

The Backend Framework uses PostgreSQL 15 as its primary database with:

- **SQLAlchemy** ORM for Python object-relational mapping
- **Flask-Migrate** for database migrations
- **PgAdmin** for visual database management
- **Docker volumes** for data persistence

## Database Configuration

### Connection String

The database connection URL follows this format:

```
postgresql://username:password@host:port/database
```

Example from `.env`:
```env
DATABASE_URL=postgresql://postgres:your_password@postgres:5432/backend_db
```

### SQLAlchemy Configuration

In `api/app.py`:

```python
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@postgres:5432/backend_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    db.init_app(app)
    
    return app
```

## Creating Models

### Basic Model

```python
from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
```

### Model with Relationships

```python
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # One-to-many relationship
    products = db.relationship('Product', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Many-to-many relationship
    tags = db.relationship('Tag', secondary='product_tags', backref=db.backref('products', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Product {self.name}>'


class Tag(db.Model):
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


# Association table for many-to-many relationship
product_tags = db.Table('product_tags',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)
```

### Advanced Model Features

```python
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Order(db.Model):
    __tablename__ = 'orders'
    
    # UUID primary key
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User relationship
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orders', lazy='dynamic'))
    
    # Status with choices
    STATUS_CHOICES = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    status = db.Column(db.String(20), default='pending')
    
    # JSON field for metadata
    metadata = db.Column(JSONB, default={})
    
    # Decimal for money
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None
    
    def soft_delete(self):
        self.deleted_at = datetime.utcnow()
        db.session.commit()
    
    def validate_status(self):
        if self.status not in self.STATUS_CHOICES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.STATUS_CHOICES)}")
    
    def __repr__(self):
        return f'<Order {self.id}>'


# Event listeners
@event.listens_for(Order, 'before_insert')
@event.listens_for(Order, 'before_update')
def validate_order(mapper, connection, target):
    target.validate_status()
```

## Database Migrations

### Initialize Migrations

```bash
docker-compose exec api flask db init
```

### Create Migration

```bash
# Auto-generate migration from model changes
docker-compose exec api flask db migrate -m "Add users and products tables"

# Create empty migration for custom changes
docker-compose exec api flask db revision -m "Custom migration"
```

### Review Migration

Check the generated migration file in `migrations/versions/`:

```python
"""Add users and products tables

Revision ID: abc123
Revises: 
Create Date: 2025-11-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create tables
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

def downgrade():
    # Rollback
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
```

### Apply Migrations

```bash
# Apply all pending migrations
docker-compose exec api flask db upgrade

# Upgrade to specific revision
docker-compose exec api flask db upgrade abc123

# Rollback one migration
docker-compose exec api flask db downgrade

# Rollback to specific revision
docker-compose exec api flask db downgrade abc123

# Show current revision
docker-compose exec api flask db current

# Show migration history
docker-compose exec api flask db history
```

## Querying Data

### Basic Queries

```python
from models import User, Product

# Get all records
users = User.query.all()

# Get first record
user = User.query.first()

# Get by primary key
user = User.query.get(1)
user = User.query.get_or_404(1)  # Raises 404 if not found

# Count records
user_count = User.query.count()

# Filter
active_users = User.query.filter_by(is_active=True).all()
user = User.query.filter_by(username='john').first()

# Advanced filtering
from sqlalchemy import and_, or_

users = User.query.filter(
    and_(
        User.is_active == True,
        User.created_at > datetime(2025, 1, 1)
    )
).all()

users = User.query.filter(
    or_(
        User.username == 'john',
        User.email == 'john@example.com'
    )
).first()
```

### String Queries

```python
# LIKE query (case-sensitive)
users = User.query.filter(User.username.like('john%')).all()

# ILIKE query (case-insensitive, PostgreSQL-specific)
users = User.query.filter(User.username.ilike('%john%')).all()

# IN query
users = User.query.filter(User.id.in_([1, 2, 3, 4])).all()

# NOT IN
users = User.query.filter(~User.id.in_([1, 2, 3])).all()

# NULL checks
users = User.query.filter(User.deleted_at.is_(None)).all()
deleted_users = User.query.filter(User.deleted_at.isnot(None)).all()
```

### Ordering and Limiting

```python
# Order by
users = User.query.order_by(User.created_at.desc()).all()
users = User.query.order_by(User.username.asc()).all()

# Multiple order by
users = User.query.order_by(User.is_active.desc(), User.created_at.desc()).all()

# Limit and offset
users = User.query.limit(10).all()
users = User.query.offset(20).limit(10).all()

# Pagination
page = 1
per_page = 20
pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
users = pagination.items
total = pagination.total
```

### Joins

```python
# Inner join
products = Product.query.join(Category).filter(Category.name == 'Electronics').all()

# Left outer join
products = Product.query.outerjoin(Category).all()

# Multiple joins
from models import Order, OrderItem

orders = Order.query\
    .join(User)\
    .join(OrderItem)\
    .join(Product)\
    .filter(User.username == 'john')\
    .all()

# Eager loading relationships
products = Product.query.options(db.joinedload(Product.category)).all()
```

### Aggregation

```python
from sqlalchemy import func

# Count
user_count = db.session.query(func.count(User.id)).scalar()

# Sum
total_price = db.session.query(func.sum(Product.price)).scalar()

# Average
avg_price = db.session.query(func.avg(Product.price)).scalar()

# Group by
category_counts = db.session.query(
    Category.name,
    func.count(Product.id)
).join(Product).group_by(Category.name).all()

# Having clause
popular_categories = db.session.query(
    Category.name,
    func.count(Product.id).label('product_count')
).join(Product)\
 .group_by(Category.name)\
 .having(func.count(Product.id) > 10)\
 .all()
```

## Database Operations

### Creating Records

```python
# Create single record
user = User(username='john', email='john@example.com')
db.session.add(user)
db.session.commit()

# Create multiple records
users = [
    User(username='john', email='john@example.com'),
    User(username='jane', email='jane@example.com')
]
db.session.add_all(users)
db.session.commit()

# Bulk insert (faster for large datasets)
db.session.bulk_insert_mappings(User, [
    {'username': 'user1', 'email': 'user1@example.com'},
    {'username': 'user2', 'email': 'user2@example.com'},
])
db.session.commit()
```

### Updating Records

```python
# Update single record
user = User.query.get(1)
user.email = 'newemail@example.com'
db.session.commit()

# Update with query
User.query.filter_by(id=1).update({'email': 'new@example.com'})
db.session.commit()

# Bulk update
User.query.filter(User.is_active == False).update({'is_active': True})
db.session.commit()
```

### Deleting Records

```python
# Delete single record
user = User.query.get(1)
db.session.delete(user)
db.session.commit()

# Delete with query
User.query.filter_by(id=1).delete()
db.session.commit()

# Bulk delete
User.query.filter(User.is_active == False).delete()
db.session.commit()
```

### Transactions

```python
try:
    user = User(username='john', email='john@example.com')
    db.session.add(user)
    
    product = Product(name='Test', price=99.99, category_id=1)
    db.session.add(product)
    
    db.session.commit()
except Exception as e:
    db.session.rollback()
    raise
```

## Advanced Features

### Full-Text Search

```python
# Enable pg_trgm extension (add to init SQL)
# CREATE EXTENSION IF NOT EXISTS pg_trgm;

from sqlalchemy import func

# Similarity search
products = Product.query.filter(
    func.similarity(Product.name, 'laptop') > 0.3
).all()

# Full-text search with tsvector
products = Product.query.filter(
    func.to_tsvector('english', Product.description).match('laptop computer')
).all()
```

### JSON Queries

```python
from sqlalchemy.dialects.postgresql import JSONB

# Query JSON field
orders = Order.query.filter(
    Order.metadata['status'].astext == 'completed'
).all()

# JSON contains
orders = Order.query.filter(
    Order.metadata.contains({'priority': 'high'})
).all()
```

### Raw SQL

```python
# Execute raw SQL
result = db.session.execute('SELECT * FROM users WHERE id = :id', {'id': 1})
users = result.fetchall()

# Use text()
from sqlalchemy import text

result = db.session.execute(
    text('SELECT * FROM users WHERE username = :username'),
    {'username': 'john'}
)
```

## Database Maintenance

### Backup

```bash
# Full database backup
docker-compose exec postgres pg_dump -U postgres backend_db > backup.sql

# Compressed backup
docker-compose exec postgres pg_dump -U postgres backend_db | gzip > backup.sql.gz

# Backup specific tables
docker-compose exec postgres pg_dump -U postgres -t users -t products backend_db > tables_backup.sql
```

### Restore

```bash
# Restore from backup
docker-compose exec -T postgres psql -U postgres backend_db < backup.sql

# Restore from compressed backup
gunzip -c backup.sql.gz | docker-compose exec -T postgres psql -U postgres backend_db
```

### Vacuum and Analyze

```bash
# Vacuum database
docker-compose exec postgres psql -U postgres -d backend_db -c "VACUUM;"

# Analyze tables
docker-compose exec postgres psql -U postgres -d backend_db -c "ANALYZE;"

# Full vacuum (locks tables)
docker-compose exec postgres psql -U postgres -d backend_db -c "VACUUM FULL;"
```

## Performance Optimization

### Indexes

```python
# Add index to model
class User(db.Model):
    email = db.Column(db.String(120), nullable=False, index=True)
    
    __table_args__ = (
        db.Index('idx_user_email_username', 'email', 'username'),
        db.Index('idx_user_created', 'created_at'),
    )
```

### Query Optimization

```python
# Use select_related for foreign keys
products = Product.query.options(db.joinedload(Product.category)).all()

# Use prefetch_related for collections
categories = Category.query.options(db.subqueryload(Category.products)).all()

# Only select needed columns
users = db.session.query(User.id, User.username).all()
```

### Connection Pooling

Already configured in `app.py` SQLAlchemy settings.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common database issues.

## Next Steps

- Review [API Documentation](API_DOCUMENTATION.md) for using models in APIs
- Check [Deployment Guide](DEPLOYMENT.md) for production database setup
- See [Getting Started](GETTING_STARTED.md) for initial setup
