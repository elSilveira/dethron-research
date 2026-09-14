const $ = id => document.getElementById(id);
const names = {intact:['Duas rotas íntegras','Duas cadeias sustentam a mesma conclusão.'],lost_a:['Rota A removida','A rota B precisa sustentar a reconstrução sozinha.'],lost_essential:['Evidência indispensável removida','Nenhuma rota completa: a resposta deve ser UNKNOWN.'],conflict:['Rotas em conflito','Conclusões diferentes exigem abstenção.']};
let token, signature;
function element(tag, text, cls) { const node = document.createElement(tag); if(text !== undefined) node.textContent=text; if(cls) node.className=cls; return node; }
function output(label,value,bad=false) {const node=element('div',label,`output${bad?' bad':''}`);node.append(element('strong',value));return node;}
function renderCases(rows) {
  $('cases').replaceChildren();
  for(const [id,[title,note]] of Object.entries(names)) {
    const row=rows.find(r=>r.id===id), card=element('article',undefined,'case');card.dataset.case=id;
    card.append(element('h2',title),element('p',note,'note'));
    if(!row) card.append(element('p','Aguardando cálculo real…','pending'));
    else {
      if(id==='lost_a'||id==='lost_essential') card.append(element('div','Rota A · ausente','route missing'));
      for(const route of row.routes) {
        const incomplete=route.sources.length<2, box=element('div',undefined,`route${incomplete?' missing':''}`);
        for(const fact of route.sources) box.append(element('p',`${fact.entity} → ${fact.relation} → ${fact.target}`));
        if(incomplete) box.append(element('p','× Evidência final ausente'));
        card.append(box);
      }
      const values=element('div',undefined,'outputs');
      values.append(output('Conclusão DNA',row.dna.conclusion??'UNKNOWN'),output('Escolha do modelo',row.raw_model,!row.model_correct),output('Saída protegida',row.guarded_output),output('Tempo do modelo',`${row.model_seconds.toFixed(2)} s`));
      card.append(values,element('p',`${row.dna_correct?'✓':'×'} DNA corresponde ao esperado · ${row.model_correct?'✓ Modelo corresponde':'× Modelo errou ou não se absteve'}`,'proof'));
      card.append(element('p',`${row.dna.dna_bytes} bytes de DNA · ${row.dna.source_checks} comparações · ${row.response.data.evaluated_tokens} tokens avaliados`,'proof'));
    }
    $('cases').append(card);
  }
}
async function poll() {
  try {
    const response=await fetch('/api/reconstruction/state');if(!response.ok)throw new Error('Servidor indisponível');
    const state=await response.json(); token=state.token;
    const rows=state.events.filter(e=>e.kind==='case').map(e=>e.data);
    const worker=state.events.find(e=>e.kind==='worker')?.data;
    const statuses={idle:'Pronto para iniciar uma execução nova.',running:'Executando — build, carregamento e inferências reais.',completed:'Execução concluída · evidências disponíveis',failed:`Execução falhou: ${state.error}`};
    $('status').textContent=`${statuses[state.status]??state.status}${state.run_id?' · '+state.run_id:''}`;
    $('start').disabled=state.status==='running';$('device').disabled=state.status==='running';
    $('download').hidden=state.status!=='completed';
    $('progress').textContent=`${rows.length} / 4`;
    $('dna-score').textContent=rows.length?`${rows.filter(r=>r.dna_correct).length} / ${rows.length}`:'—';
    $('model-score').textContent=rows.length?`${rows.filter(r=>r.model_correct).length} / ${rows.length}`:'—';
    $('identity').textContent=worker?`Worker PID ${worker.handshake.pid} · ${worker.handshake.data.device}`:'Nenhum worker carregado';
    const next=JSON.stringify([state.run_id,rows]); if(next!==signature){renderCases(rows);signature=next;}
    $('evidence').textContent=JSON.stringify(state.report??{run_id:state.run_id,worker,events:state.events},null,2);
  } catch(error) {$('status').textContent=`Sem conexão: ${error.message}`;$('start').disabled=true;}
}
$('start').addEventListener('click',async()=>{
  $('start').disabled=true;
  try {
    const response=await fetch('/api/reconstruction/start',{method:'POST',headers:{'Content-Type':'application/json','X-Tron-Token':token},body:JSON.stringify({device:$('device').value})});
    const data=await response.json();if(!response.ok)throw new Error(data.error);
    await poll();
  }catch(error){$('status').textContent=error.message;$('start').disabled=false;}
});
renderCases([]); await poll();setInterval(poll,1000);
