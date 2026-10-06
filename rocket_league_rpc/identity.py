"""Local read-only providers and pure lobby matching. No network or game commands."""
from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

STEAM_ID_BASE = 76561197960265728


@dataclass(frozen=True)
class IdentityCandidate:
    primary_id_key: str = ''
    name_hint: str = ''
    source: str = ''
    confidence: str = 'medium'


@dataclass(frozen=True)
class IdentityResolution:
    player: dict
    source: str
    confidence: str


def normalize_primary_id(value):
    if not isinstance(value, str): return None
    parts = value.strip().split('|')
    if len(parts) < 2 or not parts[0].strip() or not parts[1].strip(): return None
    return parts[0].strip().casefold(), parts[1].strip()


def normalize_name(value):
    if not isinstance(value, str): return ''
    value = unicodedata.normalize('NFKC',value)
    value = re.sub(r'^\s*\[[^\]\r\n]{1,32}\]\s*','',value)
    return ' '.join(value.casefold().split())


def steam_id64(account_id):
    return str(STEAM_ID_BASE+account_id) if type(account_id) is int and 0 < account_id <= 0xffffffff else None


def parse_loginusers(content):
    """Strict bounded KeyValues reader; retain only IDs, PersonaName and MostRecent."""
    if not isinstance(content,str) or len(content)>1024*1024: return {}
    content=content.lstrip('\ufeff')
    token=re.compile(r'\s*(?:(//[^\r\n]*)|([{}])|"((?:\\.|[^"\\])*)")')
    tokens=[];position=0
    while position<len(content):
        if not content[position:].strip(): break
        match=token.match(content,position)
        if not match: return {}
        position=match.end()
        if match[1] is not None: continue
        if match[2] is not None: tokens.append((True,match[2]))
        else: tokens.append((False,re.sub(r'\\(["\\])',r'\1',match[3])))
    iterator=iter(tokens)
    def read_object(depth=0,closed=False):
        if depth>16: raise ValueError('nesting')
        result={};seen=set()
        for brace,key in iterator:
            if brace:
                if key=='}' and closed: return result
                raise ValueError('unexpected brace')
            key=key.casefold()
            if key in seen: raise ValueError('duplicate key')
            seen.add(key)
            value_brace,value=next(iterator)
            if value_brace:
                if value!='{': raise ValueError('missing value')
                value=read_object(depth+1,True)
            if key in ('users','personaname','mostrecent') or re.fullmatch(r'\d{17}',key): result[key]=value
        if closed: raise ValueError('missing closing brace')
        return result
    try:
        root=read_object()
        users=root.get('users',{})
        return users if isinstance(users,dict) else {}
    except (ValueError,StopIteration,RecursionError): return {}


def _registry(name):
    import winreg
    key=r'Software\Valve\Steam\ActiveProcess' if name=='ActiveUser' else r'Software\Valve\Steam'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as handle:
        return winreg.QueryValueEx(handle,name)[0]


def _steam_running():
    import psutil
    return any(str(p.info.get('name','')).casefold()=='steam.exe' for p in psutil.process_iter(['name']))


class SteamProvider:
    def __init__(self,registry=None,read_loginusers=None,steam_running=None):
        self.registry=registry or _registry
        self.read_loginusers=read_loginusers or self._read_loginusers
        self.steam_running=steam_running or _steam_running

    def _read_loginusers(self):
        path=self.registry('SteamPath')
        if not isinstance(path,str) or not path: return ''
        file=Path(path)/'config/loginusers.vdf'
        if file.stat().st_size>1024*1024: return ''
        return file.read_text(encoding='utf-8-sig')

    def candidates(self):
        try: users=parse_loginusers(self.read_loginusers())
        except Exception: users={}
        try: active=steam_id64(self.registry('ActiveUser')) if self.steam_running() else None
        except Exception: active=None
        if active:
            persona=users.get(active,{})
            persona=persona.get('personaname','') if isinstance(persona,dict) else ''
            return (IdentityCandidate('Steam|'+active,persona if isinstance(persona,str) else '', 'steam_active','high'),)
        recent=[(uid,item) for uid,item in users.items() if isinstance(item,dict) and item.get('mostrecent')=='1'
                and uid.isdigit() and STEAM_ID_BASE < int(uid) <= STEAM_ID_BASE+0xffffffff]
        if len(recent)!=1: return ()
        uid,item=recent[0];name=item.get('personaname','')
        return (IdentityCandidate('Steam|'+uid,name if isinstance(name,str) else '', 'steam_recent','medium'),)


class EpicCmdlineProvider:
    """Launch parameter spelling remains UNVERIFIED until observed on the host."""
    def __init__(self,snapshot=None):
        if snapshot is None:
            from .game_watcher import sanitized_game_cmdline
            snapshot=sanitized_game_cmdline
        self.snapshot=snapshot

    def candidates(self):
        try:
            data=self.snapshot()
            if not isinstance(data,dict) or not data.get('running') or not data.get('readable'): return ()
            uid=data.get('epicuserid');name=data.get('epicusername')
            if not isinstance(uid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',uid): return ()
            return (IdentityCandidate('Epic|'+uid,name if isinstance(name,str) else '', 'epic_launch','high'),)
        except Exception: return ()


def discover_identity_candidates():
    return EpicCmdlineProvider().candidates()+SteamProvider().candidates()


def resolve_candidates(candidates,players):
    players=[p for p in players if isinstance(p,dict)] if isinstance(players,(list,tuple)) else []
    candidates=[c for c in candidates if isinstance(c,IdentityCandidate)] if isinstance(candidates,(list,tuple)) else []
    # Search every candidate's ID before accepting any candidate's name.
    for candidate in candidates:
        primary=normalize_primary_id(candidate.primary_id_key)
        if primary is None: continue
        matches=[p for p in players if normalize_primary_id(p.get('PrimaryId'))==primary]
        if len(matches)>1:
            exact=[p for p in matches if p.get('PrimaryId')==candidate.primary_id_key]
            matches=exact if len(exact)==1 else []
        if len(matches)==1: return IdentityResolution(matches[0],candidate.source,candidate.confidence)
    for candidate in candidates:
        name=normalize_name(candidate.name_hint)
        if not name: continue
        matches=[p for p in players if normalize_name(p.get('Name'))==name]
        if len(matches)==1: return IdentityResolution(matches[0],candidate.source,'medium')
    return None


def resolve_identity(candidates,players):
    resolution=resolve_candidates(candidates,players)
    return resolution.player if resolution else None
