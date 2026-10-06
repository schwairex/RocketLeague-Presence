"""Public GitHub releases, verified staging and a Windows update handoff.

No account/token is needed. This module never accepts a repository or executable
URL from configuration or the UI. A failed check/download leaves RPC running.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from . import __version__

log = logging.getLogger(__name__)
PROJECT_URL = 'https://github.com/schwairex/RocketLeague-Presence'
RELEASES_URL = PROJECT_URL + '/releases'
API_URL = 'https://api.github.com/repos/schwairex/RocketLeague-Presence/releases?per_page=10'
MAX_EXE = 200 * 1024 * 1024


def version_tuple(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not re.fullmatch(r'v?\d{1,4}\.\d{1,4}\.\d{1,4}', value):
        raise ValueError('Invalid stable version')
    return tuple(map(int, value.removeprefix('v').split('.')))


@dataclass(frozen=True)
class Release:
    version: str
    name: str
    notes: str
    published: str
    asset: dict | None
    checksum_url: str | None

    def public(self):
        return {'version': self.version, 'name': self.name, 'notes': self.notes,
                'published': self.published, 'installable': self.asset is not None}


@dataclass(frozen=True)
class StagedUpdate:
    path: Path
    sha256: str


def asset_url(value) -> bool:
    return (isinstance(value, str) and
            value.startswith(PROJECT_URL + '/releases/download/') and
            not any(c in value for c in ('\r', '\n', '\\')))


def parse_releases(data) -> list[Release]:
    releases = []
    for row in data[:10] if isinstance(data, list) else []:
        if not isinstance(row, dict) or row.get('draft') or row.get('prerelease'):
            continue
        try:
            version = '.'.join(map(str, version_tuple(row.get('tag_name'))))
        except ValueError:
            continue
        asset = None
        checksum_url = None
        for item in row.get('assets', []) if isinstance(row.get('assets'), list) else []:
            if not isinstance(item, dict) or not asset_url(item.get('browser_download_url')):
                continue
            if item.get('name') == 'rl-presence.exe' and type(item.get('size')) is int and 0 < item['size'] <= MAX_EXE:
                asset = {key: item.get(key) for key in ('name', 'size', 'digest', 'browser_download_url')}
            if item.get('name') == 'SHA256SUMS.txt':
                checksum_url = item['browser_download_url']
        releases.append(Release(version,
            row.get('name', '')[:200] if isinstance(row.get('name'), str) else 'RL Presence ' + version,
            row.get('body', '')[:12000] if isinstance(row.get('body'), str) else '',
            row.get('published_at', '')[:40] if isinstance(row.get('published_at'), str) else '',
            asset, checksum_url))
    return sorted(releases, key=lambda r: version_tuple(r.version), reverse=True)


class GitHubReleases:
    def _open(self, url):
        if url != API_URL and not asset_url(url):
            raise ValueError('Unexpected update URL')
        response = urlopen(Request(url, headers={'User-Agent': 'RL-Presence/' + __version__,
            'Accept': 'application/vnd.github+json' if url == API_URL else 'application/octet-stream'}), timeout=15)
        parsed = urlparse(response.geturl())
        host = parsed.hostname or ''
        if parsed.scheme != 'https' or not (host in ('api.github.com', 'github.com') or host.endswith('.githubusercontent.com')):
            response.close()
            raise ValueError('Unexpected update redirect')
        return response

    def _read(self, url, limit):
        with self._open(url) as response:
            data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Update response too large')
        return data

    def fetch(self) -> list[Release]:
        try:
            return parse_releases(json.loads(self._read(API_URL, 1024 * 1024)))
        except HTTPError as exc:
            if exc.code == 404:
                raise OSError('GitHub deposu/sürümleri erişilemiyor (404). Depoyu herkese açık yapıp bir Release yayımlayın.') from exc
            if exc.code == 403:
                raise OSError('GitHub erişim sınırına ulaşıldı. Daha sonra tekrar deneyin.') from exc
            raise

    def _download(self, url, path, expected_size, progress):
        count = 0
        with self._open(url) as response, path.open('wb') as target:
            while chunk := response.read(128 * 1024):
                count += len(chunk)
                if count > expected_size or count > MAX_EXE:
                    raise ValueError('Unexpected update size')
                target.write(chunk)
                # 100 is reserved for stage(), after EOF and the size check.
                progress(min(99, round(count / expected_size * 100)))
        if count != expected_size:
            raise ValueError('Incomplete update download')

    def stage(self, release: Release, folder: Path, progress=lambda percent: None) -> StagedUpdate:
        asset = release.asset
        if not asset:
            raise ValueError('Release içinde rl-presence.exe bulunamadı.')
        digest = asset.get('digest')
        checksum = digest[7:] if isinstance(digest, str) and re.fullmatch(r'sha256:[a-fA-F0-9]{64}', digest) else None
        if not checksum and release.checksum_url:
            for line in self._read(release.checksum_url, 65536).decode('utf-8-sig').splitlines():
                match = re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?rl-presence\.exe', line.strip())
                if match:
                    checksum = match[1]
                    break
        if not checksum:
            raise ValueError('Release için SHA-256 doğrulaması yok. SHA256SUMS.txt yayımlayın.')
        version_tuple(release.version)  # do not use arbitrary tags as paths
        folder.mkdir(parents=True, exist_ok=True)
        partial = folder / ('rl-presence-' + release.version + '.part')
        target = partial.with_suffix('.exe')
        try:
            self._download(asset['browser_download_url'], partial, asset['size'], progress)
            if partial.stat().st_size != asset['size']:
                raise ValueError('Incomplete update download')
            progress(100)  # Download finished; checksum verification starts now.
            with partial.open('rb') as source:
                actual = hashlib.file_digest(source, 'sha256').hexdigest()
            if actual.casefold() != checksum.casefold():
                raise ValueError('SHA-256 doğrulaması başarısız; mevcut uygulama korundu.')
            with partial.open('rb') as source:
                if source.read(2) != b'MZ':
                    raise ValueError('İndirilen dosya Windows EXE değil.')
            partial.replace(target)
            return StagedUpdate(target, checksum.casefold())
        finally:
            partial.unlink(missing_ok=True)


HELPER = r'''param([Parameter(Mandatory=$true)][string]$Manifest)
$ErrorActionPreference = 'Stop'
$data = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json
$current = [IO.Path]::GetFullPath($data.current)
$staged = [IO.Path]::GetFullPath($data.staged)
$backup = $current + '.previous'
$incoming = $current + '.incoming'
$report = Join-Path ([IO.Path]::GetDirectoryName($Manifest)) 'update.log'
$readyFile = Join-Path ([IO.Path]::GetDirectoryName($Manifest)) 'update-ready.json'
$failedFile = Join-Path ([IO.Path]::GetDirectoryName($Manifest)) 'failed-release.json'
function Get-UpdateHash([string]$path) {
    $stream = [IO.File]::OpenRead($path)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '') }
    finally { $stream.Dispose(); $sha.Dispose() }
}
function Restart-App([bool]$updated = $false) {
    $options = @{FilePath=$current; WorkingDirectory=[IO.Path]::GetDirectoryName($current); WindowStyle='Hidden'; PassThru=$true}
    $arguments = if ($updated) { $data.updated_command_line } else { $data.command_line }
    if ($arguments) { $options.ArgumentList = $arguments }
    Start-Process @options
}
$replaced = $false
$newProcess = $null
try {
    $owner = Get-Process -Id $data.pid -ErrorAction SilentlyContinue
    if ($owner) { Wait-Process -Id $data.pid -Timeout 120 -ErrorAction Stop }
    if ((Get-UpdateHash $staged) -ne $data.staged_sha256) {
        throw 'Staged executable checksum changed.'
    }
    if (Test-Path -LiteralPath $readyFile) { Remove-Item -LiteralPath $readyFile }
    # PyInstaller's child can briefly hold the old executable after parent exit.
    Copy-Item -LiteralPath $staged -Destination $incoming -Force
    if ((Get-UpdateHash $incoming) -ne $data.staged_sha256) { throw 'Copied executable checksum changed.' }
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        try { Move-Item -LiteralPath $current -Destination $backup -Force; break }
        catch { if ($attempt -eq 39) { throw }; Start-Sleep -Milliseconds 250 }
    }
    try { Move-Item -LiteralPath $incoming -Destination $current -Force; $replaced = $true }
    catch { Move-Item -LiteralPath $backup -Destination $current -Force; throw }
    $newProcess = Restart-App $true
    $healthy = $false
    for ($check = 0; $check -lt 180; $check++) {
        $newProcess.Refresh()
        if ($newProcess.HasExited) { throw "New application exited: $($newProcess.ExitCode)" }
        if (Test-Path -LiteralPath $readyFile) {
            try {
                $health = Get-Content -LiteralPath $readyFile -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($health.version -eq $data.version) { $healthy = $true; break }
            } catch {}
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $healthy) { throw 'New application did not confirm a healthy startup.' }
    if (Test-Path -LiteralPath $failedFile) { Remove-Item -LiteralPath $failedFile }
    'Update installed and restarted.' | Set-Content -LiteralPath $report
} catch {
    $failure = $_.Exception.Message
    if ($newProcess) {
        $newProcess.Refresh()
        if (-not $newProcess.HasExited) {
            # Only terminate the process tree launched by this helper.
            $null = & "$env:SystemRoot\System32\taskkill.exe" /PID $newProcess.Id /T /F
            Start-Sleep -Milliseconds 500
        }
    }
    if ($replaced -and (Test-Path -LiteralPath $backup)) {
        for ($attempt = 0; $attempt -lt 40; $attempt++) {
            try { Copy-Item -LiteralPath $backup -Destination $current -Force; break }
            catch { if ($attempt -eq 39) { throw }; Start-Sleep -Milliseconds 250 }
        }
    }
    @{version=$data.version;digest=$data.staged_sha256;message=$failure} | ConvertTo-Json | Set-Content -LiteralPath $failedFile -Encoding UTF8
    "Update failed: $failure. Previous application preserved." | Set-Content -LiteralPath $report
    try { $null = Restart-App } catch {}
}
'''


def prepare_handoff(current: Path, staged: Path, pid: int, args: list[str], expected_sha256: str):
    current, staged = current.resolve(), staged.resolve()
    folder = current.parent / '.updates'
    folder.mkdir(parents=True, exist_ok=True)
    script = folder / 'apply-update.ps1'
    manifest = folder / 'handoff.json'
    ready_file = folder / 'update-ready.json'
    match = re.fullmatch(r'rl-presence-(\d+\.\d+\.\d+)\.exe', staged.name)
    version = match[1] if match else ''
    with staged.open('rb') as stream:
        staged_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    if not re.fullmatch(r'[a-fA-F0-9]{64}', expected_sha256) or staged_hash.casefold() != expected_sha256.casefold():
        raise ValueError('Staged update SHA-256 changed before handoff')
    script.write_text(HELPER, encoding='utf-8-sig')
    manifest.write_text(json.dumps({'current': str(current), 'staged': str(staged),
        'pid': pid, 'args': args, 'version':version, 'staged_sha256':expected_sha256,
        'command_line': subprocess.list2cmdline(args),
        'updated_command_line':subprocess.list2cmdline(args + ['--update-ready-file',str(ready_file)])}, ensure_ascii=False), encoding='utf-8')
    return script, manifest


def launch_handoff(current: Path, staged: StagedUpdate, args: list[str]):
    if os.name != 'nt':
        raise OSError('Automatic EXE update requires Windows')
    script, manifest = prepare_handoff(current, staged.path, os.getpid(), args, staged.sha256)
    system_root = Path(os.environ.get('SystemRoot', 'C:/Windows'))
    powershell = system_root / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    subprocess.Popen([str(powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', str(script), '-Manifest', str(manifest)], creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True, cwd=str(current.parent))


def relaunch_args(args: list[str], config_path: Path) -> list[str]:
    """Keep the resolved config even when the launch working directory changes."""
    result = []
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg in ('--config','--update-ready-file'):
            skip = True
        elif not arg.startswith(('--config=','--update-ready-file=')):
            result.append(arg)
    return result + ['--config', str(config_path.resolve())]


def acknowledge_startup(path: Path | None):
    if path is not None:
        from .config import atomic_write
        atomic_write(path, json.dumps({'version':__version__}))


class UpdateManager:
    def __init__(self, app_dir: Path, client=None, on_ready=None, frozen=None):
        self.app_dir = app_dir
        self.client = client or GitHubReleases()
        self.on_ready = on_ready
        self.frozen = getattr(sys, 'frozen', False) if frozen is None else frozen
        self._lock = threading.Lock()
        self._state = {'status': 'idle', 'message': 'Açılışta otomatik kontrol edilir.',
            'progress': 0, 'current_version': __version__, 'latest_version': None,
            'releases': [], 'automatic': self.frozen, 'checked_at': None}
        self._busy = False

    def snapshot(self):
        with self._lock:
            return {**self._state, 'releases': [dict(row) for row in self._state['releases']]}

    def _set(self, **changes):
        with self._lock:
            self._state.update(changes)

    def check(self, background=True, retry_failed=False):
        with self._lock:
            if self._busy or self._state['status'] == 'restarting':
                return self.snapshot_unlocked()
            self._busy = True
            self._state.update(status='checking', message='GitHub sürümleri kontrol ediliyor…', progress=0)
        if background:
            threading.Thread(target=self._check, args=(retry_failed,), name='github-updates', daemon=True).start()
        else:
            self._check(retry_failed)
        return self.snapshot()

    def snapshot_unlocked(self):
        return dict(self._state)

    def _download_progress(self, percent):
        if percent >= 100:
            self._set(status='verifying', progress=100,
                      message='İndirilen dosyanın SHA-256 özeti doğrulanıyor…')
        else:
            self._set(progress=max(0, percent))

    def _check(self, retry_failed=False):
        try:
            releases = self.client.fetch()
            latest = releases[0] if releases else None
            self._set(releases=[r.public() for r in releases], checked_at=time.time(),
                      latest_version=latest.version if latest else None)
            if latest and version_tuple(latest.version) > version_tuple(__version__):
                try:
                    failed = json.loads((self.app_dir/'.updates'/'failed-release.json').read_text(encoding='utf-8-sig'))
                except (OSError,ValueError):
                    failed = {}
                if (not retry_failed and isinstance(failed,dict) and failed.get('version') == latest.version):
                    self._set(status='blocked',message='Bu sürüm önceki denemede açılamadı. Mevcut sürüm korundu. Yeniden denemek için Güncellemeleri kontrol et düğmesine basın.')
                    return
                self._set(status='available', message=f'v{latest.version} hazır. ' +
                    ('Otomatik güncelleme başlıyor…' if self.frozen else 'Kaynak sürümünde EXE güncellemesi uygulanmaz.'))
                if self.frozen:
                    time.sleep(2)  # allow the visible startup notification to render
                    self._set(status='downloading', message='Yeni sürüm indiriliyor…')
                    staged = self.client.stage(latest, self.app_dir / '.updates',
                        self._download_progress)
                    self._set(status='restarting', progress=100, message='Güncelleme hazır; uygulama yeniden açılıyor…')
                    if self.on_ready:
                        self.on_ready(staged)
                    else:
                        raise RuntimeError('Update handoff is unavailable')
            else:
                self._set(status='current' if latest else 'empty',
                    message='En güncel sürümü kullanıyorsun.' if latest else 'GitHub üzerinde henüz yayımlanmış sürüm yok.')
        except Exception as exc:
            log.warning('Update check/install failed: %s', exc)
            self._set(status='error', message=str(exc)[:500])
        finally:
            with self._lock:
                self._busy = False
