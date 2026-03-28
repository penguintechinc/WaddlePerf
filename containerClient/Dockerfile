# WaddlePerf containerClient Dockerfile
# Multi-arch support: linux/amd64, linux/arm64
# Python 3.12 Debian-based

FROM python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    iputils-ping \
    iproute2 \
    dnsutils \
    traceroute \
    tcptraceroute \
    libcap2-bin \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && setcap cap_net_raw+ep /usr/bin/traceroute.db \
    && setcap cap_net_raw+ep /usr/bin/tcptraceroute.mt

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user (UID 1000)
RUN groupadd -g 1000 waddleperf && \
    useradd -m -u 1000 -g waddleperf waddleperf && \
    mkdir -p /app /data && \
    chown -R waddleperf:waddleperf /app /data

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=waddleperf:waddleperf client.py .
COPY --chown=waddleperf:waddleperf tests/ tests/

# Make client.py executable
RUN chmod +x client.py

# Switch to non-root user
USER waddleperf

# Environment variables (defaults)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AUTH_TYPE=none \
    MANAGER_URL=http://localhost:8080 \
    TEST_SERVER_URL=http://localhost:8081 \
    RUN_SECONDS=0 \
    ENABLE_HTTP_TEST=true \
    ENABLE_TCP_TEST=true \
    ENABLE_UDP_TEST=true \
    ENABLE_ICMP_TEST=true \
    HTTP_TARGETS=https://www.google.com \
    ICMP_TARGETS=8.8.8.8

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Entry point
ENTRYPOINT ["python3", "client.py"]

# Default command (can be overridden)
CMD ["--schedule"]

# Labels
LABEL org.opencontainers.image.title="WaddlePerf containerClient" \
      org.opencontainers.image.description="Network performance testing client for WaddlePerf" \
      org.opencontainers.image.vendor="Penguin Technologies Inc." \
      org.opencontainers.image.source="https://github.com/penguintechinc/WaddlePerf" \
      org.opencontainers.image.version="1.0.0"
