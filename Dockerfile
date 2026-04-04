# KT-BOT Dockerfile - Multi-stage build for production
# Stage 1: Builder - Install dependencies and build
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production - Minimal runtime image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r ktbot && useradd -r -g ktbot ktbot

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=ktbot:ktbot . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/data/chat_history /app/data/bm25_cache /app/data/chroma_db && \
    chown -R ktbot:ktbot /app

# Switch to non-root user
USER ktbot

# Expose ports
# 7860: FastAPI backend
# 7861: Gradio frontend
EXPOSE 7860 7861

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/api/v1/health || exit 1

# Default command
CMD ["python", "src/main.py"]
