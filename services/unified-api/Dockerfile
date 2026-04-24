# Multi-stage build for WaddlePerf Unified API
FROM python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libmariadb-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python dependencies
WORKDIR /tmp
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r waddleperf && useradd -r -u 1000 -g waddleperf waddleperf

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=waddleperf:waddleperf /root/.local /home/waddleperf/.local

# Copy application code
COPY --chown=waddleperf:waddleperf . .

# Set environment variables
ENV PATH=/home/waddleperf/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER waddleperf

# Expose ports
EXPOSE 5000 50051

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:5000/health || exit 1

# Start application with Hypercorn
CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:5000"]
