"""Realistic documented envelopes; deliberately fragmented/concatenated TCP.

Run: python -m rocket_league_rpc.mock_stats_server --port 49123 --delay 1
Stop Rocket League first to avoid a port conflict. Never sends API commands.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging

log = logging.getLogger(__name__)
GUID = 'A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6'


def packet(event: str, **data) -> dict:
    return {'Event':event, 'Data':{'MatchGuid':GUID, **data}}


def update_packet(seconds: int, blue: int = 0, orange: int = 0,
                  overtime: bool = False, replay: bool = False, winner: bool = False) -> dict:
    players = []
    for name, ident, side, shortcut in [('PlayerA','Steam|123|0',0,1),('PlayerB','Epic|456|0',1,2)]:
        players.append({'Name':name,'PrimaryId':ident,'Shortcut':shortcut,'TeamNum':side,
                        'Score':blue*100 if side==0 else orange*100,'Goals':blue if side==0 else orange,
                        'Shots':4,'Assists':0,'Saves':1,'Touches':14,'CarTouches':3,'Demos':0,
                        'Loadout':['body_grain','Skin_bartees','Wheel_SoccerBall','Boost_AlphaReward','None','None']})
    return packet('UpdateState', Players=players, Game={
        'Teams':[{'Name':'Blue','TeamNum':0,'Score':blue,'ColorPrimary':'0000FF','ColorSecondary':'0000AA'},
                 {'Name':'Orange','TeamNum':1,'Score':orange,'ColorPrimary':'FF8800','ColorSecondary':'AA4400'}],
        'PlaylistId':11,'TimeSeconds':seconds,'bOvertime':overtime,
        'Ball':{'Speed':850.5,'TeamNum':255 if seconds==300 else 0},
        'bReplay':replay,'bHasWinner':winner,'Winner':'Blue' if winner else '',
        'Arena':'Stadium_P','bHasTarget':True,'Target':{'Name':'PlayerA','Shortcut':1,'TeamNum':0}})


def simulated_match() -> list[dict]:
    messages = [packet('MatchCreated'),packet('PlayerJoined',PlayerName='PlayerA',PrimaryId='Steam|123|0'),
                packet('MatchInitialized'),update_packet(300),packet('CountdownBegin'),packet('RoundStarted')]
    for seconds in [299,298,240,180]:
        messages += [packet('ClockUpdatedSeconds',TimeSeconds=seconds,bOvertime=False),update_packet(seconds)]
    messages += [packet('GoalScored',Scorer={'Name':'PlayerA','Shortcut':1,'TeamNum':0},
                         Assister={'Name':'PlayerC','Shortcut':3,'TeamNum':0},GoalTime=120.0,
                         GoalSpeed=87.3,ImpactLocation={'X':0,'Y':-2944,'Z':320},
                         BallLastTouch={'Player':{'Name':'PlayerA','Shortcut':1,'TeamNum':0},'Speed':125}),
                 packet('GoalReplayStart'), update_packet(180,1,0,replay=True),packet('GoalReplayWillEnd'),
                 packet('GoalReplayEnd'),packet('CountdownBegin'),packet('RoundStarted'),
                 packet('MatchPaused'),update_packet(150,1,0),packet('MatchUnpaused'),
                 packet('ClockUpdatedSeconds',TimeSeconds=1,bOvertime=False),update_packet(1,1,1),
                 packet('ClockUpdatedSeconds',TimeSeconds=0,bOvertime=True),packet('CountdownBegin'),
                 update_packet(0,1,1,overtime=True),packet('RoundStarted')]
    for seconds in [1,2,3,10]:
        messages += [packet('ClockUpdatedSeconds',TimeSeconds=seconds,bOvertime=True),update_packet(seconds,1,1,overtime=True)]
    messages += [packet('GoalScored',Scorer={'Name':'PlayerA','Shortcut':1,'TeamNum':0},GoalTime=10.0,GoalSpeed=900.0),
                 update_packet(10,2,1,overtime=True),packet('MatchEnded',WinnerTeamNum=0),
                 update_packet(10,2,1,overtime=True,winner=True),packet('PodiumStart'),
                 packet('PlayerLeft',PlayerName='PlayerB',PrimaryId='Epic|456|0'),packet('MatchDestroyed')]
    return messages


class MockStatsServer:
    def __init__(self, host='127.0.0.1', port=49123, delay: float = 1.0, encoded_data: bool = False):
        self.host, self.port, self.delay = host, port, delay
        self.server = None
        self.clients = set()
        self.encoded_data = encoded_data

    async def __aenter__(self):
        self.server = await asyncio.start_server(self._handle, self.host, self.port)
        self.port = self.server.sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *_):
        self.server.close()
        await self.server.wait_closed()
        for task in list(self.clients):
            task.cancel()
        await asyncio.gather(*self.clients, return_exceptions=True)

    async def _handle(self, reader, writer):
        task = asyncio.current_task()
        self.clients.add(task)
        try:
            messages = simulated_match()
            if self.encoded_data:
                messages = [{**m,'Data':json.dumps(m['Data'],ensure_ascii=False)} for m in messages]
            for index in range(0,len(messages),2):
                # Two complete objects in one wire stream; fragment through
                # keys, nested objects and UTF-8 sequences with no delimiters.
                wire = b''.join(json.dumps(m,ensure_ascii=False).encode('utf-8') for m in messages[index:index+2])
                cursor = 0
                sizes = [1,7,2,31,3,257,len(wire)]
                for size in sizes:
                    fragment = wire[cursor:cursor+size]
                    cursor += len(fragment)
                    writer.write(fragment)
                    await writer.drain()
                    await asyncio.sleep(0)  # encourage real split reads
                await asyncio.sleep(self.delay)
        except (BrokenPipeError,ConnectionError):
            log.info('Mock client disconnected')
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
            self.clients.discard(task)


async def _serve(args):
    async with MockStatsServer(port=args.port, delay=args.delay,encoded_data=args.encoded_data) as server:
        print(f'Mock Stats API at 127.0.0.1:{server.port}. Each connection replays a new match. Ctrl+C to quit.')
        await server.server.serve_forever()


def cli():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=49123)
    parser.add_argument('--delay',type=float,default=1.0,help='Seconds between pairs of events; 5 gives Discord more time to display phases')
    parser.add_argument('--encoded-data',action='store_true',help='Use JSON-string Data as observed on real Windows TCP packets')
    args=parser.parse_args()
    if not 0<=args.port<=65535 or args.delay<0:
        parser.error('port must be 0-65535 and delay must be nonnegative')
    try:
        asyncio.run(_serve(args))
    except KeyboardInterrupt:
        pass


if __name__=='__main__':
    cli()
