# G1 — mensagem persistente e confirmação autenticada

Fechamento: 16/09/2026. Predecessor: [G0](G0_REFERENCE.md).
Plano: [arquitetura e marcos](../DETHRON_MASTER_PLAN.md).

## Avaliação antes de investir

**G0 foi satisfatório para uma integração limitada.** Sua reauditoria confirmou
três objetos recebidos após reinícios, com assinatura e conteúdo válidos.
Isso não demonstrou novidade do Dethron: mostrou que é possível aproveitar
Reticulum/LXMF. O investimento autorizado em G1 foi uma fronteira de aplicação
pequena, necessária para testar depois mensagens compostas por partes.

**Pergunta de G1:** conseguimos manter uma obrigação de entrega entre reinícios,
sem confundir envio com confirmação, sem duplicar a mensagem recebida e sem
aceitar confirmação de outro participante?

## Implementação e decisão de arquitetura

Pacote [dethron_gateway](dethron_gateway/__init__.py), em Python, junto à API
nativa Reticulum 1.5.4/LXMF 1.1.1. O núcleo Rust v2 de recuperação permanece
separado. Esta escolha altera a proposta de colocar todas as primeiras transições
em Rust: a integração e a caixa da aplicação são validadas primeiro na linguagem
da referência, evitando uma segunda implementação e uma ponte entre linguagens
antes de medir necessidade. Não é uma migração do núcleo v2.

| Componente | Responsabilidade |
| --- | --- |
| `protocol.py` | Manifesto versionado de objeto completo; IDs, endpoints, tamanho, SHA-256, prazo e payload limitado |
| `wire.py` | Verificar assinatura nativa LXMF e vincular manifesto à origem e ao destino efetivos |
| `database.py` | SQLite, transações, identidade do banco e admissão por capacidade |
| `mailbox.py` | Outbox, inbox, recibos, deduplicação, tentativas e expiração |
| `adapter.py` | Integração de envio/recepção real com LXMF; avanço explícito por `pump()` |
| `g1_node.py` | Processo de laboratório, identidade persistente e controle JSONL |
| `g1_scenario.py` / `run_g1_probe.py` | Agenda de falhas, execução e reauditoria dos bancos e pacotes |

