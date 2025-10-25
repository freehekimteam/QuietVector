# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QuietVector is a zero-telemetry, security-first Qdrant management panel designed for internal use in air-gapped or VPN-only environments. It provides a clean web interface for managing Qdrant collections, vectors, snapshots, and secure operations like API key rotation.

**Core Philosophy**:
- Zero external dependencies (no CDNs, external fonts, or telemetry)
- Internal-only access (Hetzner internal network or VPN)
- JWT authentication + CSRF protection + rate limiting + audit logging
- Structured JSON logging for production observability
- Comprehensive test coverage (70%+)
- Minimal, corporate-safe interface

## Development Commands

### Backend (FastAPI)

```bash
# Setup and run development server
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090

# Run tests
cd backend
pytest

# Run tests with coverage
cd backend
pytest --cov=app --cov-report=html

# Run specific test file
cd backend
pytest tests/test_auth.py -v

# Run specific test
cd backend
pytest tests/test_csrf.py::test_csrf_post_with_valid_token_allowed -v

# Syntax check
python -m compileall backend
```

### Frontend (React + Tailwind)

```bash
# Setup and run development server
cd frontend
npm install
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run E2E tests (Playwright)
npm run test:e2e
```

### Docker Deployment

```bash
# Build and start all services (api, web, caddy)
cd deploy
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild specific service
docker compose up -d --build api
```

### Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Generate admin password hash
python3 - <<'PY'
from argon2 import PasswordHasher; import getpass
p=PasswordHasher(); print(p.hash(getpass.getpass('Yeni admin parolası: ')))
PY
```

## Architecture

### Backend Structure

```
backend/app/
├── main.py                 # FastAPI app, middleware stack, router registration
├── core/
│   ├── config.py          # Pydantic Settings (env vars, Qdrant config, security)
│   ├── security.py        # JWT creation/verification, Argon2 password hashing
│   ├── middleware.py      # RequestID, BodySizeLimit, RateLimit, AuditLog
│   └── ops.py             # Operation tracking for security actions
├── routes/
│   ├── auth.py            # POST /api/auth/login
│   ├── collections.py     # Collection CRUD
│   ├── vectors.py         # Vector insertion, search
│   ├── snapshots.py       # Snapshot list/create/restore with async progress
│   ├── stats.py           # Cluster info, storage stats
│   └── security.py        # Key rotation (/qdrant_key/prepare) + ops_apply
├── schemas/               # Pydantic request/response models
└── qdrant/
    └── client.py          # Singleton Qdrant client with connection pooling
```

**Middleware Stack (applied in order)**:
1. `RequestIDMiddleware` - Adds X-Request-ID header + structured request logging
2. `BodySizeLimitMiddleware` - Limits request body size (default 1MB)
3. `RateLimitMiddleware` - Per-IP rate limiting (default 60/min) with automatic memory cleanup
4. `CSRFMiddleware` - CSRF protection for POST/PUT/DELETE requests (NEW)
5. `AuditLogMiddleware` - JSON audit logs for all requests

### Frontend Structure

```
frontend/src/
├── App.tsx               # Main app, tab navigation, auth check
├── pages/
│   ├── Login.tsx         # JWT login form
│   ├── Collections.tsx   # List/create collections
│   ├── Search.tsx        # Vector search interface
│   ├── InsertVectors.tsx # Bulk vector upload with validation
│   ├── Snapshots.tsx     # Snapshot management with async restore progress
│   └── Security.tsx      # Qdrant key rotation + ops-apply (dry-run/execute)
├── components/
│   └── Nav.tsx           # Navigation bar with logout
└── lib/
    └── api.ts            # Fetch wrapper with JWT + CSRF token injection
