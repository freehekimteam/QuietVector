# QuietVector Deployment Guide

Production deployment checklist and best practices for QuietVector.

---

## Pre-Deployment Checklist

### 1. Code Quality & Testing

- [ ] All tests passing: `cd backend && pytest`
- [ ] Type checking passes: `cd frontend && npm run type-check`
- [ ] Test coverage ≥ 70%: `pytest --cov=app --cov-report=term`
- [ ] E2E tests passing: `cd frontend && npm run test:e2e`
- [ ] No security vulnerabilities: `pip check` and `npm audit`
- [ ] Code linting clean: `ruff check backend/app`

### 2. Configuration Review

- [ ] `.env` file created from `.env.example`
- [ ] **MASTER_PASSWORD** set to strong passphrase (min 24 chars)
- [ ] **JWT_SECRET** generated: `openssl rand -hex 32`
- [ ] **QDRANT_API_KEY** generated: `openssl rand -base64 32`
- [ ] **ADMIN_TOKEN** generated for ops-apply: `openssl rand -base64 32`
- [ ] Token expiry appropriate for use case (default: 60 min)
- [ ] Rate limit thresholds set appropriately
- [ ] Body size limits configured for expected payloads

### 3. Security Hardening

- [ ] All secrets rotated from defaults
- [ ] `.env` file has `chmod 600` permissions
- [ ] Git history checked for leaked secrets: `git log -p | grep -i password`
- [ ] Firewall rules configured (only 443/tcp public)
- [ ] SSL/TLS certificates configured in Caddy
- [ ] CSRF protection enabled (default: on)
- [ ] Rate limiting enabled (default: 100 req/min)
- [ ] Body size limit enabled (default: 10 MB)
- [ ] Audit logging enabled (default: on)

### 4. Infrastructure Preparation

- [ ] Docker & Docker Compose installed (min: Docker 24.0, Compose v2.20)
- [ ] Sufficient disk space (min: 20 GB for Qdrant data)
- [ ] Sufficient RAM (min: 4 GB, recommended: 8 GB)
- [ ] Backups configured for:
  - Qdrant data volume: `deploy/qdrant_data/`
  - SQLite database: `backend/audit.db`
  - `.env` file (encrypted)
- [ ] Monitoring/alerting configured (Prometheus + Grafana recommended)
- [ ] Log rotation configured for Docker logs

---

## Deployment Steps

### Option 1: Standard Deployment (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/yourorg/QuietVector.git
cd QuietVector

# 2. Create and configure .env
cp .env.example .env
nano .env  # Configure all secrets

# 3. Build and start services
docker compose -f deploy/docker-compose.yml up -d --build

# 4. Verify health
docker compose -f deploy/docker-compose.yml ps
curl https://your-domain.com/health

# 5. Check logs
docker compose -f deploy/docker-compose.yml logs -f
```

### Option 2: Development Deployment

```bash
# Backend (terminal 1)
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090

# Frontend (terminal 2)
cd frontend
npm install
npm run dev

# Qdrant (terminal 3)
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_data:/qdrant/storage \
  qdrant/qdrant:v1.7.4
```

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# Overall system health
curl https://your-domain.com/health

# Individual service health
docker compose -f deploy/docker-compose.yml ps

# Expected output:
# NAME     STATUS              PORTS
# api      Up (healthy)        8090/tcp
# web      Up (healthy)        5173/tcp
# qdrant   Up (healthy)        6333-6334/tcp
# caddy    Up (healthy)        80/tcp, 443/tcp
```

### 2. Functional Testing

```bash
# Test login
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-master-password"}'

# Expected: {"access_token":"...", "csrf_token":"..."}

# Test collection creation (use tokens from above)
curl -X POST https://your-domain.com/api/collections \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","size":384,"distance":"Cosine"}'

# Expected: {"status":"ok"}
```

### 3. Performance Baseline

```bash
# Measure response times
ab -n 100 -c 10 https://your-domain.com/health

# Expected:
# - 50th percentile: < 50ms
# - 95th percentile: < 200ms
# - 99th percentile: < 500ms
```

### 4. Security Validation

```bash
# Test CSRF protection
curl -X POST https://your-domain.com/api/collections \
  -H "Authorization: Bearer VALID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","size":384,"distance":"Cosine"}'

# Expected: 403 Forbidden (missing CSRF token)

# Test rate limiting
for i in {1..150}; do
  curl https://your-domain.com/health
done

# Expected: 429 Too Many Requests after ~100 requests
```

