"""Explicit development probe. Local/read-only, redacted, no settings or log writes."""
import json
from pathlib import Path
import re
import psutil

from .game_watcher import sanitized_game_cmdline


def _redact(value):
    return '<redacted>' if value else ''


def run_probe(base=None, packet_log=None):
    from .config import app_directory
    base = Path(base) if base else app_directory()
    launch = sanitized_game_cmdline()
    result = {'read_only': True, 'network_requests': 0, 'game': {
        **{key: launch[key] for key in ('running','readable','error','argument_names')},
        'epicusername':launch['epicusername'], 'epicuserid':_redact(launch['epicuserid'])}}
    active_id, steam_path, users = '', None, []
    steam = {'active_user_readable':False,'steam_running':False,'active_id':'',
             'loginusers_readable':False,'most_recent':[],'error':''}
    try:
        steam['steam_running'] = any(str(p.info.get('name','')).casefold()=='steam.exe'
                                     for p in psutil.process_iter(['name']))
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam\ActiveProcess') as key:
            account = winreg.QueryValueEx(key,'ActiveUser')[0]
            if type(account) is int and 0 < account <= 0xffffffff:
                active_id = str(76561197960265728 + account)
                steam['active_user_readable'] = True
                steam['active_id'] = 'Steam|<redacted>'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam') as key:
            value = winreg.QueryValueEx(key,'SteamPath')[0]
            if isinstance(value,str): steam_path = Path(value)
    except (ImportError,OSError,psutil.Error,ValueError) as exc:
        steam['error'] = type(exc).__name__
    if steam_path:
        try:
            file = steam_path/'config/loginusers.vdf'
            if file.stat().st_size > 1024*1024: raise ValueError('oversize')
            content = file.read_text(encoding='utf-8-sig')
            steam['loginusers_readable'] = True
            from .identity import parse_loginusers
            for uid, fields in parse_loginusers(content).items():
                if isinstance(fields,dict):
                    users.append((uid,fields.get('personaname',''),fields.get('mostrecent')=='1'))
            steam['most_recent'] = [{'id':'Steam|<redacted>','persona_name':name,'matches_active_user':uid==active_id}
                                    for uid,name,recent in users if recent]
            steam['users_count'] = len(users)
            steam['active_user_in_loginusers'] = any(uid==active_id for uid,_,_ in users)
            steam['active_user_persona'] = next((name for uid,name,_ in users if uid==active_id),'')
        except (OSError,UnicodeError,ValueError) as exc:
            steam['error'] = type(exc).__name__
    result['steam'] = steam
    logs = [Path(packet_log)] if packet_log else [base/'logs/raw_packets.log', base/'dist/logs/raw_packets.log']
    if not packet_log:
        try:
            for process in psutil.process_iter(['name','exe']):
                if str(process.info.get('name','')).casefold()=='rl-presence.exe' and process.info.get('exe'):
                    logs.append(Path(process.info['exe']).parent/'logs/raw_packets.log')
        except (psutil.Error,OSError): pass
    snapshot, path_used = None, None
    for path in dict.fromkeys(logs):
        try:
            with path.open('rb') as file:
                file.seek(max(0,path.stat().st_size-4*1024*1024))
                lines = file.read().decode('utf-8',errors='replace').splitlines()
            for line in reversed(lines):
                try:
                    message = json.loads(line)
                    if not isinstance(message,dict) or message.get('Event')!='UpdateState': continue
                    data = message.get('Data')
                    if isinstance(data,str): data=json.loads(data)
                    if isinstance(data,dict) and isinstance(data.get('Players'),list) and data['Players']:
                        snapshot,path_used=data,path
                        break
                except (ValueError,RecursionError): continue
            if snapshot: break
        except OSError: continue
    packet = {'found':bool(snapshot),'source':str(path_used) if path_used else '', 'players':[], 'confirmed_local_matches':[]}
    for player in snapshot.get('Players',[]) if snapshot else []:
        if not isinstance(player,dict): continue
        primary = player.get('PrimaryId','')
        pieces = primary.split('|') if isinstance(primary,str) else []
        name = player.get('Name','') if isinstance(player.get('Name'),str) else ''
        platform = pieces[0] if pieces else ''
        mapped = {'name':name,'primary_id':platform+'|<redacted>'+('|'+'|'.join(pieces[2:]) if len(pieces)>2 else ''),
                  'platform':platform,'matches_steam_active':len(pieces)>1 and platform.casefold()=='steam' and pieces[1]==active_id,
                  'matches_epic_launch':len(pieces)>1 and platform.casefold()=='epic' and pieces[1]==launch['epicuserid'] and bool(launch['epicuserid'])}
        packet['players'].append(mapped)
        if mapped['matches_steam_active'] or mapped['matches_epic_launch']:
            mapped={**mapped,'steam_persona':next((n for uid,n,_ in users if len(pieces)>1 and uid==pieces[1]),'')}
            packet['confirmed_local_matches'].append(mapped)
    result['update_state'] = packet
    return result
