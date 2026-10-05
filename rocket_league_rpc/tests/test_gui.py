import asyncio
from pathlib import Path
import pytest


def test_gui_engine_runs_in_worker_thread_and_shuts_down(tmp_path):
    from rocket_league_rpc.gui import EngineHost, GuiBridge
    from rocket_league_rpc.config import Config
    from .test_runtime import FakeDiscord
    host=EngineHost(Config(),tmp_path/'config.json',mock_game=False,
                    discord_factory=lambda:FakeDiscord(lambda:0))
    host.start()
    try:
        bridge=GuiBridge(host,tmp_path/'logs')
        snap=bridge.get_snapshot()
        assert snap['ok'] and snap['data']['config']['rank_tier']=='Unranked'
        saved=bridge.save_settings({'rank_tier':'Diamond II','rank_division':3,'manual_activity':'shop'})
        assert saved['ok'] and saved['data']['config']['manual_activity']=='shop'
        assert not bridge.save_settings('bad')['ok']
    finally:
        host.close()
    assert not host.thread.is_alive() and host.error is None


def test_html_uses_supplied_assets_and_local_bridge_without_remote_runtime():
    from rocket_league_rpc.gui import ui_document
    html=ui_document()
    assert 'RL <span' in html and 'data-canvas-width="1120"' in html
    assert 'data:font/woff2;base64,' in html
    assert 'pywebview.api' in html and 'Kaydet' in html and 'rank_tier' in html
    assert 'https://fonts.' not in html and 'DCLogic' not in html and '<x-dc>' not in html


async def test_settings_transport_change_cancels_session_without_resetting_rate_floor(tmp_path):
    from rocket_league_rpc.main import Application
    from rocket_league_rpc.config import Config
    app=Application(Config(),tmp_path/'config.json')
    await app.set_running(True)
    app.stats_task=asyncio.create_task(asyncio.sleep(60))
    app.publisher.last_attempt=100
    await app.apply_config({'stats_port':49125})
    await asyncio.gather(app.stats_task,return_exceptions=True)
    assert app.stats_task.cancelled() and app.publisher.last_attempt==100