---

## Monitoring & Maintenance

### 1. Metrics to Monitor

**System Level:**
- CPU usage (target: < 70% avg)
- Memory usage (target: < 80%)
- Disk usage (target: < 75%)
- Network I/O

**Application Level:**
- Request rate (req/s)
- Response times (p50, p95, p99)
- Error rate (target: < 1%)
- Active connections

**Qdrant Specific:**
- Collection count
- Vector count per collection
- Search latency
- Memory usage per collection

### 2. Log Monitoring

```bash
# Watch application logs
docker compose -f deploy/docker-compose.yml logs -f api

# Check for errors
docker compose -f deploy/docker-compose.yml logs api | grep ERROR

# Audit log review
sqlite3 backend/audit.db "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100;"
```

### 3. Backup Strategy

**Daily Automated Backups:**
```bash
#!/bin/bash
# backup.sh - Run daily via cron

BACKUP_DIR="/backups/quietvector/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# Backup Qdrant data
docker compose -f deploy/docker-compose.yml exec -T qdrant \
  tar czf - /qdrant/storage > "$BACKUP_DIR/qdrant_data.tar.gz"

# Backup audit database
cp backend/audit.db "$BACKUP_DIR/audit.db"

# Backup .env (encrypted)
gpg --encrypt --recipient admin@example.com .env > "$BACKUP_DIR/env.gpg"

# Retention: keep last 30 days
find /backups/quietvector -type d -mtime +30 -exec rm -rf {} +
```

**Restore Procedure:**
```bash
# Stop services
docker compose -f deploy/docker-compose.yml down

# Restore Qdrant data
tar xzf backup/qdrant_data.tar.gz -C deploy/qdrant_data/

# Restore audit database
cp backup/audit.db backend/audit.db

# Restart services
docker compose -f deploy/docker-compose.yml up -d
```

### 4. Update Procedure

```bash
# 1. Backup current state (see above)

# 2. Pull latest code
git pull origin main

# 3. Review changes
git log -p ORIG_HEAD..HEAD

# 4. Rebuild and restart
docker compose -f deploy/docker-compose.yml up -d --build

# 5. Verify health
docker compose -f deploy/docker-compose.yml ps
curl https://your-domain.com/health

# 6. Test critical functionality
# (login, collection create, search)
```

---

## Scaling Considerations

### Horizontal Scaling

QuietVector can be scaled horizontally with:

**Load Balancer (Nginx/HAProxy):**
```nginx
upstream quietvector_backend {
    least_conn;
    server api1.internal:8090;
    server api2.internal:8090;
    server api3.internal:8090;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://quietvector_backend;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Qdrant Cluster:**
- Deploy Qdrant in distributed mode
- Use Qdrant Cloud for managed scaling
- Configure collection replication factor ≥ 2

### Vertical Scaling

**When to scale up:**
- CPU usage consistently > 70%
- Memory usage > 80%
- Search latency > 500ms p95

**Resource allocation guide:**

| Workload | vCPUs | RAM | Disk |
|----------|-------|-----|------|
| Small (< 1M vectors) | 2 | 4 GB | 20 GB |
| Medium (1-10M vectors) | 4 | 8 GB | 100 GB |
| Large (10-100M vectors) | 8 | 16 GB | 500 GB |
| XLarge (> 100M vectors) | 16 | 32 GB | 1 TB+ |

---

## Troubleshooting

### Issue: Services fail to start

**Symptoms:** `docker compose ps` shows unhealthy services

**Solutions:**
```bash
# Check logs
docker compose -f deploy/docker-compose.yml logs api

# Common issues:
# 1. Port already in use
sudo lsof -i :8090  # Check what's using port
sudo kill -9 <PID>  # Kill offending process

# 2. Permission issues
sudo chown -R 1000:1000 deploy/qdrant_data/
sudo chown -R 1000:1000 backend/

# 3. Out of memory
docker system prune -a  # Free up space
```

### Issue: High response times

**Symptoms:** p95 latency > 500ms

**Solutions:**
```bash
# 1. Check Qdrant performance
curl http://localhost:6333/metrics

# 2. Enable query caching
# (Edit Qdrant config: enable_result_cache: true)

# 3. Optimize collection parameters
# (Use HNSW indexing, adjust m and ef_construct)

# 4. Add more replicas
docker compose -f deploy/docker-compose.yml up -d --scale api=3
```

### Issue: Rate limit false positives

**Symptoms:** Legitimate users getting 429 errors

**Solutions:**
```bash
# Increase rate limit in .env
RATE_LIMIT_PER_MINUTE=200  # Default: 100

