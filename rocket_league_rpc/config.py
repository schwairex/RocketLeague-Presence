"""Validated preferences and atomic, recoverable JSON persistence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
import math
from pathlib import Path
import shutil
import sys
import time

log = logging.getLogger(__name__)
APPLICATION_ID = '802869954805760020'

RANK_TIERS = ('Unranked',) + tuple(f'{rank} {level}' for rank in (
    'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Champion', 'Grand Champion')
    for level in ('I', 'II', 'III')) + ('Supersonic Legend',)
ACTIVITIES = {'auto': 'In menus / Queueing', 'main_menu': 'Main menu', 'menu': 'In menus',
              'queue': 'Queueing', 'shop': 'Item shop', 'training': 'Free play',
              'custom_training': 'Custom training', 'garage': 'Garage'}


def app_directory() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent


@dataclass
class Config:
    schema_version: int = 3
    language: str = 'tr'
    install_path: str = ''
    player_name: str = ''
    player_primary_id: str = ''
    stats_host: str = '127.0.0.1'
    stats_port: int = 49123
    stats_web_port: int = 49124
    update_interval: float = 1.0
    log_level: str = 'INFO'
    show_score: bool = True
    show_map: bool = True
    show_mode: bool = True
    show_perspective: bool = False
    show_time: bool = True
    show_rank: bool = True
    show_player_stats: bool = True
    rank_tier: str = 'Unranked'
    rank_division: int = 1
    manual_activity: str = 'auto'
    player_platform: str = 'auto'
    stats_transport: str = 'tcp'
    spectating: bool = False
    auto_learn_primary_id: bool = True
    install_prompted: bool = False

    @property
    def client_id(self) -> str:
        """Application identity belongs to the build, never to user settings."""
        return APPLICATION_ID


def backup_file(path: Path) -> Path:
    """Keep the first .bak; subsequent recovery never overwrites evidence."""
    backup = path.with_name(path.name + '.bak')
    if backup.exists():
        backup = path.with_name(f'{path.name}.{time.time_ns()}.bak')
    if path.exists():
        shutil.copy2(path, backup)
    else:
        backup.write_bytes(b'')  # records that the original did not exist
    return backup


def atomic_write(path: Path, text: str, encoding: str = 'utf-8') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    try:
        temporary.write_text(text, encoding=encoding)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def save_config(config: Config, path: Path) -> bool:
    try:
        atomic_write(path, json.dumps(asdict(config), ensure_ascii=False, indent=2) + '\n')
        return True
    except (OSError, UnicodeError) as exc:
        log.error('Cannot save configuration %s: %s. Use a writable app folder.', path, exc)
        return False


def _bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.casefold() in ('true', 'false'):
        return value.casefold() == 'true'
    return default


def _port(value, default: int) -> int:
    if type(value) is int and 1 <= value <= 65535:
        return value
    return default


def validate_config(data: dict) -> Config:
    cfg = Config()
    language = data.get('language')
    if isinstance(language, str) and language.casefold() in ('tr', 'en'):
        cfg.language = language.casefold()
    for key in ('install_path', 'player_name', 'player_primary_id', 'stats_host'):
        value = data.get(key)
        if isinstance(value, str):
            try:
                value.encode('utf-8')
            except UnicodeError:
                log.warning('Invalid Unicode in config field %s; using its default.', key)
                continue
            setattr(cfg, key, value.strip())
    cfg.stats_host = cfg.stats_host or '127.0.0.1'
    cfg.stats_port = _port(data.get('stats_port'), 49123)
    cfg.stats_web_port = _port(data.get('stats_web_port'), 49124)
    if cfg.stats_web_port == cfg.stats_port:
        cfg.stats_web_port = 49124 if cfg.stats_port != 49124 else 49123
    value = data.get('update_interval')
    if type(value) is int:
        cfg.update_interval = float(min(3600, max(1, value)))
    elif type(value) is float and math.isfinite(value):
        cfg.update_interval = min(3600.0, max(1.0, float(value)))
    if data.get('schema_version') != 3 and cfg.update_interval == 15:
        cfg.update_interval = 1.0  # migrate the old mandatory 15-second floor
    level = data.get('log_level')
    if isinstance(level, str) and level.upper() in ('DEBUG','INFO','WARNING','ERROR','CRITICAL'):
        cfg.log_level = level.upper()
    transport = data.get('stats_transport')
    if isinstance(transport, str) and transport.casefold() in ('tcp','websocket'):
        cfg.stats_transport = transport.casefold()
    for key in ('show_score','show_map','show_mode','show_perspective',
                'show_time','show_rank','show_player_stats',
                'spectating','auto_learn_primary_id','install_prompted'):
        setattr(cfg, key, _bool(data.get(key), getattr(cfg, key)))
    if data.get('rank_tier') in RANK_TIERS:
        cfg.rank_tier = data['rank_tier']
    if type(data.get('rank_division')) is int:
        cfg.rank_division = min(4, max(1, data['rank_division']))
    if isinstance(data.get('manual_activity'), str) and data['manual_activity'] in ACTIVITIES:
        cfg.manual_activity = data['manual_activity']
    if data.get('player_platform') in ('auto', 'steam', 'epic'):
        cfg.player_platform = data['player_platform']
    return cfg


def load_config(path: Path | None = None) -> Config:
    path = path or app_directory()/'config.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(data, dict):
            raise ValueError('configuration root must be an object')
        cfg = validate_config(data)
    except FileNotFoundError:
        cfg = Config()
    except (ValueError, UnicodeError, RecursionError) as exc:
        log.warning('Malformed config %s: %s. Backing up and regenerating.', path, exc)
        try:
            backup_file(path)
        except OSError as backup_error:
            log.error('Cannot back up config; keeping original: %s', backup_error)
            return Config()
        cfg = Config()
    except OSError as exc:
        log.error('Cannot read config: %s. Using defaults in memory.', exc)
        return Config()
    save_config(cfg, path)
    return cfg
