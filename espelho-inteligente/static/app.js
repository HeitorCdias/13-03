'use strict';
const $ = id => document.getElementById(id);
let config, messageIndex = 0, weatherBusy = false;
const days = ['dom.', 'seg.', 'ter.', 'qua.', 'qui.', 'sex.', 'sáb.'];
function parts() {
  const entries = new Intl.DateTimeFormat('sv-SE', {timeZone: config.fuso, year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit', hourCycle:'h23'}).formatToParts(new Date());
  return Object.fromEntries(entries.map(p => [p.type, p.value]));
}
function tick() {
  if (!config) return;
  const p = parts();
  $('time').textContent = `${p.hour}:${p.minute}`;
  $('seconds').textContent = p.second;
  $('date').textContent = new Intl.DateTimeFormat('pt-BR', {timeZone:config.fuso, weekday:'long', day:'numeric', month:'long'}).format(new Date());
  const hour = Number(p.hour);
  $('greeting').textContent = `${hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite'}, ${config.nome}.`;
  renderAgenda(`${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`);
}
function renderAgenda(now) {
  const items = config.agenda.filter(e => e.data >= now).sort((a,b) => a.data.localeCompare(b.data)).slice(0,5);
  const container = $('agenda'); container.replaceChildren();
  if (!items.length) {
    const empty = document.createElement('p'); empty.className = 'muted';
    empty.textContent = 'Sem compromissos por enquanto. Aproveite o seu tempo.'; container.append(empty); return;
  }
  for (const item of items) {
    const event = document.createElement('div'); event.className = 'event';
    const time = document.createElement('span'); time.className = 'event-time'; time.textContent = item.data.slice(11);
    const body = document.createElement('div');
    const title = document.createElement('p'); title.className = 'event-title'; title.textContent = item.titulo;
    const date = document.createElement('span'); date.className = 'event-date';
    date.textContent = item.data.slice(0,10) === now.slice(0,10) ? 'Hoje' : new Intl.DateTimeFormat('pt-BR', {day:'numeric',month:'long', timeZone:'UTC'}).format(new Date(item.data.slice(0,10)+'T12:00:00Z'));
    body.append(title,date); event.append(time,body); container.append(event);
  }
}
function showMessage() {
  const messages = config?.mensagens || [];
  $('message').textContent = messages.length ? messages[messageIndex++ % messages.length] : 'Um momento para você.';
}
function weatherLabel(code) {
  if (code === 0) return ['☀', 'Céu limpo'];
  if ([1,2].includes(code)) return ['☀', 'Parcialmente nublado'];
  if (code === 3) return ['☁', 'Nublado'];
  if ([45,48].includes(code)) return ['≋', 'Nevoeiro'];
  if ([51,53,55,56,57].includes(code)) return ['☂', 'Garoa'];
  if ([61,63,65,66,67,80,81,82].includes(code)) return ['☂', 'Chuva'];
  if ([71,73,75,77,85,86].includes(code)) return ['❄', 'Neve'];
  if ([95,96,99].includes(code)) return ['ϟ', 'Trovoadas'];
  return ['◌', 'Condição indisponível'];
}
function renderWeather(data, cached = false) {
  const current = data.current;
  if (!current || !Number.isFinite(current.temperature_2m) || !Number.isFinite(current.relative_humidity_2m) || !Number.isFinite(current.apparent_temperature) || !data.daily?.time?.length) throw new Error('Previsão incompleta');
  const [icon, label] = weatherLabel(current.weather_code);
  $('weather-icon').textContent = icon; $('condition').textContent = label;
  $('temperature').textContent = `${Math.round(current.temperature_2m)}°`;
  $('weather-details').textContent = `Umidade ${Math.round(current.relative_humidity_2m)}% · Sensação ${Math.round(current.apparent_temperature)}°`;
  $('forecast').replaceChildren();
  data.daily.time.slice(0,4).forEach((date, i) => {
    const day = document.createElement('div'); day.className = 'forecast-day';
    const name = document.createElement('span'); name.textContent = i === 0 ? 'Hoje' : days[new Date(date+'T12:00:00Z').getUTCDay()];
    const symbol = document.createElement('span'); symbol.textContent = weatherLabel(data.daily.weather_code[i])[0];
    const values = document.createElement('span'); values.textContent = `${Math.round(data.daily.temperature_2m_max[i])}° `;
    const low = document.createElement('span'); low.className = 'low'; low.textContent = `${Math.round(data.daily.temperature_2m_min[i])}°`;
    values.append(low); day.append(name,symbol,values); $('forecast').append(day);
  });
  const timestamp = new Intl.DateTimeFormat('pt-BR', {timeZone: config.fuso, hour:'2-digit',minute:'2-digit', day:'2-digit',month:'2-digit'}).format(new Date(data.savedAt));
  $('weather-status').textContent = `${cached ? 'Sem conexão · última consulta' : 'Open-Meteo · atualizado em'} ${timestamp}`;
}
async function updateWeather() {
  if (!config || weatherBusy) return;
  weatherBusy = true;
  const key = `weather:${config.latitude}:${config.longitude}:${config.fuso}`;
  try {
    const query = new URLSearchParams({latitude:config.latitude, longitude:config.longitude, timezone:config.fuso, current:'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code', daily:'weather_code,temperature_2m_max,temperature_2m_min', forecast_days:'4'});
    const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 12000);
    let data;
    try {
      const response = await fetch(`https://api.open-meteo.com/v1/forecast?${query}`, {signal:controller.signal});
      if (!response.ok) throw new Error('Clima indisponível');
      data = await response.json();
    } finally { clearTimeout(timeout); }
    data.savedAt = Date.now(); renderWeather(data);
    try { localStorage.setItem(key, JSON.stringify(data)); } catch (_) { /* Cache opcional. */ }
  } catch (_) {
    try {
      const cached = JSON.parse(localStorage.getItem(key));
      if (!cached || Date.now() - cached.savedAt > 86400000) throw new Error('Cache expirado');
      renderWeather(cached, true);
    } catch (_) {
      $('temperature').textContent = '--°'; $('weather-icon').textContent = '◌';
      $('condition').textContent = 'Clima indisponível';
      $('weather-details').textContent = 'Umidade — · Sensação —'; $('forecast').replaceChildren();
      $('weather-status').textContent = 'Confira a conexão. Nova tentativa em 15 minutos.';
    }
  } finally { weatherBusy = false; }
}
async function loadConfig() {
  try {
    const response = await fetch('/api/config', {cache:'no-store'});
    if (!response.ok) throw new Error('Configuração indisponível');
    const next = await response.json();
    const changed = !config || ['latitude','longitude','fuso'].some(k => next[k] !== config[k]);
    config = next; $('city').textContent = config.cidade; $('app-status').textContent = '';
    tick(); showMessage(); if (changed) updateWeather();
  } catch (_) { $('app-status').textContent = 'Não foi possível carregar a configuração. Verifique o servidor e config.json.'; }
}
async function fullscreen() {
  try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
  catch (_) { $('app-status').textContent = 'Use F11 ou o modo quiosque para abrir em tela cheia.'; }
}
$('fullscreen').addEventListener('click', fullscreen);
document.addEventListener('keydown', e => { if(e.key.toLowerCase() === 'f') fullscreen(); });
loadConfig(); setInterval(tick, 1000); setInterval(showMessage, 30000);
setInterval(loadConfig, 60000); setInterval(updateWeather, 15 * 60000);
window.addEventListener('online', updateWeather);
