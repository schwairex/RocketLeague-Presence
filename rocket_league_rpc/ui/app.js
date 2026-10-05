'use strict';
(() => {
  let bridge=null, persisted=null, draft=null, snapshot=null, busy=false, previewToken=0;
  const $=id=>document.getElementById(id);
  const clone=value=>JSON.parse(JSON.stringify(value));
  const text=(id,value)=>{$(id).textContent=value??'—';};
  const pad=n=>String(n).padStart(2,'0');
  const clock=n=>n==null?'—':`${Math.floor(Math.max(0,n)/60)}:${pad(Math.max(0,n)%60)}`;
  const previewArt=$('preview-image').firstElementChild;
  const fieldArt=previewArt.querySelector('svg').cloneNode(true);
  const logoArt=document.querySelector('#app-frame > div:nth-child(2) svg').cloneNode(true);
  let toastTimer;
  function toast(message,error=false){text('toast',message);$('toast').hidden=false;$('toast').style.borderColor=error?'#FF8F2B':'#3D8BFF';clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,6500);}
  async function invoke(method,...args){
    if(!bridge)throw Error('Masaüstü bağlantısı hazırlanıyor.');
    const result=await bridge[method](...args);
    if(!result||!result.ok)throw Error(result?.error||'İşlem tamamlanamadı.');
    return result.data;
  }
  function hydrate(){
    for(const el of document.querySelectorAll('[data-field]'))el.value=draft[el.dataset.field]??'';
    for(const button of document.querySelectorAll('[data-setting]')){
      const on=!!draft[button.dataset.setting];button.setAttribute('aria-pressed',String(on));
      button.querySelector('.tr').className='tr '+(on?'on':'off');
    }
    const noDivision=['Unranked','Supersonic Legend'].includes(draft.rank_tier);
    document.querySelector('[data-field="rank_division"]').disabled=noDivision;
  }
  function renderPreview(payload){
    const isMap=payload?.large_image&&payload.large_image!=='rl_logo';
    previewArt.replaceChildren((isMap?fieldArt:logoArt).cloneNode(true));
    previewArt.style.background=isMap?'#0E3A2E':'#172040';
    previewArt.title=payload?.large_text||'Rocket League';
    text('preview-details',payload?.details||'Rocket League kapalı');
    text('preview-status',payload?.state||'Oyun açılınca presence etkinleşir.');
    let timer='';
    if(payload?.end)timer=`${clock(Math.ceil(payload.end-Date.now()/1000)).padStart(5,'0')} kaldı`;
    else if(payload?.start)timer=`${clock(Math.round(Date.now()/1000-payload.start))} uzatma`;
    text('preview-timer',timer);
    const team=$('preview-team');team.hidden=!payload?.small_image||payload.small_image==='rl_logo';
    team.style.background=payload?.small_image==='orange'?'#FF8F2B':'#3D8BFF';
    $('discord-preview').title='Kaydedildiğinde gönderilecek içerik. Örnek önizleme Discord’a gönderilmez.';
  }
  async function preview(){
    if(!draft||!bridge)return;
    const token=++previewToken;
    try{const payload=await invoke('preview_settings',draft,$('preview-state').value);if(token===previewToken)renderPreview(payload);}
    catch(e){if(token===previewToken)renderPreview(snapshot?.discord.pending_payload);}
  }
  function pill(id,ok,label){const el=$('pill-'+id);el.querySelector('.dot').style.background=ok?'#3DDC97':'#FFC24D';el.title=label;}
  const phases={MENU:'Menü',COUNTDOWN:'Başlama geri sayımı',PLAYING:'Yayında',GOAL_REPLAY:'Gol tekrarı',PAUSED:'Duraklatıldı',OVERTIME:'Uzatma',ENDED:'Maç bitti',REPLAY_VIEWER:'Tekrar izleniyor',TRAINING:'Eğitim'};
  function statusMessage(s){
    if(!s.game_running)return 'Rocket League kapalı';
    if(!s.stats.connected)return 'Stats API bağlantısı bekleniyor';
    if(s.stats.status==='awaiting_data')return 'Bağlandı · maç verisi bekleniyor';
    return phases[s.match.phase]||s.match.phase;
  }
  function renderDiagnostics(){
    if(!snapshot)return;
    text('diagnostic-status',`${statusMessage(snapshot)} · Son olay: ${snapshot.stats.last_event||'Henüz yok'}${snapshot.stats.error?' · '+snapshot.stats.error:''}`);
    const container=$('player-stats');container.replaceChildren();
    const table=document.createElement('table');const head=document.createElement('tr');
    for(const title of ['Oyuncu','Takım','Puan','Gol','Kurtarış']){const th=document.createElement('th');th.textContent=title;head.append(th);}table.append(head);
    for(const p of snapshot.match.players){const row=document.createElement('tr');for(const value of [p.name,p.team===0?'Mavi':p.team===1?'Turuncu':'—',p.score,p.goals,p.saves]){const td=document.createElement('td');td.textContent=value??'—';row.append(td);}table.append(row);}container.append(table);
    text('diagnostic-json',JSON.stringify({stats:snapshot.stats,match:snapshot.match,discord:snapshot.discord},null,2));
  }
  function render(s){
    snapshot=s;
    pill('discord',s.discord.connected,s.config.client_id?'Discord: '+(s.discord.connected?'bağlı':s.discord.error||'bağlantı bekleniyor'):'Genel sekmesinde Discord Application ID gir.');
    pill('game',s.game_running,s.game_running?'Rocket League çalışıyor':'Rocket League kapalı');
    pill('stats',s.stats.connected&&s.stats.status==='live',statusMessage(s)+(s.stats.error?' · '+s.stats.error:''));
    const m=s.match;const hasMatch=s.stats.connected&&m.phase!=='MENU'&&m.phase!=='REPLAY_VIEWER';
    const competitive=hasMatch&&m.phase!=='TRAINING';
    text('blue-score',competitive?m.blue_score:'—');text('orange-score',competitive?m.orange_score:'—');
    text('match-clock',competitive?(m.is_overtime?'OT':clock(m.time_remaining)):'—');
    text('clock-label',competitive?(m.is_overtime?'uzatma':'kalan süre'):m.phase==='TRAINING'?'eğitim':'veri bekleniyor');
    text('live-map',hasMatch?m.map_name:'—');text('live-mode',hasMatch?m.mode_name:'—');
    const label=$('live-label');label.replaceChildren();const dot=document.createElement('span');dot.className='dot';dot.style.background=hasMatch?'#3DDC97':'#FFC24D';label.append(dot,document.createTextNode(statusMessage(s)));label.style.color=hasMatch?'#3DDC97':'#FFC24D';
    const log=$('log-lines');log.replaceChildren();
    for(const row of (s.logs||[]).slice(-35)){const line=document.createElement('div');const time=document.createElement('span');time.style.color='#5E6A92';time.textContent=`[${row.time}] `;const level=document.createElement('span');level.style.color=row.level==='INFO'?'#3DDC97':row.level==='MAÇ'?'#3D8BFF':'#FF8F2B';level.textContent=row.level+' ';line.append(time,level,document.createTextNode(`${row.logger?row.logger+': ':''}${row.message}`));log.append(line);}log.scrollTop=log.scrollHeight;
    const port=s.config.stats_transport==='websocket'?s.config.stats_web_port:s.config.stats_port;
    text('footer-status',`Stats API · ${s.config.stats_host}:${port} · ${s.stats.packets_per_second} paket/sn${s.discord.next_send_in>0?' · RPC '+Math.ceil(s.discord.next_send_in)+' sn':''}`);
    text('install-result',s.install_result||'Yolu kaydet, ardından yapılandır. INI değişirse oyunu tamamen yeniden başlat.');
    for(const el of document.querySelectorAll('.version'))el.textContent=s.version||'0.2.0';
    if(!$('diagnostics').hidden&&$('diagnostics').open)renderDiagnostics();
    preview();
  }
  async function refresh(){
    if(busy)return;
    busy=true;
    try{
      const s=await invoke('get_snapshot');
      if(!persisted){persisted=clone(s.config);draft=clone(s.config);const select=$('rank-tier');for(const rank of s.rank_tiers){const option=document.createElement('option');option.value=rank;option.textContent=rank;select.append(option);}hydrate();}
      else if(JSON.stringify(s.config)!==JSON.stringify(persisted)){
        // Keep unsaved user edits, while adopting engine-learned IDs and the
        // installer's discovered path for fields the user hasn't changed.
        for(const key of Object.keys(s.config))if(draft[key]===persisted[key])draft[key]=s.config[key];
        persisted=clone(s.config);hydrate();
      }
      render(s);
    }catch(e){toast(e.message,true);}finally{busy=false;}
  }
  for(const el of document.querySelectorAll('[data-field]'))el.addEventListener('input',()=>{
    if(!draft)return;const key=el.dataset.field;draft[key]=el.type==='number'||key==='rank_division'?Number(el.value):el.value;hydrateTogglesOnly();preview();
  });
  function hydrateTogglesOnly(){document.querySelector('[data-field="rank_division"]').disabled=['Unranked','Supersonic Legend'].includes(draft.rank_tier);}
  for(const button of document.querySelectorAll('[data-setting]'))button.addEventListener('click',()=>{if(!draft)return;draft[button.dataset.setting]=!draft[button.dataset.setting];hydrate();preview();});
  for(const tab of document.querySelectorAll('[data-tab]'))tab.addEventListener('click',()=>{
    for(const other of document.querySelectorAll('[data-tab]'))other.classList.toggle('act',other===tab);
    for(const page of document.querySelectorAll('.tab-content'))page.hidden=page.id!==tab.dataset.tab;
  });
  for(const button of document.querySelectorAll('[data-window]'))button.addEventListener('click',async()=>{try{await invoke('window_action',button.dataset.window);}catch(e){toast(e.message,true);}});
  $('preview-state').addEventListener('change',preview);
  $('cancel').addEventListener('click',()=>{if(!persisted)return;draft=clone(persisted);hydrate();preview();toast('Kaydedilmemiş değişiklikler geri alındı.');});
  $('save').addEventListener('click',async()=>{
    if(!draft)return;const button=$('save');button.disabled=true;
    try{const changes=Object.fromEntries(Object.entries(draft).filter(([key,value])=>value!==persisted[key]));const s=await invoke('save_settings',changes);persisted=clone(s.config);draft=clone(s.config);hydrate();await refresh();toast('Ayarlar kaydedildi. RPC en erken 15 saniyelik pencere açıldığında güncellenir.');}
    catch(e){toast(e.message,true);}finally{button.disabled=false;}
  });
  async function action(id,method){$(id).disabled=true;try{const message=await invoke(method);toast(typeof message==='string'?message:'Günlük klasörü açıldı.');await refresh();}catch(e){toast(e.message,true);}finally{$(id).disabled=false;}}
  $('setup-api').addEventListener('click',()=>action('setup-api','setup_stats_api'));
  $('open-logs').addEventListener('click',()=>action('open-logs','open_logs'));
  $('export-report').addEventListener('click',()=>action('export-report','export_diagnostics'));
  function diagnostics(){renderDiagnostics();$('diagnostics').showModal();}
  $('diagnostics-button').addEventListener('click',diagnostics);$('live-panel').addEventListener('click',diagnostics);
  $('live-panel').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();diagnostics();}});
  $('close-diagnostics').addEventListener('click',()=>$('diagnostics').close());
  function start(api){if(bridge)return;bridge=api;refresh();setInterval(refresh,1000);}
  window.addEventListener('pywebviewready',()=>start(window.pywebview.api));
  if(window.rpcBrowserBridge)start(window.rpcBrowserBridge);
  window.rpcUI={refresh,getDraft:()=>clone(draft)};
})();
