# V1 — custódia: prova de entrada e pendência localizável

17/09/2026. Primeira metade do marco V1 da [versão 7 do plano](../DETHRON_MASTER_PLAN.md),
sobre Reticulum 1.5.4/LXMF 1.1.1. A segunda metade — o recibo do destinatário
voltando à origem pelos relés — está em [V1_RECEIPT_RETURN.md](V1_RECEIPT_RETURN.md).

## O que se prova aqui, e o que não

Até G4, a única evidência de que um objeto tinha sido confiado à rede era o
callback `handoff` do LXMF no processo da origem: um evento do harness, sem
assinatura, sem persistência e sem valor probatório. Esta fatia substitui isso
por um **recibo de custódia assinado pelo relé**, obtido pela origem enquanto
ainda está em contato, e por um auditor que deriva pendência desses recibos.

Custódia é **alegação do relé**. Prova que o objeto entrou na rede; não prova
saída. Só o recibo do destinatário prova saída, e ele continua sendo produzido
localmente em `D`, como em G1–G4. O auditor mantém as duas provas separadas
por construção: um `handoff` sem pacote de custódia é registrado como ausência,
e custódia nunca altera o estado `completed`.

## Fatos do LXMF confirmados na fonte instalada

Cada item abaixo foi lido no código do pacote, não deduzido:

- `LXMessage.pack()` define `transient_id = SHA-256(lxmf_data)` para mensagens
  propagadas (LXMessage.py, linha 434), então **a origem conhece o id** no
  callback de handoff.
- O relé recalcula o mesmo id sobre os bytes recebidos (LXMRouter.py, linha 2495)
  e guarda `[destino, caminho, recebido, tamanho, …]` por id.
- O arquivo em disco é `lxmf_data + stamp`, logo **o sha256 do arquivo não é o
  `transient_id`**. O vínculo entre origem e relé é pelo id; o digest do arquivo
  é uma segunda amarração, conferida contra o inventário que o relé reportou.
- `full_hash` é SHA-256 (Identity.py, linha 352); entrega DIRECT existe e é o
  método padrão; o callback de entrega recebe um `LXMessage` com `packed` e
  `source_hash` (LXMRouter.py, linha 1914).

## Contrato

Três novos envelopes em `dethron_gateway/protocol.py`, com conjuntos de campos
fechados e limites, sem alterar `data` e `receipt`:

| Envelope | Quem assina | Conteúdo |
| --- | --- | --- |
| `custody_request` | origem → relé | `transient_id`, chave pública da origem |
| `custody` | relé → origem | `transient_id`, destinatário visto pelo relé, tamanho e digest do que está em disco, instante de recepção |
| `custody_refusal` | relé → origem | `transient_id` e motivo legível; ausência de custódia nunca é silêncio |

O relé só atesta o que encontra em `propagation_entries`, esperando até 10 s
pela indexação assíncrona; fora disso, recusa. A origem só aceita a resposta
vinda da chave do relé a quem perguntou, para exatamente o `transient_id`
pedido, e guarda o pacote LXMF bruto em `custody/<id>.lxmf`. O relé guarda
uma cópia do que emitiu em `custody/<id>.issued.json`.

Quatro cenários, com resultado exigido antes da execução:

| Cenário | O que acontece | Resultado exigido |
| --- | --- | --- |
| `delivered` | três partes, custódia de cada relé, `D` busca nos três | 3 provas de entrada, prova de saída |
| `pending` | idem, `D` nunca aparece | 3 provas de entrada, sem saída, pendência em A, B e C |
| `discarded` | relé B atesta e depois descarta a parte | 3 provas de entrada, sem saída, **B nomeado** como quem atestou e não entregou |
| `fake` | origem pede custódia de um id nunca submetido | recusa assinada, nenhuma atestação para esse id |

## Resultado

A [rodada final](results/gateway-v1-1789648766782072700/report.json), com
[fontes congelados](results/gateway-v1-1789648766782072700/sources.json), passou
nos quatro cenários em 211,6 s: veredito `v1_custody_scoped_pass`.

| Cenário | Tempo | Provas de entrada | Saída | Pendência derivada | Recusa |
| --- | --- | --- | --- | --- | --- |
| `delivered` | 55,3 s | 3 | 24.576 bytes exatos, recibo válido | nenhuma | — |
| `pending` | 43,2 s | 3 | não | `awaiting_contact: A, B, C` | — |
| `discarded` | 51,6 s | 3 | não; partes 0 e 2 | `attested_not_delivered: B` | — |
| `fake` | 61,5 s | 3 | 24.576 bytes exatos | nenhuma | `transient id not in store` |

