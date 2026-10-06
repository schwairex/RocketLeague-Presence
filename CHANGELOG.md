# v0.2.4 — RL Presence

## Yeni
- Oynanan ranked moda ait rank, küçük Discord ikonu ve rank/küme tooltip’iyle gösteriliyor.

## İyileştirme
- Rank metni details/state satırlarından çıkarıldı; harita büyük görseli ve tooltip’i korundu.
- Bulundu → İndiriliyor → Doğrulanıyor → Yeniden başlat ilerlemesi artık kartın içinde gösteriliyor.
- "Hakkında" ve "Güncellemeler" sayfalarının arayüzleri güncellendi. 
- Bilgi sekmelerinde yalnızca canlı bağlantı durumu görünüyor. Kaydet/İptal ise ayar sekmesinde gösteriliyor.

## Düzeltme
- Çerçevesiz Windows penceresinde kenar/köşe boyutlandırması geri getirildi.
- Minimum 900×640, başlangıç 1120×760; beş sekmede esnek/kaydırılabilir içerik.
- Yeni metinlerin Türkçe/İngilizce desteği, okunabilir kontrast ve klavye focus durumu düzenlendi.

English: rank artwork/tooltips replace inline text, reference-based Updates/About
layouts, actual verification progress, native frameless sizing and responsive tabs.
Rank artwork must be uploaded separately using ART_ASSETS.md / RANK_ASSET_KEYS.txt.

# v0.2.3 — RL Presence

- Sekiz ranked mod için ayrı manuel rank/küme terchileri eklendi.
- Casual ve Ranked mod adları düzenlendi.
- Genişletilmiş harita/varyant tablosu ve Discord RCP için 'ART_ASSETS' eklendi.
- Açılışta bütün Steam/Epic kurulumlarında otomatik Stats API seçilme ayarı eklendi.
- pywebview açılışındaki “unhashable type: dict” callback hatası giderildi.
- Worker’a tanımlayıcı User-Agent ile rapor gönderimi düzenlendi.

English: per-playlist manual ranks, sized mode names, expanded arena catalog,
automatic multi-install setup/active executable selection, startup callback and
report HTTP fixes, and two developer profiles. Official API only; restart the
game when an INI is edited while it is running. Arena tables remain best effort.

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
