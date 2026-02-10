# WaddlePerf CI/CD Workflows & Performance Monitoring Deployment

Comprehensive CI/CD pipeline documentation for WaddlePerf's multi-component performance testing platform deployed across multiple services.

## Table of Contents

1. [Overview](#overview)
2. [Workflow Architecture](#workflow-architecture)
3. [Build Services & Components](#build-services--components)
4. [Naming Conventions](#naming-conventions)
5. [Path Filter Requirements](#path-filter-requirements)
6. [Security Scanning](#security-scanning)
7. [Multi-Component Deployment](#multi-component-deployment)
8. [Performance Monitoring Integration](#performance-monitoring-integration)
9. [Version Release Workflow](#version-release-workflow)
10. [Build Optimization](#build-optimization)
11. [Local Testing](#local-testing)
12. [Troubleshooting](#troubleshooting)

---

## Overview

WaddlePerf uses GitHub Actions for comprehensive CI/CD automation across multiple components:

- **testServer** (Go): High-performance network test execution
- **managerServer** (Python/Flask): Centralized management and authentication
- **webClient** (Python/Flask): Browser-based testing interface
- **goClient** (Go): Cross-platform desktop client
- **containerClient** (Python): Automated container-based testing
- **WebUI** (React): Dashboard interfaces for manager and webClient

**Key Philosophy**: All workflows optimized for **speed, reliability, and security**. Path filters ensure workflows only run when relevant files change, saving CI/CD resources.

---

## Workflow Architecture

### Pipeline Structure

Each build service has a dedicated workflow with this progression:

```
┌──────────────┐
│ Lint Stage   │ (Fail fast on code quality issues)
└───────┬──────┘
        │
        ▼
┌──────────────┐
│ Test Stage   │ (Unit + Integration tests)
└───────┬──────┘
        │
        ▼
┌──────────────────────┐
│ Build & Push Stage   │ (Docker image build for multi-arch)
└───────┬──────────────┘
        │
        ▼
┌──────────────────────┐
│ Security Scan Stage  │ (Trivy container scan, CodeQL)
└──────────────────────┘
```

### Job Dependencies

- **Lint** → Runs immediately on push/PR
- **Test** → Requires lint to pass (fails fast on quality)
- **Build** → Requires both lint and test to pass
- **Security Scan** → Runs after build (informational)

### When Workflows Trigger

Workflows trigger when:
1. Code changes in the service directory
2. `.version` file changes (ensures version updates trigger all builds)
3. The workflow file itself changes
4. Manual trigger via `workflow_dispatch`

**Branches**: Main workflow triggers on `main` and `develop` branches. Pull requests trigger on `main` branch only.

---

## Build Services & Components

### Service Directory Structure

| Service | Type | Directory | Dockerfile | Trigger |
|---------|------|-----------|-----------|---------|
| testServer | Go | `testserver/` | `testserver/Dockerfile` | `.version`, `testserver/**` |
| managerServer API | Python | `managerServer/` | `managerServer/Dockerfile` | `.version`, `managerServer/**` |
| managerServer UI | Node.js | `managerServer/ui/` | `managerServer/ui/Dockerfile` | `.version`, `managerServer/ui/**` |
| webClient API | Python | `webClient/` | `webClient/Dockerfile` | `.version`, `webClient/**` |
| webClient UI | Node.js | `webClient/ui/` | `webClient/ui/Dockerfile` | `.version`, `webClient/ui/**` |
| goClient | Go | `goClient/` | `goClient/Dockerfile` | `.version`, `goClient/**` |
| containerClient | Python | `containerClient/` | `containerClient/Dockerfile` | `.version`, `containerClient/**` |

### Workflow Files

```
.github/workflows/
├── build-testserver.yml        # testServer build pipeline
├── build-manager-api.yml       # managerServer API build
├── build-manager-ui.yml        # managerServer UI build
├── build-webclient-api.yml     # webClient API build
├── build-webclient-ui.yml      # webClient UI build
├── build-go-client.yml         # goClient build pipeline
├── build-container-client.yml  # containerClient build pipeline
├── version-release.yml         # Version-based pre-release creation
└── security-scan.yml           # Comprehensive security scanning
```

---

## Naming Conventions

### Image Naming Patterns

#### Regular Builds (No Version Change)

When code changes but `.version` file doesn't change:

**Main Branch**:
```
ghcr.io/penguintechinc/waddleperf-testserver:beta-<epoch64>
ghcr.io/penguintechinc/waddleperf-manager-api:beta-<epoch64>
```

**Development Branches**:
```
ghcr.io/penguintechinc/waddleperf-testserver:alpha-<epoch64>
ghcr.io/penguintechinc/waddleperf-manager-api:alpha-<epoch64>
```

#### Version Builds (Version Change)

When `.version` file changes:

**Main Branch**:
```
ghcr.io/penguintechinc/waddleperf-testserver:v4.0.0-beta
ghcr.io/penguintechinc/waddleperf-manager-api:v4.0.0-beta
```

**Development Branches**:
```
ghcr.io/penguintechinc/waddleperf-testserver:v4.0.0-alpha
ghcr.io/penguintechinc/waddleperf-manager-api:v4.0.0-alpha
```

#### Release Tags (Official Releases)

```
ghcr.io/penguintechinc/waddleperf-testserver:v4.0.0
ghcr.io/penguintechinc/waddleperf-testserver:latest
```

---

## Path Filter Requirements

### Why Path Filters Matter

Path filters optimize CI/CD by:
- **Reducing build time**: Don't rebuild unrelated services
- **Saving costs**: Fewer GitHub Actions minutes used
- **Faster feedback**: Developers get results quicker
- **Isolation**: Changes in one service don't trigger others

### Standard Path Filter Pattern

Every build workflow must include these paths:

```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'testserver/**'          # Service code
      - '.version'               # Critical: trigger on version changes
      - '.github/workflows/build-testserver.yml'  # Workflow itself
  pull_request:
    branches: [main]
    paths:
      - 'testserver/**'
      - '.version'
      - '.github/workflows/build-testserver.yml'
```

---

## Security Scanning

### Language-Specific Security Checks

#### Python Services (Flask)

**Bandit** - Scans for Python security issues:
```bash
bandit -r managerServer webClient -ll  # Only HIGH/CRITICAL
```

**Additional Checks**:
- Linting: `flake8`, `black`, `isort`
- Type checking: `mypy` for type safety
- Dependency audit: `safety check` for vulnerable packages

#### Go Services

**gosec** - Scans for Go security issues:
```bash
gosec -fmt json -out results.json ./...
```

**Additional Checks**:
- Linting: `golangci-lint` (includes gosec rules)
- Dependency audit: `go mod audit`

#### Node.js Services

**npm audit** - Scans npm dependencies:
```bash
npm audit --audit-level=high
```

**Additional Checks**:
- Linting: `eslint`, `prettier`
- Dependency tracking: Dependabot alerts

### Container Scanning

**Trivy** - Scans built Docker images:
```bash
trivy image ghcr.io/penguintechinc/waddleperf-testserver:latest
```

- Scans for known vulnerabilities in base image and installed packages
- Results uploaded to GitHub Security tab
- Does not fail build (allows informational scanning)

### CodeQL Analysis

GitHub's CodeQL performs automatic code analysis:
- Detects common code patterns that could be exploited
- Runs on all push events to main/develop
- Results visible in Security tab → Code scanning alerts

---

## Multi-Component Deployment

### Coordinated Deployment Strategy

When `.version` changes, all services rebuild together:

```
Update .version → Commit to main → All workflows trigger → All services rebuild
```

This ensures:
- Consistent versioning across all components
- All services use same version tag
- Coordinated release and rollout
- Simple version tracking

### Service Dependencies

**Deployment Order**:
1. **Database service** (MariaDB Galera) - Required by all others
2. **testServer** - Independent, can start immediately
3. **managerServer API** - Needs database
4. **managerServer UI** - Communicates with API
5. **webClient API** - Needs database and testServer
6. **webClient UI** - Communicates with API
7. **goClient** - Can run independently
8. **containerClient** - Needs testServer

---

## Performance Monitoring Integration

### Performance Metrics Collection

Workflows collect build performance metrics:

- **Build duration**: Time from start to finish
- **Cache hit rate**: Percentage of cached layers used
- **Image size**: Final Docker image size
- **Security scan duration**: Time to scan for vulnerabilities

### Deployment Status Tracking

Each workflow updates deployment status:

```yaml
- name: Create deployment status
  if: always()
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.repos.createDeploymentStatus({
        owner: context.repo.owner,
        repo: context.repo.repo,
        deployment_id: deploymentId,
        state: '${{ job.status }}',
        description: 'WaddlePerf service deployment',
        auto_merge: false,
      })
```

---

## Version Release Workflow

### Overview

The `version-release.yml` workflow automatically creates GitHub pre-releases when `.version` file changes on the main branch.

### Workflow Behavior

**Trigger**: `.version` file change on `main` branch

**Actions**:
1. Read `.version` file and extract semantic version
2. Check if version is not default (0.0.0)
3. Check if release already exists
4. Generate release notes from commit history
5. Create GitHub pre-release with auto-generated notes
6. Skip if version is 0.0.0 or release already exists

### Release Lifecycle

```
Developer updates .version file
         │
         ▼
        Commit on main branch
         │
         ▼
       Push to GitHub
         │
         ▼
version-release.yml triggers
         │
         ├─→ Extract version from .version file
         │
         ├─→ Check if 0.0.0 (skip if true)
         │
         ├─→ Check if release exists (skip if true)
         │
         └─→ Create pre-release with notes
         │
         ▼
GitHub pre-release created & visible
```

---

## Build Optimization

### Multi-Architecture Builds

All Docker builds target multiple architectures:

```yaml
platforms: linux/amd64,linux/arm64
```

Benefits:
- Single image works across architectures
- Automatic architecture selection when pulling
- Future-proof for ARM adoption

### GitHub Actions Cache

Builds use GitHub Actions cache for faster builds:

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

**How it works**:
- First build: Takes full time, stores cache
- Subsequent builds: Reuse cached layers (often 50-80% faster)
- Cache includes: Base image, dependencies, intermediate steps

### Docker Build Caching Strategy

**Layer caching order** (from slowest to fastest to change):

1. **Base image** (rarely changes) → Cached longest
2. **System dependencies** (change occasionally) → Medium cache
3. **Application dependencies** (change per commit) → Regular cache
4. **Application code** (always changes) → Not cached

---

## Local Testing

### Prerequisites

Ensure you have:

```bash
# Docker for building/running containers
docker --version          # Docker 24+
docker-compose --version  # Docker Compose 2+

# Language runtimes
python --version          # 3.13+ for Python services
go version                # 1.23+ for Go services
node --version            # 18+ for Node.js services
```

### Testing Before Commit

**Always run these checks locally before committing**:

```bash
# 1. Linting (catches code quality issues first)
make lint

# 2. Security checks (catches vulnerable dependencies)
make security-scan

# 3. Unit tests (verify functionality)
make test-unit

# 4. Build locally
docker-compose build --no-cache

# 5. Run locally
docker-compose up -d

# 6. Smoke tests
make smoke-test
```

---

## Troubleshooting

### Workflow Doesn't Trigger

**Check if `.version` is in path filter**:
```yaml
paths:
  - '.version'  # Critical: must be included
```

**Verify branch is configured**: Only `main` and `develop` have workflows

**Check path filter syntax**: Make sure patterns are correct
```yaml
paths:
  - 'testserver/**'  # Correct
  - 'services/**'    # Might be too broad
```

### Build Fails in GitHub Actions

**Common causes**:
1. Environment variable missing
2. Permissions issue with Docker registry
3. Dependency version mismatch
4. File not found in container

**Debug steps**:
```bash
# View full build output in GitHub Actions
# → Actions → [Workflow] → [Run] → Click job to expand

# Test in container locally
docker run -it waddleperf-testserver:test /bin/bash
# Verify files exist, permissions correct, etc.
```

### Security Scan Failures

**Fix vulnerable dependencies**:
```bash
# Go
go get -u ./...

# Python
pip install --upgrade vulnerable-package

# Node.js
npm update
npm audit fix
```

---

## Quick Reference

### Checklist: Before Committing Code

```
[ ] Linting passes (make lint)
[ ] Security checks pass (make security-scan)
[ ] Tests pass (make test)
[ ] Docker builds (docker-compose build --no-cache)
[ ] Smoke tests pass (make smoke-test)
[ ] No debug code left in
[ ] Configuration is correct
```

### Checklist: After Pushing Code

```
[ ] GitHub Actions workflow triggered
[ ] Workflow completes successfully
[ ] Images pushed to registry
[ ] Image tagged correctly
[ ] Pre-release created (if .version changed)
[ ] No security vulnerabilities
```

### Checklist: Updating .version

```
[ ] Determine version type (patch/minor/major)
[ ] Update .version file
[ ] Verify format (X.Y.Z)
[ ] Commit and push
[ ] Verify pre-release created
```

---

## Related Documentation

- **Testing**: [Testing Documentation](TESTING.md)
- **Pre-Commit**: [Pre-Commit Checklist](PRE_COMMIT.md)
- **Development**: [Development Guide](DEVELOPMENT.md)
- **Standards**: [Development Standards](STANDARDS.md)

---

**Last Updated**: 2026-01-06
**Maintained by**: Penguin Tech Inc