O objeto tem 24.576 bytes em três partes exatas de 8.192; cada relé guardou
15.664 bytes por parte, incluindo envelope, codificação e stamp, e cada
atestação declarou esse mesmo tamanho. A pendência distingue duas situações que
outros sistemas confundem: em `pending` ninguém buscou, então os relés ficam
**aguardando contato**; em `discarded` `D` buscou nos três e B não tinha nada,
então B fica **nomeado**. A distinção vem dos eventos de busca, não de opinião.

## Evidência e auditoria

`v1_audit.py` recomputa tudo a partir dos pacotes e do registro:

- **Entrada**: para cada `handoff`, exige `custody/<id>.lxmf` na origem, verifica
  a assinatura LXMF contra a chave pública do relé, o destinatário declarado e
  o `transient_id`, e confere que o digest atestado está no inventário que o
  relé reportou logo após o handoff. Handoff sem pacote é `missing_entry`.
- **Saída**: a mesma auditoria de G3/G4 — pacotes de `D` autenticados contra a
  chave da origem, partes validadas, reconstrução byte a byte e recibo local.
- **Pendência**: por relé com custódia cuja parte não chegou, `awaiting_contact`
  se ninguém buscou dele, `attested_not_delivered` se buscaram e nada veio.
- **Recusa**: verificada contra a chave do relé; a existência de uma atestação
  para o id falso reprovaria a rodada.

Os testes do auditor incluem os casos em que ele **deve reprovar**: handoff sem
custódia não é prova de entrada; custódia de outro id ou de outro destinatário é
recusada; digest que não bate com o inventário do relé é recusado; custódia
nunca implica entrega; relé sem custódia não é culpado por parte ausente.

## Rodadas e verificações

A primeira execução real reprovou na auditoria com `handoff without custody: ['C']`,
e o motivo é instrutivo. O *ack* do comando `custody` é um evento com o mesmo
nome da atestação e também carrega o `transient_id`; o cenário confundiu um com
o outro, registrou custódia de C que não existia e aposentou a origem antes de C
responder — o terceiro pedido ainda estava na fila. **O cenário mentiu e o
auditor recusou**, porque só confia no pacote assinado em disco. Os eventos
passaram a `custody_received` e `custody_refused`, distintos do comando, e a
rodada seguinte passou com C atestando normalmente.

A execução pela via de reprodução declarada repetiu o veredito em 209,0 s, com os
mesmos resultados por cenário: [segunda rodada](results/gateway-v1-1789649067110742100/report.json).

- Testes V1 rápidos no ambiente fixado: **13 passaram, 1 opt-in pulado**.
- `unittest discover -s window/tests` no ambiente fixado: **153 passaram,
  7 opt-in pulados**.
- `python -m pytest window/tests probes/tests -q` no Python global:
  **167 passaram, 17 pulados**; módulos que dependem de RNS/LXMF são executados
  separadamente no ambiente fixado. G0–G4 reais não foram repetidos nesta entrega.
- Fontes de V1 com menos de 200 linhas; `protocol.py` foi estendido sem alterar
  os envelopes `data` e `receipt`, e os 40 testes de G1/G2 que o consomem passaram.

## Limites

Mesmo host, TCP de loopback: o meio não é a pergunta aqui, a evidência é.
Custódia é alegação: um relé hostil pode assinar e descartar, e é exatamente o
que `discarded` simula — por comando do laboratório, não por um relé hostil de
verdade. O que a auditoria garante é que essa conduta **fica nomeada** quando o
destinatário busca e não recebe; não impede que aconteça.

A origem precisa estar em contato com o relé para obter a custódia. Isso vale
para entrada, que é local por natureza; não vale para saída. Nesta entrega, o
recibo do destinatário ainda não tinha caminho de volta à origem offline; a
segunda metade de V1 e a hipótese H20 foram executadas em seguida, em
[V1_RECEIPT_RETURN.md](V1_RECEIPT_RETURN.md). Foram uma rodada por cenário e um
objeto de 24 KiB, sem estimativa estatística.

## Reprodução

Usar o ambiente fixado em [G0](G0_REFERENCE.md#reprodução), a partir da raiz:

```powershell
$env:PYTHONPATH='window'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p 'test_v1_*.py'
$env:RUN_GATEWAY_V1='1'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p test_v1_reference.py
Remove-Item Env:RUN_GATEWAY_V1
```

A campanha real leva cerca de quatro minutos e grava cada cenário separadamente.
Artefatos locais incluem chaves de laboratório e são ignorados pelo Git.

## Decisão e próximo passo

Prova de entrada e pendência localizável estão no escopo declarado. Sozinhas,
não são entrega verificável completa: falta o recibo do destinatário chegar a
quem enviou sem contato direto com o destino. Essa segunda metade — recibo
replicado nos relés, obtido pela origem por qualquer um deles, com origem e
destino nunca simultaneamente online — está em
[V1_RECEIPT_RETURN.md](V1_RECEIPT_RETURN.md).