O store de `v2/src/network/node_store.rs` persiste unidades opacas em arquivos,
mas não oferece a transação conjunta de inbox e recibo requerida nesta fatia.
Por isso a caixa usa SQLite, `journal_mode=DELETE`, `synchronous=FULL` e
`BEGIN IMMEDIATE`: a mensagem e o recibo pendente entram na mesma transação.
Os testes cobrem crash de processo antes/depois do commit; não validam queda de
energia ou falha de hardware. [Semântica e pressupostos do SQLite](https://www.sqlite.org/atomiccommit.html).

Não foi criada criptografia nova. O manifesto viaja dentro de LXMF, cifrado no
transporte nativo e assinado pela identidade remetente. A verificação usa Ed25519
de `cryptography` e o formato nativo; não confia apenas em um flag de sucesso.
Os bancos e chaves do laboratório ficam em disco **sem proteção adicional em repouso**.

## Contrato e estados

API mínima reutilizável:

- `Mailbox.queue(envelope, now)`: admite mensagem local e persiste antes de retornar.
- `Mailbox.pending(now)`: lista elegíveis e marca expiração; não transmite.
- `Adapter.pump()`: submete pendências ao LXMF; a agenda de chamadas pertence ao chamador.
- `Adapter.receive(message)`: autentica, valida e aplica a transação local.
- `Mailbox.snapshot()`: consulta estados, tentativas e referências.

`accept_verified()` é uma fronteira interna de confiança: só deve receber
objetos já autenticados pelo adaptador. Um hash isolado não autentica remetente.

```text
origem: queued -> sending -> handed_off
                           -> confirmed, somente com recibo válido do destino
        pendências sem confirmação -> expired ao atingir o prazo

destino: validar -> [inbox received + recibo queued] na mesma transação
                   -> transmitir recibo pelo LXMF
```

Um recibo vincula versão, ID, origem/destino invertidos, tamanho, digest e prazo.
Assinatura válida de outra identidade não confirma a obrigação. Um callback de
handoff tardio não rebaixa `confirmed`. Reenvio com o mesmo ID e conteúdo mantém
uma única entrada na inbox; mesmo ID com conteúdo diferente é rejeitado.

Uma duplicata pode recolocar o recibo na fila, preservando seu limite de tentativas.
Isso não garante execução exatamente uma vez de efeitos externos como um pagamento.
Um recibo significa que esta implementação persistiu a mensagem antes de assiná-lo;
assinaturas de participantes desonestos não são prova econômica de serviço.

## Perfil congelado de laboratório

| Item | Valor |
| --- | --- |
| Meio | TCP loopback, um host Windows; entrega direta LXMF, sem propagador nesta fatia |
| Participantes | O envia; D recebe; X tenta confirmar com outra identidade; uma identidade adicional nunca tem processo |
| Mensagem positiva | 65.536 bytes determinísticos SHAKE-256; expiração em 180 s |
| Negativo | Destinatário sem identidade conhecida/rota local; expiração em 30 s; nenhuma confirmação |
| Limites da aplicação | 1 MiB de payload; 1.500.000 bytes de envelope JSON; 128 registros; 8 MiB lógicos de corpos/pacotes armazenados |
| Tentativas | Até 3 submissões por obrigação ao adaptador, persistidas entre reinícios |
| Crashes | `os._exit(23)`, preservando disco e identidade |
| Evidência | Bancos locais, pacotes LXMF assinados, manifesto, logs, timeline, versões e hashes dos fontes registrados |

O limite de tentativas não conta as retransmissões internas do LXMF. A cota
lógica não mede ocupação física nem limita todos os caches/logs da biblioteca.
Registros antigos são conservados: não há coleta automática nem política de
retenção de produção; ao atingir capacidade, a admissão falha explicitamente.
O relógio UTC local é confiado; rollback de relógio ainda não foi validado.

O negativo desta rodada não envia payload a um intermediário: a identidade
ausente não é conhecida, permanece pendente e expira. Isso complementa o negativo
G0, que realmente armazenou a mensagem de destino ausente em um propagador.

## Testes e critérios de satisfação

| Teste | Critério |
| --- | --- |
| Origem cai antes de transmitir | Fila e identidade sobrevivem; envio posterior usa o registro persistido |
| Destino cai depois do commit e antes do recibo | Inbox e recibo sobrevivem juntos |
| Crash dentro da transação, antes do commit | Nenhuma inbox parcial nem recibo persistido; testado em subprocesso real |
| Retransmissão após restart | Uma entrada lógica; duplicata identificada |
| Handoff sem recibo | Origem permanece não confirmada |
| X envia recibo com assinatura própria válida | Rejeição; nenhuma confirmação |
| Manifesto corrompido assinado e enviado por LXMF | Rejeição no receptor |
| Recibo legítimo retorna; origem reinicia | `confirmed` persiste; reauditoria verifica assinatura do destino |
| Destinatário ausente | Expira sem recibo nem confirmação |
| Capacidade insuficiente | Admissão falha e inbox/recibo são desfeitos juntos |
| Versão, campos, assinatura, endpoint ou conteúdo inválidos | Rejeição nos testes de contrato/autenticação |
| Auditor recebe obrigação ou prazo adulterado | Não aceita mesmo que exista uma assinatura válida |

Os testes rápidos usam entradas sintéticas; um teste de fronteira usa um router
substituto para reproduzir a regressão de rota em cache. Esses testes não são
contados como prova de rede. O ensaio de integração usa processos e LXMF reais.

## Reprodução

Na raiz, com o [ambiente fixado em G0](G0_REFERENCE.md#reprodução):

```powershell
$env:PYTHONPATH='window'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p 'test_g1_*.py'
$env:RUN_GATEWAY_G1='1'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p test_g1_reference.py
Remove-Item Env:RUN_GATEWAY_G1
```

Para acompanhar eventos: `window/.venv-gateway/Scripts/python.exe window/run_g1_probe.py`.
Cada rodada cria `window/results/gateway-g1-ID`, sem sobrescrever tentativas.
Artefatos locais contêm chaves privadas e conteúdo de laboratório e são ignorados
pelo Git. O resumo documental preserva resultado e limites para outras instalações.

## Rodadas e avaliação final

| Rodada | Resultado |
| --- | --- |
| `1789498739568561700` | Inconclusiva: adaptador exigia rota em cache e bloqueava o canal de retorno nativo. Erro reproduzido em teste e corrigido delegando a escolha de caminho ao LXMF. |
| `1789498865120420300` | Integração passou em 30,230 s; confirmação persistente, duplicata, corrupção e identidade errada verificadas. |
| `1789581740304500500` | Versão final passou em 31,124 s, com auditor endurecido e reauditoria dos bancos/pacotes. |

[Primeiro relatório aprovado](evidence/gateway-g1-1789498865120420300/report.json).
A revisão posterior endureceu o auditor para comparar todos os campos da obrigação
e fechar explicitamente conexões SQLite; a versão final foi repetida antes do fechamento.

[Relatório final](evidence/gateway-g1-1789581740304500500/report.json),
[manifesto](evidence/gateway-g1-1789581740304500500/manifest.json) e
[timeline](evidence/gateway-g1-1789581740304500500/timeline.jsonl).
Regressão G0 com o launcher compartilhado também passou:
[relatório](evidence/gateway-g0-1789498911484614700/report.json).

Verificação final:

- **19 testes rápidos G1 passaram** no ambiente `.venv-gateway`; o ensaio opt-in
  foi pulado nessa chamada e executado separadamente: **1 integração real passou**.
- Suíte geral: **136 passaram, 7 pulados**. Os pulos são os cinco módulos que
  dependem do ambiente RNS/LXMF e os dois ensaios de rede opt-in; a execução G1
  e a regressão G0 são registradas separadamente acima. Os testes G0 rápidos
  já haviam passado no fechamento de G0.
- Hashes dos fontes conferem com a rodada final; módulos/testes novos têm menos
  de 200 linhas; links locais da documentação foram conferidos.
- As duas rodadas funcionais são evidência de desenvolvimento, sem estimativa
  estatística de confiabilidade, benefício energético ou ganho de desempenho.

**Decisão:** satisfatório como integração funcional de laboratório; não como rede
pronta para produção nem como demonstração de vantagem competitiva. Há razão
para um G2 pequeno: testar se partes vindas de contatos incompletos acrescentam
utilidade sob orçamento comparável. G2 não fica aprovado de antemão.

G2 deve comparar, com os mesmos contatos e limites, objetos completos, partes
exatas e depois codificação estabelecida. Se o ganho desaparecer ao contar
metadados, retransmissões e armazenamento, manter apenas a integração ou encerrar
a hipótese de protocolo próprio. Não ampliar para mesh físico, tokens ou escala
global para compensar ausência de ganho.

O G1 não testa o recibo de aplicação atravessando propagadores offline; G0 e G1
provaram partes distintas. Essa composição, rádio, disco cheio físico, ataques
persistentes, rotação de chaves e operação sem supervisor continuam pendentes.
