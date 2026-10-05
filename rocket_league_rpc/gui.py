"""Offline HTML desktop window, with a thread-safe bridge to the RPC engine."""
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import asdict
import json
import logging
import os
from pathlib import Path
import threading
import time

from . import __version__
from .config import Config, RANK_TIERS, ACTIVITIES
from .modes import RANKED_MODES
from .main import Application
from .updates import UpdateManager, PROJECT_URL, RELEASES_URL, launch_handoff, relaunch_args, acknowledge_startup

log = logging.getLogger(__name__)


def startup_update_check(updates):
    # pywebview.Event stores callback results in a set. Do not return check()'s
    # dict: that caused the startup "unhashable type: dict" error.
    updates.check()


class UiLogHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.rows = deque(maxlen=100)

    def emit(self, record):
        with self.lock:
            self.rows.append({'time':time.strftime('%H:%M:%S',time.localtime(record.created)),
                              'level':record.levelname,'logger':record.name.rsplit('.',1)[-1],
                              'message':record.getMessage()})

    def snapshot(self):
        with self.lock:
            return list(self.rows)


class EngineHost:
    def __init__(self, config: Config, config_path: Path, **options):
        self.config, self.config_path, self.options = config, config_path, options
        self.loop = None
        self.app = None
        self.error = None
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run,name='rpc-engine',daemon=True)

    def _run(self):
        async def run():
            self.loop = asyncio.get_running_loop()
            self.app = Application(self.config,self.config_path,**self.options)
            self.ready.set()
            await self.app.run()
        try:
            asyncio.run(run())
        except Exception as exc:
            self.error = exc
            self.ready.set()
            log.exception('RPC engine stopped unexpectedly')

    def start(self):
        self.thread.start()
        if not self.ready.wait(5) or self.error:
            raise RuntimeError(f'RPC engine could not start: {self.error}')

    def call(self, coroutine):
        if self.loop is None or not self.thread.is_alive():
            coroutine.close()
            raise RuntimeError(f'RPC engine is unavailable: {self.error}')
        future = asyncio.run_coroutine_threadsafe(coroutine,self.loop)
        try:
            return future.result(timeout=12)
        except TimeoutError:
            future.cancel()
            raise RuntimeError('RPC engine response timed out')

    def close(self):
        if self.loop and self.thread.is_alive():
            self.loop.call_soon_threadsafe(self.app.stop.set)
            if threading.current_thread() is not self.thread:
                self.thread.join(10)


