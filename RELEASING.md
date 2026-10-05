# GitHub sürümü yayımlama / Publishing releases

Güncelleyici yalnızca `schwairex/RocketLeague-Presence` deposunun herkese açık,
kararlı GitHub Releases kayıtlarını kullanır. Taslak/pre-release kayıtları atlanır.
Sürüm etiketi `v0.2.2` gibi üç sayılı olmalıdır. Bir dal commit'i güncelleme sayılmaz.

1. `rocket_league_rpc/__init__.py` ve `pyproject.toml` sürümünü aynı değere yükseltin.
2. Windows üzerinde bağımlılıkları kurun, `python -m pytest` ve `build.ps1` çalıştırın.
3. Çıktı adı her zaman `rl-presence.exe` olur. SHA-256 dosyasını üretin:

```powershell
$releaseHash = (Get-FileHash -LiteralPath dist/rl-presence.exe -Algorithm SHA256).Hash.ToLowerInvariant()
"$releaseHash  rl-presence.exe" | Set-Content -LiteralPath dist/SHA256SUMS.txt -Encoding ascii
```

4. GitHub'da sürüm etiketiyle **Release** oluşturun. Anlaşılır Türkçe/İngilizce
   yenilik notlarını Release açıklamasına yazın; uygulama bunları güvenli metin
   olarak gösterir. `rl-presence.exe` ve `SHA256SUMS.txt` dosyalarını ekleyin.
5. Release'i yayımlayın. Gelecek açılışta eski sürümler bunu algılar. ZIP dosyası
   ayrıca dağıtılabilir; otomatik güncelleyici doğrudan EXE varlığını indirir.

GitHub API'nin `sha256:...` asset digest'i varsa o tercih edilir; yoksa aynı
Release'in `SHA256SUMS.txt` dosyası gerekir. Doğrulama yoksa güncelleme uygulanmaz.
Sadece ZIP eklemek yeterli değildir. Aynı etiketi değiştirmek yerine yeni sürüm
numarası kullanın; başarısız bir sürüm otomatik tekrar denenmez.

Yeni uygulama pencere/motor açılışını 45 saniye içinde onaylar. Yardımcı önceki
EXE'yi `.previous` dosyasında tutar; başarısız açılışta geri yükler. Yardımcının
raporu `.updates/update.log` içindedir. Ayarlar/günlükler silinmez. Uygulama
klasörünün yazılabilir olması gerekir. Bu teslim GitHub'a dosya yüklemez.

English: bump both version declarations, run pytest and build on Windows, then
publish a public stable Release tagged `vX.Y.Z` with `rl-presence.exe` and
`SHA256SUMS.txt`. Release descriptions populate the Updates tab. The updater
checks each launch, validates the downloaded digest, waits for the app to exit,
replaces/restarts it, and requires startup acknowledgement within 45 seconds.
It rolls back on failed startup and avoids retry loops. Source runs never update
the Python interpreter. Repository errors leave RPC running.
