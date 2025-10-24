# 📦 QuietVector Deployment Guide

## 🏗️ Topology
- api (FastAPI) + web (React build) + caddy (TLS reverse proxy)
- Dinleme portu: 8443 (localhost bağlanır). Erişim tünel/VPN üzerinden.

## 📋 Prerequisites
- Docker, Docker Compose
- Qdrant (host/port/key) — yalnız iç ağ erişimi

## ⚙️ Environment
`.env` dosyası gereklidir. Önemli anahtarlar:
- `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_API_KEY` veya `QDRANT_API_KEY_FILE`
- `ADMIN_PASSWORD_HASH` (argon2)
- `FRONTEND_ORIGIN=https://localhost:8443`

Ops-Apply (opsiyonel):
- `ENABLE_OPS_APPLY=true`
- `OPS_APPLY_MODE=docker_compose` (veya `systemctl`)
- `OPS_APPLY_COMPOSE_FILE=./deploy/docker-compose.yml`
- `OPS_APPLY_SERVICE=qdrant`

Not: Ops-apply yalnızca docker/systemctl komutlarının çalıştığı host’ta, dikkatle kullanılmalıdır.

## ▶️⏹️ Start/Stop
```
cd deploy
docker compose up -d --build

docker compose down
```

## 📈 Health/Metrics
- `https://localhost:8443/api/health` → `{status: ok}`
- `https://localhost:8443/api/metrics` → Prometheus formatı

## 🧾 Logs
- API: `docker logs -f quietvector-api`
- Caddy: `deploy/caddy/*`

## 🔐 Security Notes
- Caddy TLS internal sertifika kullanır (self-signed). Üretimde tünel/VPN arkasında çalıştırın.
- Rate limit ve body limit varsayılanları `.env` ile ayarlanabilir.
