# WaddlePerf — App-Specific Standards

> **Supplement to**: `/CLAUDE.md` and `.claude/rules/`. This file documents WaddlePerf-specific architecture, constraints, and decisions. Do not duplicate generic standards here — only WaddlePerf-specific context.

## What WaddlePerf Is

WaddlePerf is a **network performance testing platform** built by Penguin Tech Inc. It enables complete end-to-end user experience testing: endpoint internet connectivity, latency measurement between regions, and cluster-internal performance benchmarking.

It is **not** a generic web application. Its architecture is shaped by the need to:
- Execute concurrent network tests across protocols (HTTP, TCP, UDP, ICMP, traceroute)
- Stream real-time test results to connected browser clients
- Support both manual (browser) and automated (container client) test execution
- Operate as both SaaS and self-hosted deployment

---

## Service Architecture

WaddlePerf is composed of **7 containers**:

| Container | Language | Framework | Port(s) | Role |
|-----------|----------|-----------|---------|------|
| `unified-api` | Python 3.13 | Quart (async) | 5000 (HTTP), 50051 (gRPC) | Central API: auth, orgs, devices, tests, stats |
| `managerserver-frontend` | TypeScript | React + Vite | 3000 | Admin/manager web UI |
| `webclient-frontend` | TypeScript | React + Vite | 3001 | Browser-based test client UI |
| `testserver` | Go 1.24 | custom HTTP | 8080 | High-performance test execution engine |
| `containerclient` | Python 3.13 | async | — | Automated testing container (no HTTP server) |
| `mariadb` | MariaDB 11.2 | Galera-ready | 3306 | Primary database |
| `adminer` | PHP | Adminer | 8081 | Dev DB admin UI (dev only) |

### Why Quart for unified-api (not Flask)

unified-api **must** be async because:
1. It streams real-time test results over WebSocket while simultaneously handling API requests
2. It calls the Go testServer over HTTP and must not block the event loop during I/O
3. It manages concurrent device connections and test state

Flask (sync) cannot handle these requirements without thread pool hacks. Quart provides native `async/await` with the same Flask API surface.

**Implication**: All DB calls in unified-api use `AsyncDB` from penguin-dal, not `DB`. All route handlers are `async def`.

### Why Flask for managerServer/api (not Quart)

managerServer/api is the **admin backend** — it handles infrequent admin operations (user management, org config, device enrollment). It does not stream data and has low concurrency requirements. Synchronous Flask + penguin-dal `DB` is simpler and sufficient.

### Why Go for testServer

The test execution engine runs potentially hundreds of concurrent network tests (TCP SYN, UDP, ICMP, HTTP). Go's goroutine model handles this workload with far lower overhead than Python threads. XDP/AF_XDP support is included for high-frequency packet processing.

### containerClient

A Python container deployed on test target machines. It:
- Connects to unified-api to register as a device
- Executes test instructions (HTTP, TCP, UDP, ICMP) sent by the platform
- Reports results back to unified-api
- Runs headlessly, no web server

---

## Database Architecture

### Single Shared MariaDB Instance

All services share **one MariaDB 11.2 instance** with **per-service database accounts**:

| Account | Access | Service |
|---------|--------|---------|
| `unified_api_rw` | read/write own tables | unified-api |
| `manager_rw` | read/write own tables | managerServer/api |
| `readonly` | SELECT only | reporting, adminer |

See `database/` directory for schema DDL and seed scripts.

### penguin-dal (as of v1.2.0)

All runtime database access uses **penguin-dal** (replaces PyDAL + Flask-SQLAlchemy ORM):
- `unified-api`: `penguin-dal[quart,mysql]` → `AsyncDB` for async operations
- `managerServer/api`: `penguin-dal[flask,mysql]` → `DB` for sync operations
- Schema reflection is automatic at startup — no `define_table()` calls
- Alembic manages schema migrations (not penguin-dal)

**PyDAL and Flask-SQLAlchemy are no longer used as of v1.2.0.**

### MariaDB Galera (Production)

Production uses Galera cluster for HA. Development uses single-node MariaDB 11.2.
- Short transactions required
- `utf8mb4` charset enforced
- WSREP readiness checks in healthcheck scripts
- `innodb_autoinc_lock_mode=2` required

---

## gRPC Topology

unified-api exposes gRPC on port **50051** for internal service-to-service calls.

