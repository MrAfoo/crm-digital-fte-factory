# NovaDeskAI Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY production/k8s/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY context/ ./context/
COPY production/ ./production/
COPY .env.example .env.example

# Create non-root user
RUN useradd -m -u 1000 nova && chown -R nova:nova /app
USER nova

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "production.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
