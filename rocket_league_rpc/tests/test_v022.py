import json
from dataclasses import replace
from urllib.error import HTTPError, URLError

import pytest

from rocket_league_rpc.config import Config, load_config, save_config, validate_config
from rocket_league_rpc.presence import build_presence
from rocket_league_rpc.state import MatchState, Phase, reduce_event


def test_goal_clock_survives_replay_and_countdown_then_resyncs():
    cfg = Config()
    state = MatchState(phase=Phase.PLAYING, arena='Stadium_P', playlist_id=2,
                       time_remaining=153, clock_end=1153)
    for event, now in [('GoalScored',1000),('GoalReplayStart',1001),
                       ('GoalReplayEnd',1007),('CountdownBegin',1008)]:
        state = reduce_event(state, {'Event':event,'Data':{}}, cfg, now)
        assert state.clock_end is None  # real game clock remains stopped
        payload = build_presence(state,cfg,now)
        assert payload['end'] == 1153
        assert 'Kickoff' not in payload['state'] and 'Goal replay' not in payload['state']
    state = reduce_event(state, {'Event':'UpdateState','Data':{'Game':{
        'TimeSeconds':153,'bReplay':False,'Teams':[{'TeamNum':0,'Score':2},{'TeamNum':1,'Score':1}]}}}, cfg,1009)
    assert 'Blue 2 - 1 Orange' in build_presence(state,cfg,1009)['details']
    assert build_presence(state,cfg,1009)['end'] == 1153
    state = reduce_event(state, {'Event':'RoundStarted','Data':{}},cfg,1010)
    assert build_presence(state,cfg,1010)['end'] == 1163
    assert state.goal_clock_end is None


def test_replay_flag_without_goal_event_preserves_clock():
    state = MatchState(phase=Phase.PLAYING,arena='Park_P',playlist_id=2,clock_end=1153,time_remaining=153)
    state = reduce_event(state,{'Event':'UpdateState','Data':{'Game':{'bReplay':True}}},Config(),1000)
    assert build_presence(state,Config(),1000)['end']==1153
    paused = reduce_event(state,{'Event':'MatchPaused','Data':{}},Config(),1001)
    assert 'end' not in build_presence(paused,Config(),1001)
    assert 'end' not in build_presence(state,Config(show_time=False),1000)


@pytest.mark.parametrize('phase',list(Phase))
def test_activity_name_is_rocket_league_in_every_phase(phase):
    state = MatchState(phase=phase,arena='Stadium_P',playlist_id=2)
    assert build_presence(state,Config(),1000)['name']=='Rocket League'


def test_language_validation_and_persistence(tmp_path):
    assert validate_config({'language':'EN'}).language=='en'
    assert validate_config({'language':False}).language=='tr'
    assert validate_config({'language':'de'}).language=='tr'
    path=tmp_path/'config.json'
    assert save_config(Config(language='en'),path)
    assert load_config(path).language=='en'


class Response:
    def __init__(self,status):self.status=status
    def __enter__(self):return self
    def __exit__(self,*args):pass


@pytest.mark.parametrize('status,code',[(200,'sent'),(429,'limited'),(400,'invalid'),(500,'error'),(302,'error')])
def test_report_request_and_status(status,code):
    from rocket_league_rpc.reports import ReportClient, REPORT_ENDPOINT
    calls=[]
    def send(request,timeout):
        calls.append(request)
        assert timeout==10
        assert request.full_url==REPORT_ENDPOINT
        assert request.method=='POST'
        assert request.get_header('Content-type')=='application/json'
        data=json.loads(request.data)
        assert set(data)=={'title','description','version','os'}
        assert data['title']=='Bir hata 🚀' and data['description']=='Açıklama\niki satır'
        from rocket_league_rpc import __version__
        assert data['version']==__version__ and data['os']
        return Response(status)
    result=ReportClient(send).submit(' Bir hata 🚀 ','Açıklama\niki satır')
    assert result['status']==code and len(calls)==1


@pytest.mark.parametrize('title,description',[('abcd','long description'),('valid','short'),('a'*101,'x'*20),('valid','x'*2001),(None,'x'*20),('🚀'*4,'x'*20)])
def test_invalid_reports_never_make_network_request(title,description):
    from rocket_league_rpc.reports import ReportClient
    def send(*args,**kwargs):raise AssertionError('invalid input reached network')
    assert ReportClient(send).submit(title,description)['status']=='invalid'


@pytest.mark.parametrize('error,code',[(HTTPError('url',429,'limit',{},None),'limited'),(HTTPError('url',400,'bad',{},None),'invalid'),(URLError('offline'),'network'),(TimeoutError(),'network'),(RuntimeError('unexpected'),'error')])
def test_report_failures_do_not_escape(error,code):
    from rocket_league_rpc.reports import ReportClient
    def send(*args,**kwargs):raise error
    assert ReportClient(send).submit('valid title','long description')['status']==code


def test_translations_have_matching_keys_and_report_tab_follows_about():
    from rocket_league_rpc.i18n import TRANSLATIONS
    from rocket_league_rpc.gui import ui_document
    assert set(TRANSLATIONS['tr'])==set(TRANSLATIONS['en'])
    html=ui_document()
    assert html.index('data-tab="about"') < html.index('data-tab="report"')
    assert 'report-title' in html and 'report-description' in html
    assert 'language' in html and 'Şifre veya kişisel bilgi yazmayın.' in html


def test_report_concurrent_submissions_are_rejected_and_lock_recovers():
    import threading
    from rocket_league_rpc.reports import ReportClient
    entered, finish = threading.Event(), threading.Event()
    calls=[]
    def send(*args,**kwargs):
        calls.append(1); entered.set(); assert finish.wait(3)
        return Response(200)
    client=ReportClient(send)
    thread=threading.Thread(target=lambda:client.submit('valid title','long description'))
    thread.start()
    try:
        assert entered.wait(2)
        assert client.submit('another title','another description')['status']=='busy'
        assert len(calls)==1
    finally:
        finish.set();thread.join(3)
    assert client.submit('valid again','long description')['status']=='sent'


def test_worker_redirect_is_not_followed():
    from rocket_league_rpc.reports import _NoRedirect
    from urllib.request import Request
    handler=_NoRedirect()
    assert handler.redirect_request(Request('https://example.org',data=b'private report'),None,
                                    302,'Found',{},'https://other.example') is None


async def test_activity_name_reaches_pypresence_wire():
    from rocket_league_rpc.rpc import DiscordClient
    client=DiscordClient(Config().client_id)
    writes=[]
    class Writer:
        def write(self,data):writes.append(data)
    client.sock_writer=Writer()
    async def output():return {'evt':'SET_ACTIVITY'}
    client.read_output=output
    await client.update(**build_presence(MatchState(),Config(),1000))
    activity=json.loads(writes[0][8:])['args']['activity']
    assert activity['name']=='Rocket League'
    assert activity['status_display_type']==0  # compact profile shows activity name
