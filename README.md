# FIVEGUARD SCANNER PRO

Türkçe siyah-kırmızı tanıtım sitesi ve Discord OAuth2 giriş başlangıç altyapısı.

## Render'da yayınlama

1. Render'da **New → Blueprint** veya **New → Web Service** seç.
2. GitHub deposu olarak `lazzamissi/fiveguard` deposunu bağla.
3. Blueprint kullanıyorsan `render.yaml` dosyasını seç; Web Service kullanıyorsan:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Render Environment bölümüne Discord uygulamasından aldığın değerleri gir:
   - `DISCORD_CLIENT_ID`
   - `DISCORD_CLIENT_SECRET`
   - `SESSION_SECRET` (uzun ve rastgele)
5. Deploy tamamlanınca Render'ın atadığı gerçek `.onrender.com` adresini al.
6. Discord Developer Portal → OAuth2 → Redirects alanına şu biçimde adres ekle:
   `https://GERCEK-RENDER-ADRESI/auth/discord/callback`

## Güvenlik notları

- Discord Client Secret yalnızca Render Environment bölümünde tutulmalı. GitHub'a veya sohbete eklenmemeli.
- Bu repo herkese açık olsa bile gizli anahtar içermemelidir.
- Bu sürüm tanıtım sitesi ve Discord kimlik doğrulama örneğidir.
- FiveM tarama motoru, ödeme, üyelik veritabanı ve LEADERS rol yönetimi bu sürümde henüz yoktur.
- Tarama bulguları insan incelemesine sunulmalıdır; tek bir sinyale dayalı otomatik ceza uygulanmamalıdır.
