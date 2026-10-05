"""Steam/Epic discovery and idempotent Stats API ini patching."""
from __future__ import annotations

import configparser
from dataclasses import dataclass
import io
import json
import logging
import math
import os
from pathlib import Path
import re
import threading

from .config import Config, atomic_write, backup_file, save_config

log = logging.getLogger(__name__)
SECTION = 'TAGame.MatchStatsExporter_TA'
_INI_LOCK = threading.RLock()


@dataclass(frozen=True)
class PatchResult:
    path: Path
    changed: bool
    backup: Path | None = None


def patch_stats_ini(install: Path, tcp_port: int = 49123, web_port: int = 49124) -> PatchResult:
    with _INI_LOCK:
        return _patch_stats_ini(install,tcp_port,web_port)


def _patch_stats_ini(install: Path, tcp_port: int, web_port: int) -> PatchResult:
    if type(tcp_port) is not int or type(web_port) is not int or not (1 <= tcp_port <= 65535 and 1 <= web_port <= 65535) or tcp_port == web_port:
        raise ValueError('TCP and WebSocket ports must be different, nonzero ports (1-65535).')
    folder = Path(install)/'TAGame'/'Config'
    path = folder/'TAStatsAPI.ini'
    if not path.exists():
        path = folder/'DefaultStatsAPI.ini'
    ini = configparser.ConfigParser(interpolation=None, strict=False)
    ini.optionxform = str
    encoding = 'utf-8'
    if path.exists():
        raw = path.read_bytes()
        try:
            text = raw.decode('utf-8-sig')
            encoding = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
        except UnicodeDecodeError:
            if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
                encoding = 'utf-16'
            else:
                encoding = 'cp1252'
            text = raw.decode(encoding)
        try:
            ini.read_string(text)
        except configparser.Error as exc:
            raise ValueError(f'Malformed ini {path}; fix its syntax before patching (original untouched): {exc}') from exc
    changed = not ini.has_section(SECTION)
    if changed:
        ini.add_section(SECTION)
    section = ini[SECTION]
    try:
        rate = float(section.get('PacketSendRate', '0'))
    except ValueError:
        rate = 0
    if not math.isfinite(rate) or rate <= 0:
        section['PacketSendRate'] = '30'
        changed = True
    elif rate > 120:
        section['PacketSendRate'] = '120'
        changed = True
    for key, wanted in [('Port',tcp_port), ('WebPort',web_port)]:
        try:
            current = int(section.get(key, '0'))
        except ValueError:
            current = 0
        if current != wanted:
            section[key] = str(wanted)
            changed = True
    if not changed:
        return PatchResult(path, False)
    folder.mkdir(parents=True, exist_ok=True)
    backup = backup_file(path)
    output = io.StringIO()
    ini.write(output)
    atomic_write(path, output.getvalue(), encoding)
    return PatchResult(path, True, backup)


