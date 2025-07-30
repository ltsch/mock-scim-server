# Use Python 3.11 slim image as base
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs and database directories and ensure proper permissions
RUN mkdir -p logs db && chmod 755 logs db

# Make startup script executable
RUN chmod +x start.sh

# Create non-root user for security (but allow running as root if needed)
RUN groupadd -r scim && useradd -r -g scim scim
RUN chown -R scim:scim /app

# Expose port
EXPOSE 7001

# Health check using curl with longer timeout and start period
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:7001/healthz || exit 1

# Default command
CMD ["./start.sh"]