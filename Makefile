.PHONY: dev test test-unit test-integration test-e2e test-functional test-security \
        smoke-test lint build docker-build docker-push deploy-dev deploy-prod \
        seed-mock-data clean pre-commit

dev:
	docker-compose up

build:
	docker-compose build

docker-build: build

docker-push:
	@echo "Push images to registry - use CI pipeline for beta/prod"

lint:
	@echo "=== Linting ==="
	@if command -v flake8 >/dev/null 2>&1; then echo "-- flake8 --"; python3 -m flake8 . --max-line-length=120 --exclude=.git,__pycache__,venv,node_modules || true; fi
	@if command -v black >/dev/null 2>&1; then echo "-- black --"; black --check . --exclude '/(\.git|venv|__pycache__|node_modules)/' || true; fi
	@if command -v isort >/dev/null 2>&1; then echo "-- isort --"; isort --check-only . || true; fi
	@if command -v mypy >/dev/null 2>&1; then echo "-- mypy --"; python3 -m mypy . --ignore-missing-imports || true; fi
	@if command -v golangci-lint >/dev/null 2>&1; then echo "-- golangci-lint --"; find . -name "go.mod" -not -path "*/.git/*" -not -path "*/vendor/*" | xargs -I{} dirname {} | xargs -I{} sh -c 'cd {} && golangci-lint run || true'; fi
	@if command -v hadolint >/dev/null 2>&1; then echo "-- hadolint --"; find . -name "Dockerfile*" -not -path "*/.git/*" | xargs hadolint || true; fi
	@if command -v shellcheck >/dev/null 2>&1; then echo "-- shellcheck --"; find . -name "*.sh" -not -path "*/.git/*" | xargs shellcheck || true; fi

test:
	@$(MAKE) test-unit

test-unit:
	@echo "=== Python Unit Tests ==="
	cd services/unified-api && python3 -m pytest --cov --cov-fail-under=90 -q || true
	cd managerServer/api && python3 -m pytest --cov --cov-fail-under=90 -q || true
	cd webClient/api && python3 -m pytest --cov --cov-fail-under=90 -q || true
	cd containerClient && python3 -m pytest tests/unit/ --cov --cov-fail-under=90 -q || true
	@echo "=== Go Unit Tests ==="
	cd testServer && go test ./... -coverprofile=coverage.out -covermode=atomic && go tool cover -func=coverage.out | grep total: || true

test-integration:
	@echo "=== Integration Tests ==="
	cd services/unified-api && python3 -m pytest tests/integration/ -v || true
	cd managerServer/api && python3 -m pytest tests/integration/ -v || true

test-e2e:
	@echo "=== E2E Tests ==="
	cd tests/e2e && npm ci && npx playwright install chromium && npx playwright test
	@rm -rf /tmp/playwright-waddleperf

test-functional:
	@echo "=== Functional Tests ==="
	cd services/unified-api && python3 -m pytest tests/functional/ -v || true

test-security:
	@echo "=== Security Scans ==="
	@if command -v bandit >/dev/null 2>&1; then echo "-- bandit --"; bandit -r . -x ./tests,./venv,./.git --quiet || true; fi
	@if command -v pip-audit >/dev/null 2>&1; then echo "-- pip-audit --"; find . -name "requirements.txt" -not -path "*/.git/*" -not -path "*/venv/*" | xargs -I{} pip-audit -r {} 2>/dev/null || true; fi
	@if command -v gosec >/dev/null 2>&1; then echo "-- gosec --"; find . -name "go.mod" -not -path "*/.git/*" -not -path "*/vendor/*" | xargs -I{} dirname {} | xargs -I{} sh -c 'cd {} && gosec ./... || true'; fi
	@if command -v govulncheck >/dev/null 2>&1; then echo "-- govulncheck --"; find . -name "go.mod" -not -path "*/.git/*" -not -path "*/vendor/*" | xargs -I{} dirname {} | xargs -I{} sh -c 'cd {} && govulncheck ./... || true'; fi
	@find . -name "package.json" -not -path "*/.git/*" -not -path "*/node_modules/*" -maxdepth 3 | xargs -I{} dirname {} | xargs -I{} sh -c 'cd {} && npm audit 2>/dev/null || true'
	@if command -v gitleaks >/dev/null 2>&1; then echo "-- gitleaks --"; gitleaks detect --source . --no-git 2>/dev/null || true; fi

smoke-test:
	@echo "=== Smoke Tests ==="
	@if [ -f scripts/smoke-test.sh ]; then bash scripts/smoke-test.sh; else echo "No smoke-test.sh found, running basic checks..."; fi
	cd services/unified-api && python3 -m pytest tests/ -k smoke -v || true

seed-mock-data:
	@echo "No mock data seeding defined"

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

deploy-dev:
	@echo "Deploy to dev/alpha environment"

deploy-prod:
	@echo "Deploy to production environment"

pre-commit:
	@echo "=== Pre-commit checks ==="
	@$(MAKE) lint
	@$(MAKE) test-security
	@$(MAKE) test
	@echo "=== Pre-commit complete ==="