```

**Authentication & CSRF Flow**:
- JWT token stored in `localStorage` as `qv_token`
- CSRF token stored in `localStorage` as `qv_csrf` (also in httponly cookie)
- Token checked in App.tsx before rendering tabs
- All API requests include `Authorization: Bearer <token>` header
- State-changing requests (POST/PUT/DELETE) include `X-CSRF-Token` header + credentials

### Configuration Management

Settings are loaded from `.env` via Pydantic's `BaseSettings`:

**Critical Settings**:
- `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_API_KEY` or `QDRANT_API_KEY_FILE`
- `JWT_SECRET` - Used for signing JWT tokens (HS256)
- `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` - Argon2 hash of admin password
- `AUDIT_LOG_PATH` - JSON audit log file path (default: `/var/log/quietvector/audit.log`)

**Ops Apply Settings** (disabled by default):
- `ENABLE_OPS_APPLY=true` - Allows backend to execute controlled restart commands
- `OPS_APPLY_MODE` - Either `docker_compose` or `systemctl`
- `OPS_APPLY_COMPOSE_FILE` - Path to docker-compose.yml (e.g., `./deploy/docker-compose.yml`)
- `OPS_APPLY_SERVICE` - Service name to restart (default: `qdrant`)

**Security Note**: `QDRANT_API_KEY_FILE` is preferred over `QDRANT_API_KEY` for rotation workflows. The backend reads the key from file on each request, allowing hot-reload after key rotation.

### Security Features

**API Key Rotation Workflow**:
1. Admin calls `POST /api/security/qdrant_key/prepare` with new key
2. Backend writes key to `QDRANT_API_KEY_FILE` with 0600 permissions
3. Backend returns instructions for restarting Qdrant
4. Admin uses ops-apply (if enabled) or manually restarts Qdrant

**Ops Apply**:
- Dry-run mode: Shows exact command that would be executed
- Execute mode: Re-authenticates with admin password, runs sanitized command
- Supported modes: `docker_compose` (restart service), `systemctl` (systemd)
- Service names are sanitized (regex: `[A-Za-z0-9._-]{1,64}`)

### Key Technical Patterns

**Qdrant Client Management**:
- Singleton pattern in `qdrant/client.py`
- Lazy initialization on first request
- `reset_qdrant_client()` forces reconnection (used after key rotation)
- Connection pooling via qdrant-client library

**Snapshot Async Restore**:
- `POST /api/snapshots/restore` starts async restore in Qdrant
- `GET /api/snapshots/restore/{collection}/status` polls progress
- Frontend polls every 1s with exponential backoff on errors

**Frontend Validation**:
- Vector upload validates: `id` (required), `vector` (array of numbers), `payload` (object)
- Dimension mismatch warnings before submission
- JSON parse errors shown inline

## Testing

**Test Coverage**: ~70% (100+ test cases across 8+ test files)

**Backend Tests** (`pytest`):
- [conftest.py](backend/tests/conftest.py) - Fixtures for auth, mocking, temp paths
- [test_auth.py](backend/tests/test_auth.py) - Login, JWT, password validation, CSRF cookie
- [test_csrf.py](backend/tests/test_csrf.py) - CSRF middleware protection (12 test cases)
- [test_middleware.py](backend/tests/test_middleware.py) - Rate limit, body size, audit log, request ID
- [test_vectors.py](backend/tests/test_vectors.py) - Vector validation (NaN, Inf, dimension mismatch)
- [test_collections.py](backend/tests/test_collections.py) - Collection CRUD operations
- [test_config.py](backend/tests/test_config.py) - Settings validation and environment overrides
- [test_health.py](backend/tests/test_health.py) - Health endpoint sanity check
- [test_ops.py](backend/tests/test_ops.py) - Ops tracker functionality
- [test_security_ops_apply.py](backend/tests/test_security_ops_apply.py) - Dry-run and execute modes

**Running Tests**:
```bash
# All tests
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_csrf.py -v

