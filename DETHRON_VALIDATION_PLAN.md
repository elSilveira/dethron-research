# Dethron — plano de decisão, testes e implementação

Consolidado no [plano mestre](DETHRON_MASTER_PLAN.md), que detalha a arquitetura
e estende esta sequência com processamento (G8) e incentivos (G9).

Versão documental: 4, 16/09/2026. G0 executado no recorte de mensagens completas:
[configuração, controles e decisão de integrar](window/G0_REFERENCE.md).
G1 foi validado como [integração de laboratório](window/G1_INTEGRATION.md).
G2 está encerrado: [partes exatas e comparação pareada ampliada](window/G2_PARTS.md).
G3 executou [duas gerações de nós e quatro supervisores](window/G3_GENERATIONS.md).
G4 entregou [sem a pilha IP, com controles de corte](window/G4_INDEPENDENCE.md).
A versão 7 do plano mestre reenquadra o foco para harness de evidência e entrega
verificável, com a trilha V1–V3; G5 e G7 ficam adiados, G8 e G9 após aceitação
externa. V1 está executado nas duas metades:
[custódia, prova de entrada e pendência](window/V1_CUSTODY.md) e
[recibo de volta sem contato direto](window/V1_RECEIPT_RETURN.md).
V2 tem [roteiro e resultados esperados](window/V2_REPRODUCTION.md) e aguarda a
execução por outra pessoa em outra máquina.
Ver [plano mestre](DETHRON_MASTER_PLAN.md).
A visão está na [direção](DETHRON_NETWORK_DIRECTION.md)
e as garantias de autonomia no [contrato](DETHRON_AUTONOMY_CONTRACT.md).

## Ordem de decisão

1. Validar um requisito e uma referência existente.
2. Demonstrar uma lacuna mensurável.
3. Implementar apenas o mecanismo que tenta resolver a lacuna.
4. Reavaliar frente à mesma referência, incluindo todos os custos.
5. Continuar, integrar a referência, reduzir o escopo ou abandonar a hipótese.

Não tornar "terminar uma rede global" pré-requisito para decidir se existe valor.
Os estudos de LLM permanecem secundários e não bloqueiam a validação da rede.

## Antes da primeira nova execução

Criar uma configuração versionada contendo:

- Uso e participante pretendidos; serviço solicitado e prazo tolerado.
- Identidades, dispositivos, recursos, transporte e domínio de falha de cada nó.
- Mensagens originais, tamanhos, hashes e destinatários; a fonte do avaliador não
  pode ficar acessível ao sistema durante recuperação.
- Topologia e calendário de contatos, falhas, expiração e orçamento de filas.
- Política de réplicas/codificação, retenção, reparo e recuperação de identidade.
- Dependências externas permitidas: chave, raiz, bootstrap, tempo e controlador.
- Versões e configuração da referência, cenários de desenvolvimento e reservados.
- Métricas, metas, repetições e critério de parada definidos antes de ver resultados.

Não há configuração reservada pronta nesta etapa. Valores iniciais candidatos:
mensagens curtas e arquivos pequenos em classes separadas, várias ordens de
contato e múltiplas sementes. Fixar números conforme o hardware/serviço escolhido;
não alegar suficiência estatística por um número arbitrário de repetições.

## Marcos e controles

| Marco | Execução | Aprovação | Controle que deve falhar |
| --- | --- | --- | --- |
| G0 — referência | Reticulum/LXMF ou implementação BPv7 adequada, identificada | Serviço funciona ou lacuna é reproduzida e atribuída | Sem destinatário, nenhuma confirmação final válida |
| G1 — envelope e caixa | Persistir mensagem/fragmentos, reiniciar receptor | Bytes e identidade preservados; uma entrega lógica | Alteração de payload/versão/ID não pode passar |
| G2 — complementos | Três caminhos individualmente incompletos, contatos separados | União suficiente reconstrói bytes exatos | Duplicatas não substituem partes; união insuficiente fica pendente |
| G3 — gerações | Substituir todos os originais e supervisor em ciclos | Estado e mensagens pendentes continuam sem fonte oculta | Retirar recurso declarado indispensável produz falha explícita |
| G4 — via externa | Cortar internet, inclusive antes da inicialização | Serviço no escopo definido usa caminhos físicos alternativos | Cortar também todas as pontes impede entrega, preservando pendência |
| G5 — sobreviventes | Testar 5% escolhidos, aleatórios, correlacionados e direcionados | Placar separado por modelo de falha e nível de sobrevivência | Sobreviventes isolados não podem ser relatados como conectividade global |
| G6 — hardware | Repetir em dispositivos distintos e pelo menos dois meios reais | Evidências de interfaces e transmissão, sem tunnel externo oculto | Meio desligado deixa de transportar dados |
| G7 — custo | Mesma carga e garantias com e sem diferença Dethron | Benefício líquido reprodutível; incerteza declarada | Metadados/reparo/ociosidade não desaparecem da conta |

G0 vem antes de ampliar código próprio. G1–G5 podem começar em laboratório local,
mas devem ser rotulados como emulação de contatos/processos. G6 é necessário
para alegar diversidade de meios físicos. Usar TCP em duas portas não é prova
de dois rádios ou de dois domínios independentes de falha.

Para G5, medir perdas simultâneas e graduais separadamente. No cenário gradual,
registrar a janela de reparo e a capacidade disponível para repor os nós.
Relatar perda de capacidade e latência, mesmo quando a recuperação for correta.

## Implementações pequenas, condicionadas à lacuna de G0

