#!/bin/bash
# Deploy to Beta - waddleperf
# Deploys to beta K8s cluster with rollback capability

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
KUBE_CONTEXT="${KUBE_CONTEXT:-dal2-beta}"
NAMESPACE="${NAMESPACE:-waddleperf}"
RELEASE_NAME="waddleperf"
CHART_PATH="$PROJECT_ROOT/k8s/helm/waddleperf"
VALUES_FILE="$CHART_PATH/values-beta.yaml"
IMAGE_REGISTRY="ghcr.io/penguintechinc/waddleperf"
APP_HOST="waddleperf.penguintech.cloud"

# Default flags
DRY_RUN=0
ROLLBACK=0
BUILD_IMAGES=1
SERVICE=""
IMAGE_TAG=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_section() { echo ""; echo -e "${BLUE}========================================${NC}"; echo -e "${BLUE}$1${NC}"; echo -e "${BLUE}========================================${NC}"; echo ""; }

check_prerequisites() {
    log_section "Checking Prerequisites"
    for cmd in docker kubectl helm; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "$cmd is not installed"
            return 1
        fi
        log_info "$cmd: found"
    done
    if ! kubectl config get-contexts "$KUBE_CONTEXT" &>/dev/null; then
        log_error "Context not found: $KUBE_CONTEXT"
        return 1
    fi
    if [ ! -d "$CHART_PATH" ]; then
        log_error "Chart not found: $CHART_PATH"
        return 1
    fi
    if [ ! -f "$VALUES_FILE" ]; then
        log_error "Values file not found: $VALUES_FILE"
        return 1
    fi
}

build_and_push_images() {
    log_section "Building and Pushing Docker Images"
    local EPOCH
    EPOCH=$(date +%s)
    if [ -z "$IMAGE_TAG" ] || [ "$IMAGE_TAG" = "beta" ]; then
        IMAGE_TAG="beta-${EPOCH}"
    fi
    local SERVICES=("testserver" "unified-api" "webui")
    for svc in "${SERVICES[@]}"; do
        if [ -n "$SERVICE" ] && [ "$SERVICE" != "$svc" ]; then continue; fi
        local dockerfile=""
        case "$svc" in
            testserver) dockerfile="$PROJECT_ROOT/testServer/Dockerfile";;
            unified-api) dockerfile="$PROJECT_ROOT/services/unified-api/Dockerfile";;
            webui) dockerfile="$PROJECT_ROOT/webClient/Dockerfile";;
        esac
        if [ ! -f "$dockerfile" ]; then
            log_warn "Dockerfile not found for $svc at $dockerfile, skipping..."
            continue
        fi
        log_info "Building $svc..."
        docker build -t "$IMAGE_REGISTRY/$svc:$IMAGE_TAG" -t "$IMAGE_REGISTRY/$svc:beta" -f "$dockerfile" "$PROJECT_ROOT"
        log_info "Pushing $svc with tag $IMAGE_TAG..."
        docker push "$IMAGE_REGISTRY/$svc:$IMAGE_TAG"
        docker push "$IMAGE_REGISTRY/$svc:beta"
        log_info "✓ $svc pushed successfully"
    done
}

do_deploy() {
    log_section "Deploying with Helm"
    local helm_args=("upgrade" "--install" "$RELEASE_NAME" "$CHART_PATH" "--kube-context=$KUBE_CONTEXT" "--namespace=$NAMESPACE" "--values=$VALUES_FILE" "--set=image.tag=$IMAGE_TAG" "--wait" "--timeout=10m")
    if ! kubectl --context="$KUBE_CONTEXT" get namespace "$NAMESPACE" &>/dev/null; then
        log_info "Creating namespace $NAMESPACE..."
        helm_args+=("--create-namespace")
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
        helm_args+=("--dry-run")
        log_warn "DRY RUN MODE - No changes will be applied"
    fi
    helm "${helm_args[@]}"
}

do_rollback() {
    log_section "Rolling Back"
    helm rollback "$RELEASE_NAME" --kube-context="$KUBE_CONTEXT" -n "$NAMESPACE"
    log_info "Rollback completed"
}

verify_deployment() {
    if [ "$DRY_RUN" -eq 1 ]; then return 0; fi
    log_section "Verifying Deployment"
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" rollout status deployment/"$RELEASE_NAME" --timeout=300s || true
    log_info "Pod status:"
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" get pods
}

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag=*) IMAGE_TAG="${1#*=}"; shift;;
        --tag) IMAGE_TAG="$2"; shift 2;;
        --service=*) SERVICE="${1#*=}"; shift;;
        --service) SERVICE="$2"; shift 2;;
        --ci-tag=*) IMAGE_TAG="${1#*=}"; BUILD_IMAGES=0; shift;;
        --ci-tag) IMAGE_TAG="$2"; BUILD_IMAGES=0; shift 2;;
        --skip-build) BUILD_IMAGES=0; shift;;
        --dry-run) DRY_RUN=1; shift;;
        --rollback) ROLLBACK=1; shift;;
        -h|--help) echo "Usage: $0 [--tag=TAG] [--ci-tag=TAG] [--service=SVC] [--skip-build] [--dry-run] [--rollback]"; exit 0;;
        *) log_error "Unknown: $1"; exit 1;;
    esac
done

main() {
    log_section "WaddlePerf - Beta Deployment"
    check_prerequisites || exit 1
    if [ "$ROLLBACK" -eq 1 ]; then do_rollback; exit $?; fi
    if [ "$BUILD_IMAGES" -eq 1 ]; then build_and_push_images || exit 2; fi
    do_deploy || exit 3
    verify_deployment
    log_section "Deployment Summary"
    echo -e "${GREEN}✓${NC} Release: $RELEASE_NAME"
    echo -e "${GREEN}✓${NC} Namespace: $NAMESPACE"
    echo -e "${GREEN}✓${NC} Tag: $IMAGE_TAG"
    echo -e "${GREEN}✓${NC} URL: https://$APP_HOST"
    log_info "Deployment complete!"
}

main
