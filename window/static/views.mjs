import { labels, detail } from './model.mjs';

export const $ = id => document.getElementById(id);
const text = (id, value) => { $(id).textContent = value; };
const number = value => value == null ? '—' : value.toLocaleString();
const escape = value => String(value).replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
const checked = (id, ok, yes, pending) => {
  text(id, ok ? `✓ ${yes}` : `○ ${pending}`);
  $(id).classList.toggle('positive', Boolean(ok));
};

export function render(state, model) {
  text('baseline', number(model.baseline));
  text('evolved', number(model.evolved));
  text('net', number(model.net));
  $('net').className = model.net === null ? '' : model.net >= 0 ? 'positive' : 'negative';
  text('net-note', model.cycles.length ? `After ${number(model.evaluation)} evaluation divisions` : 'Includes candidate evaluation cost');
  text('correctness', model.correct === null ? 'Waiting' : model.correct ? `${model.tasks.length} / 8` : 'Mismatch');
  $('correctness').className = model.correct === null ? '' : model.correct ? 'positive' : 'negative';
  text('correctness-note', model.tasks.length ? 'Compared inputs · matching factor outputs' : 'No inputs compared yet');
  if (model.correct === false) text('correctness-note', 'A workload comparison failed');
  const statuses = { idle:'Ready to begin', running:'Running', stopping:'Stopping', stopped:'Stopped · partial evidence', failed:'Run failed', completed:'Completed · verified' };
  text('run-status', statuses[state.status]);
  $('run-status').className = `status ${state.status}`;
  text('run-id', state.run_id ? `RUN ${state.run_id}` : 'No run started');
  const latest = state.events.at(-1);
  text('stage-note', state.error || (state.status === 'stopped' ? 'Stopped by you. Collected events remain available.' :
    model.completed ? 'The worker exited successfully. Inspect the evidence below.' :
      latest ? detail(latest) : 'Start an experiment to bring the first TRON into view.'));
  renderLineage(model);
  renderAnalysis(model);
  const completedSteps = [Boolean(model.learned), model.cycles.length === state.cycles,
    model.tasks.length === 8, Boolean(model.restored), model.completed];
  const current = completedSteps.findIndex(done => !done);
  document.querySelectorAll('#journey li').forEach((item, index) => {
    item.classList.toggle('done', completedSteps[index]);
    item.classList.toggle('active', state.status === 'running' && index === current);
  });
}

function renderLineage(m) {
  $('parent-node').classList.toggle('present', Boolean(m.parent));
  $('child-node').classList.toggle('present', Boolean(m.child));
  $('inherit-link').classList.toggle('present', Boolean(m.child));
  text('parent-id', m.parent?.identity ?? 'Identity assigned on creation');
  text('child-id', m.child?.identity ?? 'A distinct identity, shared knowledge');
  text('parent-state', m.parent ? 'Created' : 'Awaiting birth');
  text('child-state', m.restored ? 'Restored & recalled' : m.child ? 'Created' : 'Awaiting parent');
  text('strategy', m.strategy ?? '—');
  text('version', number(m.version));
  text('knowledge', number(m.learned?.knowledge_count));
  text('inherited', number(m.child?.knowledge_count));
  text('restored', m.restored ? 'Yes' : '—');
  text('recall', m.restored ? m.restored.child_recalled ? 'Verified' : 'Failed' : '—');
  checked('audit-check', m.audit?.verified, 'Both audit chains verified', 'Audit pending');
  checked('snapshot-check', m.checkpoint, `${number(m.checkpoint?.bytes)} encrypted bytes`, 'Checkpoint pending');
  checked('encoding-check', m.encoding?.roundtrip,
    `${number(m.encoding?.trit_bytes)} / ${number(m.encoding?.two_bit_bytes)} payload bytes`, 'Encoding pending');
}

function renderAnalysis(m) {
  text('cycle-count', `${m.cycles.length} CYCLES`);
  $('evolution-body').innerHTML = m.cycles.length ? m.cycles.map(c => `<tr>
    <td>${escape(c.cycle)}</td><td>${escape(c.strategy)}</td>
    <td>${number(c.measurement.evaluation_divisions)}</td>
    <td><span class="decision ${c.measurement.promoted ? '' : 'plateau'}">${c.measurement.promoted ? '↑ Promoted' : 'Plateau'}</span></td></tr>`).join('') :
    '<tr><td colspan="4" class="empty">Candidate evaluations will appear here.</td></tr>';
  const max = Math.max(1, ...m.tasks.flatMap(t => [t.baseline_divisions, t.evolved_divisions]));
  $('work-chart').innerHTML = m.tasks.length ? m.tasks.map(t => `<div class="chart-row" aria-label="Input ${escape(t.input)}: baseline ${t.baseline_divisions}, evolved ${t.evolved_divisions} divisions">
    <span>${escape(t.input)}</span><div class="bar-pair"><div class="bar" style="width:${100 * t.baseline_divisions / max}%"></div>
    <div class="bar evolved" style="width:${100 * t.evolved_divisions / max}%"></div></div>
    <span class="chart-value">${number(t.baseline_divisions)} / <b>${number(t.evolved_divisions)}</b></span></div>`).join('') :
    '<p class="empty">Eight held-out inputs will be compared here.</p>';
  const r = m.report;
  text('timing-note', r ? `Baseline ${(r.baseline_task_ns / 1000).toFixed(1)} µs · Evolved ${(r.evolved_task_ns / 1000).toFixed(1)} µs + evolution ${(r.evolution_ns / 1000).toFixed(1)} µs. Display delays excluded.` : 'Compute timings appear after a completed run.');
}

export function renderEvents(state, selected, filter) {
  text('event-count', state.events.length);
  const list = $('event-list');
  const nearBottom = list.scrollTop + list.clientHeight >= list.scrollHeight - 60;
  const scroll = list.scrollTop;
  const filtered = state.events.filter(e => filter === 'all' || e.kind === filter ||
    (filter === 'lineage' && ['parent_created', 'learned', 'child_created', 'checkpoint', 'restored', 'audit_verified'].includes(e.kind)));
  list.innerHTML = filtered.length ? filtered.map(e => `<button type="button" class="event-row ${selected === e.sequence ? 'selected' : ''}" data-sequence="${e.sequence}" aria-pressed="${selected === e.sequence}">
    <time>${(e.elapsed_ms / 1000).toFixed(2)}s</time><span class="event-dot"></span>
    <span><strong>${escape(labels[e.kind] ?? e.kind)}</strong><small>${escape(detail(e))}</small></span></button>`).join('') :
    `<div class="empty event-empty"><span class="empty-symbol">⌁</span><h3>${state.events.length ? 'No matching events yet.' : 'A clear view of every step.'}</h3><p>${state.events.length ? 'Try another filter or let the experiment continue.' : 'Start a run. Its activity will appear here as it happens.'}</p></div>`;
  list.scrollTop = nearBottom ? list.scrollHeight : scroll;
  const chosen = state.events.find(e => e.sequence === selected);
  text('inspect-title', chosen ? labels[chosen.kind] : 'Nothing selected yet');
  text('inspect-note', chosen ? `Event ${chosen.sequence + 1} · ${(chosen.elapsed_ms / 1000).toFixed(3)}s since start (includes pacing)` : 'Choose an event from the timeline.');
  text('inspect-data', chosen ? JSON.stringify(chosen.data, null, 2) : 'Public event data only.\nPrivate keys and payload openings stay in the engine.');
}
