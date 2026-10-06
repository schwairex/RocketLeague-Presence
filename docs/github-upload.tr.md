# README, logo ve kaynakları GitHub'a yükleme

[Türkçe ana sayfa](../README.tr.md) · [English](../README.md)

Bu pakette README ve görseller hazırdır. GitHub'a henüz yükleme yapılmamıştır.

## Hangi dosya nereye?

| Dosya / klasör | GitHub konumu |
| --- | --- |
| `README.md` | Deponun kökü; GitHub'ın ana sayfada gösterdiği dosya |
| `README.tr.md` | Deponun kökü; README'deki Türkçe bağlantısının hedefi |
| `assets/branding/logo.svg` | Verdiğin orijinal logo, değişmeden korunmuştur |
| `assets/branding/readme-hero.svg` | Logonu kullanan README kapak görseli |
| `assets/branding/download.svg`, `download.tr.svg` | İngilizce/Türkçe indirme düğmesi |
| `assets/screenshots/` | README'deki uygulama ekran görüntüleri |
| `docs/` | Ayrıntılı rehberler, art asset anahtarları ve doğrulama kayıtları |
| `rocket_league_rpc/`, `run.py`, diğer kök proje dosyaları | Kaynak kod; klasör yapısını aynen koru |

README görselleri **göreli yollarla** açılır. Ayrı bir görsel barındırma servisine
yüklemene veya bağlantıları değiştirmene gerek yoktur. Klasör adları ve dosya
adları birebir aynı kalmalı; GitHub büyük/küçük harf ayrımını yapar.

Bu logo yüklemesi GitHub README'si içindir. Discord'da harita/rank ikonları için
ayrıca [art-assets.md](art-assets.md) içindeki sabit uygulama anahtarları kullanılır.

## Önerilen yöntem: GitHub Desktop

1. GitHub Desktop'ta **File → Clone repository → URL** ile
   `https://github.com/schwairex/RocketLeague-Presence` deposunu bilgisayarına klonla.
2. Yeni kaynak ZIP'ini farklı bir klasöre çıkar. İçindeki `rl-presence` klasörünün
   **içeriğini** klonladığın deponun köküne kopyala; `rl-presence` adlı ek bir üst
   klasör oluşturma. Klonun `.git` klasörünü koru.
3. Önceki yapıda aşağıdaki belgeler kökte bulunuyorsa yeni konumlarını kontrol
   et, sonra yalnızca eski kök kopyalarını kaldır:

   | Eski kök konumu | Yeni konumu |
   | --- | --- |
   | `ART_ASSETS.md` | `docs/art-assets.md` |
   | `RANK_ASSET_KEYS.txt` | `docs/rank-asset-keys.txt` |
   | `RELEASING.md` | `docs/releasing.md` |
   | `FONT_LICENSES.txt` | `docs/licenses/fonts.txt` |
   | `ICON_LICENSE.txt` | `docs/licenses/icons.txt` |
   | `VERIFICATION.md` | `docs/qa/verification.md` |
   | `design-qa.md`, `design-qa-v0.2.1.md`, `release-smoke.json` | `docs/qa/` |
   | `IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_PLAN_V2.md` | `docs/qa/plans/` |
   | Eski kök `.png` doğrulama ekranları | `docs/qa/images/` |

4. GitHub Desktop'ın **Changes** ekranında dosyaları incele. Kişisel `config.json`,
   `logs/`, `.venv/`, `build/`, `dist/` veya `.updates/` yükleme; `.gitignore` bunları
   dışarıda tutar. README, assets, docs ve uygulama kaynakları görünmelidir.
5. Bir dal oluştur, örneğin `docs/readme-refresh`. Commit mesajını
   `docs: refresh README and organize repository` yaz, **Commit** ve **Push origin**
   yap. Pull request açıp birleştirince yeni README ana sayfada görünür.

## Tarayıcıdan yükleme

Depoyu aç → **Add file → Upload files**. Yeni README dosyalarını ve `assets/`,
`docs/` klasörlerini sürükleyip bırak. Kaynak yapısını da güncelleyeceksen paketin
diğer proje dosyalarını aynı kök yerleşimiyle ekle. Yeni bir dalda değişiklik
önerip birleştir. Eski kök belgeleri yukarıdaki tabloya göre kaldır.

ZIP dosyasını Code bölümüne yüklemek içindeki dosyaları açmaz; README ve assets
klasörü ayrı dosyalar olarak depoda bulunmalıdır. Yükledikten sonra üst düzeyde
`README.md`, `assets/`, `docs/`, `rocket_league_rpc/` bulunduğunu kontrol et.

GitHub'ın tarayıcı yüklemesinde aynı anda en fazla 100 dosya ve dosya başına
25 MiB sınırı vardır; gerekirse gruplar halinde yükle veya GitHub Desktop kullan.
[Resmî GitHub yükleme rehberi](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository).

## İndirme düğmesinin çalışması

README'deki düğme şuraya gider:

`https://github.com/schwairex/RocketLeague-Presence/releases/latest/download/rl-presence.exe`

**Releases → Draft a new release** bölümünde kararlı sürümü yayımla ve
`rl-presence.exe` ile `SHA256SUMS.txt` dosyalarını ekle. EXE'nin adı tam olarak
`rl-presence.exe` olmalı. Yalnızca ZIP yüklemek bu düğmeyi veya otomatik
güncelleyiciyi çalıştırmaz. Mevcut Release'te bu dosya varsa düğme onu kullanır.
Tam akış: [Sürüm yayımlama](releasing.md).

## Son kontrol

- Ana README'de kapak/logo ve ekran görüntüleri açılıyor.
- Türkçe bağlantısı `README.tr.md` dosyasına gidiyor.
- İndirme düğmesi doğrudan EXE'yi indiriyor.
- Rehber bağlantıları açılıyor; eski kök belgeler tekrarlanmıyor.
- Kaynak kurulumunda `python run.py`, test ve `build.ps1` komutları kökten çalışıyor.

README grafiklerinin metinleri self-contained SVG'dir; font, script veya dış
görsel indirmez. Örnek ekran görüntülerindeki maç verileri tanıtım amaçlıdır.
