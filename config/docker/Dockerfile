# ============================================
# Stage 1: Builder - Python dependencies
# ============================================
FROM python:3.11-slim as python-builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install --no-warn-script-location -r requirements.txt

# ============================================
# Stage 2: Builder - Frontend assets
# ============================================
FROM node:18-slim as frontend-builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install Node.js dependencies
RUN npm ci --only=production

# Copy source files needed for build
COPY tailwind.config.js postcss.config.js ./
COPY templates ./templates
COPY static ./static

# Build frontend assets
RUN npm run build

# ============================================
# Stage 3: Runtime
# ============================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    PATH="/usr/local/bin:$PATH"

# Set work directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN groupadd -r django && useradd -r -g django django

# Copy Python packages from builder
COPY --from=python-builder /install /usr/local

# Copy frontend assets from builder
COPY --from=frontend-builder /app/static/css/output.css /tmp/static/css/

# Copy application code
COPY --chown=django:django . .

# Copy built frontend assets to correct location
RUN mkdir -p static/css && \
    cp /tmp/static/css/output.css static/css/ && \
    rm -rf /tmp/static

# Create necessary directories
RUN mkdir -p staticfiles media logs && \
    chown -R django:django staticfiles media logs

# Collect static files (run as django user)
USER django
RUN python manage.py collectstatic --noinput --clear

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "--config", "gunicorn_config.py", "better_laser_erp.wsgi:application"]