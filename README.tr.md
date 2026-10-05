# rocket-league-rpc — Türkçe kullanım kılavuzu

Rocket League için Windows üzerinde Python 3.11+ ile çalışan Discord Rich Presence uygulaması. Veriler yalnızca [resmî yerel Stats API](https://www.rocketleague.com/developer/stats-api) üzerinden okunur. Oyun belleğine erişilmez; oyun komutu gönderilmez. [English guide](README.md).

## Kurulum ve çalıştırma

Projeyi yazılabilir bir klasöre çıkarın. PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Hazır derleme varsa `rocket-league-rpc.exe` dosyasını çalıştırabilirsiniz. `config.json` ve `logs/`, kaynak kullanımında `run.py` yanında, exe kullanımında exe yanında bulunur. Alternatif ayar dosyası: `--config C:\klasor\config.json`. Arayüzde Kaydet ile ayarlar hemen uygulanır; JSON dosyasını dışarıdan düzenlediyseniz RPC’yi yeniden başlatın.


## Yeni masaüstü arayüzü (v0.2)

Eski RPC’yi kapatıp yeni EXE’yi açın. Mevcut config.json dosyanızı yeni EXE’nin yanında tutarak Application ID’yi koruyabilirsiniz. Windows 10/11, .NET Framework 4.8 ve Microsoft Edge WebView2 Runtime gerekir. Python, yazı tipleri ve verilen SVG görselleri EXE’ye dahildir; arayüz internet gerektirmez.

**Görünüm** verilen HTML düzenini kullanır. **Genel** sekmesinde rank/küme, ana menü, menü, sıra, mağaza, serbest/özel antrenman ve garaj seçilir. Seçimler kaydedilir; gerçek maç verileri bunların önüne geçer. **Resmî Stats API rank ve ayrıntılı menü durumlarını vermez.** Rank elle belirlenir, tüm modlarda aynı seçim gösterilir.

Kaydet değişiklikleri uygulamayı yeniden başlatmadan uygular; İptal kaydedilmemiş değişiklikleri geri alır. Örnek önizlemeler Discord’a gönderilmez. Canlı maç kartına veya hata simgesine tıklayınca tüm oyuncuların puan/gol/kurtarış değerleri, ham maç alanları, son olay, bağlantı hatası ve son gönderilen/bekleyen RPC açılır. Genel sekmesinde günlük klasörünü açabilir veya logs/diagnostics.json raporu kaydedebilirsiniz.

Menüde takılma hatası gerçek TCP paketinde bulundu: Data alanı JSON nesnesi yerine JSON metniydi. v0.2 her iki biçimi güvenli şekilde okur. Eğitimde TimeSeconds ham verisi tanılamada tutulur; maç geri sayımı olarak gösterilmez. Alt satırdaki paket/sn gerçek ölçümdür.

Discord ve Rocket League göstergeleri gerçek bağlantı durumunu kullanır. Stats API sarıysa bağlantı ya da maç paketi bekleniyor olabilir; simgenin ipucu ve tanılama paneli ayrıntıyı gösterir. Discord’a gönderim en az 15 saniye arayladır. Kısa durumlar birleştirilebilir; canlı panel daha hızlı güncellenir.

## Discord uygulaması ve görseller

1. [Discord Developer Portal](https://discord.com/developers/applications) üzerinde yeni bir uygulama oluşturun. Adını örneğin **Rocket League** yapın; Discord bu adı gösterir.
2. **Application ID** değerini **Genel** sekmesine yazıp **Kaydet**’e basın veya `config.json` içindeki `client_id` alanını düzenleyin. Bot token, OAuth veya client secret gerekmez.
3. Rich Presence / Art Assets bölümüne aşağıdaki anahtarlarla görseller yükleyin. Anahtarlar küçük harflerle **birebir aynı** olmalıdır. Liste `maps.py` tarafından kullanılan bütün farklı anahtarları ve genel/takım simgelerini kapsar. Kullanma hakkınız olan görseller seçin; varyantlar temel harita görselini paylaşır.
4. Aynı Windows oturumunda Discord masaüstü uygulamasını açın. Aktivite görünmüyorsa Discord'un aktivite paylaşımı gizlilik ayarını kontrol edin.

| Birebir görsel anahtarı | Görsel |
|---|---|
| `rl_logo` | Genel Rocket League görseli |
| `blue` | Mavi takım simgesi |
| `orange` | Turuncu takım simgesi |
| `dfh_stadium` | DFH Stadium |
| `beckwith_park` | Beckwith Park |
| `utopia_coliseum` | Utopia Coliseum |
| `wasteland` | Wasteland |
| `neo_tokyo` | Neo Tokyo |
| `urban_central` | Urban Central |
| `aquadome` | Aquadome |
| `mannfield` | Mannfield |
| `forbidden_temple` | Forbidden Temple |
| `farmstead` | Farmstead |

Bu dağıtım harita görselleri veya hazır Application ID içermez. Eksik görsel yüklemeleri maç yazısını engellemez; ilgili resim görünmeyebilir.

## İlk çalıştırma ve Stats API

Varsayılan config.json oluşturulur ve pencere açılır; Application ID eksik olsa da kapanmaz. **Genel** sekmesinde ID, rank/küme ve maç dışında durum seçin, **Kaydet**’e basın. **Görünüm**’de oyun içi adınızı/platformunuzu kaydedin. Eski PrimaryId varsa hesap değiştirirken temizleyin.

**Genel → Stats API’yi yapılandır** düğmesine basın. Steam kayıt defteri/libraryfolders.vdf ve Epic .item manifestleri (Sugar dahil) taranır. Bulunamazsa TAGame klasörünü içeren kurulum yolunu girip kaydedin, düğmeye tekrar basın. `--console` kullanımında bir kez yol soran eski kurulum akışı korunur.

Varsa `<kurulum>\TAGame\Config\TAStatsAPI.ini`, yoksa `DefaultStatsAPI.ini` kullanılır. Dosya tamamen yoksa oluşturulur:

```ini
[TAGame.MatchStatsExporter_TA]
PacketSendRate=30
Port=49123
WebPort=49124
```

Pozitif ve 120'yi aşmayan paket hızı korunur. Kapalı/geçersiz hız 30, 120 üzeri hız 120 yapılır. Portlar ayarlardan alınır; sıfır olamaz ve farklı olmalıdır. Gerekli her değişiklikten **önce `.bak` yedeği** alınır; sonraki yedekler benzersiz son ek alır. Yeni dosyanın boş yedeği, daha önce dosya olmadığını belirtir. Ayarlar doğruysa tekrar yazılmaz. `configparser` anahtarların büyük/küçük harfini ve diğer bölüm/değerleri korur; boşlukları düzenler ve yorumları kaldırır. Gerekirse yorumları yedekten geri alın. Bozuk ini sözdizimi bildirilir ve orijinal dosya korunur.

**Ini değişikliğinden sonra Rocket League'i tamamen kapatıp yeniden açın.** Oyun açıksa ayrıca uyarı gösterilir; çalışan oyun değişikliği yükleyemez. Yetki hatasında yönetici olarak çalıştırma önerilir. RPC klasörünün yazılabilir olması ayar/log sorunlarını giderir. `--skip-install` otomatik ini işlemini atlar.

Arayüzde `client_id` boşsa Genel sekmesinde ID girmeniz beklenir. `--console` modunda açıklama gösterip çıkar. Bundan sonra oyun ve Discord herhangi bir sırada açılabilir. Stats bağlantısı 3–5 saniye arayla, Discord bağlantısı 3–30 saniyeye kadar artan beklemeyle yeniden denenir. Oyun kapalıysa presence temizlenir. Oyun açık ancak bağlantı/aktif maç yoksa `In menus / Queueing` gösterilir. API gerçek sıraya girme durumunu menüden ayıramaz.

## Ayarlar

`config.example.json` bütün varsayılanları içerir. Bozuk JSON veya nesne olmayan kök yedeklenip yeniden oluşturulur. Hatalı alan türleri varsayılana döner; dosyalar atomik yazılır. Yazma yetkisi yoksa uygulama bellekteki varsayılanlarla çalışır ve hata bildirir.

| Alan | Varsayılan / açıklama |
|---|---|
| `client_id` | Boş; Discord Application ID gerekli |
| `install_path` | Boş; otomatik arama veya tek seferlik soru |
| `player_name` | Boş; kendi oyuncu adınız, harf duyarsız eşleşme |
| `player_primary_id` | Boş; `Platform\|Uid\|Splitscreen`, addan öncelikli |
| `stats_host` | `127.0.0.1` |
| `stats_port` | `49123`; TCP, 1–65535 |
| `stats_web_port` | `49124`; TCP'den farklı WebSocket portu |
| `stats_transport` | `tcp`; isteğe bağlı alternatif `websocket` |
| `update_interval` | `15`; 15–3600 saniyeye sınırlandırılır |
| `log_level` | `INFO`; DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `show_score`, `show_map`, `show_mode` | `true`; harita kapalıysa görsel/ipucu da gizlenir |
| `show_perspective` | `false`; takım biliniyorsa `You … Opp` |
| `show_time` | `true`; saat yazısı ve Discord zaman damgaları |
| `show_rank`, `show_player_stats` | `true`; manuel rank ve yerel P/G/S |
| `rank_tier`, `rank_division` | `Unranked`, `1`; küme 1–4, SSL’de küme yok |
| `manual_activity` | `auto`; main_menu/menu/queue/shop/training/custom_training/garage |
| `player_platform` | `auto`; steam/epic ad eşleştirmesini filtreler |
| `spectating` | `false`; canlı maçı izliyorsanız true yapın |
| `auto_learn_primary_id` | `true`; yalnızca ayarlanmış oyuncu adından öğrenilen ID kaydedilir |
| `install_prompted` | `false`; kurulum yolu sorusunun gösterilip gösterilmediği |

Önce ayarlanmış ID, sonra ad eşleştirilir. Ayarlanmış oyuncu bulunamadığında rakibin görüntülenen arabasına geçilmez. Kimlik ayarlanmamışsa `bHasTarget` true olduğunda ve izleyiciye özel alanlar görülmediğinde `Game.Target` kullanılabilir. **Target yalnızca izlenen arabadır; sizin kimliğinizi kanıtlamaz.** İzleyici tespiti kesin değildir; güvenilir sonuç için kimliğinizi ayarlayın veya `spectating: true` kullanın. Bilinmeyen takımda Blue/Orange ve tarafsız kazanan yazısı gösterilir. PlayerJoined takım bilgisi içermez; UpdateState beklenir.

## Saat, maç sonucu ve güncelleme sınırı

Geri sayım, normal oyun, gol tekrarı, duraklatma, uzatma, maç sonu ve geçmiş tekrar durumları ayrı işlenir. Yeni MatchGuid maç durumunu sıfırlar. Boş çevrimdışı MatchGuid ayrılana kadar tek maçtır. ReplayCreated sonrasında MatchDestroyed gelene kadar `Watching a replay` gösterilir; canlı skor/saat gönderilmez. Skor UpdateState'ten alınır; GoalScored'dan kendi kalesine gol gibi durumlarda tahmin edilmez.

RoundStarted bitiş zamanını eşitler. Saat tahminden **2 saniyeden fazla** saparsa yeniden eşitlenir. Gol bildirimi, gol tekrarı, geri sayım, duraklatma ve maç sonunda hareketli zaman damgası yoktur. Sonuç MatchDestroyed gelene veya 60 saniye dolana kadar tutulur. Bilinen yerel takım için Win/Loss, bilinmiyorsa Blue wins/Orange wins gösterilir.

**Uzatmada TimeSeconds yönü doğrulanmamıştır.** Yerel geçen süre başlangıcı kullanılır. İlk gözlenen uzatma başlangıcı esas alınır; maçın ortasında yeniden bağlanılırsa ilk paket geçici başlangıç olur ve geçen süre eksik görünebilir. DEBUG günlükleri gerçek TimeSeconds örneklerini içerir. Politikayı değiştirmek için tek yer `state.overtime_clock_start()` fonksiyonudur.

Normal temizlemeler dahil bütün aktivite yazımları arasında **en az 15 saniye** vardır. Son durum birleştirilir; aynı içerik tekrar gönderilmez. Başlangıç/bitiş önceliği daha uzun ayar aralığını atlayabilir, 15 saniyeyi atlayamaz. Başarısız yazımlar da pencereyi tüketir; yeniden bağlanma sınırı sıfırlamaz. Kısa durumlar görünmeden birleştirilebilir; Discord önceki durumu 15 saniyeye kadar gösterebilir. Ctrl+C sırasında süre uygunsa temizleme gönderilir; değilse yeni aktivite yazılmadan IPC kapatılır ve presence bağlantıyla birlikte kaldırılır.

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

Görünür manuel testte geçerli client_id ve masaüstü Discord gerekir. Sahte sunucu belgelenmiş zarfları bölerek/birleştirerek gönderir; geri sayım, gol tekrarı, duraklatma, uzatma, sonuç ve ayrılmayı canlandırır. Sahte uzatma saati artar; bu gerçek API yönüne ilişkin kanıt değildir. pytest uçtan uca testi gerçek geçici TCP sunucusu ve taklit Discord istemcisi kullanır; gerçek oyun/Discord gerekmez. Enjekte edilen saat olay başına 15 saniye ilerler, üretim hız sınırı gerçekten test edilir.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest rocket_league_rpc/tests/test_e2e.py -v
.\build.ps1 -Python .\.venv\Scripts\python.exe -InstallDependencies
```

Tek exe `dist\rocket-league-rpc.exe` olarak üretilir. Windows exe için Windows'ta derleyin. EXE konsol/PowerShell açmadan verilen HTML tasarımını masaüstü pencerede gösterir. Kaynak kullanımında `run.py --console` konsol modunu seçer. İsteğe bağlı tray simgesi bu sürümde bulunmaz. Windows oturumu başına adlandırılmış mutex ikinci kopyayı engeller ve kapanışta otomatik bırakılır.

## Sınırlar ve mimari

PlaylistId tablosu **DOĞRULANMAMIŞTIR**; resmî sayfa ID listesini vermez. Bilinmeyen değer `Playlist <id>` olur ve INFO'ya bir kez yazılır. Arena/harita varyantları da en iyi tahmindir; harf duyarsızdır, aile son eklerini tolere eder. Bilinmeyen arena ham adı ve `rl_logo` ile gösterilir; bir kez loglanır. Gerçek DEBUG paketlerinden `maps.py`/`modes.py` tablolarını genişletin ve yeni görsel anahtarlarını yükleyin.

Kimlik ve uzatma davranışı gerçek paketlerle doğrulanmalıdır. ReplayCreated kaçırılan bir geçmiş tekrar, yalnızca bReplay üzerinden gol tekrarından kesin ayrılamaz. WebSocket otomatik yedek bağlantı değildir; ayarla seçilen alternatiftir. Testler Discord hesabınızdaki görselleri doğrulamaz. Gerçek Windows TCP paketleriyle JSON metni biçimindeki Data, Stadium_P ve eğitim PlaylistId 9 doğrulandı; diğer mod/harita eşleştirmeleri ve uzatma yönü için gerçek paketler gereklidir.

`config.py` ayarları; `installer.py` kurulum/ini işlemini; `game_watcher.py` süreci; `stats_client.py` salt okunur akışı; `state.py` durumları; `presence.py` metni; `rpc.py` IPC/hız sınırını; `runtime.py` log/görev kurtarmayı; `main.py` bütün bileşenleri yönetir.

[Its-Haze/league-rpc](https://github.com/Its-Haze/league-rpc) yalnızca modül düzeni, süreçle koşullanan bağlantı/yeniden deneme, ayar doğrulama ve konsol/tray mimarisi için incelendi. Güncel proje Go/Wails kullanır. League'e özel mantık, veri kaynağı veya kod kopyalanmadı.

Sahte sunucuda `--encoded-data`, gerçek TCP’de gözlenen zarf biçimini canlandırır. Katlicia/LOLCustomRPC yalnızca arayüz/iş parçacığı ve Kaydet/İptal mimarisi için incelendi; League veri mantığı kullanılmadı.
