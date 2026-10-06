# v0.2.4 — RL Presence

## Yeni
- Oynanan ranked moda ait rank, küçük Discord ikonu ve rank/küme tooltip’iyle gösterilir.

## İyileştirme
- Rank metni details/state satırlarından çıkarıldı; harita büyük görseli ve tooltip’i korundu.
- Güncellemeler: durum kartında butonlar/son kontrol, etiketli sürüm kartları ve kapalı önceki sürümler listesi.
- Bulundu → İndiriliyor → Doğrulanıyor → Yeniden başlat ilerlemesi kartın içinde gösterilir.
- Hakkında: yatay hero/bağlantılar, eşit özellik kartları, Genel kısayolu ve geliştirici avatarları.
- Bilgi sekmelerinde yalnızca canlı bağlantı durumu; Kaydet/İptal sadece ayar sekmelerinde.

## Düzeltme
- Çerçevesiz Windows penceresinde kenar/köşe boyutlandırması geri getirildi.
- Minimum 900×640, başlangıç 1120×760; beş sekmede esnek/kaydırılabilir içerik.
- Yeni metinlerin Türkçe/İngilizce desteği, okunabilir kontrast ve klavye focus durumu.

English: rank artwork/tooltips replace inline text, reference-based Updates/About
layouts, actual verification progress, native frameless sizing and responsive tabs.
Rank artwork must be uploaded separately using docs/art-assets.md / docs/rank-asset-keys.txt.

# v0.2.3 — RL Presence

- Sekiz ranked mod için ayrı manuel rank/küme; eski tercihler korunur.
- Casual 1v1/2v2/3v3/4v4 ve Ranked 1v1/2v2/3v3 mod adları.
- Parc de Paris dahil genişletilmiş harita/varyant tablosu; docs/art-assets.md tam anahtar listesi.
- Açılışta bütün Steam/Epic kurulumlarında otomatik, yedekli Stats API hazırlığı;
  çalışan oyunun yolu otomatik seçilir, izin/yeniden başlatma sorunları görünür.
- pywebview açılışındaki “unhashable type: dict” callback hatası giderildi.
- Worker’a tanımlayıcı User-Agent ile rapor gönderimi; ağ/HTTP hataları çökmez.
- Hakkında: schwairex — Founder / App Developer; Nyris — Co-Developer / QA.

English: per-playlist manual ranks, sized mode names, expanded arena catalog,
automatic multi-install setup/active executable selection, startup callback and
report HTTP fixes, and two developer profiles. Official API only; restart the
game when an INI is edited while it is running. Arena tables remain best effort.

# v0.2.2 — RL Presence

- Gol sonrası Kickoff countdown etiketi kaldırıldı; Discord sayacı silinmez,
  son zaman damgası korunur ve kickoff’ta kalan süreye tekrar eşitlenir.
- Discord kartı ve profil etkinliği için `name: Rocket League` gönderilir.
- Türkçe/İngilizce arayüz ve Genel sekmesinde kalıcı dil tercihi eklendi.
- Hakkında’nın hemen sağına Sorun Bildir sekmesi eklendi: çift katmanlı alan
  doğrulaması, Worker’a JSON POST, otomatik sürüm/OS, yüklenme ve hata mesajları.
- Rapor için yeni bağımlılık/gizli bilgi yok; yalnızca Worker kullanılır.

English: retained goal-break countdown anchor and kickoff resync, Rocket League
activity name, persisted Turkish/English UI, public issue-report form through
the specified Worker with validation, timeout and localized response handling.
Discord's native green clock cannot pause; it advances during the goal break
and is corrected on kickoff. This platform limitation remains explicit.

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
