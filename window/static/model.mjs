export function shouldAcceptPoll(requestGeneration, currentGeneration, busy) {
  return !busy && requestGeneration === currentGeneration;
}

export function summarize(state) {
  const events = state.events || [];
  const all = kind => events.filter(event => event.kind === kind).map(event => event.data);
  const last = kind => all(kind).at(-1) ?? null;
  const tasks = all('task'), cycles = all('evolution');
  const baseline = tasks.length ? tasks.reduce((sum, task) => sum + task.baseline_divisions, 0) : null;
  const evolved = tasks.length ? tasks.reduce((sum, task) => sum + task.evolved_divisions, 0) : null;
  const evaluation = cycles.reduce((sum, cycle) => sum + cycle.measurement.evaluation_divisions, 0);
  return {
    tasks, cycles, baseline, evolved, evaluation,
    net: baseline === null ? null : baseline - evolved - evaluation,
    correct: tasks.length ? tasks.every(task => task.correct === true) : null,
    strategy: cycles.at(-1)?.strategy ?? last('parent_created')?.strategy ?? null,
    version: cycles.at(-1)?.version ?? last('parent_created')?.version ?? null,
    parent: last('parent_created'), child: last('child_created'),
    learned: last('learned'), restored: last('restored'),
    checkpoint: last('checkpoint'), audit: last('audit_verified'), encoding: last('encoding'),
    completed: state.status === 'completed' && state.report != null,
    report: state.status === 'completed' ? state.report : null,
  };
}

export const labels = {
  started: 'Experiment started', parent_created: 'Parent created', learned: 'Knowledge stored',
  evolution: 'Strategy evaluated', task: 'Workload compared', child_created: 'Child inherited knowledge',
  checkpoint: 'Checkpoint encrypted', restored: 'Child restored', audit_verified: 'Audit chains verified',
  encoding: 'Ternary packing verified', completed: 'Computation finished',
};

export function detail(event) {
  const d = event.data;
  switch (event.kind) {
    case 'started': return `${d.cycles} cycles · ${d.step_delay_ms} ms between steps`;
    case 'parent_created': return `Identity ${d.identity.slice(0, 12)}… · strategy ${d.strategy}`;
    case 'learned': return `Input ${d.input} · ${d.divisions} divisions · retained for inheritance`;
    case 'evolution': return `Cycle ${d.cycle} · ${d.measurement.promoted ? 'promoted' : 'plateau'} · ${d.measurement.evaluation_divisions} evaluation divisions`;
    case 'task': return `${d.input} · ${d.baseline_divisions} → ${d.evolved_divisions} divisions · ${d.correct ? 'outputs match' : 'MISMATCH'}`;
    case 'child_created': return `Generation ${d.generation} · ${d.knowledge_count} inherited item(s)`;
    case 'checkpoint': return `${d.bytes.toLocaleString()} encrypted bytes`;
    case 'restored': return d.child_recalled ? 'Inherited answer recalled after restore' : 'Recall failed';
    case 'audit_verified': return 'Both public signature chains verified against their heads';
    case 'encoding': return `${d.trit_bytes.toLocaleString()} bytes · ${d.roundtrip ? 'exact roundtrip' : 'roundtrip failed'}`;
    case 'completed': return 'Waiting for a clean worker exit before accepting the report';
    default: return '';
  }
}
