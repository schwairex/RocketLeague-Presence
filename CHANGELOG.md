# v0.2.2 — RL Presence

- Gol sonrası Kickoff countdown etiketi kaldırıldı; Discord sayacı artık silinmiyor, son zaman damgası korunuyor ve kickoff’ta kalan süreye tekrar eşitleniyor.
- Uygulamanın, Discord kartı ve profil etkinliğinde 'RocketLeageRPC' olarak görünme hatası düzeltildi.
- Türkçe/İngilizce arayüz ve Genel sekmesinde kalıcı dil tercihi eklendi.
- Sorun Bildir sekmesi eklendi.

English: retained goal-break countdown anchor and kickoff resync, Rocket League
activity name, persisted Turkish/English UI, public issue-report form through
the specified Worker with validation, timeout and localized response handling.
Discord's native green clock cannot pause; it advances during the goal break
and is corrected on kickoff. This platform limitation remains explicit.

# v0.2.1 — RL Presence

- Eğitim açılışında mod verisi gelmeden yanlış 0–0 geri sayım kartı gönderilmez.
- Eğitimde P/G/S kaldırıldı. Maç kartında yinelenen süre ve Goal replay metni kaldırıldı.
- Uygulama logosu güncellendi.
- Uygulamadaki "Güncellemeler" ve "Hakkında" sekmeleri mevcut tema içinde yenilendi.
- Her açılışta GitHub Release kontrolü, bildirim, SHA-256 doğrulamalı indirme, otomatik değiştirme/yeniden açma, sağlıklı açılış kontrolü ve geri alma eklendi.
- Başarısız aynı sürümün yeniden başlatma döngüsüne girmesi önlendi.
- Eski ayarlar korunur; özel config yolu yeniden açılışta mutlak yol olarak taşınır.

English: fixed application identity, synced Discord timestamps, immediate eligible
phase changes, cleaner training/live text, branded EXE icon, modern Updates/About,
GitHub stable-release auto-update with checksum verification and healthy-startup
rollback. Public GitHub Releases and a direct `rl-presence.exe` asset are required.
