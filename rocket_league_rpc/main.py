"""Console entry point and supervised asyncio application lifecycle."""
from __future__ import annotations

import argparse
import asyncio
import logging
import copy
from dataclasses import asdict, replace
from collections import deque
from pathlib import Path
import signal
import os
import time

from . import __version__
from .config import Config, app_directory, load_config, save_config, validate_config
from .game_watcher import rocket_league_running, watch_game, running_game_info
from .installer import setup_install, InstallationSetup
from .presence import build_presence
from .rpc import DiscordClient, PresencePublisher, UNSET
from .maps import lookup_map
from .modes import lookup_mode
from .runtime import AlreadyRunning, SingleInstance, configure_logging, supervise, wait_or_stop
from .state import MatchState, Phase, reduce_event, normalize_event
from .stats_client import StatsClient

log = logging.getLogger(__name__)


class Application:
    def __init__(self, config: Config, config_path: Path | None = None,
                 discord_factory=None, wall_clock=time.time, monotonic_clock=time.monotonic,
                 mock_game: bool = False, raw_packets: bool = False, auto_setup: bool = False):
        self.config = config
        self.config_path = config_path
        self.wall_clock = wall_clock
        self.running = False
        self.connected = False
        self.state = MatchState()
        self.stop = asyncio.Event()
        self.stats_task = None
        self.mock_game = mock_game
        self.raw_packets = raw_packets
        self.custom_discord_factory = discord_factory is not None
        self.last_event = None
        self.last_packet_at = None
        self.last_update = None
        self.stats_error = ''
        self.packet_times = deque(maxlen=1000)
        self.settings_lock = asyncio.Lock()
        self.setup_lock = asyncio.Lock()
        self.auto_setup = auto_setup and not mock_game
        self.install_setup = InstallationSetup()
        if not self.auto_setup:self.install_setup.result['status']='manual'
        self.publisher = PresencePublisher(discord_factory or (lambda:DiscordClient(self.config.client_id)),
                                           interval=config.update_interval, clock=monotonic_clock)

    def snapshot(self) -> dict:
        now = self.wall_clock()
        match = asdict(self.state)
        match['phase'] = self.state.phase.value
        match['players'] = list(match['players'])
        match['map_name'], match['map_asset'] = lookup_map(self.state.arena) if self.state.arena else ('—','rl_logo')
        match['mode_name'] = lookup_mode(self.state.playlist_id) if self.state.playlist_id is not None else '—'
        status = ('game_off' if not self.running else 'disconnected' if not self.connected else
                  'awaiting_data' if self.last_event is None else 'menu' if self.state.phase == Phase.MENU else 'live')
        return {'config':{**asdict(self.config), 'client_id':self.config.client_id}, 'game_running':self.running, 'match':match,
                'installation':copy.deepcopy(self.install_setup.result),
                'stats':{'connected':self.connected, 'status':status, 'last_event':self.last_event,
                         'last_packet_at':self.last_packet_at, 'error':self.stats_error,
                         'packets_per_second':sum(t >= now-1 for t in self.packet_times)},
                'discord':{'connected':self.publisher.client is not None,
                           'error':self.publisher.error,
                           'sent_payload':copy.deepcopy(self.publisher.sent) if self.publisher.sent is not UNSET else None,
                           'pending_payload':self.current_payload(),
                           'next_send_in':self.publisher.next_send_in() if self.publisher.desired != self.publisher.sent else 0}}

    async def apply_config(self, changes: dict) -> dict:
        if not isinstance(changes,dict):
            raise ValueError('Settings must be an object')
        async with self.settings_lock:
            candidate = validate_config({**asdict(self.config), **changes})
            if self.config_path and not await asyncio.to_thread(save_config,candidate,self.config_path):
                raise OSError('Ayarlar kaydedilemedi. Yazılabilir bir klasör kullanın.')
            old = self.config
            self.config = candidate
            self.publisher.interval = candidate.update_interval
            if any(getattr(old,k) != getattr(candidate,k) for k in ('stats_host','stats_port','stats_web_port','stats_transport')):
                self.connected = False
                self.state = MatchState()
                self.last_update = None
                self.last_event = None
                if self.stats_task and not self.stats_task.done():
                    self.stats_task.cancel()
            elif self.last_update is not None:
                # Re-evaluate identity only; an old packet must never restart a
                # clock or change a paused/replay phase during settings save.
                matched = reduce_event(self.state,self.last_update,candidate,self.wall_clock())
                self.state = replace(self.state, **{key:getattr(matched,key) for key in (
                    'local_team','local_player_name','local_primary_id','local_player_score',
                    'local_player_goals','local_player_saves')})
            self.refresh(priority=True)
            log.info('Settings saved and applied.')
            return self.snapshot()

    async def on_stats_error(self, exc):
        self.stats_error = f'{type(exc).__name__}: {exc}'

    def current_payload(self):
        if not self.running:
            return None
        state = self.state if self.connected else MatchState()
        return build_presence(state, self.config, self.wall_clock())

    def refresh(self, priority: bool = False):
        self.publisher.offer(self.current_payload(), priority)

    async def set_running(self, running: bool):
        if self.running != running:
            log.info('Rocket League %s', 'running' if running else 'not running')
        self.running = running
        if not running:
            self.install_setup.pending.clear()
            self.connected = False
            self.state = MatchState()
            self.last_update = None
            self.last_event = None
            self.last_packet_at = None
            self.packet_times.clear()
            if self.stats_task is not None and not self.stats_task.done():
                self.stats_task.cancel()
        self.refresh(priority=True)

    async def on_connection(self, connected: bool):
        previous = self.connected
        self.connected = connected and self.running
        if not self.connected:
            self.state = MatchState()
            self.last_update = None
        if self.connected:
            self.last_event = None
            self.last_packet_at = None
            self.stats_error = ''
            self.packet_times.clear()
        if previous != self.connected:
            log.info('Stats API %s', 'connected; awaiting match packets' if self.connected else 'disconnected; showing menus')
        self.refresh(priority=True)

    async def on_event(self, message):
        if not self.running:
            return
        message = normalize_event(message)
        if isinstance(message,dict) and isinstance(message.get('Event'),str):
            self.last_event = message['Event']
            self.last_packet_at = self.wall_clock()
            self.packet_times.append(self.last_packet_at)
            if message['Event'] == 'UpdateState' and isinstance(message.get('Data'),dict):
                self.last_update = copy.deepcopy(message)
            elif message['Event'] == 'MatchDestroyed':
                self.last_update = None
        old = self.state
        self.state = reduce_event(old, message, self.config, self.wall_clock())
        priority = (old.phase != self.state.phase or old.match_guid != self.state.match_guid
                    or old.playlist_id != self.state.playlist_id or old.clock_end != self.state.clock_end
                    or (old.blue_score,old.orange_score) != (self.state.blue_score,self.state.orange_score)
                    or (old.local_player_goals,old.local_player_saves,old.local_player_score) != (
                        self.state.local_player_goals,self.state.local_player_saves,self.state.local_player_score))
        self.refresh(priority=priority)
        if (self.config.auto_learn_primary_id and self.config.player_name
            and not self.config.player_primary_id and self.state.local_primary_id
            and self.state.local_player_name.casefold() == self.config.player_name.casefold()):
            async with self.settings_lock:
                self.config.player_primary_id = self.state.local_primary_id
                if self.config_path:
                    await asyncio.to_thread(save_config, self.config, self.config_path)
            log.info('Learned PrimaryId for configured player name.')

    async def stats_loop(self):
        delay = 3.0
        while not self.stop.is_set():
            if not self.running:
                delay = 3
                await wait_or_stop(self.stop, 1)
                continue
            client = StatsClient(self.config, self.on_event, self.on_connection, self.raw_packets)
            self.stats_task = asyncio.create_task(client.session(), name='stats-session')
            try:
                await self.stats_task
                delay = 3
            except asyncio.CancelledError:
                if self.stop.is_set() or asyncio.current_task().cancelling():
                    raise
                continue  # process watcher cancelled the old game session
            except Exception as exc:
                await self.on_stats_error(exc)
                log.debug('Stats API connect/read failed: %s', exc, exc_info=True)
            finally:
                self.stats_task = None
            await wait_or_stop(self.stop, delay)
            delay = min(5.0, delay*1.5)

    async def configure_game_installs(self):
        async with self.setup_lock:
            active,started_at=await asyncio.to_thread(running_game_info)
            # Executable inspection can be denied while name detection works.
            # On first launch the watcher may not have delivered its state yet.
            running=self.running or active is not None or await asyncio.to_thread(rocket_league_running)
            result=await asyncio.to_thread(self.install_setup.check,copy.deepcopy(self.config),running,active,started_at)
            selected=result['active_path'] or (result['installs'][0]['path'] if result['installs'] else '')
            if selected and selected!=self.config.install_path:
                await self.apply_config({'install_path':selected})
            return copy.deepcopy(result)

    async def setup_loop(self):
        while not self.stop.is_set():
            await self.configure_game_installs()
            await wait_or_stop(self.stop,5)

    async def presence_loop(self):
        while not self.stop.is_set():
            self.refresh()
            if self.custom_discord_factory or (self.config.client_id.isascii() and self.config.client_id.isdigit() and self.config.client_id != '0'):
                await self.publisher.pump()
            await wait_or_stop(self.stop, 0.25)

    async def run(self, on_ready=None):
        loop = asyncio.get_running_loop()
        previous_handlers = {}
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                previous = signal.getsignal(sig)
                signal.signal(sig, lambda *_: loop.call_soon_threadsafe(self.stop.set))
                previous_handlers[sig] = previous
            except (ValueError, OSError):
                pass
        tasks = []
        try:
            detector = (lambda:True) if self.mock_game else rocket_league_running
            tasks = [asyncio.create_task(supervise(name, factory, self.stop), name=name) for name,factory in [
                ('game-watcher',lambda:watch_game(self.set_running,self.stop,detector)),
                ('stats-client',self.stats_loop), ('discord-publisher',self.presence_loop)]]
            if self.auto_setup:
                tasks.append(asyncio.create_task(supervise('automatic-installation',self.setup_loop,self.stop),name='automatic-installation'))
            if on_ready:
                on_ready()
            await self.stop.wait()
        finally:
            self.stop.set()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.publisher.shutdown()
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
            log.info('Presence cleared/IPC closed. Goodbye.')


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Rocket League Discord Rich Presence (official Stats API, read-only)')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--config', type=Path, help='Alternate configuration JSON (default beside launcher/exe)')
    parser.add_argument('--debug', action='store_true', help='DEBUG logs including every raw Stats event name')
    parser.add_argument('--raw-packets', action='store_true', help='Also rotate full JSON in logs/raw_packets.log')
    parser.add_argument('--skip-install', action='store_true', help='Do not discover or patch the game ini')
    parser.add_argument('--mock-game', action='store_true', help='Test with the mock server without RocketLeague.exe')
    parser.add_argument('--console', action='store_true', help='Run without the desktop interface (Ctrl+C to quit)')
    parser.add_argument('--update-ready-file',type=Path,help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    base = app_directory()
    config_path = args.config.resolve() if args.config else base/'config.json'
    configure_logging(base/'logs', debug=args.debug or args.raw_packets, raw=args.raw_packets)
    try:
        # The verification harness uses an isolated, credential-free instance
        # while the user's installed version may still be running.
        mutex = 'Local\\rocket-league-rpc-7b543a5e'
        if os.environ.get('RL_RPC_UI_SMOKE_PATH'):
            mutex = f'Local\\rocket-league-rpc-smoke-{os.getpid()}'
        with SingleInstance(base/'.app.lock',mutex):
            config = load_config(config_path)
            configure_logging(base/'logs', config.log_level, args.debug or args.raw_packets, args.raw_packets)
            if not args.console:
                from .gui import launch
                launch(config,config_path,base/'logs',mock_game=args.mock_game,raw_packets=args.raw_packets,
                       skip_install=args.skip_install,
                       update_ready_file=args.update_ready_file)
                return 0
            if not args.skip_install and not args.mock_game:
                try:
                    running = rocket_league_running()
                except Exception as exc:
                    log.debug('Initial process scan failed: %s', exc)
                    running = False
                setup_install(config, config_path, running)
            log.info('rocket-league-rpc %s. Ctrl+C to quit. Config: %s', __version__, config_path)
            async def console_run():
                import sys
                from .updates import UpdateManager, launch_handoff, relaunch_args, acknowledge_startup
                app = Application(config, config_path, mock_game=args.mock_game, raw_packets=args.raw_packets)
                def ready(staged):
                    launch_handoff(Path(sys.executable), staged, relaunch_args(sys.argv[1:],config_path))
                    loop.call_soon_threadsafe(app.stop.set)
                loop = asyncio.get_running_loop()
                updates = UpdateManager(base, on_ready=ready)
                updates.check()
                await app.run(on_ready=lambda:acknowledge_startup(args.update_ready_file))
            asyncio.run(console_run())
    except AlreadyRunning as exc:
        if args.console:
            print(exc)
        else:
            show_startup_error('RL Presence zaten açık. Yeni sürümü açmadan önce eski RPC uygulamasını kapatın.')
        return 1
    except KeyboardInterrupt:
        return 0
    except (OSError,RuntimeError) as exc:
        log.error('Startup failed: %s. Use a writable app folder.', exc)
        if not args.console:
            show_startup_error(f'Uygulama açılamadı: {exc}\nYazılabilir bir klasör, .NET Framework 4.8 ve WebView2 Runtime kullanın. Ayrıntılar logs/app.log dosyasında.')
        return 1
    return 0


def show_startup_error(message):
    if os.name == 'nt':
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,str(message),'RL Presence',0x10)
    else:
        print(message)


if __name__ == '__main__':
    raise SystemExit(cli())
