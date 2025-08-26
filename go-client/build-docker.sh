#!/bin/bash
set -euo pipefail

# WaddlePerf Go Client Docker Build Script
# Builds binaries for multiple architectures using Docker

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${SCRIPT_DIR}/dist"
DOCKERFILE="${SCRIPT_DIR}/Dockerfile.build"

# Build metadata
VERSION="${VERSION:-$(git describe --tags --always --dirty 2>/dev/null || echo 'dev')}"
BUILD_TIME="${BUILD_TIME:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}"
GIT_COMMIT="${GIT_COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')}"

# Supported platforms
declare -a PLATFORMS=(
    "linux/amd64"
    "linux/arm64"
    "darwin/amd64"
    "darwin/arm64"
    "windows/amd64"
    "windows/arm64"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build WaddlePerf Go client binaries using Docker for consistent environments.

OPTIONS:
    -p, --platform PLATFORM    Build for specific platform (e.g., linux/amd64)
    -a, --all                   Build for all supported platforms (default)
    -t, --test                  Run tests before building
    -c, --clean                 Clean output directory before building
    -r, --runtime              Build runtime Docker images as well
    -h, --help                  Show this help message

EXAMPLES:
    $0                          # Build for all platforms
    $0 -p linux/amd64          # Build only for Linux AMD64
    $0 -t -c                    # Clean, test, then build all
    $0 -r                       # Build binaries and runtime images

PLATFORMS:
$(printf "    %s\n" "${PLATFORMS[@]}")

EOF
}

clean_output() {
    if [[ -d "$OUTPUT_DIR" ]]; then
        log "Cleaning output directory: $OUTPUT_DIR"
        rm -rf "$OUTPUT_DIR"
    fi
    mkdir -p "$OUTPUT_DIR"
}

build_binary() {
    local platform=$1
    local os="${platform%/*}"
    local arch="${platform#*/}"
    local ext=""
    
    # Windows binaries need .exe extension
    if [[ "$os" == "windows" ]]; then
        ext=".exe"
    fi
    
    local output_name="waddleperf-${os}-${arch}${ext}"
    
    log "Building binary for ${platform}..."
    
    # Build using Docker with buildx for cross-platform support
    docker buildx build \
        --file "$DOCKERFILE" \
        --target extractor \
        --platform "$platform" \
        --build-arg "TARGETOS=$os" \
        --build-arg "TARGETARCH=$arch" \
        --build-arg "VERSION=$VERSION" \
        --build-arg "BUILD_TIME=$BUILD_TIME" \
        --build-arg "GIT_COMMIT=$GIT_COMMIT" \
        --output "type=local,dest=$OUTPUT_DIR" \
        "$SCRIPT_DIR"
    
    # Rename the extracted binary if needed
    if [[ -f "$OUTPUT_DIR/waddleperf-${os}-${arch}" && "$ext" == ".exe" ]]; then
        mv "$OUTPUT_DIR/waddleperf-${os}-${arch}" "$OUTPUT_DIR/waddleperf-${os}-${arch}.exe"
    fi
    
    if [[ -f "$OUTPUT_DIR/$output_name" ]]; then
        success "Built $output_name ($(du -h "$OUTPUT_DIR/$output_name" | cut -f1))"
    else
        error "Failed to build $output_name"
        return 1
    fi
}

build_runtime_image() {
    local platform=$1
    local tag="waddleperf-go-client:${VERSION}-${platform//\//-}"
    
    log "Building runtime image for ${platform}: $tag"
    
    docker buildx build \
        --file "$DOCKERFILE" \
        --target runtime \
        --platform "$platform" \
        --build-arg "VERSION=$VERSION" \
        --build-arg "BUILD_TIME=$BUILD_TIME" \
        --build-arg "GIT_COMMIT=$GIT_COMMIT" \
        --tag "$tag" \
        --load \
        "$SCRIPT_DIR"
    
    success "Built runtime image: $tag"
}

