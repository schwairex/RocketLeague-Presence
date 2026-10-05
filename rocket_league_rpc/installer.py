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

from .config import Config, atomic_write, backup_file, save_config

log = logging.getLogger(__name__)
SECTION = 'TAGame.MatchStatsExporter_TA'


@dataclass(frozen=True)
class PatchResult:
    path: Path
    changed: bool
    backup: Path | None = None


def patch_stats_ini(install: Path, tcp_port: int = 49123, web_port: int = 49124) -> PatchResult:
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
    except OSError:
        pass
    return list(dict.fromkeys(libraries))


def discover_install(roots: list[Path] | None = None, manifests: Path | None = None) -> Path | None:
    for root in steam_roots() if roots is None else roots:
        for library in steam_libraries(root):
            path = library/'steamapps'/'common'/'rocketleague'
            if (path/'TAGame').is_dir():
                return path
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
                    return Path(location)
            except (OSError, ValueError, UnicodeError):
                log.debug('Cannot parse Epic manifest %s', item, exc_info=True)
    except OSError:
        log.debug('Cannot scan Epic manifests', exc_info=True)
    return None


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
