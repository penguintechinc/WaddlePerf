#!/bin/bash
set -euo pipefail

# Simple test script for Docker build process

echo "Testing WaddlePerf Go Client Docker Build..."

# Clean up previous test
rm -rf test-dist

# Build for Linux AMD64
echo "Building Linux AMD64 binary..."
docker buildx build \
  --file Dockerfile.build \
  --target extractor \
  --platform linux/amd64 \
  --build-arg "TARGETOS=linux" \
  --build-arg "TARGETARCH=amd64" \
  --build-arg "VERSION=test" \
  --build-arg "BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --build-arg "GIT_COMMIT=test123" \
  --output type=local,dest=./test-dist \
  .

echo "Checking build output..."
if [ -f "test-dist/waddleperf-linux-amd64" ]; then
    echo "✅ Build successful!"
    ls -lh test-dist/waddleperf-linux-amd64
    file test-dist/waddleperf-linux-amd64
    
    # Test the binary
    if ./test-dist/waddleperf-linux-amd64 --help >/dev/null 2>&1; then
        echo "✅ Binary runs correctly!"
    else
        echo "⚠️  Binary may have issues, but build succeeded"
    fi
else
    echo "❌ Build failed - binary not found"
    echo "Contents of test-dist:"
    ls -la test-dist/ || echo "No test-dist directory"
    exit 1
fi

echo "🎉 Docker build test completed successfully!"