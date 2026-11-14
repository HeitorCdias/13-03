'use strict';
const $ = id => document.getElementById(id);
let config, hardware, messageIndex=0, lastPresence=Date.now(), photoUrl, cameraBusy=false, weatherBusy=false;
let timerEnd=0, timerRemaining=0, timerRunning=false;
const currencyNumber = n => Number.isFinite(n) ? Math.round(n) : '—';
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {cache:'no-store'} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || 'Falha na solicitação.');
  return value;
}
function localParts() {
  return Object.fromEntries(new Intl.DateTimeFormat('sv-SE',{timeZone:config.fuso,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date()).map(p=>[p.type,p.value]));
}
function tick() {
  if (config) {
    const p=localParts(), hour=Number(p.hour);
    $('clock').textContent=`${p.hour}:${p.minute}`; $('seconds').textContent=p.second;
    $('date').textContent=new Intl.DateTimeFormat('pt-BR',{timeZone:config.fuso,weekday:'long',day:'numeric',month:'long'}).format(new Date());
    $('greeting').textContent=`${hour<12?'Bom dia':hour<18?'Boa tarde':'Boa noite'}, ${config.nome}.`;
    renderAgenda(`${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`);
    const asleep = config.repouso && hardware?.connected && !hardware.demo && Date.now()-lastPresence>60000 && !document.querySelector('dialog[open]');
    $('wake-screen').hidden=!asleep;
  }
  if(timerRunning) {
    timerRemaining=Math.max(0,timerEnd-Date.now());
    if(timerRemaining===0) {timerRunning=false;$('notice').textContent='Seu tempo terminou. ✧';$('timer-pause').textContent='Concluído';$('timer-pause').disabled=true;}
  }
  const seconds=Math.ceil(timerRemaining/1000);
  $('timer-display').textContent=`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;
}
function renderAgenda(now) {
  const items=config.agenda.filter(e=>e.data>=now).sort((a,b)=>a.data.localeCompare(b.data)).slice(0,5);
  $('agenda-list').replaceChildren();
  if(!items.length) {const p=document.createElement('p');p.className='subtle';p.textContent='Sua agenda está livre. Abra espaço para o que importa.';$('agenda-list').append(p);return;}
  for(const item of items) {
    const row=document.createElement('div');row.className='event';
    const time=document.createElement('time');time.textContent=item.data.slice(11);
    const body=document.createElement('div'),title=document.createElement('p'),date=document.createElement('small');
    title.textContent=item.titulo;
    date.textContent=item.data.slice(0,10)===now.slice(0,10)?'Hoje':new Intl.DateTimeFormat('pt-BR',{timeZone:'UTC',day:'numeric',month:'long'}).format(new Date(item.data.slice(0,10)+'T12:00:00Z'));
    body.append(title,date);row.append(time,body);$('agenda-list').append(row);
  }
}
function rotateMessage(){if(config){$('message').textContent=config.mensagens.length?config.mensagens[messageIndex++%config.mensagens.length]:'Seu tempo merece cuidado.';}}
async function refreshHardware() {
  try {
    hardware=await api('/api/state');const t=hardware.telemetry;
    $('connection').textContent=hardware.demo?'DEMONSTRAÇÃO · dados simulados':hardware.connected?'Arduino conectado · USB':'Arduino desconectado';
    $('indoor').textContent=`${currencyNumber(t.temp_c)}°`; $('humidity').textContent=`${currencyNumber(t.humidity)}%`;
    $('presence').textContent=hardware.connected?(t.presence?'Presença detectada':'Sem movimento agora'):'Sensores indisponíveis';
    $('hardware-detail').textContent=hardware.connected?`LED ${Math.round(t.led/255*100)}% · ${t.mode==='auto'?'automático':'manual'}`:hardware.error;
    $('sensor-status').textContent=hardware.connected && (t.temp_c==null || t.humidity==null)?'DHT22 sem leitura. Confira alimentação e pinagem.':'';
    if(!hardware.connected || t.presence) lastPresence=Date.now();
  } catch (_) {$('connection').textContent='Servidor sem resposta';hardware=null;lastPresence=Date.now();}
}
function weatherLabel(code){
  if(code===0)return['☀','Céu limpo'];if([1,2].includes(code))return['☀','Parcialmente nublado'];if(code===3)return['☁','Nublado'];if([45,48].includes(code))return['≋','Nevoeiro'];if(code>=51&&code<=67||code>=80&&code<=82)return['☂','Chuva ou garoa'];if(code>=71&&code<=77||[85,86].includes(code))return['❄','Neve'];if(code>=95)return['ϟ','Trovoadas'];return['◌','Clima indisponível'];
}
function renderWeather(data,cached=false){
  const c=data.current;
  if(!c||!Number.isFinite(c.temperature_2m)||!Number.isFinite(c.relative_humidity_2m)||!Number.isFinite(c.apparent_temperature))throw new Error('Previsão inválida');
  const [icon,label]=weatherLabel(c.weather_code);
  $('weather-icon').textContent=icon;$('outdoor').textContent=`${Math.round(c.temperature_2m)}°`;$('weather-label').textContent=label;
  $('weather-detail').textContent=`Umidade ${Math.round(c.relative_humidity_2m)}% · sensação ${Math.round(c.apparent_temperature)}°`;
  $('weather-status').textContent=`${cached?'Offline · última consulta':'Open-Meteo · atualizado'} ${new Intl.DateTimeFormat('pt-BR',{timeZone:config.fuso,day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(data.savedAt))}`;
}
async function weather(){
  if(!config||weatherBusy)return;weatherBusy=true;
  const key=`weather-touch:${config.latitude}:${config.longitude}`;
  try {
    const q=new URLSearchParams({latitude:config.latitude,longitude:config.longitude,current:'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code',timezone:config.fuso});
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);let data;
    try{const r=await fetch('https://api.open-meteo.com/v1/forecast?'+q,{signal:controller.signal});if(!r.ok)throw new Error('Previsão indisponível');data=await r.json();}finally{clearTimeout(timer);}
    data.savedAt=Date.now();renderWeather(data);try{localStorage.setItem(key,JSON.stringify(data));}catch(_){}
  }catch(_){
    try{const cached=JSON.parse(localStorage.getItem(key));if(!cached||Date.now()-cached.savedAt>86400000)throw new Error();renderWeather(cached,true);}
    catch(_){$('outdoor').textContent='—°';$('weather-icon').textContent='◌';$('weather-label').textContent='Clima indisponível';$('weather-detail').textContent='Confira a conexão de internet.';$('weather-status').textContent='Nova tentativa em 15 minutos.';}
  }finally{weatherBusy=false;}
}
function clearPhoto(){if(photoUrl)URL.revokeObjectURL(photoUrl);photoUrl=null;$('photo').removeAttribute('src');$('photo').hidden=true;$('camera-placeholder').hidden=false;}
document.querySelectorAll('[data-open]').forEach(button=>button.addEventListener('click',()=>{lastPresence=Date.now();if(button.dataset.open==='settings')fillSettings();$(button.dataset.open).showModal();}));
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
$('camera').addEventListener('close',clearPhoto);
$('capture').onclick=async()=>{
  if(cameraBusy)return;cameraBusy=true;$('capture').disabled=true;$('camera-status').textContent='Solicitando foto…';clearPhoto();
  try{const r=await fetch('/api/camera',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirm:true})});if(!r.ok){const d=await r.json();throw new Error(d.error);}const blob=await r.blob();if($('camera').open){photoUrl=URL.createObjectURL(blob);$('photo').src=photoUrl;$('photo').hidden=false;$('camera-placeholder').hidden=true;$('camera-status').textContent='Foto exibida apenas nesta janela.';}}
  catch(e){$('camera-status').textContent=e.message||'Não foi possível consultar a câmera.';}
  finally{cameraBusy=false;$('capture').disabled=false;}
};
$('brightness').oninput=()=>{$('brightness-value').textContent=`${Math.round(Number($('brightness').value)/255*100)}%`;};
async function light(mode,value){try{const result=await api('/api/light',{mode,value});$('light-status').textContent=result.status==='simulado'?'Simulação: nenhum dispositivo acionado.':'Comando enviado. Confira o valor confirmado no painel.';await refreshHardware();}catch(e){$('light-status').textContent=e.message;}}
$('light-manual').onclick=()=>light('manual',Number($('brightness').value));$('light-auto').onclick=()=>light('auto',0);$('light-off').onclick=()=>light('manual',0);
$('timer-start').onclick=()=>{const minutes=Number($('minutes').value);if(!Number.isInteger(minutes)||minutes<1||minutes>180){$('notice').textContent='Informe de 1 a 180 minutos.';return;}timerRemaining=minutes*60000;timerEnd=Date.now()+timerRemaining;timerRunning=true;$('timer-strip').hidden=false;$('timer-pause').disabled=false;$('timer-pause').textContent='Pausar';$('notice').textContent='';$('timer').close();tick();};
$('timer-pause').onclick=()=>{if(timerRunning){timerRemaining=Math.max(0,timerEnd-Date.now());timerRunning=false;$('timer-pause').textContent='Continuar';}else{timerEnd=Date.now()+timerRemaining;timerRunning=true;$('timer-pause').textContent='Pausar';}};
$('timer-stop').onclick=()=>{timerRunning=false;timerRemaining=0;$('timer-strip').hidden=true;};
let nextEvent=0;
function addEvent(item={}){
  if($('event-editors').children.length>=100){$('settings-status').textContent='Limite de 100 eventos.';return;}
  const row=document.createElement('div');row.className='event-editor';const id=nextEvent++;
  const titleLabel=document.createElement('label');titleLabel.textContent='Compromisso';titleLabel.htmlFor='title-'+id;
  const title=document.createElement('input');title.id=titleLabel.htmlFor;title.className='event-title';title.required=true;title.maxLength=150;title.value=item.titulo||'';
  const dateLabel=document.createElement('label');dateLabel.textContent='Data e hora';dateLabel.htmlFor='event-date-'+id;
  const date=document.createElement('input');date.id=dateLabel.htmlFor;date.type='datetime-local';date.className='event-date';date.required=true;date.value=item.data||'';
  const remove=document.createElement('button');remove.type='button';remove.textContent='Remover';remove.onclick=()=>row.remove();row.append(titleLabel,title,dateLabel,date,remove);$('event-editors').append(row);
}
function fillSettings(){if(!config)return;for(const k of ['nome','cidade','latitude','longitude','fuso'])$(k).value=config[k];$('messages').value=config.mensagens.join('\n');$('repouso').checked=config.repouso;$('event-editors').replaceChildren();config.agenda.forEach(addEvent);$('settings-status').textContent='';}
$('add-event').onclick=()=>addEvent();
$('settings-form').onsubmit=async e=>{e.preventDefault();$('save').disabled=true;const data={};for(const k of ['nome','cidade','fuso'])data[k]=$(k).value.trim();for(const k of ['latitude','longitude'])data[k]=Number($(k).value);data.mensagens=$('messages').value.split('\n').map(m=>m.trim()).filter(Boolean);data.repouso=$('repouso').checked;data.agenda=[...document.querySelectorAll('.event-editor')].map(r=>({titulo:r.querySelector('.event-title').value.trim(),data:r.querySelector('.event-date').value}));try{config=await api('/api/config',data);$('city').textContent=config.cidade;tick();rotateMessage();weather();$('settings-status').textContent='Ajustes salvos.';}catch(err){$('settings-status').textContent=err.message;}finally{$('save').disabled=false;}};
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch(_){$('notice').textContent='Use F11 para tela cheia.';}};
document.addEventListener('pointerdown',()=>{lastPresence=Date.now();$('wake-screen').hidden=true;});
async function init(){try{config=await api('/api/config');$('city').textContent=config.cidade;tick();rotateMessage();weather();}catch(e){$('notice').textContent=e.message;document.querySelector('[data-open="settings"]').disabled=true;}}
init();refreshHardware();setInterval(tick,1000);setInterval(refreshHardware,2000);setInterval(rotateMessage,30000);setInterval(weather,900000);window.addEventListener('online',weather);
