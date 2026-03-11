# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies required for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Set PATH to include local bin
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs && chmod 755 logs

# Create knowledge_base directory
RUN mkdir -p app/knowledge_base && chmod 755 app/knowledge_base

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8000}/health', timeout=5)"

# Expose port (Render will override PORT env var)
EXPOSE 8000

# Run application with gunicorn for production
CMD ["gunicorn", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:${PORT:-8000}", "main:app"]
