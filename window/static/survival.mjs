const stages = [
  ['genesis','Gênesis persistido','Um processo gerou um objeto novo, cifrou os dados e salvou a receita. O controlador reteve apenas a autoridade necessária à recuperação.'],
  ['expanded','Expansão para 20 serviços','Os vinte processos têm PIDs e diretórios próprios. Todos receberam dados por TCP e passaram por leitura e verificação do objeto.'],
  ['restarted','Reinício do sobrevivente','O processo foi encerrado. Outro processo abriu o mesmo diretório, manteve a identidade e recuperou o objeto. A sessão deve mudar.'],
  ['failure_injected','Perda de 19 processos','Dezenove processos foram encerrados e seus diretórios retirados dos caminhos ativos. Apenas um serviço permaneceu disponível.'],
  ['repaired','Reparo pelo supervisor','O supervisor consultou os serviços, identificou os indisponíveis e criou substitutos vazios. O único sobrevivente forneceu os dados; cada destino foi verificado.'],
  ['survivor_removed','Retirada do último original','O último sobrevivente original também foi encerrado. Os dezenove substitutos demonstraram capacidade de reconstrução sem ele.'],
  ['second_repair','Segundo ciclo de reparo','Uma nova observação detectou a falha do antigo sobrevivente e recompôs o vigésimo serviço a partir dos substitutos.'],
  ['restart_all','Reinício completo','Todos os vinte processos foram encerrados e reabertos. Cada serviço reconstruiu o objeto individualmente, usando somente seu próprio armazenamento.'],
  ['wrong_key','Chave errada recusada','Um processo de recuperação recebeu uma chave alterada. Deve terminar com erro, sem publicar um objeto como resultado válido.'],
  ['missing_content','Perda de informação recusada','Uma unidade indispensável foi retirada de todos os vinte nós. Mesmo com chave e hash corretos, a recuperação deve falhar.'],
  ['complete','Auditoria da execução','As etapas terminaram. O servidor audita a sequência, as mortes de processos, os reinícios e os hashes antes de declarar o conjunto aprovado.']
];
const $ = id => document.getElementById(id);
let state = {events: []}, token = '', selected = null, signature = '';
function element(tag, text, className) {
  const node = document.createElement(tag); node.textContent = text;
  if (className) node.className = className;
  return node;
}
function inspect(event) {
  const index = stages.findIndex(s => s[0] === event.kind), data = event.data;
  $('step-number').textContent = `ETAPA ${index + 1} · ${event.elapsed_seconds.toFixed(2)} s desde o início`;
  $('step-title').textContent = stages[index][1]; $('explanation').textContent = stages[index][2];
  $('raw').textContent = JSON.stringify(data, null, 2);
  const repair = data.repair || data.verification || data.checks?.[0];
  let nodes = data.nodes instanceof Array ? data.nodes : data.after instanceof Array ? data.after :
    data.observations || data.killed || repair?.targets?.map(t => t.node) || (data.node ? [data.node] : []);
  $('node-phase-control').hidden = !data.observations;
  if (data.observations && $('node-phase').value === 'after') {
    const replacements = repair?.targets.map((t,i) => ({...t.node,slot:data.failed_slots[i],state:'verified'})) || [];
    nodes = [...data.observations.filter(n => n.state === 'alive'), ...replacements].sort((a,b) => a.slot-b.slot);
  }
  $('nodes').replaceChildren(...nodes.map((n, i) => {
    const dead = n.state === 'unavailable' || event.kind === 'failure_injected';
    const cell = element('div', '', `node${dead ? ' dead' : ''}`);
    cell.append(element('strong', `Nó ${n.slot ?? i}`), element('span', dead ? 'Indisponível' : `PID ${n.pid ?? '—'}`),
      element('small', n.node_id?.slice(0, 10) || n.error || '')); return cell;
  }));
  const facts = [];
  if (repair) facts.push(`Objeto: ${repair.object_bytes} bytes · ${repair.verified_steps} operações verificadas`,
    `Destinos verificados nesta chamada: ${repair.verified_targets} · bytes cifrados escritos: ${repair.ciphertext_bytes_written}`);
  if (data.failed_slots) facts.push(`Sobreviventes observados: ${data.survivors} · falhas detectadas: ${data.failed_slots.length}`, `Ciclo medido: ${data.seconds.toFixed(3)} s`);
  if (data.before?.session) facts.push(`Identidade preservada: ${data.before.node_id === data.after.node_id ? 'sim' : 'não'}`, `Sessão mudou: ${data.before.session !== data.after.session ? 'sim' : 'não'}`);
  if (data.exit_code !== undefined) facts.push(`Código de saída observado: ${data.exit_code}`, data.error || 'Processo encerrado pelo probe.');
  if (data.checks) facts.push(`${data.checks.length} reconstruções independentes após reinício completo.`);
  $('facts').replaceChildren(...facts.map(f => element('p', f)));
  $('object-panel').hidden = !repair?.object;
  $('object').textContent = repair?.object || '';
  $('hash').textContent = `SHA-256: ${repair?.object_hash || ''}`;
}
function render() {
  const trial = Number($('trial').value), events = state.events.filter(e => e.trial === trial);
  if (selected === null) selected = events.at(-1)?.kind;
  $('steps').replaceChildren(...stages.map(([kind, title], i) => {
    const event = events.find(e => e.kind === kind), button = element('button', `${String(i + 1).padStart(2,'0')}  ${title}`);
    button.disabled = !event; button.setAttribute('aria-current', String(kind === selected));
    button.append(element('small', event ? `Registrado · ${event.elapsed_seconds.toFixed(2)} s` : 'Aguardando execução'));
    button.addEventListener('click', () => { selected = kind; render(); }); return button;
  }));
  const event = events.find(e => e.kind === selected);
  if (event) inspect(event);
  else {
    $('step-number').textContent = 'AGUARDANDO EVIDÊNCIAS'; $('step-title').textContent = 'Nenhuma etapa executada';
    $('explanation').textContent = 'Os resultados desta execução aparecem quando cada operação termina.';
    $('nodes').replaceChildren(); $('facts').replaceChildren(); $('raw').textContent = 'Nenhum evento.';
    $('object-panel').hidden = true; $('object').textContent = ''; $('hash').textContent = '';
    $('node-phase-control').hidden = true;
  }
  const repaired = events.find(e => e.kind === 'repaired');
  $('survivors').textContent = repaired ? `${repaired.data.survivors} / 20` : '—';
  $('repair-time').textContent = repaired ? `${repaired.data.seconds.toFixed(3)} s` : '—';
  $('passed').textContent = state.report ? `${state.report.summary.passed} / ${state.report.summary.runs}` : '—';
}
async function poll() {
  try {
    const response = await fetch('/api/survival/state'); if (!response.ok) throw Error('Falha ao consultar estado');
    state = await response.json(); token = state.token;
    const active = ['running','stopping'].includes(state.status);
    $('start').disabled = active; $('stop').disabled = !active || state.status === 'stopping'; $('runs').disabled = active;
    $('download').hidden = state.status !== 'completed';
    const names = {idle:'Pronto para executar.',running:'Executando processos reais…',stopping:'Encerrando e preservando evidências…',
      completed:'Validação concluída.',failed:'Validação falhou.',stopped:'Execução interrompida.',interrupted:'Execução anterior incompleta.'};
    $('status').textContent = `${names[state.status] || state.status} ${state.run_id || ''} ${state.error || ''}`;
    const next = `${state.run_id}:${state.events.length}:${state.status}`;
    if (signature !== next) {
      const count = Math.max(1, ...state.events.map(e => e.trial + 1)), previous = $('trial').value;
      $('trial').replaceChildren(...Array.from({length:count}, (_,i) => { const o = element('option', `Execução ${i+1}`); o.value = i; return o; }));
      $('trial').value = Number(previous) < count ? previous : '0';
      if (signature.split(':')[0] !== String(state.run_id) || active) selected = null;
      signature = next; render();
    }
  } catch (error) { $('status').textContent = `Conexão indisponível: ${error.message}`; $('start').disabled = true; }
}
async function control(action, body) {
  $('start').disabled = true;
  try {
    const response = await fetch(`/api/survival/${action}`, {method:'POST',headers:{'Content-Type':'application/json','X-Tron-Token':token},body:JSON.stringify(body)});
    const data = await response.json(); if (!response.ok) throw Error(data.error);
    await poll();
  } catch (error) { $('status').textContent = error.message; }
}
$('start').addEventListener('click', () => control('start', {runs:Number($('runs').value)}));
$('stop').addEventListener('click', () => control('stop', {}));
$('trial').addEventListener('change', () => { selected = null; render(); });
$('node-phase').addEventListener('change', render);
await poll(); setInterval(poll, 700);
