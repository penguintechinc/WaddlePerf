# CLAUDE.md - AI Assistant Context for WaddlePerf

## Project Overview
WaddlePerf is a comprehensive network performance testing and monitoring platform that tests user experience between endpoints. It provides both client and server components for network diagnostics, bandwidth testing, and connectivity analysis.

## Important Instructions for AI Assistants

### Core Principles
1. **NEVER leave placeholders** - Always fully complete each task without leaving TODO comments, placeholder values, or incomplete implementations
2. **Always test and lint** - Before marking any Go or Docker work as complete:
   - Run `go build` and `go test` for Go code
   - Run `docker build` for Dockerfiles
   - Ensure all linting passes without errors
3. **Verify functionality** - Test that your changes work as intended before moving on
4. **No partial implementations** - If you start a feature, complete it entirely

## Project Structure

### Client Component (`/client/`)
- Python-based with py4web framework
- Web UI at `client/web/apps/`
- Testing tools in `client/bins/`
- Ansible playbooks in `client/jobs/`
- Configuration in `client/vars/base.yml`

### Server Component (`/server/`)
- Python Flask application
- Web services in `server/web/`
- Server utilities in `server/bins/`
- LibreSpeed integration in `server/libs/speedtest/`
- Configuration in `server/vars/base.yml`

### Go Clients (`/go-client/`)
- Currently in development phase
- Will provide native desktop clients
- Requires multi-platform builds (Linux, Windows, macOS)

## Technology Stack
- **Languages**: Python 3, Go
- **Frameworks**: Flask (server), py4web (client)
- **Infrastructure**: Docker, Ansible, nginx
- **Testing Tools**: iperf3, pping, httptrace, MTR, sshping
- **CI/CD**: GitHub Actions

## Testing Requirements

### For Python Code
- Use async and threading where possible for performance
- Test with py4web's built-in testing if modifying web components
- Verify Docker containers build and run successfully

### For Go Code
- Run `go mod tidy` to manage dependencies
- Run `go fmt` for code formatting
- Run `go vet` for static analysis
- Run `go test ./...` for all tests
- Build for target platforms before committing

### For Docker
- Test builds with `docker build`
- Verify containers run with `docker run`
- Check health endpoints work correctly

## Build Commands

### Client Docker Build
```bash
docker build -t waddleperf-client ./client
```

### Server Docker Build
```bash
docker build -t waddleperf-server ./server
```

### Go Client Build (multi-platform)
```bash
# Linux AMD64
GOOS=linux GOARCH=amd64 go build -o waddleperf-linux-amd64

# Linux ARM64
GOOS=linux GOARCH=arm64 go build -o waddleperf-linux-arm64

# Windows AMD64
GOOS=windows GOARCH=amd64 go build -o waddleperf-windows-amd64.exe

# macOS Universal (requires additional tooling)
GOOS=darwin GOARCH=amd64 go build -o waddleperf-darwin-amd64
GOOS=darwin GOARCH=arm64 go build -o waddleperf-darwin-arm64
# Then use lipo to create universal binary
```

## Testing Approach
WaddlePerf uses a 3-tier testing system:
1. **Tier 1**: Basic connectivity tests (frequent)
2. **Tier 2**: Intermediate diagnostics (on threshold breach)
3. **Tier 3**: Comprehensive analysis (on critical issues)

## Configuration Files
- Docker Compose: `/docker-compose.yml`
- Client config: `/client/vars/base.yml`
- Server config: `/server/vars/base.yml`
- GitHub Actions: `/.github/workflows/`

## Network Ports
- HTTP: 80
- HTTPS: 443
- iperf3: 5201
- Web UI: 8080
- UDP Ping: 2000

## Development Workflow
1. Make changes in feature branch
2. Test thoroughly (unit, integration, Docker builds)
3. Lint and format code
4. Update documentation if needed
5. Create pull request to main branch

## Key Features to Maintain
- AutoPerf mode for continuous monitoring
- Multi-tier escalation testing
- S3 integration for results storage
- Geographic IP analysis
- Multiple protocol support (TCP, UDP, HTTP, HTTPS, SSH, DNS)

## Security Considerations
- Containers run as non-root user (www-data)
- SSL/TLS certificate management
- Input validation for all user inputs
- No hardcoded secrets or credentials
- Use environment variables for configuration

## Documentation
- Main docs in `/docs/` folder
- README.md for overview
- RELEASE_NOTES.md for version history
- In-code comments for complex logic only

## Common Tasks

### Adding a New Test Tool
1. Add binary to appropriate bins/ folder
2. Create wrapper function in Python
3. Update Ansible playbook to install
4. Add to configuration variables
5. Test in Docker container
6. Document usage

### Updating Dependencies
1. Python: Update requirements.txt
2. Go: Update go.mod and run `go mod tidy`
3. Docker: Update base images in Dockerfiles
4. Test all changes thoroughly

### Creating a Release
1. Update version numbers
2. Update RELEASE_NOTES.md
3. Test all components
4. Tag release in git
5. GitHub Actions will build and publish

## Contact and Support
- Organization: Penguin Technologies Inc.
- Repository: https://github.com/penguintechinc/WaddlePerf
- Issues: Report at GitHub Issues page

Remember: Always complete tasks fully, test thoroughly, and never leave placeholders!