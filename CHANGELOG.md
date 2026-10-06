# v0.2.7 — RL Presence

## Yeni
- Otomatik olarak Steam/Epic playerID doğrulaması eklendi. Ayrıca isteğe bağlı kimlik doğrulama alanı da Gelişmiş seçeneği altına alındı.
- Salt okunur, kimlikleri gizleyen `--identity-probe` komutu eklendi.

## Düzeltme
- Eski EXE güncellemesinin silinmiş PyInstaller geçici çalışma alanını devralması giderildi.
- Güncelleme ve geri alma temiz süreç ortamıyla başlıyor. EXE/ayar yolları kullanıcı klasöründe kalıyor.
- Eski PrimaryId algılamayı engellemiyor ve hesap değişimi eski istatistikleri temizliyor..
- Algılanamayan kişisel istatistik satırı RPC tarafına gönderilmiyor. Target tahmini yalnızca düşük güvenle ve korumalı oylamayla kullanılıyor.
English: local automatic identity candidates, per-match validation, optional Advanced override, guarded Target voting, omission of unresolved personal stats, independent frozen restart and legacy-update-compatible Windows bootstrap. Steam registry/loginusers mapping verified locally; live match/Epic/admin/offline behavior remains UNVERIFIED until real acceptance checks.

# v0.2.6 — RL Presence

## İyileştirme
- Ranked/casual kartının ikinci satırı yalnızca `⚽gol  🧤kurtarış  ⭐puan`; harita adı büyük görsel tooltip’inde kalır.
- Yerel gol/kurtarış/puan değişiklikleri ek 4 saniyelik bekleme olmadan, Discord bütçesi izin verdiğinde gönderilir.
- Eğitimde Training/harita görünümü ve ranked moda özel rank ikonu/tooltip’i korunur.

## Düzeltme
- Gol/replay/kickoff/duraklatmadaki beyaz/sabit saat metni kaldırıldı; duran oyunda hareketli damga yoktur, kickoff ile canlı sayaç devam eder.
- Eksik oyuncu eşleşmesi/API alanı — ile belirtilir; yanlış oyuncu veya tahminî sıfır kullanılmaz.
- UTF-8 IPC, gerçek parçalı TCP stat akışı ve hızlı değişikliklerde kayan gönderim sınırı doğrulandı.
- README tasarımı, kullanıcı logosu ve dosya düzeni korunarak açıklamalar/önizlemeler güncellendi.

English: stats-only ranked/casual text, map tooltip retained, no white stopped
clock, eligible immediate personal stat updates, and explicit unknown values.
Casual uses its actual playlist name. Native active/OT timestamps and the
rolling activity budget are retained; no new asset key or dependency.

# v0.2.5 — RL Presence

## İyileştirme
- Discord kartı: `Ranked 2v2 • 🔵 5 - 2 🟠`, `Harita • ⚽gol 🧤kurtarış ⭐puan`.
- Casual gerçek mod adını kullanır; casual/eğitim kartlarında küçük görsel ve tooltip gönderilmez.
- Ranked kartında yalnızca oynanan mod için seçilmiş rank ikonu ve rank/küme tooltip'i bulunur.
- Mevcut README tasarımı ve dosya düzeni korunarak yeni davranış iki dilde belgelendi.

## Düzeltme
- Gol tekrarı/kickoff/duraklatmada eski Discord bitiş damgası kaldırılır; kalan süre sabit `⏸ M:SS` olarak görünür.
- RoundStarted ile kalan süreye yeniden eşitlenen canlı sayaç devam eder.
- Replay veya countdown sırasında duraklatma doğru evreye döner; uzatma bekleme süresini saymaz.
- UTF-8 emojili RPC paketleri ve eski rank/zaman damgasının temizlenmesi doğrulandı.

English: compact emoji score/stat lines, ranked-only small artwork, map-only
training, frozen static time during goal/kickoff/pause and synchronized resume.
Discord has no native pause field; rapid updates still obey the rolling budget.

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
