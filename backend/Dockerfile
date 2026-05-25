FROM python:3.11-slim

LABEL maintainer="AutoRadixAI" \
      version="1.0.0" \
      description="AutoRadixAI Medical AI Platform — Backend"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    g++ \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY start.sh ./start.sh

# Create runtime directories
RUN mkdir -p uploads outputs/reports outputs/heatmaps outputs/anonymized logs \
             ai-models/registry ai-models/weights

# Non-root user for security
RUN addgroup --system autoradix && adduser --system --group autoradix
RUN chown -R autoradix:autoradix /app && chmod +x /app/start.sh
USER autoradix

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["/bin/sh", "/app/start.sh"]