class GuiBridge:
    def __init__(self, host: EngineHost, log_dir: Path, handler=None, updates=None):
        # pywebview recursively inspects public attributes for JS exports.
        # Keep engine/thread/native-window objects private to the bridge.
        self._host, self._log_dir = host, log_dir
        self._handler = handler or UiLogHandler()
        self._window = None
        self._maximized = False
        self._install_result = ''
        self._version = __version__
        self._updates = updates
        from .reports import ReportClient
        self._reports = ReportClient()

    def submit_report(self, title, description):
        # pywebview executes JS API calls on background threads. Never block the
        # UI or the asyncio game/RPC engine while waiting for the Worker.
        return self._result(lambda: self._reports.submit(title, description))

    def _result(self, operation):
        try:
            return {'ok':True,'data':operation()}
        except Exception as exc:
            log.error('UI operation failed: %s',exc)
            return {'ok':False,'error':str(exc)}

    async def _snapshot(self):
        result = self._host.app.snapshot()
        result.update(logs=self._handler.snapshot(),rank_tiers=list(RANK_TIERS),
                      ranked_modes={key:label for key,(_,label) in RANKED_MODES.items()},
                      activities=ACTIVITIES,version=self._version,install_result=self._install_result)
        result['updates'] = self._updates.snapshot() if self._updates else None
        return result

    def check_updates(self):
        return self._result(lambda: self._updates.check(retry_failed=True) if self._updates else None)

    def open_project(self, page='project'):
        def open_page():
            import webbrowser
            urls = {'project': PROJECT_URL, 'releases': RELEASES_URL,
                    'stats': 'https://www.rocketleague.com/developer/stats-api'}
            if page not in urls:
                raise ValueError('Unknown project page')
            return webbrowser.open(urls[page])
        return self._result(open_page)

    def get_snapshot(self):
        return self._result(lambda:self._host.call(self._snapshot()))

    def save_settings(self, changes):
        return self._result(lambda:self._host.call(self._host.app.apply_config(changes)))

    def preview_settings(self, changes, scenario='live'):
        from dataclasses import replace
        from .config import validate_config
        from .presence import build_presence
        from .state import MatchState, Phase
        async def preview():
            app = self._host.app
            cfg = validate_config({**asdict(app.config),**changes})
            state = app.state if app.connected else MatchState()
            now = app.wall_clock()
            if scenario != 'live':
                state = MatchState(phase=Phase.PLAYING,arena='Stadium_P',playlist_id=11,
                    blue_score=2,orange_score=1,time_remaining=222,clock_end=now+222,local_team=0)
                if scenario == 'menu':state=MatchState()
                elif scenario == 'ended':state=replace(state,phase=Phase.ENDED,winner_team=0,ended_at=now,clock_end=None)
                elif scenario == 'replay':state=MatchState(phase=Phase.REPLAY_VIEWER)
            payload = build_presence(state,cfg,now) if app.running or scenario != 'live' else None
            return payload
        return self._result(lambda:self._host.call(preview()))

    def setup_stats_api(self):
        return self._result(lambda:self._host.call(self._host.app.configure_game_installs()))

    def open_logs(self):
        def open_folder():
            self._log_dir.mkdir(parents=True,exist_ok=True)
            os.startfile(str(self._log_dir.resolve()))
            return True
        return self._result(open_folder)

    def export_diagnostics(self):
        def export():
            snapshot = self._host.call(self._snapshot())
            self._log_dir.mkdir(parents=True,exist_ok=True)
            path = self._log_dir/'diagnostics.json'
            path.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
            return str(path.resolve())
        return self._result(export)

    def window_action(self, action):
        def perform():
            if self._window is None:
                return False
            if action == 'minimize':
                self._window.minimize()
            elif action == 'maximize':
                if self._maximized:
                    self._window.restore()
                else:
                    self._window.maximize()
                self._maximized = not self._maximized
            elif action == 'close':
                self._window.destroy()
            else:
                raise ValueError('Unknown window action')
            return True
        return self._result(perform)


def ui_document() -> str:
    from .i18n import TRANSLATIONS
    folder = Path(__file__).resolve().parent/'ui'
    html = (folder/'index.html').read_text(encoding='utf-8')
    translations = json.dumps(TRANSLATIONS,ensure_ascii=False).replace('<','\\u003c')
    return html.replace('<!--APP_SCRIPT-->', '<script>window.RL_TRANSLATIONS='+translations+';</script><script>'+(folder/'app.js').read_text(encoding='utf-8')+'</script>')