# Restart services
docker compose -f deploy/docker-compose.yml restart api
```

### Issue: CSRF token mismatch

**Symptoms:** POST requests failing with 403

**Solutions:**
```bash
# 1. Clear browser cookies
# 2. Re-login to get fresh CSRF token
# 3. Check clock sync on server
sudo ntpdate -s time.nist.gov
```

---

## Security Best Practices

### 1. Secret Rotation Schedule

| Secret | Rotation Frequency | Method |
|--------|-------------------|--------|
| MASTER_PASSWORD | 90 days | Use ops-apply script |
| JWT_SECRET | 180 days | Update .env + restart |
| QDRANT_API_KEY | 180 days | Update .env + Qdrant config |
| ADMIN_TOKEN | 90 days | Update .env only |
| SSL certificates | Auto (Let's Encrypt) | Caddy auto-renewal |

### 2. Access Control

```bash
# Limit SSH access
sudo ufw allow from OFFICE_IP to any port 22

# Limit HTTPS to known IPs (optional)
sudo ufw allow from 0.0.0.0/0 to any port 443

# Block all other ports
sudo ufw default deny incoming
sudo ufw enable
```

### 3. Audit Log Review

```bash
# Weekly audit review
sqlite3 backend/audit.db << EOF
.headers on
.mode column
SELECT
  date(timestamp) as date,
  COUNT(*) as requests,
  SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
FROM audit_log
WHERE timestamp >= date('now', '-7 days')
GROUP BY date(timestamp);
EOF
```

### 4. Intrusion Detection

```bash
# Monitor failed login attempts
docker compose -f deploy/docker-compose.yml logs api | \
  grep "Authentication failed" | \
  awk '{print $NF}' | \
  sort | uniq -c | sort -rn

# Block IPs with > 10 failed attempts
# (Implement with fail2ban or similar)
```

---

## Compliance & Governance

### GDPR Compliance

- **Data minimization:** Only store necessary vector data and metadata
- **Right to erasure:** Use `/api/vectors/delete` endpoint
- **Data portability:** Export collections via Qdrant snapshot API
- **Audit trail:** All operations logged in `audit.db`

### SOC 2 Considerations

- **Access control:** JWT + password authentication
- **Encryption:** TLS 1.3 in transit, at-rest optional
- **Monitoring:** Prometheus metrics + audit logs
- **Incident response:** See troubleshooting section
- **Change management:** Git-based version control

### HIPAA Compliance (if handling medical data)

- **Encryption at rest:** Enable Qdrant encryption
- **Audit logging:** Already enabled
- **Access controls:** Implement role-based access (future)
- **Backup encryption:** Use GPG in backup script (see above)

---

## Support & Resources

### Documentation
- [README.md](../README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [SECURITY.md](SECURITY.md) - Security guide
- [CHANGELOG.md](../CHANGELOG.md) - Version history

### External Resources
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Caddy Documentation](https://caddyserver.com/docs/)

### Getting Help
- GitHub Issues: https://github.com/yourorg/QuietVector/issues
- Security Issues: security@yourorg.com (PGP: ABCD1234)

---

## Appendix: Environment Variables Reference

```bash
# Authentication
MASTER_PASSWORD=          # Primary admin password (min 24 chars)
JWT_SECRET=               # JWT signing key (openssl rand -hex 32)
TOKEN_EXPIRE_MINUTES=60   # JWT token lifetime

# Qdrant Configuration
QDRANT_HOST=qdrant        # Qdrant hostname
QDRANT_PORT=6333          # Qdrant HTTP port
QDRANT_GRPC_PORT=6334     # Qdrant gRPC port
QDRANT_API_KEY=           # Qdrant API key (openssl rand -base64 32)

# Security
RATE_LIMIT_PER_MINUTE=100  # Rate limit per IP
MAX_BODY_SIZE=10485760     # Max request body (bytes)
ENABLE_CSRF=true           # CSRF protection toggle
ENABLE_AUDIT=true          # Audit logging toggle

# Operational
ADMIN_TOKEN=              # ops-apply.sh authentication
LOG_LEVEL=INFO            # Logging level (DEBUG|INFO|WARNING|ERROR)
```

---

**Last Updated:** 2025-10-25
**QuietVector Version:** 0.2.0
**Deployment Checklist Version:** 1.0
