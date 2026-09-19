# V1 — recibo de volta: a prova de saída chega a uma origem que nunca esteve online com o destino

17/09/2026. Segunda metade do marco V1 da [versão 7 do plano](../DETHRON_MASTER_PLAN.md),
sobre Reticulum 1.5.4/LXMF 1.1.1. A primeira metade, custódia e pendência, está em
[V1_CUSTODY.md](V1_CUSTODY.md). Juntas, fecham o que o plano chama de entrega verificável.

## O que se prova aqui

Até a primeira metade, o recibo do destinatário era produzido localmente em `D` e
nunca chegava a quem enviou. Esta fatia testa a hipótese H20: **o recibo alcança a
origem em fração útil dos casos sem que origem e destino estejam alcançáveis ao
mesmo tempo.** A condição de não simultaneidade é o controle central — sem ela,
qualquer entrega direta passaria por retorno.

O que se prova é estreito e é dito assim: quando houve entrega, a prova existe no
destino e é obtida pela origem de **qualquer relé que carregue uma cópia**. Quando
nenhum relé visitado a carrega, isso aparece como **pendência de prova**, distinta
da pendência de entrega. Quando não houve entrega, nenhuma prova existe em lugar
algum — e nada que se pareça com uma pode surgir.

## Fatos do LXMF confirmados na fonte instalada

- O nó de propagação de saída é lido **no processamento assíncrono** da fila, não
  na entrega ao roteador (LXMRouter.py, linhas 2849–2860). Publicar o recibo em
  três relés exige sequência: apontar, enviar, esperar o handoff, próximo. Três
  envios seguidos com nós diferentes iriam todos para o último apontado.
- A busca da origem usa exatamente o caminho da busca do destinatário:
  `request_messages_from_propagation_node(identity)` identifica a origem no link e
  pede as mensagens para a sua destination de entrega (linhas 502–514).

## Desenho

1. Ao completar, `D` grava o envelope do recibo em `completion.json`, além do
   pacote `completion.lxmf` que já existia.
2. Sob comando, `D` publica o recibo como mensagem **propagada** endereçada à
   origem, um relé por vez, e o laboratório espera o handoff e a persistência no
   relé antes do seguinte. Três cópias, uma em cada relé.
3. `D` sai. A origem volta como **processo novo**, com a mesma identidade, e busca
   em um relé como qualquer destinatário buscaria. Ao receber, verifica a
   assinatura LXMF contra a chave do destinatário a quem enviou, guarda o pacote
   em `receipts/<id>.lxmf` e emite `receipt_received`.
4. O auditor exige que o recibo na origem autentique com a chave de `D`, seja
   idêntico ao envelope esperado sobre os **bytes exatos** que `D` reconstruiu,
   seja idêntico ao `completion.json` local de `D`, e que as sessões de `O` e `D`
   sejam **disjuntas** pelos timestamps de lançamento e parada.

O recibo tem 395 bytes empacotado, contra 15.664 bytes por parte armazenada: para
a prova, réplica simples em todo relé custa quase nada e dispensa partes ou
paridade. DNA para a carga, réplica para a prova.

## Cenários e resultado

Três cenários com resultado exigido antes da execução, na
[rodada final](evidence/gateway-v1-return-1789650235930527800/report.json) com
[fontes congelados](evidence/gateway-v1-return-1789650235930527800/sources.json):
veredito `v1_return_scoped_pass` em 346,4 s.

| Cenário | Tempo | `D` completou | Cópias nos relés | Origem visitou | Prova obtida via | Sem prova em |
| --- | --- | --- | --- | --- | --- | --- |
| `returned` | 82,5 s | sim | A, B, C | C | **C** | — |
| `proof_pending` | 116,5 s | sim | A, B; C descartou a sua | C, depois A | **A** | C |
| `never_completed` | 147,3 s | não (buscou só A e B) | nenhuma | A, B, C | nenhuma | A, B, C |

Nos três, a origem teve **duas sessões** e o destinatário **uma**, sem sobreposição.
Em `returned`, um único relé bastou. Em `proof_pending`, a primeira visita voltou
vazia e ficou registrada como prova ausente em C; a segunda, em A, trouxe o recibo
— pendência de prova resolvida por outro portador, como o plano previa. Em
`never_completed`, `D` ficou incompleto, não publicou nada, e a origem visitou os
três relés sem receber coisa alguma: nenhuma prova falsa apareceu.

## Evidência e auditoria

`v1_return_audit.py` recomputa a partir dos pacotes e do registro:

- **Entrada** — os três recibos de custódia da primeira metade, verificados da
  mesma forma.
- **Saída local** — a auditoria de G3/G4 sobre os pacotes de `D`.
- **Saída na origem** — exatamente um `receipts/<id>.lxmf`, autenticado com a chave
  de `D`, endereçado à origem, igual a `receipt_envelope(data_envelope(...))` sobre
  o conteúdo reconstruído e igual ao `completion.json` de `D`. Se `D` não
  completou, a existência de qualquer recibo reprova a rodada.
- **Disjunção** — intervalos de `O` e `D` derivados dos eventos `launch`/`stop`;
  qualquer sobreposição reprova; origem sem retorno reprova.
- **Rota** — qual relé entregou a prova e quais foram visitados antes sem tê-la.

Os testes do auditor incluem o que ele **deve reprovar**: recibo forjado por outra
identidade; recibo sobre outros bytes; recibo existente sem conclusão; sessões
sobrepostas; origem que nunca voltou.

## Rodadas e verificações

A primeira execução real reprovou com `proof via None`, e o motivo é um achado de
desenho, não de código. O recibo **chegou** à origem, mas ela o rejeitou:
`receipt from an unknown recipient`. A origem é um processo novo depois do
período offline, e a lista de "para quem enviei" vivia só em memória. Sem ela, a
origem não reconhece a própria prova. A correção persiste os destinatários em
`recipients.json`, e isso vira parte do estado declarado que o remetente precisa
manter — o que é honesto dizer: **entrega verificável exige que quem envia guarde
o que espera receber.** A rodada seguinte passou.

Os intervalos entre sessões foram curtos — décimos de segundo entre a parada de
um e o lançamento do outro — mas estritamente disjuntos pelos timestamps. A
afirmação é de disjunção lógica, não de longos períodos offline.

A execução pela via de reprodução declarada repetiu o veredito em 342,8 s, com as
mesmas rotas de prova por cenário: [segunda rodada](evidence/gateway-v1-return-1789650685925011100/report.json).

- Testes V1 rápidos no ambiente fixado: **22 passaram, 2 opt-in pulados**.
- `unittest discover -s window/tests` no ambiente fixado: **163 passaram,
  8 opt-in pulados**.
- `python -m pytest window/tests probes/tests -q` no Python global:
  **167 passaram, 19 pulados**; módulos que dependem de RNS/LXMF são executados
  separadamente no ambiente fixado. G0–G4 reais não foram repetidos nesta entrega.
- `g2_receiver.py` ganhou uma linha, compatível, para gravar `completion.json`;
  os 40 testes de G1/G2 passaram.

## Limites

Mesmo host, TCP de loopback, relés cooperativos: nenhum relé hostil de verdade,
e o descarte em `proof_pending` é comando do laboratório. O mecanismo de
replicação e retorno é a propagação do LXMF; a contribuição aqui é o contrato de
evidência — o que o recibo prova, como se verifica, como a pendência de prova é
reportada — e os controles que devem falhar.

A prova só chega se a origem alcançar **algum** relé que ainda carregue a cópia.
Quanto tempo os relés retêm cópias não foi medido; é política do nó de propagação
e entra como dependência declarada, não como garantia. Uma rodada por cenário,
um objeto de 24 KiB, sem estimativa estatística. A origem só aceita recibos de
destinatários que registrou — recibo de desconhecido é rejeitado, o que é
desejável, e significa que `recipients.json` é parte do estado a preservar.

## Reprodução

Usar o ambiente fixado em [G0](G0_REFERENCE.md#reprodução), a partir da raiz:

```powershell
$env:PYTHONPATH='window'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p 'test_v1_*.py'
$env:RUN_GATEWAY_V1_RETURN='1'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p test_v1_return_reference.py
Remove-Item Env:RUN_GATEWAY_V1_RETURN
```

A campanha real leva cerca de seis minutos e grava cada cenário separadamente.
Artefatos locais incluem chaves de laboratório e são ignorados pelo Git.

## Decisão e próximo passo

Com as duas metades, V1 está no escopo declarado: prova de entrada por custódia,
pendência localizável, prova de saída no destino e prova de saída obtida pela
origem sem contato direto com o destino, com pendência de prova visível quando o
portador visitado não a tem. É entrega verificável em laboratório — não é entrega
garantida, e o documento não a chama assim.

Próxima fatia: **V2 — reprodução por estranho**, clone limpo em uma segunda
máquina, um comando por marco, mesmo veredito, sem ajuda de quem escreveu o código.
