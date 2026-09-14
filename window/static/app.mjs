import { summarize, shouldAcceptPoll } from './model.mjs';
import { $, render, renderEvents } from './views.mjs';

let state = { status:'idle', events:[], report:null, run_id:null };
let token = '', connected = false, busy = false, selected = null, signature = '';
let pollTimer;
let generation = 0;

function controls() {
  const active = ['running', 'stopping'].includes(state.status);
  $('start').disabled = !connected || busy || active;
  $('stop').disabled = !connected || busy || state.status !== 'running';
  $('cycles').disabled = busy || active;
  $('pace').disabled = busy || active;
  $('export-events').disabled = !connected || !state.events.length;
  $('export-report').disabled = !connected || state.status !== 'completed' || !state.report;
}

function error(message = '') {
  $('control-error').textContent = message;
  $('control-error').hidden = !message;
}

function connection(ok) {
  connected = ok;
  $('connection').className = `connection ${ok ? 'online' : 'offline'}`;
  $('connection').innerHTML = `<i></i>${ok ? 'Engine connected' : 'Reconnecting…'}`;
  controls();
}

function accept(next) {
  if (next.token) token = next.token;
  if (state.run_id !== next.run_id) selected = null;
  state = next;
  const nextSignature = `${state.run_id}:${state.status}:${state.events.length}`;
  if (nextSignature !== signature) {
    signature = nextSignature;
    render(state, summarize(state));
    renderEvents(state, selected, $('event-filter').value);
    if (state.error) error(state.error);
  }
  controls();
}

async function request(path, options = {}) {
  const response = await fetch(path, { ...options, signal:AbortSignal.timeout(5000) });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}

async function poll() {
  const requestGeneration = generation;
  try {
    const next = await request('/api/state');
    connection(true);
    // A response fetched before a control mutation must not replace its newer state.
    if (shouldAcceptPoll(requestGeneration, generation, busy)) accept(next);
  } catch {
    connection(false);
  } finally {
    pollTimer = setTimeout(poll, connected ? 200 : 1000);
  }
}

async function action(path, payload) {
  if (busy) return;
  generation += 1;
  busy = true;
  error();
  controls();
  try {
    const next = await request(path, { method:'POST',
      headers:{ 'Content-Type':'application/json', 'X-Tron-Token':token }, body:JSON.stringify(payload) });
    accept(next);
  } catch (failure) {
    error(failure.message);
  } finally {
    busy = false;
    generation += 1;
    controls();
  }
}

$('controls').addEventListener('submit', event => {
  event.preventDefault();
  if (!$('controls').reportValidity()) return;
  action('/api/start', { cycles:Number($('cycles').value), delay_ms:Number($('pace').value) });
});
$('stop').addEventListener('click', () => action('/api/stop', {}));
$('event-filter').addEventListener('change', () => renderEvents(state, selected, $('event-filter').value));
$('event-list').addEventListener('click', event => {
  const row = event.target.closest('[data-sequence]');
  if (!row) return;
  selected = Number(row.dataset.sequence);
  renderEvents(state, selected, $('event-filter').value);
});
$('export-events').addEventListener('click', () => { window.location.href = '/api/events'; });
$('export-report').addEventListener('click', () => { window.location.href = '/api/report'; });
window.addEventListener('pagehide', () => clearTimeout(pollTimer));
poll();