```
containerClient  →  unified-api:5000  (REST, device registration + test dispatch)
webClient UI     →  unified-api:5000  (REST + WebSocket)
managerServer    →  unified-api:5000  (REST, stats pull)
testServer       →  unified-api:50051 (gRPC, test result reporting)
unified-api      →  testServer:8080   (REST, test execution requests)
```

Proto definitions: `services/unified-api/proto/`

---

## Protocol Test Types

WaddlePerf tests are typed by network protocol:

| Type | Implementation | Port |
|------|---------------|------|
| `http` | aiohttp (Python) / net/http (Go) | 80/443 or custom |
| `tcp` | asyncio / net.Dial (Go) | custom |
| `udp` | asyncio / net.PacketConn (Go) | custom |
| `icmp` | scapy / golang.org/x/net/icmp | — |
| `trace` | traceroute logic | — |

testServer (Go) handles high-volume test execution. containerClient (Python) handles single-device testing from the target end.

---

## Authentication & Authorization

- **JWT** for user authentication (unified-api issues tokens)
- **Manager API key** for inter-service auth (testServer ↔ unified-api)
- **OIDC scopes** for permission checks (not role names in code)
- `penguin-aaa` used for auth helpers (as of v1.2.0)

Key environment variables:
```
JWT_SECRET=<secret>
MANAGER_API_KEY=<key>
LICENSE_KEY=<key>
MARIADB_HOST=mariadb
MARIADB_USER=unified_api_rw
MARIADB_PASSWORD=<secret>
MARIADB_DATABASE=waddleperf
```

---

## License Gating

Enterprise features are gated via `penguin-licensing`:
- AI-powered test analysis (WaddleAI integration)
- SSO / SAML
- Advanced analytics and reporting
- Multi-region scheduling

Domain-based bypass applies to `*.penguintech.cloud` and `*.penguincloud.io` — no license check for PenguinTech-hosted instances.

---

## Shared Libraries Status

### shared/go_libs/ — KEEP

`shared/go_libs/` provides gin, golang-jwt, gRPC, and uuid utilities used by testServer and goClient. `go-common` from penguin-libs provides only zap logging — it does not replace gin or gRPC.

**Decision**: Keep `shared/go_libs/`. Add `go-common` as a dependency for structured logging.

### shared/react_libs/ — EVALUATE FOR MIGRATION

`shared/react_libs/` may duplicate components from `@penguintechinc/react-libs` v1.3.0 (LoginPageBuilder, FormModalBuilder, SidebarMenu).

**Migration path**: When refactoring React frontends, prefer `@penguintechinc/react-libs`. New components must use the published package. Existing duplicates should be migrated progressively — do not maintain both.

---

## Test Coverage Requirements

**90%+ mandatory** for all services, enforced at CI:

| Service | Test framework | Coverage tool |
|---------|---------------|---------------|
| unified-api | pytest + pytest-asyncio | pytest-cov (--cov-fail-under=90) |
| managerServer/api | pytest | pytest-cov |
| webClient/api | pytest | pytest-cov |
| containerClient | pytest + pytest-asyncio | pytest-cov |
| testServer (Go) | go test | go tool cover (-func, fail < 90%) |
| webClient/frontend | Vitest | @vitest/coverage-v8 (90% threshold) |
| managerServer/frontend | Vitest | @vitest/coverage-v8 (90% threshold) |
| E2E | Playwright | — (functional coverage) |

Playwright artifacts use `/tmp/playwright-waddleperf/` and are cleaned up after each run.

---

## Deployment Environments

| Env | URL | Deploy method |
|-----|-----|---------------|
| Alpha | `https://waddleperf.localhost.local` | Kustomize → `local-alpha` context |
| Beta | `https://waddleperf.penguintech.cloud` | Helm → `dal2-beta` context |
| Production | `https://waddleperf.penguincloud.io` | Helm → `waddleperf-prod` context |

Kubernetes namespace: `waddleperf` (all environments).

---

## Development Quick Reference

```bash
# Start local stack
docker compose up -d

# Run all tests
make test

# Run specific service tests
cd services/unified-api && pytest --cov --cov-fail-under=90
cd managerServer/api && pytest --cov --cov-fail-under=90
cd testServer && go test ./... -coverprofile=coverage.out

# Lint
make lint

# Security scan
make test-security

# Seed dev data
make seed-mock-data

# Version management
./scripts/version/update-version.sh minor   # Only if current version is tagged
./scripts/version/update-version.sh         # Build timestamp only
```

---

*Last updated: v1.2.0 | Maintained by Penguin Tech Inc*