def steam_roots() -> list[Path]:
    roots = []
    try:
        import winreg
        for hive, key, value in [(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam','SteamPath'),
                                  (winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\WOW6432Node\Valve\Steam','InstallPath')]:
            try:
                with winreg.OpenKey(hive, key) as handle:
                    roots.append(Path(winreg.QueryValueEx(handle, value)[0]))
            except OSError:
                pass
    except ImportError:
        pass
    return roots


def steam_libraries(root: Path) -> list[Path]:
    libraries = [root]
    try:
        content = (root/'steamapps'/'libraryfolders.vdf').read_text(encoding='utf-8-sig')
        # Both current "path" entries and old numeric -> path VDF are supported.
        for key, raw in re.findall(r'"([^"\n]+)"\s*"((?:\\.|[^"\\])*)"', content):
            if key == 'path' or (key.isdigit() and (':' in raw or raw.startswith('/'))):
                libraries.append(Path(raw.replace('\\\\', '\\')))
    except (OSError,UnicodeError):
        pass
    return list(dict.fromkeys(libraries))


def discover_installs(roots: list[Path] | None = None, manifests: Path | None = None,
                      extra: list[Path] | None = None) -> list[Path]:
    found = []
    def add(path):
        try:
            path = Path(path).resolve()
            if (path/'TAGame').is_dir() and str(path).casefold() not in {str(p).casefold() for p in found}:
                found.append(path)
        except (OSError,ValueError):
            log.debug('Cannot inspect installation path',exc_info=True)
    for path in extra or []:add(path)
    for root in steam_roots() if roots is None else roots:
        for library in steam_libraries(root):
            path = library/'steamapps'/'common'/'rocketleague'
            add(path)
            manifest = library/'steamapps'/'appmanifest_252950.acf'
            try:
                match = re.search(r'"installdir"\s*"([^"\r\n]+)"',manifest.read_text(encoding='utf-8-sig'))
                if match and Path(match[1]).name == match[1]:
                    add(library/'steamapps'/'common'/match[1])
            except (OSError,UnicodeError):pass
    manifests = manifests or Path(os.environ.get('PROGRAMDATA',r'C:\ProgramData'))/'Epic'/'EpicGamesLauncher'/'Data'/'Manifests'
    try:
        for item in manifests.glob('*.item'):
            try:
                data = json.loads(item.read_text(encoding='utf-8-sig'))
                if not isinstance(data, dict):
                    continue
                names = [str(data.get('AppName','')), str(data.get('DisplayName',''))]
                # Epic's internal Rocket League AppName is commonly "Sugar".
                matches = any(re.sub(r'[^a-z]', '', name.casefold()) in ('rocketleague','sugar') for name in names)
                location = data.get('InstallLocation')
                if matches and isinstance(location, str) and (Path(location)/'TAGame').is_dir():
                    add(location)
            except (OSError, ValueError, UnicodeError):
                log.debug('Cannot parse Epic manifest %s', item, exc_info=True)
    except OSError:
        log.debug('Cannot scan Epic manifests', exc_info=True)
    return found


def discover_install(roots: list[Path] | None = None, manifests: Path | None = None) -> Path | None:
    found = discover_installs(roots,manifests)
    return found[0] if found else None


def configure_installs(installs, tcp_port=49123, web_port=49124):
    results=[]
    for install in installs:
        row={'path':str(Path(install).resolve()),'status':'ready','changed':False,'ini':'','backup':None}
        try:
            result=patch_stats_ini(Path(install),tcp_port,web_port)
            row.update(ini=str(result.path),changed=result.changed,
                       backup=str(result.backup) if result.backup else None,
                       status='restart_required' if result.changed else 'ready')
        except PermissionError:
            row['status']='permission_denied'
        except (OSError,ValueError,UnicodeError) as exc:
            row.update(status='error',error=f'{type(exc).__name__}: {exc}')
        results.append(row)
    return results


class InstallationSetup:
    """Idempotent setup for all copies; remember a running game needs restart."""
    def __init__(self):
        self.pending=set()
        self.result={'status':'checking','installs':[],'active_path':'','restart_required':False}

    def check(self, config, running=False, active=None, started_at=None):
        extra=[Path(config.install_path)] if config.install_path else []
        if active:extra.insert(0,Path(active))
        installs=discover_installs(extra=extra)
        rows=configure_installs(installs,config.stats_port,config.stats_web_port)
        active_path=str(Path(active).resolve()) if active else ''
        if not running:self.pending.clear()
        for row in rows:
            if row['changed'] and running:
                self.pending.add(row['path'])
                log.warning('Stats API configured in %s; restart the running game to apply it.',row['ini'])
            elif row['changed']:
                log.info('Stats API configured in %s. Ready for the next game launch.',row['ini'])
            # Account for game restarts between polls and RPC app restarts.
            if running and row['path']==active_path and isinstance(started_at,(int,float)) and row['ini']:
                try:
                    if Path(row['ini']).stat().st_mtime > started_at:self.pending.add(row['path'])
                    else:self.pending.discard(row['path'])
                except OSError:pass
        restart=running and (active_path in self.pending if active_path else bool(self.pending))
        selected=next((r for r in rows if r['path']==active_path),None)
        relevant=[selected] if selected else rows
        status=('missing' if not rows else 'permission_denied' if any(r['status']=='permission_denied' for r in relevant)
                else 'error' if any(r['status']=='error' for r in relevant) else 'restart_required' if restart else 'ready')
        self.result={'status':status,'installs':rows,'active_path':active_path,'restart_required':bool(restart)}
        return self.result


def setup_install(config: Config, config_path: Path, running: bool = False, prompt=input) -> PatchResult | None:
    path = Path(config.install_path) if config.install_path else discover_install()
    if path is None or not (path/'TAGame').is_dir():
        if not config.install_prompted:
            config.install_prompted = True
            save_config(config, config_path)
            try:
                supplied = prompt('Rocket League install folder (contains TAGame), or Enter to skip: ').strip().strip('"')
            except (EOFError, OSError):
                supplied = ''
            path = Path(supplied) if supplied else None
        else:
            path = None
    if path is None or not (path/'TAGame').is_dir():
        log.warning('Install not found. Set install_path in config.json; waiting for the Stats API is still possible.')
        return None
    config.install_path = str(path.resolve())
    save_config(config, config_path)
    try:
        result = patch_stats_ini(path, config.stats_port, config.stats_web_port)
    except PermissionError as exc:
        log.error('Cannot patch Stats ini: %s. Try running as administrator, then restart Rocket League.', exc)
        return None
    except (OSError, ValueError, UnicodeError) as exc:
        log.error('Cannot patch Stats ini: %s', exc)
        return None
    if result.changed:
        log.warning('Stats API enabled/configured in %s (backup %s). Fully restart Rocket League%s.',
                    result.path, result.backup, ' — the game is currently running' if running else '')
    else:
        log.info('Stats API ini already configured: %s', result.path)
    return result
