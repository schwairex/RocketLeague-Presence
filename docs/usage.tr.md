# RL Presence — ayrıntılı kullanım rehberi — Türkçe kullanım kılavuzu

[English overview](../README.md) · [Türkçe ana sayfa](../README.tr.md)

Rocket League için Windows üzerinde Python 3.11+ ile çalışan Discord Rich Presence uygulaması. Veriler yalnızca [resmî yerel Stats API](https://www.rocketleague.com/developer/stats-api) üzerinden okunur. Oyun belleğine erişilmez; oyun komutu gönderilmez. [English guide](usage.md).

## Dil seçimi ve Sorun Bildir (v0.2.5)

**Genel → Arayüz dili** alanından Türkçe veya English seçin ve **Kaydet**’e basın.
Seçim hemen önizlenir ve kaydedildikten sonra yeniden açılışta korunur. İptal,
kayıtlı dile döner. Resmî harita/mod/rank adları, Discord oyun metinleri, ham
günlükler ve GitHub’da yazılmış sürüm notları kendi dilinde kalır.

**Hakkında’nın hemen sağındaki Sorun Bildir** sekmesinde başlık (5–100 karakter)
ve açıklama (10–2000 karakter) girip **Gönder**’e basın. Üstte raporun herkese
açık olduğu ve şifre/kişisel bilgi yazılmaması gerektiği belirtilir. Yalnızca
başlık, açıklama, otomatik uygulama sürümü ve işletim sistemi JSON olarak
`https://bug-report.kralsefo123.workers.dev` adresine gönderilir. Günlükler,
oyuncu kimlikleri, token ve API anahtarları eklenmez. Worker adresi tek yerde,
`rocket_league_rpc/reports.py` içinde tanımlıdır. v0.2.3 istekleri uygulama adı/sürümüyle tanıtır; Worker’ın varsayılan Python istemcisine verdiği 403 hatası giderildi. Bu özellik doğrudan GitHub’a
istek atmaz; mevcut GitHub güncelleyicisi bağımsız çalışmaya devam eder.

Alanlar arayüzde ve Python tarafında doğrulanır. Gönderim ayrı köprü thread’inde
çalışır, 10 saniye zaman aşımı kullanır; buton kilitlenir ve yüklenme göstergesi
çıkar. HTTP 200’de teşekkür mesajı gösterilir ve alanlar temizlenir. 429, 400,
ağ/sunucu hatalarında Türkçe/İngilizce açıklama gösterilir, yazdıklarınız korunur.
Yönlendirme ve otomatik rapor tekrarları kapalıdır. Zaman aşımında istek sunucuya
ulaşmış olabilir; yinelenen rapor oluşturmamak için bilinçli olarak tekrar deneyin.

Discord etkinlik adı bütün durumlarda **Rocket League** gönderilir. Gol sonrası
Kickoff countdown etiketi gösterilmez. Gol/kickoff/duraklatmada hareketli
zaman damgası kaldırılır, son kalan oyun süresi sabit ⏸ 2:33 metniyle görünür.
RoundStarted canlı geri sayımı yeniden başlatır. Discord’un yerel sayacında
duraklatma alanı yoktur. Testler gerçek herkese açık rapor oluşturmadan mock sunucuyla yapıldı.

## Kurulum ve çalıştırma

Projeyi yazılabilir bir klasöre çıkarın. PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Hazır derleme varsa `rl-presence.exe` dosyasını çalıştırabilirsiniz. `config.json` ve `logs/`, kaynak kullanımında `run.py` yanında, exe kullanımında exe yanında bulunur. Alternatif ayar dosyası: `--config C:\klasor\config.json`. Arayüzde Kaydet ile ayarlar hemen uygulanır; JSON dosyasını dışarıdan düzenlediyseniz RPC’yi yeniden başlatın.


## Yeni masaüstü arayüzü (v0.2.5)

Eski RPC’yi kapatıp yeni EXE’yi açın. Mevcut config.json dosyanızı yeni EXE’nin yanında tutarak oyuncu/harita/rank ayarlarınızı koruyabilirsiniz. Application ID bu sürümde sabittir; eski client_id yok sayılır ve kaldırılır. Windows 10/11, .NET Framework 4.8 ve Microsoft Edge WebView2 Runtime gerekir. Python, yazı tipleri ve verilen SVG görselleri EXE’ye dahildir; arayüz internet gerektirmez.

**Görünüm** verilen HTML düzenini kullanır. **Genel** sekmesinde rank/küme, ana menü, menü, sıra, mağaza, serbest/özel antrenman ve garaj seçilir. Seçimler kaydedilir; gerçek maç verileri bunların önüne geçer. **Resmî Stats API rank ve ayrıntılı menü durumlarını vermez.** Ranked 3v3, 2v2, 1v1, Heatseeker, Rumble, Hoops, Snow Day ve Dropshot için ayrı rank/küme kaydedilir. Discord yalnızca oynanan ranked modun rankını gösterir; casual/eğitim/menüde rank gösterilmez. Eski tek rank seçimi sekiz moda bir kez taşınır, ardından ayrı düzenlenir.

Kaydet değişiklikleri uygulamayı yeniden başlatmadan uygular; İptal kaydedilmemiş değişiklikleri geri alır. Örnek önizlemeler Discord’a gönderilmez. Canlı maç kartına veya hata simgesine tıklayınca tüm oyuncuların puan/gol/kurtarış değerleri, ham maç alanları, son olay, bağlantı hatası ve son gönderilen/bekleyen RPC açılır. Genel sekmesinde günlük klasörünü açabilir veya logs/diagnostics.json raporu kaydedebilirsiniz.

Menüde takılma hatası gerçek TCP paketinde bulundu: Data alanı JSON nesnesi yerine JSON metniydi. v0.2 her iki biçimi güvenli şekilde okur. Eğitimde TimeSeconds ham verisi tanılamada tutulur; maç geri sayımı olarak gösterilmez. Alt satırdaki paket/sn gerçek ölçümdür.

Discord ve Rocket League göstergeleri gerçek bağlantı durumunu kullanır. Stats API sarıysa bağlantı ya da maç paketi bekleniyor olabilir; simgenin ipucu ve tanılama paneli ayrıntıyı gösterir. Sabit 15 saniyelik bekleme kaldırıldı. Saat Discord zaman damgasıyla ilerler; yoğun değişiklikler Discord’un 20 saniyede 5 güncelleme sınırı içinde birleştirilir.

## Discord uygulaması ve görseller

Son kullanıcılar yeni Discord uygulaması oluşturmaz. Bu derleme mevcut **802869954805760020** Application ID’sini kullanır; Genel sekmesinde salt okunur görünür. Aşağıdaki görsel yükleme adımları uygulamanın bakımcısı içindir.

1. [Discord Developer Portal](https://discord.com/developers/applications) üzerinde bu uygulamayı yönetin. Bu sürüm bütün etkinliklerde `name: Rocket League` gönderir; sabit Application ID ve görseller değişmez.
2. ID yapılandırma dosyasından veya arayüzden değiştirilemez. Bot token, OAuth veya client secret gerekmez.
3. Rich Presence / Art Assets bölümüne aşağıdaki anahtarlarla görseller yükleyin. Anahtarlar küçük harflerle **birebir aynı** olmalıdır. Liste `maps.py` tarafından kullanılan bütün farklı anahtarları ve genel/takım simgelerini kapsar. Kullanma hakkınız olan görseller seçin; varyantlar temel harita görselini paylaşır.
4. Aynı Windows oturumunda Discord masaüstü uygulamasını açın. Aktivite görünmüyorsa Discord'un aktivite paylaşımı gizlilik ayarını kontrol edin.

| Exact key / Birebir anahtar | Artwork / Görsel |
|---|---|
| `aquadome` | Aquadome |
| `arctagon` | Arctagon |
| `beckwith_park` | Beckwith Park |
| `blue` | Blue team icon / Mavi takım |
| `boostfield_mall` | Boostfield Mall |
| `calavera` | Calavera |
| `carbon` | Carbon |
| `champions_field` | Champions Field |
| `core_707` | Core 707 |
| `deadeye_canyon` | Deadeye Canyon |
| `deadeye_canyon_oasis` | Deadeye Canyon (Oasis) |
| `dfh_stadium` | DFH Stadium |
| `drift_woods` | Drift Woods |
| `dunk_house` | Dunk House |
| `estadio_vida` | Estadio Vida |
| `farmstead` | Farmstead |
| `forbidden_temple` | Forbidden Temple |
| `futura_garden` | Futura Garden |
| `mannfield` | Mannfield |
| `midnight_metro` | Midnight Metro |
| `neo_tokyo` | Neo Tokyo |
| `neon_fields` | Neon Fields |
| `orange` | Orange team icon / Turuncu takım |
| `parc_de_paris` | Parc de Paris |
| `quadron` | Quadron |
| `rivals_arena` | Rivals Arena |
| `rl_logo` | Rocket League logo |
| `rocket_labs` | Rocket Labs layouts / Rocket Labs ortak görseli |
| `salty_shores` | Salty Shores |
| `sovereign_heights` | Sovereign Heights |
| `starbase_arc` | Starbase ARC |
| `starbase_arc_aftermath` | Starbase ARC (Aftermath) |
| `sunset_dunes` | Sunset Dunes |
| `the_block` | The Block |
| `throwback_stadium` | Throwback Stadium |
| `united_futura` | United Futura |
| `urban_central` | Urban Central |
| `utopia_coliseum` | Utopia Coliseum |
| `wasteland` | Wasteland |

Yeni eklenecek anahtarlar ve kapsam: [art-assets.md](art-assets.md).

Bu dağıtım sabit Application ID kullanır; harita görselleri Discord uygulamasına portal üzerinden yüklenir. Eksik görsel yüklemeleri maç yazısını engellemez; ilgili resim görünmeyebilir.

## İlk çalıştırma ve otomatik Stats API kurulumu

Eski RPC’yi kapatın, ZIP’i yazılabilir bir klasöre çıkarın ve `rl-presence.exe`
çalıştırın. Mevcut `config.json` dosyanızı yeni EXE’nin yanına taşıyabilirsiniz.
Her normal açılışta Steam’in bütün kütüphaneleri ve Epic manifestleri otomatik
taranır; bulunan **bütün oyun kurulumlarında** Stats API hazırlanır. Butona
basmak gerekmez. Oyun çalışınca RocketLeague.exe yolu aktif Steam/Epic kopyasını
seçer. Genel sekmesi bulunan yolları ve aktif kurulumu gösterir. “Kurulumları
yeniden denetle” yalnızca tekrar deneme içindir.

Oyun zaten açıksa INI değişikliği için oyunu tamamen kapatıp yeniden açın;
üstteki uyarı bunu belirtir. Uygulama oyunu kendiliğinden kapatmaz. Eksik kurulum
ve yazma izni sorunları da görünür. İzin hatasında uygulamayı yönetici olarak
çalıştırıp yeniden denetleyin. Hiçbir kurulum bulunamazsa TAGame içeren klasörü
Genel’de yazıp Kaydet’e basın; sonraki otomatik denetim bunu alır.
İki launcher kurulumu desteklenir; aynı yerel portları kullandıkları için iki
Rocket League kopyasını eşzamanlı açmayın. `--skip-install` otomatik denetimi
kapatır. Konsol sürümünde bir kez yol soran seçenek korunur.

Genel’de her ranked modun rank/kümesini ve maç dışı durumunu seçip Kaydet’e
basın. Görünüm’de oyun içi ad/platform ayarı yerel P/G/S eşleşmesini sağlar.
INI seçiminde önce TAStatsAPI.ini, yoksa DefaultStatsAPI.ini kullanılır:

```ini
[TAGame.MatchStatsExporter_TA]
PacketSendRate=30
Port=49123
WebPort=49124
```

Pozitif ve 120'yi aşmayan paket hızı korunur. Kapalı/geçersiz hız 30, 120 üzeri hız 120 yapılır. Portlar ayarlardan alınır; sıfır olamaz ve farklı olmalıdır. Gerekli her değişiklikten **önce `.bak` yedeği** alınır; sonraki yedekler benzersiz son ek alır. Yeni dosyanın boş yedeği, daha önce dosya olmadığını belirtir. Ayarlar doğruysa tekrar yazılmaz. `configparser` anahtarların büyük/küçük harfini ve diğer bölüm/değerleri korur; boşlukları düzenler ve yorumları kaldırır. Gerekirse yorumları yedekten geri alın. Bozuk ini sözdizimi bildirilir ve orijinal dosya korunur.

**Ini değişikliğinden sonra Rocket League'i tamamen kapatıp yeniden açın.** Oyun açıksa ayrıca uyarı gösterilir; çalışan oyun değişikliği yükleyemez. Yetki hatasında yönetici olarak çalıştırma önerilir. RPC klasörünün yazılabilir olması ayar/log sorunlarını giderir. `--skip-install` otomatik ini işlemini atlar.

Application ID hazırdır. Bundan sonra oyun ve Discord herhangi bir sırada açılabilir. Stats bağlantısı 3–5 saniye arayla, Discord bağlantısı 3–30 saniyeye kadar artan beklemeyle yeniden denenir. Oyun kapalıysa presence temizlenir. Oyun açık ancak bağlantı/aktif maç yoksa `In menus / Queueing` gösterilir. API gerçek sıraya girme durumunu menüden ayıramaz.

## Ayarlar

`config.example.json` bütün varsayılanları içerir. Bozuk JSON veya nesne olmayan kök yedeklenip yeniden oluşturulur. Hatalı alan türleri varsayılana döner; dosyalar atomik yazılır. Yazma yetkisi yoksa uygulama bellekteki varsayılanlarla çalışır ve hata bildirir.

| Alan | Varsayılan / açıklama |
|---|---|
| `language` | `tr`; arayüz dili `tr` / `en` |
| `schema_version` | `3`; eski ayar geçişi için yönetilir; client_id ayarı bulunmaz |
| `install_path` | Boş; otomatik arama veya tek seferlik soru |
| `player_name` | Boş; kendi oyuncu adınız, harf duyarsız eşleşme |
| `player_primary_id` | Boş; `Platform\|Uid\|Splitscreen`, addan öncelikli |
| `stats_host` | `127.0.0.1` |
| `stats_port` | `49123`; TCP, 1–65535 |
| `stats_web_port` | `49124`; TCP'den farklı WebSocket portu |
| `stats_transport` | `tcp`; isteğe bağlı alternatif `websocket` |
| `update_interval` | `1`; 1–3600 sn; normal gönderimler en az 4 sn birleştirilir, öncelikli olaylar bu beklemeyi atlar |
| `log_level` | `INFO`; DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `show_score`, `show_map`, `show_mode` | `true`; harita kapalıysa görsel/ipucu da gizlenir |
| `show_perspective` | `false`; takım biliniyorsa `You … Opp` |
| `show_time` | `true`; Discord zaman damgaları; yinelenen kalan süre metni yoktur |
| `show_rank`, `show_player_stats` | `true`; manuel rank ve yerel ⚽/🧤/⭐ istatistikleri |
| `rank_tier`, `rank_division` | `Unranked`, `1`; küme 1–4, SSL’de küme yok |
| `manual_activity` | `auto`; main_menu/menu/queue/shop/training/custom_training/garage |
| `player_platform` | `auto`; steam/epic ad eşleştirmesini filtreler |
| `spectating` | `false`; canlı maçı izliyorsanız true yapın |
| `auto_learn_primary_id` | `true`; yalnızca ayarlanmış oyuncu adından öğrenilen ID kaydedilir |
| `install_prompted` | `false`; kurulum yolu sorusunun gösterilip gösterilmediği |

Önce ayarlanmış ID, sonra ad eşleştirilir. Ayarlanmış oyuncu bulunamadığında rakibin görüntülenen arabasına geçilmez. Kimlik ayarlanmamışsa `bHasTarget` true olduğunda ve izleyiciye özel alanlar görülmediğinde `Game.Target` kullanılabilir. **Target yalnızca izlenen arabadır; sizin kimliğinizi kanıtlamaz.** İzleyici tespiti kesin değildir; güvenilir sonuç için kimliğinizi ayarlayın veya `spectating: true` kullanın. Bilinmeyen takımda Blue/Orange ve tarafsız kazanan yazısı gösterilir. PlayerJoined takım bilgisi içermez; UpdateState beklenir.

## Saat, maç sonucu ve güncelleme sınırı

Geri sayım, normal oyun, gol tekrarı, duraklatma, uzatma, maç sonu ve geçmiş tekrar durumları ayrı işlenir. Yeni MatchGuid maç durumunu sıfırlar. Boş çevrimdışı MatchGuid ayrılana kadar tek maçtır. ReplayCreated sonrasında MatchDestroyed gelene kadar `Watching a replay` gösterilir; canlı skor/saat gönderilmez. Skor UpdateState'ten alınır; GoalScored'dan kendi kalesine gol gibi durumlarda tahmin edilmez.

RoundStarted bitiş zamanını eşitler. Saat tahminden **2 saniyeden fazla** saparsa yeniden eşitlenir. Gol tekrarı, kickoff bekleyişi ve duraklatmada hareketli zaman damgası kaldırılır; son kalan oyun süresi sabit `⏸ M:SS` metniyle gösterilir. Oyun başlayana kadar bu değer ilerlemez. Discord’un yerel sayacında duraklatma alanı yoktur. Aktif oyunda yerel yeşil sayaç devam eder; yinelenen süre/kickoff/replay etiketi gösterilmez. Replay veya countdown sırasında duraklatma doğru evreye döner. Sonuç MatchDestroyed gelene veya 60 saniye dolana kadar tutulur. Bilinen yerel takım için Win/Loss, bilinmiyorsa Blue wins/Orange wins gösterilir.

**Uzatmada TimeSeconds yönü doğrulanmamıştır.** Yerel geçen süre başlangıcı kullanılır. İlk gözlenen uzatma başlangıcı esas alınır; maçın ortasında yeniden bağlanılırsa ilk paket geçici başlangıç olur ve geçen süre eksik görünebilir. Uzatma durduğunda geçen süre sabit gösterilir; devam edince durulan saniyeler hesaba katılmaz. DEBUG günlükleri gerçek TimeSeconds örneklerini içerir. Politikayı değiştirmek için tek yer `state.overtime_clock_start()` fonksiyonudur.

Sabit 15 saniyelik bekleme yoktur. [Discord sınırı](https://docs.discord.com/developers/developer-tools/game-sdk) uyarınca kayan her 20 saniyede en fazla 5 aktivite yazılır. Başlangıç, skor, eğitim, tekrar ve bitiş geçişleri izin varsa hemen gönderilir. Normal istatistik değişiklikleri en az 4 saniye birleştirilir. Aynı içerik yeniden gönderilmez; son durum kazanır. Başarısız yazımlar/temizleme de bütçeyi tüketir, yeniden bağlanmak bütçeyi sıfırlamaz. Sayaç her saniye paket istemez: ilk eşitlenen bitiş zamanından Discord kendi geri sayar. Maç istatistikleri `⚽gol 🧤kurtarış ⭐puan` şeklindedir; eğitimde gösterilmez. Aktif oyunda yinelenen kalan süre ve gol tekrar etiketi yoktur. Gol/kickoff/duraklatmada hareketli damga kaldırılır, süre sabit metindir; kickoff ile geri sayım devam eder. Bütçe dolarsa kısa durumlar birleştirilebilir. Kapanışta uygunsa temizleme yazılır; aksi halde IPC kapanır.

## Hata ayıklama ve test

```powershell
.\.venv\Scripts\python.exe run.py --debug
.\.venv\Scripts\python.exe run.py --debug --raw-packets
```

`--debug`, yok sayılanlar dahil her ayrıştırılmış olayın adını ve beklenmeyen şekilleri kaydeder. Tam JSON için `--raw-packets` ekleyin: `logs/raw_packets.log` (10 MiB, mevcut + 3 yedek). `logs/app.log` yapılandırılmış JSONL'dir (5 MiB, mevcut + 3 yedek). Sorunu ve zamanını açıklayarak bu dosyaları/numaralı dönüşlerini paylaşın. Ham paketler oyuncu adları ve platform ID'leri içerir; isterseniz paylaşmadan önce gizleyin. Normal INFO seviyesinde ham paket kaydı yoktur. Dengeli bozuk JSON tek tek atılır; kapanmayan bozuk JSON için güvenilir sınır olmadığından 2 MiB tampon dolunca sıfırlanır.

Sahte sunucu için Rocket League'i kapatıp 49123 portunu boşaltın. İki terminal:

```powershell
.\.venv\Scripts\python.exe -m rocket_league_rpc.mock_stats_server --port 49123 --delay 5
.\.venv\Scripts\python.exe run.py --mock-game --debug --raw-packets
```

Görünür manuel testte masaüstü Discord gerekir; uygulama kimliği sabittir. Sahte sunucu belgelenmiş zarfları bölerek/birleştirerek gönderir; geri sayım, gol tekrarı, duraklatma, uzatma, sonuç ve ayrılmayı canlandırır. Sahte uzatma saati artar; bu gerçek API yönüne ilişkin kanıt değildir. pytest uçtan uca testi gerçek geçici TCP sunucusu ve taklit Discord istemcisi kullanır; gerçek oyun/Discord gerekmez. Sanal saatle gerçek üretim göndericisi sınanır; hızlı geçişler ayrıca 20 saniyede 5 gönderim ve sayaç eşitliği testleriyle doğrulanır.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest rocket_league_rpc/tests/test_e2e.py -v
.\build.ps1 -Python .\.venv\Scripts\python.exe -InstallDependencies
```

Tek exe `dist\rl-presence.exe` olarak üretilir. Windows exe için Windows'ta derleyin. EXE konsol/PowerShell açmadan verilen HTML tasarımını masaüstü pencerede gösterir. Kaynak kullanımında `run.py --console` konsol modunu seçer. İsteğe bağlı tray simgesi bu sürümde bulunmaz. Windows oturumu başına adlandırılmış mutex ikinci kopyayı engeller ve kapanışta otomatik bırakılır.

## Sınırlar ve mimari

PlaylistId tablosu **DOĞRULANMAMIŞTIR**; resmî sayfa ID listesini vermez. Bilinmeyen değer `Playlist <id>` olur ve INFO'ya bir kez yazılır. Arena/harita varyantları da en iyi tahmindir; harf duyarsızdır, aile son eklerini tolere eder. Bilinmeyen arena ham adı ve `rl_logo` ile gösterilir; bir kez loglanır. Gerçek DEBUG paketlerinden `maps.py`/`modes.py` tablolarını genişletin ve yeni görsel anahtarlarını yükleyin.

Kimlik ve uzatma davranışı gerçek paketlerle doğrulanmalıdır. ReplayCreated kaçırılan bir geçmiş tekrar, yalnızca bReplay üzerinden gol tekrarından kesin ayrılamaz. WebSocket otomatik yedek bağlantı değildir; ayarla seçilen alternatiftir. Testler Discord hesabınızdaki görselleri doğrulamaz. Gerçek Windows TCP paketleriyle JSON metni biçimindeki Data, Stadium_P ve eğitim PlaylistId 9 doğrulandı; diğer mod/harita eşleştirmeleri ve uzatma yönü için gerçek paketler gereklidir.

`config.py` ayarları; `installer.py` kurulum/ini işlemini; `game_watcher.py` süreci; `stats_client.py` salt okunur akışı; `state.py` durumları; `presence.py` metni; `rpc.py` IPC/hız sınırını; `runtime.py` log/görev kurtarmayı; `main.py` bütün bileşenleri yönetir.

[Its-Haze/league-rpc](https://github.com/Its-Haze/league-rpc) yalnızca modül düzeni, süreçle koşullanan bağlantı/yeniden deneme, ayar doğrulama ve konsol/tray mimarisi için incelendi. Güncel proje Go/Wails kullanır. League'e özel mantık, veri kaynağı veya kod kopyalanmadı.

Sahte sunucuda `--encoded-data`, gerçek TCP’de gözlenen zarf biçimini canlandırır. Katlicia/LOLCustomRPC yalnızca arayüz/iş parçacığı ve Kaydet/İptal mimarisi için incelendi; League veri mantığı kullanılmadı.

## GitHub güncellemeleri (v0.2.5)

Her açılışta [RocketLeague-Presence Releases](https://github.com/schwairex/RocketLeague-Presence/releases) kontrol edilir. Yeni kararlı sürümde uygulama içi bildirim gelir; EXE indirilir, SHA-256 doğrulanır, gizli bir Windows yardımcısı uygulama kapandıktan sonra EXE’yi değiştirip yeniden açar. config.json ve günlükler korunur. Yeni pencere ve motor sağlıklı açıldığını onaylamazsa eski EXE geri yüklenir. Başarısız aynı sürüm tekrar otomatik denenmez; Güncellemeleri kontrol et ile elle denenebilir. Kaynak/Python kullanımında sürüm notları görünür fakat Python dosyası değiştirilmez.

Depo herkese açık ve Releases erişilebilir olmalıdır. Release’te `rl-presence.exe` ve GitHub SHA-256 digest’i veya `SHA256SUMS.txt` bulunmalıdır. Yayımlama akışı: [releasing.md](releasing.md). İnternet/depo hataları RPC’yi durdurmaz.

Ranked Heatseeker PlaylistId 63 mapping reference: [author-maintained playlist enum](https://github.com/GrantJL/rl-lobby-ranks/blob/master/lobby-ranks/types.h). This is a lookup fact, not a runtime data source.


## v0.2.5 arayüz ve rank ikonları

Oynanan ranked modun manuel rankı artık küçük ikon (`diamond_1`, `champion_2` vb.)
ve tooltip (`Diamond I Div IV`) olarak gönderilir; details/state satırlarından
çıkarılmıştır. Harita büyük görseli ve harita adı tooltip’i korunur. Sabit Discord
uygulamanıza [art-assets.md](art-assets.md) / [rank-asset-keys.txt](rank-asset-keys.txt)
listesindeki anahtarlarla ikonları bir kez yükleyin. Bu paket Portal'a görsel
yüklemez; yüklenmeyen rank anahtarının ikonu Discord’da görünemez. Unranked,
casual/eğitim ve rank kapalı durumlarında small_image/small_text gönderilmez;
yalnızca büyük harita görseli ve harita adı tooltip’i kalır.

Pencere bütün kenar/köşelerden boyutlandırılabilir: en küçük 900×640,
başlangıç 1120×760. Beş sekmenin içeriği gerektiğinde kaydırılır. Güncellemeler'de
etiketli sürüm kartları ve varsayılan kapalı Önceki sürümler bulunur. Hakkında'daki
Genel ayarlara git düğmesi Genel'e geçer. Kaydet/İptal yalnızca ayar sekmelerindedir.

