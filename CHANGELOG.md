# v0.2.1 — RL Presence

- Discord Application ID sabitlendi; arayüz salt okunur, eski config ID'si yok sayılır.
- Sabit 15 saniyelik bekleme kaldırıldı. Discord sayacı oyun zamanına eşitlenir;
  güncellemeler kayan 20 saniyede en fazla 5 gönderim sınırına uyar.
- Eğitim açılışında mod verisi gelmeden yanlış 0–0 geri sayım kartı gönderilmez.
- Eğitimde P/G/S kaldırıldı. Maç kartında yinelenen süre ve Goal replay metni kaldırıldı.
- Mevcut mavi/turuncu logo EXE/pencere/görev çubuğu simgesine uygulandı.
- Dağıtılan çalıştırılabilir dosyanın adı `rl-presence.exe` oldu.
- Güncellemeler ve Hakkında sekmeleri mevcut tema içinde yenilendi.
- Her açılışta GitHub Release kontrolü, bildirim, SHA-256 doğrulamalı indirme,
  otomatik değiştirme/yeniden açma, sağlıklı açılış kontrolü ve geri alma eklendi.
- Başarısız aynı sürümün yeniden başlatma döngüsüne girmesi önlendi.
- Eski ayarlar korunur; özel config yolu yeniden açılışta mutlak yol olarak taşınır.

English: fixed application identity, synced Discord timestamps, immediate eligible
phase changes, cleaner training/live text, branded EXE icon, modern Updates/About,
GitHub stable-release auto-update with checksum verification and healthy-startup
rollback. Public GitHub Releases and a direct `rl-presence.exe` asset are required.
