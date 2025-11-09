FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and constraints files
COPY requirements.txt constraints.txt ./

# Install Python dependencies with constraints to prevent version upgrades
RUN pip install --upgrade pip && \
    PIP_CONSTRAINT=constraints.txt pip install --no-cache-dir \
    Werkzeug==2.2.3 \
    Flask==2.2.5 \
    Authlib==1.2.1 \
    cryptography==41.0.7 \
    SQLAlchemy==2.0.23 \
    Flask-SQLAlchemy==3.0.5 \
    Flask-Migrate==4.0.5 \
    Flask-CORS==4.0.0 \
    psycopg2-binary==2.9.9 \
    python-dotenv==1.0.0 \
    requests==2.31.0 \
    uWSGI==2.0.23

# Copy application code
COPY . .

# Create directories for static and media files
RUN mkdir -p /app/static /app/media

# Expose port for uWSGI
EXPOSE 8080

# Run uWSGI
CMD ["uwsgi", "--ini", "uwsgi.ini"]
