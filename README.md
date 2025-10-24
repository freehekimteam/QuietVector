QuietVector — Steril Qdrant Yönetim Paneli

Amaç
- Hetzner iç ağında çalışan Qdrant kümelerini yalnızca yetkili iç kullanıcıların yönetebilmesi için sade, güvenli ve sıfır telemetri bir web arayüzü.

Öne Çıkanlar
- Sıfır Telemetri: Harici API ve izleme yok. Tüm varlıklar yerel.
- Air‑Gap Dostu: Qdrant’a yalnız iç ağ/VPN üzerinden erişim.
- Güvenlik: JWT oturum + hız limiti + gövde boyutu limiti + denetim kaydı.
- Kurumsal Sadelik: Sadece gerekli akışlar — koleksiyon, vektör, arama, snapshot, durum.

Mimari
- Backend (FastAPI): Qdrant-client ile konuşur. Auth, collections, vectors, snapshots, stats, security/ops uçları.
- Frontend (React + Tailwind): JSON sonuçlarını yalın bileşenlerle sunar.
- Reverse Proxy (Caddy): TLS (self‑signed internal), güvenlik başlıkları.
- Dağıtım: Docker Compose (api + web + caddy). Dışa açık port gerektirmez; önerilen erişim: WireGuard/VPN veya Cloudflare Tunnel.

Güvenlik Felsefesi
- Zero Telemetry: Dış HTTP çağrısı yok. Harici font/CDN yok.
- Sadece İç Erişim: API `127.0.0.1`’e bağlanır; erişim tünel/VPN ile.
- Kimlik Doğrulama: JWT (HS256). Parola argon2 hash.
- Denetim Kaydı: Her istek JSON satır olarak dosyaya yazılır (döndürmeye uygun).

Hızlı Başlangıç (Yeni Başlayanlar İçin)
1) Gereksinimler
- Docker ve Docker Compose

2) Ortam Dosyası
```
cp .env.example .env
# Admin parolası için argon2 hash üretin:
python3 - <<'PY'
from argon2 import PasswordHasher; import getpass
p=PasswordHasher(); print(p.hash(getpass.getpass('Yeni admin parolası: ')))
PY
# Çıktıyı .env içindeki ADMIN_PASSWORD_HASH alanına yapıştırın
```

3) Qdrant Bilgileri
- Qdrant host/port/key bilgilerinizi `.env` içine girin. Sadece iç ağdan erişilebilir olmasına dikkat edin.

4) Çalıştırma
```
cd deploy
docker compose up -d --build
```

5) Erişim
- Tarayıcıdan: https://localhost:8443
- Uyarı: Sertifika self‑signed (iç kullanım için). İlk girişte admin kullanıcı ve parolayı kullanın.

İlk Kullanım Akışları
- Koleksiyonlar: Listele, yeni koleksiyon oluştur.
- Vektör Yükle: Örnek JSON’u doldurun veya .json dosyası seçin. UI temel şema doğrulaması yapar (id, vector boyutu, sayısal kontrol, payload obje).
- Arama: Koleksiyon + vektör girerek arama yapın.
- Snapshots: Listele, yeni snapshot oluştur; “Asenkron yükle” ile dosyadan geri yükleme başlatın ve ilerlemeyi UI’dan izleyin.
- Güvenlik:
  - Qdrant API Key Döndürme (Hazırlık): Yeni anahtarı sunucudaki güvenli dosyaya (0600) yazar, talimatları gösterir.
  - Ops Apply (Ops): İsteğe bağlı olarak (varsayılan kapalı) docker compose/systemctl ile güvenli şekilde Qdrant’ı yeniden başlatır. Önce Dry Run ile komutu görün.

Belgelendirme
- docs/QUICK_START.md — Adım adım kurulum ve kullanım
- docs/DEPLOYMENT.md — Docker dağıtımı ve yapılandırma
- docs/SECURITY.md — Güvenlik, anahtar döndürme ve ops-apply

Geliştirme
- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8090`
- Frontend: `cd frontend && npm i && npm run dev`
- E2E Smoke: `cd frontend && npx playwright test`

Yapılandırma (Özet)
- QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY veya QDRANT_API_KEY_FILE
- JWT_SECRET, ADMIN_USERNAME, ADMIN_PASSWORD_HASH (argon2)
- RATE_LIMIT_PER_MINUTE, MAX_BODY_SIZE_BYTES, AUDIT_LOG_PATH
- (Ops) ENABLE_OPS_APPLY, OPS_APPLY_MODE, OPS_APPLY_COMPOSE_FILE, OPS_APPLY_SERVICE

Logo
- QuietVector logosu, Qdrant’ın görsel dilinden ilham alır fakat birebir kullanım/türetim içermez.

Notlar
- Bu depo yalnızca iç kullanım ve steril kurulumlar için tasarlanmıştır. İnternet erişimi olmayan (air‑gap) ortamlarda çalışır.