def launch(config, config_path, log_dir, mock_game=False, raw_packets=False, update_ready_file=None, skip_install=False):
    import webview
    import ctypes
    import sys
    if os.name == 'nt':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('schwairex.RLPresence')
    handler = UiLogHandler()
    logging.getLogger().addHandler(handler)
    smoke_path = os.environ.get('RL_RPC_UI_SMOKE_PATH')
    options = {'auto_setup':not (smoke_path or skip_install or mock_game)}
    if smoke_path:
        # Native release QA must never write to the user's actual Discord pipe.
        class SmokeDiscord:
            async def connect(self): pass
            async def update(self, **payload): pass
            async def clear(self): pass
            async def close(self): pass
        options['discord_factory'] = SmokeDiscord
    host = EngineHost(config,config_path,mock_game=mock_game,raw_packets=raw_packets,**options)
    host.start()
    updates = UpdateManager(Path(sys.executable).parent if getattr(sys,'frozen',False) else config_path.parent)
    bridge = GuiBridge(host,log_dir,handler,updates)
    report_requests=[]
    if smoke_path:
        from .reports import ReportClient
        class SmokeResponse:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
        def report_send(request,timeout):
            report_requests.append({'headers':dict(request.header_items()),'data':json.loads(request.data),'timeout':timeout,'url':request.full_url})
            time.sleep(.3)
            return SmokeResponse()
        bridge._reports=ReportClient(report_send)
        # Exercise the same loaded-event callback without a live update.
        updates.check=lambda:{'status':'checking'}
    try:
        window = webview.create_window('RL Presence',html=ui_document(),js_api=bridge,
            width=1120,height=760,min_size=(940,680),frameless=True,easy_drag=False,
            background_color='#0A0F1F',text_select=True)
        bridge._window = window
        def apply_update(staged):
            launch_handoff(Path(sys.executable),staged,relaunch_args(sys.argv[1:],config_path))
            host.close()
            window.destroy()
        updates.on_ready = apply_update
        def healthy_startup():
            if update_ready_file is not None and window.evaluate_js('!!window.rpcUI') and bridge.get_snapshot()['ok']:
                acknowledge_startup(update_ready_file)
        window.events.loaded += healthy_startup
        window.events.closed += host.close
        def fit_initial_window():
            # WinForms changes ClientSize when removing its native frame;
            # apply the requested design dimensions after it is frameless.
            window.resize(1120,760)
            window.events.shown -= fit_initial_window
        window.events.shown += fit_initial_window
        # Only the release verification harness sets this environment variable.
        if smoke_path:
            def smoke():
                time.sleep(2)
                try:
                    window.evaluate_js("document.querySelector('[data-tab=report]').click();document.getElementById('report-title').value='Native release verification';document.getElementById('report-description').value='Isolated mocked report from the packaged desktop application.';document.getElementById('report-form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));")
                    time.sleep(.1)
                    loading=window.evaluate_js("document.getElementById('report-submit').disabled && !document.getElementById('report-spinner').hidden")
                    time.sleep(.8)
                    dom = window.evaluate_js("JSON.stringify({language:document.documentElement.lang,reportApi:typeof window.pywebview.api.submit_report==='function',reportTabAfterAbout:Array.from(document.querySelectorAll('[data-tab]')).map(e=>e.dataset.tab).join(',').includes('about,report'),title:document.title,ready:!!window.rpcUI,body:document.body.innerText,frame:[innerWidth,innerHeight],identityReadonly:document.getElementById('application-id').readOnly,identity:document.getElementById('application-id').value,remote:Array.from(document.querySelectorAll('script[src],link[href]')).map(e=>e.src||e.href)})")
                    form=window.evaluate_js("JSON.stringify({feedback:document.getElementById('report-feedback').textContent,title:document.getElementById('report-title').value,description:document.getElementById('report-description').value,rankCards:document.querySelectorAll('.rank-card').length,developers:document.getElementById('about').textContent})")
                    Path(smoke_path).write_text(json.dumps({'dom':json.loads(dom),'bridge':bridge.get_snapshot(),'report':{'loading':loading,'form':json.loads(form),'requests':report_requests}},ensure_ascii=False,indent=2),encoding='utf-8')
                    window.evaluate_js('window.rpcUI.stop()')
                finally:
                    window.destroy()
            window.events.loaded += lambda:threading.Thread(target=smoke,daemon=True).start()
        window.events.loaded += lambda:startup_update_check(updates)
        webview.start(gui='edgechromium',private_mode=True,icon=str(Path(__file__).parent/'ui'/'app.ico'))
    finally:
        host.close()
        logging.getLogger().removeHandler(handler)
