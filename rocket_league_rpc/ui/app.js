'use strict';
(() => {
  let bridge=null, persisted=null, draft=null, snapshot=null, busy=false, previewToken=0, updateNotice='';
  const $=id=>document.getElementById(id);

  const dictionaries=window.RL_TRANSLATIONS;
  const language=()=>draft?.language||persisted?.language||'tr';
  const locale=()=>language()==='en'?'en-US':'tr-TR';
  function t(key,values={}){let message=dictionaries[language()]?.[key]??key;for(const [key,value] of Object.entries(values))message=message.split('{'+key+'}').join(String(value));return message;}
  const staticText=[],staticAttrs=[];
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){const node=walker.currentNode;const key=node.textContent.trim();if(!node.parentElement.closest('script,style,svg,pre,#log-lines')&&dictionaries.tr[key])staticText.push([node,node.textContent,key]);}
  for(const el of document.querySelectorAll('[title],[aria-label],[placeholder]'))for(const attr of ['title','aria-label','placeholder']){const key=el.getAttribute(attr);if(dictionaries.tr[key])staticAttrs.push([el,attr,key]);}
  function applyLanguage(){
    document.documentElement.lang=language();document.title=t('RL Presence – Ana pencere');
    for(const [node,original,key] of staticText)node.textContent=original.replace(key,t(key));
    for(const [el,attr,key] of staticAttrs)el.setAttribute(attr,t(key));
    text('report-button-label',t(reportBusy?'Gönderiliyor…':'Gönder'));
    if(reportFeedback)showReportFeedback(reportFeedback);
  }
  let reportBusy=false,reportFeedback='';
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
    if(!bridge)throw Error(t('Masaüstü bağlantısı hazırlanıyor.'));
    const result=await bridge[method](...args);
    if(!result||!result.ok)throw Error(t(result?.error||'İşlem tamamlanamadı.'));
    return result.data;
  }
  function hydrate(){
    applyLanguage();
    $('application-id').value=draft.client_id||'';
    for(const el of document.querySelectorAll('[data-field]'))el.value=draft[el.dataset.field]??'';
    for(const button of document.querySelectorAll('[data-setting]')){
      const on=!!draft[button.dataset.setting];button.setAttribute('aria-pressed',String(on));
      button.querySelector('.tr').className='tr '+(on?'on':'off');
    }
    hydrateRanks();
  }
  function hydrateRanks(){
    const container=$('mode-ranks');container.replaceChildren();
    for(const [key,name] of Object.entries(snapshot?.ranked_modes||{})){
      draft.mode_ranks??={};
      const rank=draft.mode_ranks[key]??={tier:'Unranked',division:1};const card=document.createElement('div');card.className='rank-card';
      const heading=document.createElement('h3');heading.textContent=name;card.append(heading);
      for(const field of ['tier','division']){
        const label=document.createElement('label');label.textContent=t(field==='tier'?'Rank':'Küme');
        const select=document.createElement('select');select.dataset.rankMode=key;select.dataset.rankField=field;
        select.setAttribute('aria-label',name+' · '+label.textContent);
        for(const value of field==='tier'?snapshot.rank_tiers:[1,2,3,4]){const option=document.createElement('option');option.value=value;option.textContent=field==='tier'?value:['I','II','III','IV'][value-1];select.append(option);}
        select.value=rank[field];select.disabled=field==='division'&&['Unranked','Supersonic Legend'].includes(rank.tier);
        select.title=select.selectedOptions[0]?.textContent||'';
        select.addEventListener('change',()=>{draft.mode_ranks[key][field]=field==='division'?Number(select.value):select.value;select.title=select.selectedOptions[0]?.textContent||'';card.querySelector('[data-rank-field="division"]').disabled=['Unranked','Supersonic Legend'].includes(draft.mode_ranks[key].tier);preview();});
        label.append(select);card.append(label);
      }
      container.append(card);
    }
  }
  const setupMessages={checking:'Rocket League kurulumları otomatik denetleniyor…',ready:'Stats API tüm bulunan kurulumlarda hazır. Oyunu açabilirsin.',restart_required:'Stats API etkinleştirildi. Veri akışı için Rocket League’i tamamen kapatıp yeniden aç.',missing:'Rocket League kurulumu bulunamadı. Genel sekmesinden TAGame içeren klasörü seç.',permission_denied:'Stats API dosyasına yazılamadı. Uygulamayı yönetici olarak açıp yeniden dene.',error:'Stats API yapılandırılamadı. Kurulum yolunu ve günlükleri kontrol et.',manual:'Otomatik kurulum bu oturumda kapalı.'};
  function renderInstallation(info){
    if(!info)return;
    const warning=['restart_required','missing','permission_denied','error'].includes(info.status);
    $('setup-banner').hidden=!warning;text('setup-banner-message',t(setupMessages[info.status]||setupMessages.checking));
    text('install-result',t(setupMessages[info.status]||setupMessages.checking));
    const list=$('installations');list.replaceChildren();
    for(const item of info.installs||[]){
      const card=document.createElement('div');card.className='install-card';const header=document.createElement('header');
      const name=document.createElement('span');name.textContent=t('Kurulum')+(info.active_path===item.path?' · '+t('AKTİF OYUN'):'');
      const status=document.createElement('span');status.className='install-state'+(item.status==='permission_denied'||item.status==='error'?' warning':'');
      status.textContent=t(item.status==='permission_denied'?'Yazma izni gerekli':item.status==='error'?'Kurulum hatası':info.restart_required&&info.active_path===item.path?'Yeniden başlat':'Hazır');
      const path=document.createElement('p');path.textContent=item.path;header.append(name,status);card.append(header,path);list.append(card);
    }
  }
  function renderPreview(payload){
    const isMap=payload?.large_image&&payload.large_image!=='rl_logo';
    previewArt.replaceChildren((isMap?fieldArt:logoArt).cloneNode(true));
    previewArt.style.background=isMap?'#0E3A2E':'#172040';
    previewArt.title=payload?.large_text||'Rocket League';
    text('preview-details',payload?.details||t('Rocket League kapalı'));
    text('preview-status',payload?.state||t('Oyun açılınca presence etkinleşir.'));
    let timer='';
    if(payload?.end)timer=t('{time} kaldı',{time:clock(Math.ceil(payload.end-Date.now()/1000)).padStart(5,'0')});
    else if(payload?.start)timer=t('{time} uzatma',{time:clock(Math.round(Date.now()/1000-payload.start))});
    text('preview-timer',timer);
    const team=$('preview-team');team.hidden=!payload?.small_image||payload.small_image==='rl_logo';
    team.style.background=payload?.small_image==='orange'?'#FF8F2B':'#3D8BFF';
    $('discord-preview').title=t('Kaydedildiğinde gönderilecek içerik. Örnek önizleme Discord’a gönderilmez.');
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
    if(!s.game_running)return t('Rocket League kapalı');
    if(!s.stats.connected)return t('Stats API bağlantısı bekleniyor');
    if(s.stats.status==='awaiting_data')return t('Bağlandı · maç verisi bekleniyor');
    return t(phases[s.match.phase]||s.match.phase);
  }
  function renderDiagnostics(){
    if(!snapshot)return;
    text('diagnostic-status',t('{status} · Son olay: {event}',{status:statusMessage(snapshot),event:snapshot.stats.last_event||t('Henüz yok')})+(snapshot.stats.error?' · '+snapshot.stats.error:''));
    const container=$('player-stats');container.replaceChildren();
    const table=document.createElement('table');const head=document.createElement('tr');
    for(const title of [t('Oyuncu'),t('Takım'),t('Puan'),t('Gol'),t('Kurtarış')]){const th=document.createElement('th');th.textContent=title;head.append(th);}table.append(head);
    for(const p of snapshot.match.players){const row=document.createElement('tr');for(const value of [p.name,p.team===0?t('Mavi'):p.team===1?t('Turuncu'):'—',p.score,p.goals,p.saves]){const td=document.createElement('td');td.textContent=value??'—';row.append(td);}table.append(row);}container.append(table);
    text('diagnostic-json',JSON.stringify({stats:snapshot.stats,match:snapshot.match,discord:snapshot.discord},null,2));
  }
  function render(s){
    snapshot=s;
    pill('discord',s.discord.connected,'Discord: '+(s.discord.connected?t('bağlı'):s.discord.error||t('bağlantı bekleniyor')));
    pill('game',s.game_running,s.game_running?t('Rocket League çalışıyor'):t('Rocket League kapalı'));
    pill('stats',s.stats.connected&&s.stats.status==='live',statusMessage(s)+(s.stats.error?' · '+s.stats.error:''));
    const m=s.match;const hasMatch=s.stats.connected&&m.phase!=='MENU'&&m.phase!=='REPLAY_VIEWER';
    const competitive=hasMatch&&m.phase!=='TRAINING';
    text('blue-score',competitive?m.blue_score:'—');text('orange-score',competitive?m.orange_score:'—');
    text('match-clock',competitive?(m.is_overtime?'OT':clock(m.time_remaining)):'—');
    text('clock-label',competitive?(m.is_overtime?t('uzatma'):t('kalan süre')):m.phase==='TRAINING'?t('eğitim'):t('veri bekleniyor'));
    text('live-map',hasMatch?m.map_name:'—');text('live-mode',hasMatch?m.mode_name:'—');
    const label=$('live-label');label.replaceChildren();const dot=document.createElement('span');dot.className='dot';dot.style.background=hasMatch?'#3DDC97':'#FFC24D';label.append(dot,document.createTextNode(statusMessage(s)));label.style.color=hasMatch?'#3DDC97':'#FFC24D';
    const log=$('log-lines');log.replaceChildren();
    for(const row of (s.logs||[]).slice(-35)){const line=document.createElement('div');const time=document.createElement('span');time.style.color='#5E6A92';time.textContent=`[${row.time}] `;const level=document.createElement('span');level.style.color=row.level==='INFO'?'#3DDC97':row.level==='MAÇ'?'#3D8BFF':'#FF8F2B';level.textContent=row.level+' ';line.append(time,level,document.createTextNode(`${row.logger?row.logger+': ':''}${row.message}`));log.append(line);}log.scrollTop=log.scrollHeight;
    const port=s.config.stats_transport==='websocket'?s.config.stats_web_port:s.config.stats_port;
    text('footer-status',`Stats API · ${s.config.stats_host}:${port} · ${t('{rate} paket/sn',{rate:s.stats.packets_per_second})}${s.discord.next_send_in>0?' · RPC '+t('{seconds} sn',{seconds:Math.ceil(s.discord.next_send_in)}):''}`);
    renderInstallation(s.installation);
    for(const el of document.querySelectorAll('.version'))el.textContent='v'+(s.version||'0.2.3');
    renderUpdates(s.updates);
    if(!$('diagnostics').hidden&&$('diagnostics').open)renderDiagnostics();
    preview();
  }
  function updateMessage(u){
    const messages={idle:'Açılışta otomatik kontrol edilir.',checking:'GitHub sürümleri kontrol ediliyor…',current:'En güncel sürümü kullanıyorsun.',empty:'GitHub üzerinde henüz yayımlanmış sürüm yok.',available:u.automatic?'Yeni sürüm hazır. Otomatik güncelleme başlıyor…':'Kaynak sürümünde EXE güncellemesi uygulanmaz.',downloading:'Yeni sürüm indiriliyor ve doğrulanıyor…',restarting:'Güncelleme hazır; uygulama yeniden açılıyor…',error:'GitHub sürümlerine ulaşılamadı. İnternet bağlantısını ve depoyu kontrol et.',blocked:'Bu sürüm önceki denemede açılamadı. Mevcut sürüm korundu. Tekrar kontrol ederek yeniden deneyebilirsin.'};
    return t(messages[u.status]||messages.idle);
  }
  function renderUpdates(u){
    if(!u)return;
    const titles={idle:t('Sürüm kontrolü hazırlanıyor'),checking:t('Yeni sürümler kontrol ediliyor'),current:t('Güncelsin'),available:t('Yeni sürüm hazır'),downloading:t('Güncelleme indiriliyor'),restarting:t('Yeniden başlatılıyor'),empty:t('İlk sürüm bekleniyor'),error:t('Güncelleme kontrolü tamamlanamadı'),blocked:t('Güncelleme ertelendi')};
    const labels={idle:t('OTOMATİK KONTROL'),checking:t('GITHUB BAĞLANTISI'),current:t('EN GÜNCEL SÜRÜM'),available:'v'+u.latest_version,downloading:t('OTOMATİK GÜNCELLEME'),restarting:t('GÜNCELLEME HAZIR'),empty:'GITHUB RELEASES',error:t('TEKRAR DENEYEBİLİRSİN')};
    text('update-title',titles[u.status]||titles.idle);text('update-status-label',labels[u.status]||labels.idle);text('update-message',updateMessage(u));
    $('check-updates').disabled=['checking','available','downloading','restarting'].includes(u.status)&&u.automatic;
    if(u.status==='checking')$('check-updates').disabled=true;
    $('update-progress-wrap').hidden=!['downloading','restarting'].includes(u.status);
    $('update-progress').value=u.progress||0;text('update-percent',(u.progress||0)+'%');
    text('update-checked',u.checked_at?t('Son kontrol: {time}',{time:new Date(u.checked_at*1000).toLocaleTimeString(locale(),{hour:'2-digit',minute:'2-digit'})}):t('Açılışta otomatik kontrol'));
    const list=$('release-notes');list.replaceChildren();
    for(const release of u.releases||[]){
      const article=document.createElement('article');article.className='release-entry';
      const header=document.createElement('header');const name=document.createElement('span');name.textContent=release.name||'v'+release.version;
      const date=document.createElement('time');date.textContent=release.published?new Date(release.published).toLocaleDateString(locale()):'';header.append(name,date);
      const notes=document.createElement('pre');notes.textContent=release.notes||t('Bu sürüm için not yayımlanmamış.');article.append(header,notes);list.append(article);
    }
    if(!list.children.length){const p=document.createElement('p');p.className='empty-release';p.textContent=u.status==='error'?t('GitHub bağlantısı kurulunca sürüm notları burada görünür.'):t('Yayımlanmış sürümler kontrol sonrası burada görünür.');list.append(p);}
    if(['available','downloading','restarting'].includes(u.status)&&u.latest_version&&updateNotice!==u.latest_version){updateNotice=u.latest_version;toast(t('RL Presence v{version} hazır.',{version:u.latest_version})+' '+(u.automatic?t('Uygulama otomatik güncellenecek ve yeniden açılacak.'):t('Yeni sürümü GitHub sürümlerinden indirebilirsin.')));}
  }
  async function refresh(){
    if(busy)return;
    busy=true;
    try{
      const s=await invoke('get_snapshot');
      if(!persisted){snapshot=s;persisted=clone(s.config);draft=clone(s.config);hydrate();}
      else if(JSON.stringify(s.config)!==JSON.stringify(persisted)){
        // Keep unsaved user edits, while adopting engine-learned IDs and the
        // installer's discovered path for fields the user hasn't changed.
        for(const key of Object.keys(s.config))if(JSON.stringify(draft[key])===JSON.stringify(persisted[key]))draft[key]=clone(s.config[key]);
        persisted=clone(s.config);hydrate();
      }
      render(s);
    }catch(e){toast(e.message,true);}finally{busy=false;}
  }
  for(const el of document.querySelectorAll('[data-field]'))el.addEventListener('input',()=>{
    if(!draft)return;const key=el.dataset.field;draft[key]=el.type==='number'||key==='rank_division'?Number(el.value):el.value;hydrateTogglesOnly();if(key==='language'){applyLanguage();hydrateRanks();if(snapshot)render(snapshot);}preview();
  });
  function hydrateTogglesOnly(){}
  for(const button of document.querySelectorAll('[data-setting]'))button.addEventListener('click',()=>{if(!draft)return;draft[button.dataset.setting]=!draft[button.dataset.setting];hydrate();preview();});
  for(const tab of document.querySelectorAll('[data-tab]'))tab.addEventListener('click',()=>{
    for(const other of document.querySelectorAll('[data-tab]'))other.classList.toggle('act',other===tab);
    for(const page of document.querySelectorAll('.tab-content'))page.hidden=page.id!==tab.dataset.tab;
    $('save').hidden=tab.dataset.tab==='report';$('cancel').hidden=tab.dataset.tab==='report';
  });
  for(const button of document.querySelectorAll('[data-window]'))button.addEventListener('click',async()=>{try{await invoke('window_action',button.dataset.window);}catch(e){toast(e.message,true);}});
  $('preview-state').addEventListener('change',preview);
  $('cancel').addEventListener('click',()=>{if(!persisted)return;draft=clone(persisted);hydrate();preview();toast(t('Kaydedilmemiş değişiklikler geri alındı.'));});
  $('save').addEventListener('click',async()=>{
    if(!draft)return;const button=$('save');button.disabled=true;
    try{const changes=Object.fromEntries(Object.entries(draft).filter(([key,value])=>JSON.stringify(value)!==JSON.stringify(persisted[key])));const s=await invoke('save_settings',changes);persisted=clone(s.config);draft=clone(s.config);hydrate();await refresh();toast(t('Ayarlar kaydedildi. Discord görünümü güncelleniyor.'));}
    catch(e){toast(e.message,true);}finally{button.disabled=false;}
  });
  async function action(id,method){$(id).disabled=true;try{const message=await invoke(method);toast(method==='setup_stats_api'?t(setupMessages[message.status]||setupMessages.error):typeof message==='string'?t(message):t('Günlük klasörü açıldı.'),method==='setup_stats_api'&&['missing','error','permission_denied'].includes(message.status));await refresh();}catch(e){toast(e.message,true);}finally{$(id).disabled=false;}}
  $('setup-details').addEventListener('click',()=>document.querySelector('[data-tab="general"]').click());
  $('setup-api').addEventListener('click',()=>action('setup-api','setup_stats_api'));
  $('open-logs').addEventListener('click',()=>action('open-logs','open_logs'));
  $('export-report').addEventListener('click',()=>action('export-report','export_diagnostics'));
  $('check-updates').addEventListener('click',async()=>{try{renderUpdates(await invoke('check_updates'));}catch(e){toast(e.message,true);}});
  for(const button of document.querySelectorAll('[data-project]'))button.addEventListener('click',async()=>{try{await invoke('open_project',button.dataset.project);}catch(e){toast(e.message,true);}});
  function diagnostics(){renderDiagnostics();$('diagnostics').showModal();}
  $('diagnostics-button').addEventListener('click',diagnostics);$('live-panel').addEventListener('click',diagnostics);
  $('live-panel').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();diagnostics();}});
  $('close-diagnostics').addEventListener('click',()=>$('diagnostics').close());
  const reportMessages={sent:'Raporun için teşekkürler',limited:'Günlük bildirim limitine ulaştın, yarın tekrar dene',invalid:'Başlık veya açıklama geçersiz. Uzunluk kurallarını kontrol et.',validation:'Başlık 5–100, açıklama 10–2000 karakter olmalı.',network:'İnternet bağlantısı kurulamadı veya istek zaman aşımına uğradı. Tekrar dene.',error:'Rapor gönderilemedi. Biraz sonra tekrar dene.',busy:'Rapor gönderimi devam ediyor.'};
  function showReportFeedback(status){
    reportFeedback=status;const el=$('report-feedback');el.hidden=!status;
    if(status){el.textContent=t(reportMessages[status]||reportMessages.error);el.style.color=status==='sent'?'#3DDC97':'#FFBC80';}
  }
  const charCount=value=>Array.from(value).length;
  function reportCounts(){text('report-title-count',charCount($('report-title').value)+' / 100');text('report-description-count',charCount($('report-description').value)+' / 2000');}
  for(const id of ['report-title','report-description'])$(id).addEventListener('input',()=>{$(id).removeAttribute('aria-invalid');reportCounts();if(!reportBusy)showReportFeedback('');});
  $('report-form').addEventListener('submit',async event=>{
    event.preventDefault();if(reportBusy)return;
    const title=$('report-title').value.trim(),description=$('report-description').value.trim();
    const titleOk=charCount(title)>=5&&charCount(title)<=100,descriptionOk=charCount(description)>=10&&charCount(description)<=2000;
    $('report-title').setAttribute('aria-invalid',String(!titleOk));$('report-description').setAttribute('aria-invalid',String(!descriptionOk));
    if(!titleOk||!descriptionOk){showReportFeedback('validation');(!titleOk?$('report-title'):$('report-description')).focus();return;}
    reportBusy=true;showReportFeedback('');$('report-submit').disabled=true;$('report-title').disabled=true;$('report-description').disabled=true;$('report-spinner').hidden=false;$('report-form').setAttribute('aria-busy','true');text('report-button-label',t('Gönderiliyor…'));
    try{const result=await invoke('submit_report',title,description);showReportFeedback(result?.status||'error');if(result?.status==='sent'){$('report-title').value='';$('report-description').value='';reportCounts();}}
    catch(e){showReportFeedback('network');}
    finally{reportBusy=false;$('report-submit').disabled=false;$('report-title').disabled=false;$('report-description').disabled=false;$('report-spinner').hidden=true;$('report-form').removeAttribute('aria-busy');text('report-button-label',t('Gönder'));}
  });
  applyLanguage();
  let refreshInterval;
  function start(api){if(bridge)return;bridge=api;refresh();refreshInterval=setInterval(refresh,1000);}
  window.addEventListener('pywebviewready',()=>start(window.pywebview.api));
  if(window.rpcBrowserBridge)start(window.rpcBrowserBridge);
  window.rpcUI={refresh,getDraft:()=>clone(draft),stop:()=>clearInterval(refreshInterval)};
  window.addEventListener('beforeunload',window.rpcUI.stop);
})();
