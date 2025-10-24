# 🚀 QuietVector Quick Start

Bu kılavuz, hiç deneyimi olmayan kullanıcılar için adım adım kurulum ve ilk kullanım anlatımıdır.

## 📋 1) Gereksinimler
- Docker ve Docker Compose kurulu olmalı.
- Qdrant erişim bilgileri (host, port, api key — yalnızca iç ağdan erişim önerilir).

## 🧰 2) Projeyi Hazırlayın
```
cd QuietVector
cp .env.example .env
```

🔑 Admin kullanıcı parolasını ayarlayın (argon2 hash):
```
python3 - <<'PY'
from argon2 import PasswordHasher; import getpass
p=PasswordHasher(); print(p.hash(getpass.getpass('Yeni admin parolası: ')))
PY
```
Çıktıyı `.env` içindeki `ADMIN_PASSWORD_HASH` alanına yapıştırın.

⚙️ Qdrant bilgilerini `.env` içine yazın:
```
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=
```
Not: Anahtarı dosyada tutmak için `QDRANT_API_KEY_FILE=/etc/quietvector/qdrant.key` kullanabilirsiniz.

## ▶️ 3) Çalıştırın
```
cd deploy
docker compose up -d --build
```

## 🔗 4) Web Arayüzüne Girin
- URL: https://localhost:8443
- Sertifika self‑signed olduğu için tarayıcı uyarısı normaldir (iç kullanım için).
- Giriş: `.env`’deki `ADMIN_USERNAME` ve ayarladığınız parola.

## 🧭 5) Temel İşlemler
- Koleksiyonlar: Listeleme ve yeni koleksiyon oluşturma.
- Vektör Yükle: JSON yapıştırın veya .json dosyası seçin. UI şema doğrulaması yapar.
- Arama: Koleksiyon adı ve vektör girerek deneyin.
- Snapshots: Listeleyin, “Oluştur” ile snapshot alın, “Asenkron Yükle” ile geri yükleme başlatın (ilerleme UI’da görünür).
- Güvenlik: Qdrant API key döndürme (hazırlık) ve Ops Apply (opsiyonel, varsayılan kapalı).

## ⏹️ 6) Durdurma
```
cd deploy
docker compose down
```

## 🛠️ Sorun Giderme
- Backend logları: `docker logs -f quietvector-api`
- Caddy log/sertifika: `deploy/caddy/` altında tutulur
- Qdrant bağlantı hatası: `.env` içindeki host/port/key değerlerini kontrol edin.