Os nomes abaixo são propostos; arquivos e comandos de teste ainda não existem.
Se a referência já cumprir o requisito, criar adaptadores e testes sobre ela,
em vez de implementar o mesmo protocolo de novo no v2.

| Fatia | Arquivos propostos | Primeiro teste comportamental |
| --- | --- | --- |
| Mensagem verificável | `v2/src/network/message_envelope.rs`, `v2/tests/message_envelope.rs` | Conteúdo ou versão adulterada é rejeitado |
| Progresso persistente | `v2/src/network/message_inbox.rs`, `v2/tests/message_inbox.rs` | Reinício não perde partes nem causa segunda entrega lógica |
| Complementos | `v2/src/network/fragment_inventory.rs`, `v2/tests/fragment_inventory.rs` | Inventário pede informação ausente e ignora duplicatas |
| Contatos e encaminhamento | `v2/src/network/contact_transport.rs`, `v2/tests/contact_transport.rs` | Mensagem atravessa contatos não simultâneos, dentro dos limites |
| Experimento externo | `window/run_gateway_probe.py`, `window/gateway_audit.py`, `window/tests/test_gateway_audit.py` | Registro sem recepção final é rejeitado pelo auditor |

Após criar a interface mínima e o teste, executar, a partir de `v2`,
`cargo test --locked --offline --test message_envelope` (ou o nome da fatia).
Exigir falha pelo comportamento incorreto, não só por arquivo/import ausente.
Implementar o mínimo, repetir o teste, executar a suíte relevante e então refatorar.
Para o auditor: a partir da raiz, definir `PYTHONPATH=window` e executar
`python -m pytest window/tests/test_gateway_audit.py -q` quando o arquivo existir.

Manter cada arquivo de código/teste até 200 linhas. Preservar a execução dos
experimentos existentes. Não reutilizar a autenticação simulada dos gateways
históricos como implementação de segurança; usar primitivas estabelecidas.
Selecionar esquema de codificação e dependências depois da comparação, sem
inventar criptografia ou declarar RaptorQ implementado a partir de uma referência.

## Evidência mínima por execução

- Configuração e manifesto com hashes de código, dependências e binário.
- Relógios e sequência de eventos; PIDs/dispositivos, sessões e interfaces reais.
- Mensagens enviadas, partes recebidas, inventários, reparos e confirmação final.
- Dependências sobreviventes e quem as forneceu, incluindo supervisor e identidade.
- Registros parciais preservados em falha; status iniciado, incompleto, concluído
  ou falhou. Prazo excedido e erro nunca viram entrega correta.
- Auditor independente de contadores de sucesso do emissor: conferir bytes,
  identidade do destinatário, causa de pendência e coerência de cada cenário.
- Hashes fornecem rastreabilidade; não autenticam sozinhos uma execução remota.

Contar todas as mensagens originais, entregues no prazo, tardias, pendentes,
expiradas, corrompidas rejeitadas e entregas indevidas. Mostrar elegibilidade
separadamente sem retirar silenciosamente os casos difíceis do denominador.

## Métricas de utilidade e custo

Medir taxa de entrega íntegra no prazo, atraso, bytes úteis, tráfego total,
bytes físicos persistidos, RAM e energia elétrica. Incluir descoberta, confirmações,
criptografia, codificação, retransmissões, reparos e ociosidade atribuível.
Não tratar throughput agregado como velocidade de uma tarefa única.

Comparar modos em ensaios pareados, com ordens balanceadas. Variar falhas e
contatos; repetições idênticas não criam cenários independentes. Documentar
contaminação por aquecimento, hardware compartilhado e outras cargas.

As metas de economia de 5% em bytes e 5% em joules são separadas da sobrevivência
com 5% dos nós. Para reivindicar o ganho, a incerteza da medição deve permitir
distingui-lo de ruído, sob qualidade de serviço e recuperação equivalentes.
Sem medidor adequado, o resultado energético fica **não medido**.

## Decisão após cada marco

| Resultado | Ação |
| --- | --- |
| Referência já atende sem lacuna útil | Integrar/contribuir; interromper reimplementação equivalente |
| Falha de correção reproduzível | Corrigir a fatia ou retirar o mecanismo; não aumentar escala |
| Reconstrução correta, mas sem contatos suficientes | Rever implantação/uso; não prometer entrega universal |
| Mecanismo próprio ganha em cenários reservados com custo aceitável | Piloto limitado e nova avaliação |
| Só ganha com sobreviventes escolhidos ou custo omitido | Rejeitar a alegação geral e registrar escopo restrito |
| Não há vantagem nem demanda de integração | Abandonar a hipótese/produto nesse escopo e arquivar evidências |

Imortalidade absoluta, sobrevivência de qualquer rede com quaisquer 5% e
desconexão automática por mero tamanho devem ser abandonadas como garantias.
Essa decisão não obriga abandonar redes resilientes com contratos condicionais.

## Ponto de retomada

A observação econômica do usuário está em [incentivos](DETHRON_INCENTIVES.md).
Investigar demanda, custos e remuneração junto aos requisitos de G0; não usar
emissão de tokens como substituto de validação da rede. Recibos e contabilidade
de teste podem acompanhar os experimentos. Token negociável, pagamentos reais
e consenso próprio não foram implementados nem autorizados por esse plano.

Ler [índice](README.md), [utilidade](DETHRON_UTILITY_VALIDATION.md) e
[contrato de autonomia](DETHRON_AUTONOMY_CONTRACT.md). G0–G3 foram executados após a
consolidação inicial. Retomar por G4, corte da via externa, antes de ampliar a
autonomia ou a escala; o estado atual está em [G2](window/G2_PARTS.md) e
[G3](window/G3_GENERATIONS.md).
