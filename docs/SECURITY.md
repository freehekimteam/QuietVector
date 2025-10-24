# 🔐 QuietVector Security Guide

Bu rehber, güvenlik odaklı kurulum ve işletim notlarını içerir.

## 📵 Zero Telemetry
- Uygulama hiçbir dış telemetri/izleme servisine çağrı yapmaz.
- Harici font/CDN kullanılmaz.

## 🌐 Ağ ve Erişim
- API, yalnızca reverse proxy (Caddy) üzerinden erişilir.
- Sunucu dışa açık değildir; yalnızca VPN/Tunnel üzerinden erişim önerilir.
- `FRONTEND_ORIGIN` ile yalnızca belirli origin’e CORS açılır.

## 🔑 Kimlik Doğrulama
- JWT (HS256) ve argon2 parola hash.
- Admin parolasını `.env` içerisinde düz metin TUTMAYIN; sadece argon2 hash.
- Parola döndürme işlemlerini düzenli aralıklarla yapın.

## 🧾 Denetim Kayıtları (Audit)
- Her istek JSONL (satır başına JSON) formatında `AUDIT_LOG_PATH` dosyasına yazılır.
- Log dosyası rota döndürmeye uygun biçimdedir (logrotate önerilir).

## 🔁 Qdrant API Key Döndürme
- `QDRANT_API_KEY_FILE` kullanın; anahtar dosyada 0600 izinleriyle tutulur.
- UI → Güvenlik → “Hazırla” ile yeni anahtarı dosyaya yazın ve talimatları izleyin.
- Qdrant servisinin de yeni anahtarla yeniden başlatılması gerekir.

## ⚙️ Ops Apply (Opsiyonel)
- Varsayılan kapalıdır: `ENABLE_OPS_APPLY=false`.
- Açarsanız, yalnızca güvenilir bir host’ta kullanın. İki mod desteklenir:
  - `docker_compose`: `docker compose -f <file> up -d <service>`
  - `systemctl`: `systemctl restart <service>`
- UI’da önce “Dry Run” ile komutu görün; ardından “Uygula”.
- Hizmet adları ve dosya yolları doğrulanır; komutlar shell kullanılmadan çalıştırılır.

## 🧩 En İyi Uygulamalar
- Erişimi IP/VPN ile kısıtlayın.
- `.env` dosyasını güvenli tutun (okuma yetkisi sınırlı). 
- Düzenli olarak Qdrant anahtarlarını ve admin parolasını değiştirin.
- Backupları şifreli tutun; snapshot restore işlemlerini sadece güvenli ağda gerçekleştirin.