run_tests() {
    log "Running tests using Docker..."
    
    docker buildx build \
        --file "$DOCKERFILE" \
        --target tester \
        --platform "linux/amd64" \
        --build-arg "VERSION=$VERSION" \
        --build-arg "BUILD_TIME=$BUILD_TIME" \
        --build-arg "GIT_COMMIT=$GIT_COMMIT" \
        "$SCRIPT_DIR"
    
    success "All tests passed"
}

create_checksums() {
    log "Creating checksums..."
    cd "$OUTPUT_DIR"
    
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum * > SHA256SUMS.txt
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 * > SHA256SUMS.txt
    else
        warn "No SHA256 utility found, skipping checksums"
        return
    fi
    
    success "Created checksums: SHA256SUMS.txt"
}

create_archives() {
    log "Creating distribution archives..."
    cd "$OUTPUT_DIR"
    
    for file in waddleperf-*; do
        # Skip existing archives and checksum file
        [[ "$file" == *.tar.gz ]] && continue
        [[ "$file" == *.zip ]] && continue
        [[ "$file" == "SHA256SUMS.txt" ]] && continue
        [[ ! -f "$file" ]] && continue
        
        local base="${file%.*}"  # Remove .exe extension if present
        base="${base%.exe}"
        
        if [[ "$file" == *windows* ]]; then
            # Create zip for Windows
            zip "${base}.zip" "$file"
            success "Created ${base}.zip"
        else
            # Create tar.gz for Unix-like systems
            tar czf "${base}.tar.gz" "$file"
            success "Created ${base}.tar.gz"
        fi
    done
}

main() {
    local build_platforms=()
    local run_tests=false
    local clean=false
    local build_runtime=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--platform)
                build_platforms+=("$2")
                shift 2
                ;;
            -a|--all)
                build_platforms=("${PLATFORMS[@]}")
                shift
                ;;
            -t|--test)
                run_tests=true
                shift
                ;;
            -c|--clean)
                clean=true
                shift
                ;;
            -r|--runtime)
                build_runtime=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Default to all platforms if none specified
    if [[ ${#build_platforms[@]} -eq 0 ]]; then
        build_platforms=("${PLATFORMS[@]}")
    fi
    
    # Validate Docker and buildx
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker is required but not installed"
        exit 1
    fi
    
    if ! docker buildx version >/dev/null 2>&1; then
        error "Docker buildx is required but not available"
        exit 1
    fi
    
    # Create buildx builder if it doesn't exist
    if ! docker buildx ls | grep -q "waddleperf-builder"; then
        log "Creating buildx builder instance..."
        docker buildx create --name waddleperf-builder --use
        docker buildx inspect --bootstrap
    else
        docker buildx use waddleperf-builder
    fi
    
    log "Starting WaddlePerf Go Client build process..."
    log "Version: $VERSION"
    log "Build Time: $BUILD_TIME"
    log "Git Commit: $GIT_COMMIT"
    log "Platforms: $(printf "%s " "${build_platforms[@]}")"
    
    # Clean if requested
    if [[ "$clean" == "true" ]]; then
        clean_output
    else
        mkdir -p "$OUTPUT_DIR"
    fi
    
    # Run tests if requested
    if [[ "$run_tests" == "true" ]]; then
        run_tests
    fi
    
    # Build binaries
    local failed_builds=()
    for platform in "${build_platforms[@]}"; do
        if ! build_binary "$platform"; then
            failed_builds+=("$platform")
        fi
        
        # Also build runtime image if requested
        if [[ "$build_runtime" == "true" && "$platform" == linux/* ]]; then
            build_runtime_image "$platform" || warn "Failed to build runtime image for $platform"
        fi
    done
    
    # Report failures
    if [[ ${#failed_builds[@]} -gt 0 ]]; then
        error "Failed to build for platforms: $(printf "%s " "${failed_builds[@]}")"
    fi
    
    # Create checksums and archives
    if [[ -n "$(ls -A "$OUTPUT_DIR" 2>/dev/null)" ]]; then
        create_checksums
        create_archives
        
        log "Build completed. Output in: $OUTPUT_DIR"
        ls -la "$OUTPUT_DIR"
    else
        error "No binaries were built successfully"
        exit 1
    fi
    
    success "WaddlePerf Go Client build process completed!"
}

# Run main function with all arguments
main "$@"