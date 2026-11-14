'use strict';
const $ = id => document.getElementById(id);
let eventId = 0;
function addEvent(event = {}) {
  if ($('events').children.length >= 100) { $('save-status').textContent = 'Limite de 100 compromissos.'; return; }
  const id = eventId++;
  const row = document.createElement('div'); row.className = 'event-editor';
  const titleLabel = document.createElement('label'); titleLabel.htmlFor = `title-${id}`; titleLabel.textContent = 'Compromisso';
  const title = document.createElement('input'); title.id = titleLabel.htmlFor; title.className = 'title'; title.required = true; title.maxLength = 150; title.value = event.titulo || '';
  const dateLabel = document.createElement('label'); dateLabel.htmlFor = `date-${id}`; dateLabel.textContent = 'Data e hora';
  const date = document.createElement('input'); date.id = dateLabel.htmlFor; date.className = 'date'; date.type = 'datetime-local'; date.required = true; date.value = event.data || '';
  const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'secondary remove'; remove.textContent = 'Remover compromisso'; remove.onclick = () => row.remove();
  row.append(titleLabel,title,dateLabel,date,remove); $('events').append(row);
}
$('add-event').onclick = () => addEvent();
async function load() {
  try {
    const response = await fetch('/api/config', {cache:'no-store'}); if (!response.ok) throw new Error('Falha ao carregar configuração.');
    const config = await response.json();
    for (const key of ['nome','cidade','latitude','longitude','fuso']) $(key).value = config[key];
    $('mensagens').value = config.mensagens.join('\n'); config.agenda.forEach(addEvent);
    $('save').disabled = false; $('save-status').textContent = '';
  } catch (_) { $('save-status').textContent = 'Não foi possível carregar. Verifique config.json e recarregue esta página.'; }
}
$('settings-form').addEventListener('submit', async e => {
  e.preventDefault(); $('save').disabled = true; $('save-status').textContent = 'Salvando…';
  const config = {};
  for (const key of ['nome','cidade','fuso']) config[key] = $(key).value.trim();
  for (const key of ['latitude','longitude']) config[key] = Number($(key).value);
  config.mensagens = $('mensagens').value.split('\n').map(m => m.trim()).filter(Boolean);
  config.agenda = [...document.querySelectorAll('.event-editor')].map(row => ({titulo:row.querySelector('.title').value.trim(), data:row.querySelector('.date').value}));
  try {
    const response = await fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(config)});
    const data = await response.json(); if (!response.ok) throw new Error(data.erro || 'Não foi possível salvar.');
    $('save-status').textContent = 'Salvo! Volte ao espelho para ver as alterações.';
  } catch (err) { $('save-status').textContent = err.message || 'Não foi possível salvar.'; }
  finally { $('save').disabled = false; }
});
load();
