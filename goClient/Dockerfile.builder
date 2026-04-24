# Multi-platform builder for goClient with GUI support
# This Dockerfile provides all dependencies needed to build goClient with systray support

FROM golang:1.23-bookworm

# Install build dependencies for GUI libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    gcc \
    g++ \
    make \
    pkg-config \
    # Cross-compilation toolchains
    gcc-mingw-w64-x86-64 \
    g++-mingw-w64-x86-64 \
    # Linux GUI libraries (for systray)
    libayatana-appindicator3-dev \
    libgtk-3-dev \
    # X11 development libraries
    libx11-dev \
    libxcursor-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxi-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    # Additional dependencies
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Create non-root user (builder stage)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy go modules
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build script for all platforms
COPY build-all.sh /usr/local/bin/build-all.sh
RUN chmod 755 /usr/local/bin/build-all.sh

# Set ownership of workspace
RUN chown -R appuser:appuser /workspace

USER appuser

ENTRYPOINT ["/bin/bash", "/usr/local/bin/build-all.sh"]
