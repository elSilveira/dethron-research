const $=id=>document.getElementById(id);
function node(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
export function renderDocument(state,document,rows){
  $('document-panel').hidden=false;
  $('document-text').textContent=document.document;
  $('document-size').textContent=`${document.document.split(/\s+/).length} palavras · 10 seções · 8 situações · texto controlado em inglês`;
  $('progress').textContent=`${rows.length} / 8`;
  $('model-label').textContent='Modelo com texto inteiro';
  $('model-score').textContent=rows.length?`${rows.filter(r=>r.modes[0].answer_correct).length} / ${rows.length}`:'—';
  $('selected-metric').hidden=false;
  $('selected-score').textContent=rows.length?`${rows.filter(r=>r.modes[1].answer_correct).length} / ${rows.length}`:'—';
  $('cases').replaceChildren();
  for(const c of document.cases){
    const row=rows.find(r=>r.id===c.id),card=node('article',undefined,'case');
    card.append(node('h2',c.question),node('p',`Caso: ${c.id} · esperado: ${c.expected}`,'note'));
    if(!row)card.append(node('p','Aguardando duas gerações reais…','pending'));
    else{
      card.append(node('p',`DNA: ${row.dna.conclusion??'UNKNOWN'} · ${row.dna_correct?'correto':'incorreto'} · seções citadas: ${row.dna.source_ids.join(', ')||'nenhuma'}`,'proof'));
      if(row.removed.length)card.append(node('p',`Seções removidas do texto e do DNA: ${row.removed.join(', ')}`,'route missing'));
      for(const m of row.modes){
        const o=m.response.data.outputs[0],a=m.assessment;
        const box=node('div',undefined,`output${m.answer_correct?'':' bad'}`);
        box.append(node('span',m.mode==='full'?'Texto inteiro → modelo':'Trechos selecionados pelo DNA → modelo'),node('strong',a.answer??'Formato inválido'));
        box.append(node('p',`Resposta: ${m.answer_correct?'correta':'não validada'} · citações: ${a.citations.join(', ')||'nenhuma'} · ${a.accepted?'aceita com evidência':a.valid_abstention?'abstenção válida':'não certificada'}`));
        box.append(node('p',`${o.input_tokens} tokens de entrada · ${o.generated_tokens} gerados · ${o.finish_reason==='length'?'limite atingido':'EOS'} · ${m.seconds.toFixed(2)} s`));
        const raw=node('details');raw.append(node('summary','Ver geração integral, sem correção'),node('pre',o.text));box.append(raw);card.append(box);
      }
      const selected=node('details');selected.append(node('summary','Ver trechos realmente selecionados'),node('pre',row.selected_text||'(Sem evidência alcançável)'));card.append(selected);
    }
    $('cases').append(card);
  }
  const summary=state.report?.summary;
  $('verdict').textContent=summary?`DNA ${summary.dna_correct}/8. Texto inteiro ${summary.full.answer_correct}/8; seleção DNA ${summary.selected.answer_correct}/8. Responder sempre UNKNOWN faria ${summary.always_unknown_correct}/8. Respostas sustentadas aceitas: inteiro ${summary.full.accepted}, seleção ${summary.selected.accepted}. Saídas truncadas: inteiro ${summary.full.truncated}, seleção ${summary.selected.truncated}. Este é um diagnóstico de um documento, não uma estimativa de capacidade geral.`:'O veredito será calculado ao terminar. Erros de formato, citações e saídas cortadas permanecem visíveis.';
}