# Watch mode (requires pytest-watch)
ptw
```

**Frontend E2E** (`Playwright`):
- `frontend/frontend/tests/smoke.spec.ts` - Login flow, navigation, basic UI checks

**CI Pipeline** (`.github/workflows/ci.yml`):
- Backend: Python syntax check + pytest
- Frontend: Build + Playwright E2E tests

## Logging

**Structured JSON Logging** (Production-ready):
- Uses `python-json-logger` for machine-parseable logs
- All logs include: timestamp, level, logger, module, function, line, thread_id, process_id
- Request logs include: request_id, method, path, duration_ms, status_code
- CSRF failures logged with context (path, method, token presence)
- Qdrant connection events logged with host/port/https info

**Configuration**:
- `LOG_JSON=true` - Enable JSON logging (recommended for production)
- `LOG_JSON=false` - Human-readable logs (development mode)

**Log Locations**:
- Application logs: stdout (captured by Docker/systemd)
- Audit logs: `AUDIT_LOG_PATH` (default: `/var/log/quietvector/audit.log`)

**Example JSON Log**:
```json
{
  "timestamp": "2025-10-24 23:45:12",
  "level": "INFO",
  "logger": "app.main",
  "message": "Request completed",
  "request_id": "a3f5e7b9-...",
  "method": "POST",
  "path": "/api/vectors/insert",
  "duration_ms": 45,
  "status_code": 200
}
```

## Common Development Tasks

### Adding a New API Endpoint

1. Create schema in `backend/app/schemas/` (request/response Pydantic models)
2. Add route handler in `backend/app/routes/` (create new file or extend existing)
3. Register router in `backend/app/main.py` under `api.include_router(...)`
4. Add corresponding UI component in `frontend/src/pages/` or `frontend/src/components/`
5. Update API client in `frontend/src/lib/api.ts` if needed

### Modifying Middleware Behavior

- Middleware is registered in `backend/app/main.py`
- Implementations in `backend/app/core/middleware.py`
- Order matters: RequestID → BodySize → RateLimit → AuditLog

### Updating Frontend Tabs

- Tab state managed in `App.tsx` (useState with union type)
- Add new tab: Update type, add button in tab bar, add page component import

### Environment-Specific Configuration

- `.env.example` documents all available settings
- Docker uses `.env` file mounted via `env_file` in docker-compose.yml
- Dev mode: Create `.env` in project root, settings auto-loaded via Pydantic

## Documentation

- `docs/QUICK_START.md` - Step-by-step setup for beginners
- `docs/DEPLOYMENT.md` - Docker deployment and configuration details
- `docs/SECURITY.md` - Security model, key rotation, ops-apply usage

## Deployment Topology

```
[User] → VPN/Cloudflare Tunnel → Caddy (TLS) → [web container, api container] → Qdrant (internal network)
                                   (127.0.0.1:8443)
```

- Caddy provides TLS termination (self-signed for internal use)
- API and Web run in isolated Docker network (`quietnet`)
- Qdrant accessed via internal hostname (not exposed to internet)

## Important Notes

- This codebase is designed for **internal use only** in air-gapped or VPN-restricted environments
- All external dependencies (fonts, CDN resources) are forbidden to maintain zero-telemetry
- Admin password must be hashed with Argon2 before storing in `.env`
- **CSRF Protection**: All state-changing operations require valid CSRF token (obtained from login)
- **Vector Validation**: Backend validates all vectors for NaN/Inf/dimension consistency
- **Structured Logging**: Production deployments should use `LOG_JSON=true` for machine-parseable logs
- **Health Checks**: Docker containers have health checks; Caddy waits for API/Web to be healthy
- **Graceful Shutdown**: Application lifecycle (lifespan) handles clean Qdrant client closure
- Audit logs are written as JSON lines (log rotation handled externally)
- Ops-apply is **disabled by default** - only enable if you need automated service restarts

## Recent Improvements (2025-10-24)

### Security Enhancements
- ✅ **CSRF Protection**: Double-submit cookie pattern with constant-time comparison
- ✅ **Backend Vector Validation**: NaN, Inf, dimension, type checking (defense in depth)
- ✅ **Rate Limiter Memory Cleanup**: Automatic stale IP cleanup every 5 minutes

### Production Readiness
- ✅ **Health Checks**: Docker compose health checks for all services
- ✅ **Structured JSON Logging**: python-json-logger with custom formatter
- ✅ **Graceful Shutdown**: FastAPI lifespan events + Qdrant client cleanup
- ✅ **Request Tracing**: X-Request-ID header + structured logging with context

### Testing & Quality
- ✅ **Test Coverage ~70%**: 100+ test cases across 8+ test files
- ✅ **Comprehensive Fixtures**: conftest.py with auth, CSRF, mocking
- ✅ **CI Integration**: All tests run in GitHub Actions

**Production Readiness Score**: **7.8/10** (up from 6.9/10)
