# Build stage
FROM golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac AS builder

WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary for target architecture
ARG TARGETOS=linux
ARG TARGETARCH=amd64
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a \
    -o testserver \
    ./cmd/testserver

# Runtime stage
FROM debian:bookworm-slim@sha256:f06537653ac770703bc45b4b113475bd402f451e85223f0f2837acbf89ab020a

# Install runtime dependencies (for ping, traceroute, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tzdata \
    iputils-ping \
    iputils-tracepath \
    dnsutils \
    traceroute \
    tcptraceroute \
    libcap2 \
    libcap2-bin \
    openssh-client && \
    groupadd -g 1000 waddleperf && \
    useradd -m -u 1000 -g waddleperf waddleperf && \
    setcap cap_net_raw+ep /usr/bin/traceroute && \
    setcap cap_net_raw+ep /usr/bin/tcptraceroute && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/testserver /app/testserver

# Set ownership
RUN chown -R waddleperf:waddleperf /app

# Switch to non-root user
USER waddleperf

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD bash -c 'exec 3<>/dev/tcp/localhost/8080 && echo -e "GET /health HTTP/1.0\r\n\r\n" >&3 || exit 1'

# Set environment defaults
ENV PORT=8080 \
    LOG_LEVEL=info \
    AUTH_ENABLED=true \
    MAX_CONCURRENT_TESTS=100

# Run
CMD ["/app/testserver"]
