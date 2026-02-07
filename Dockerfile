# ==========================================
# Stage 1: Builder - Install dependencies
# ==========================================
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies required
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements fil
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# Stage 2: Runtime - Create minimal image
# ==========================================
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

# Set working directory
WORKDIR $APP_HOME

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage to /usr/local (accessible to all users)
COPY --from=builder /root/.local /usr/local

# Make sure scripts in .local are usable
ENV PATH=/usr/local/bin:$PATH

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -d $APP_HOME -s /sbin/nologin appuser

# Copy application code
COPY --chown=appuser:appuser . $APP_HOME/

# Create directories for static and media files
RUN mkdir -p $APP_HOME/staticfiles $APP_HOME/media && \
    chown -R appuser:appuser $APP_HOME

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Collect static files (done at build time)
RUN python manage.py collectstatic --noinput || true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)" || exit 1

# Run gunicorn for WSGI or uvicorn for ASGI (WebSockets)
# Default to uvicorn since you're using Channels
CMD ["uvicorn", "to7fabackend.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
