QuietVector — Steril Qdrant Yönetim Paneli

Amaç
- Hetzner iç ağında çalışan Qdrant kümelerini yalnızca yetkili iç kullanıcıların yönetebilmesi için sade, güvenli ve sıfır telemetri bir web arayüzü.

Öne Çıkanlar
- Sıfır Telemetri: Harici API ve izleme yok. Tüm varlıklar yerel.
- Air‑Gap Dostu: Qdrant’a yalnız iç ağ/VPN üzerinden erişim.
- Güvenlik: JWT oturum + hız limiti + gövde boyutu limiti + denetim kaydı.
- Kurumsal Sadelik: Sadece gerekli akışlar — koleksiyon, vektör, arama, snapshot, durum.

Mimari
- Backend (FastAPI): Qdrant-client ile konuşur. Auth, collections, vectors, snapshots, stats uçları.
- Frontend (React + Tailwind): JSON sonuçlarını yalın bileşenlerle sunar.
- Reverse Proxy (Caddy/Nginx): TLS, güvenlik başlıkları. Varsayılan: Caddy.
- Dağıtım: Docker Compose (api + web + caddy). Dışa açık port gerektirmez; önerilen erişim: WireGuard/VPN.

Güvenlik Felsefesi
- Zero Telemetry: Dış HTTP çağrısı yok. Harici font/CDN yok.
- Sadece İç Erişim: API `127.0.0.1`’e bağlanır; erişim tünel/VPN ile.
- Kimlik Doğrulama: JWT (HS256). Kullanıcı/şifre env’den (argon2 hash).
- Denetim Kaydı: Her istek JSON satır olarak dosyaya yazılır (döndürülmeye uygun).

Hızlı Başlangıç
1) .env oluştur
```
cp .env.example .env
vim .env
```
2) Docker Compose ile başlat
```
docker compose up -d --build
```
3) Erişim
- Varsayılan: https://localhost:8443 (Caddy TLS self‑signed). İlk giriş için `.env`’deki kimlik bilgilerini kullanın.

Geliştirme
- Backend: `cd backend && uvicorn app.main:app --reload --port 8090`
- Frontend: `cd frontend && npm i && npm run dev`

Yapılandırma (özet)
- QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY
- JWT_SECRET, ADMIN_USERNAME, ADMIN_PASSWORD_HASH (argon2)
- RATE_LIMIT_PER_MINUTE, MAX_BODY_SIZE_BYTES, AUDIT_LOG_PATH

Logo
- QuietVector logosu, Qdrant’ın görsel dilinden ilham alır fakat birebir kullanım/türetim içermez. Basit geometrik şekiller ve Q harfi ile kilit/koruma çağrışımı yapılır.

Notlar
- Bu depo yalnızca iç kullanım ve steril kurulumlar için tasarlanmıştır. İnternet erişimi olmayan (air‑gap) ortamlarda çalışır.
