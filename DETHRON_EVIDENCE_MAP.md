# Mapa de evidências, antecedentes e documentação

Consolidação: 15/09/2026. Serve para retomar sem confundir planos com resultados.
Entrada principal: [README](README.md). Plano atual: [G0–G7](DETHRON_VALIDATION_PLAN.md).

## Estado verificável no material examinado

| Área | Evidência registrada | Limite |
| --- | --- | --- |
| Recuperação v2 | Unidades cifradas, hashes, referências, receitas e falha por dependência ausente | Não reconstrói informação perdida a partir de hash |
| Regeneração em memória | 20/20 ensaios, 100 stores, cinco sobreviventes | Objetos no processo, replicação completa; não são máquinas |
| Sobrevivência local | 3/3 provas, 20 processos, reposição a partir de um sobrevivente | Mesmo computador, controlador/raiz/chave disponíveis |
| Comparação de respostas | 32 gerações: full 4/8, lexical 3/8, parágrafos 5/8, frases 2/8 | Desenvolvimento anotado; não prova swarm ou extração automática |
| Testes Python da comparação | 124 testes passaram, incluindo 11 novos | Testes locais, executados antes desta consolidação documental |
| Gateway histórico | Intenção registrada e alguns servidores/adaptadores | Descoberta/envio/autenticação simulados em caminhos examinados |
| G0 com referência real | Reticulum 1.5.4/LXMF 1.1.1: três mensagens de 1 KiB a 1 MiB recebidas após crash dos propagadores e saída da origem; negativo retido | TCP no mesmo host, mensagens completas, contatos provisionados; não prova fragmentos ou rádio |
| G1 integrado | Mensagem de 64 KiB, caixa/recibo atômicos, assinatura do destinatário, crashes, duplicata e negativos; auditoria passou | Entrega direta local; composição do recibo com propagação offline, rádio e produção ainda não validadas |
| G2, primeira fatia | 96 KiB reconstruídos a partir de três partes após saída da origem e crash dos propagadores; parte ausente impede conclusão | Limite nativo de 64 kB por busca, mesmo host, colocação provisionada; sem codificação redundante ou custo total |
| G2, comparação ampliada | 12 casos pareados: sem perda, partes exatas gastam menos tráfego; com uma rota perdida, só a paridade XOR conclui | Duas repetições, um host, perda induzida por omissão de contato; armazenamento cresce ao contrário do tráfego |
| G3, gerações | Duas trocas completas de transportadores e quatro supervisores distintos; 24 KiB entregues exatos com recibo; retirada da credencial declarada recusa o serviço | Mesmo host e processos; bloqueio das gerações aposentadas é hook do Python, não isolamento do sistema operacional |
| G4, independência lógica | 16 KiB entregues sem nenhuma interface IP, com zero endpoints em seis processos; linha de base IP mostra três endpoints; meio removido não entrega e preserva pendência | Independência da pilha IP, não física; ponte de arquivos no mesmo host, sem perda, latência ou alcance reais; amostra de netstat, não captura de pacotes |
| V1, custódia | Três relés atestam por assinatura o que guardam; auditor deriva pendência, nomeia relé que atestou e descartou, e verifica recusa explícita para id nunca submetido | Custódia é alegação do relé, prova entrada e não saída; um host, uma rodada por cenário |
| V1, recibo de volta | Recibo de 395 bytes replicado em três relés; origem volta como processo novo e obtém a prova de um único relé; relé que descartou a cópia aparece como prova ausente e outro relé resolve; sem conclusão, nenhuma prova surge | Sessões disjuntas por décimos de segundo, não longos períodos offline; relés cooperativos; retenção de cópias não medida; mecanismo de propagação é do LXMF |
| Rádio e independência da internet | Plano e antecedentes externos | Sem prova nova do Dethron em hardware |
| Sobrevivência universal com 5% | Nenhuma evidência suficiente | Percentual sozinho não garante dados ou contatos |
| Energia e armazenamento global | Metas | Sem medição de economia líquida de 5% |

## Documentação atual de decisão

- [V1, segunda metade](window/V1_RECEIPT_RETURN.md): recibo publicado em
  sequência pelos relés, origem que volta e verifica contra destinatários
  persistidos, auditor com disjunção de sessões e rota da prova.

- [V1, primeira metade](window/V1_CUSTODY.md): envelopes de custódia, fatos do
  LXMF confirmados na fonte, auditor que separa entrada, saída e pendência, e o
  cenário que mentiu e foi recusado pelo auditor.

- [G4 executado](window/G4_INDEPENDENCE.md): via externa definida como a pilha IP,
  ponte alternativa sem socket, evidência de sistema operacional com controle
  positivo e controles de corte total e reversível.

- [G3 executado](window/G3_GENERATIONS.md): contrato de checkpoint público,
  transferência nativa entre gerações, bloqueio do que foi aposentado e recusa
  explícita sem o recurso declarado indispensável.

- [G2 encerrado](window/G2_PARTS.md): comparação restrita, campanha pareada
  ampliada, auditoria, controles e limites das conclusões.

- [G1 e revisão de avanço](window/G1_INTEGRATION.md): contrato, persistência,
  avaliação de satisfação e condição de utilidade para um G2 pequeno.

- [G0 executado](window/G0_REFERENCE.md): configuração, controles, artefatos,
  limitações e decisão de integrar a referência em G1.

- [Plano mestre](DETHRON_MASTER_PLAN.md): ponto de partida principal, matriz de
  hipóteses, arquitetura, contratos, marcos G0–G9 e campanha inicial proposta.

- [Incentivos e remuneração](DETHRON_INCENTIVES.md): hipótese econômica e
  antecedentes Golem/Filecoin; nenhum token ou experimento econômico executado.

- [Direção](DETHRON_NETWORK_DIRECTION.md): intenção histórica, swarm e gateways.
- [Autonomia](DETHRON_AUTONOMY_CONTRACT.md): uso opcional da internet, sobrevivência,
  denominadores, informação e conectividade.
- [Utilidade](DETHRON_UTILITY_VALIDATION.md): referências existentes e lacunas a medir.
- [Plano](DETHRON_VALIDATION_PLAN.md): requisitos, controles, fatias e decisões.

## Núcleo e provas locais

- [v2 README](v2/README.md).
- [Recuperação conectada](v2/CONNECTED_RECOVERY.md).
- [Regeneração em memória](v2/SURVIVAL.md).
- [Status de evidências semânticas](v2/EVIDENCE_STATUS.md).
- [Window README](window/README.md).
- [Sobrevivência com processos](window/PROCESS_SURVIVAL.md).

Registros de referência:

- [Relatório de sobrevivência](window/results/survival-20260915T125653Z-71e25ad2/report.json).
- [Resumo da regeneração em memória](v2/results/survival-20260915/summary.json).
- [Relatório dos quatro modos](window/results/comparison-20260915T132942Z-19a1b580/report.json).

Esses arquivos são artefatos locais e podem não acompanhar um clone limpo,
pois resultados são ignorados pelo Git. Disponibilidade local não equivale a
publicação externa. Preservar cópias ao compartilhar a evidência.

## Aplicações e diagnósticos de modelo, escopo secundário

- [Comparação atual](window/RESPONSE_COMPARISON.md).
- [Documento inicial](window/DOCUMENT_PROBE.md).
- [Átomos](window/ATOMIC_DNA.md).
- [Reconstrução visual](window/RECONSTRUCTION_VISUAL.md).
- [Auditoria do harness](window/HARNESS_VALIDATION.md).
- [Avaliadores](probes/README.md).
- [Contrato de capacidade](CAPABILITY_VALIDATION_CONTRACT.md).
- [Plano anterior de inferência](PROBE_VALIDATION_PLAN.md).
- [Roadmap DeepSeek](DEEPSEEK_DISTRIBUTED_INFERENCE_ROADMAP.md).

As regras de integridade continuam úteis. Acertos de modelo não medem
conectividade e não são pré-requisito de G0. Não promover resultados em dados
de desenvolvimento a prova de generalização ou economia global.

## História e intenção

- [Síntese conceitual](dethron_genesis_sintese_cientifica.md).
- [Auditoria do repositório em 13/09](PROJECT_FEASIBILITY_REPORT.md): achados
  históricos, anteriores às provas novas do v2/Window; não é inventário atual.
- [Arquitetura de 2025](BITNET_ECOSYSTEM_ARCHITECTURE.md).
- [Guia de implementação de 2025](BITNET_IMPLEMENTATION_GUIDE.md).
- [Templates e casos de uso](BITNET_TEMPLATES_AND_USE_CASES.md).
- [Plano Genesis Gateway](bkp-dethron/future-plans/01-genesis-gateway-service.md).

Os três guias de 2025 contêm afirmações e exemplos que exigem caracterização,
como disponibilidade de APIs e propriedades biológicas. Avisos de contexto
foram adicionados; corpos históricos não foram reescritos como especificação nova.

## Código histórico de gateway examinado estaticamente

- [Extensão P2P](backup/bitnet_extension/bitnet-p2p-gateway.js): DHT devolve lista
  vazia; descoberta WebRTC não estabelece troca de dados; envio contém logs.
- [Genesis Gateway Service](bkp-dethron/Dethron/services/genesis_gateway_service.py):
  fallback mock e verificação de "assinatura" por formato de string.
- [Papéis e descoberta Rust](Genesis-Protocol/src/network.rs): Gateway/Relay
  declarados; descoberta preenche nós loopback simulados.
- [Gateway HTTP/SSE](backup/BitNet-lib/bitnet_lib/core/tron_streaming/living_tron_internet_gateway.py):
  código de servidor HTTP presente, sem comprovar mesh ou reconstrução por rádio.

Não foram executados esses gateways nesta análise. Não afirmar que cada arquivo
duplicado em backup ou cada dependência foi auditado. Código atual fica no v2;
qualquer reaproveitamento deve passar por testes comportamentais próprios.

## Escopo da consolidação

Foram consolidados os documentos de visão/decisão e conectadas as páginas de
evidência e planos identificados nesta conversa. Documentos históricos receberam
contexto sem apagar resultados, exemplos ou alegações anteriores. Não foi feita
reescrita de milhares de arquivos de backup, nem certificação de todos os projetos.
`1.md` é uma nota separada sobre emulação neural e não foi modificada.

A verificação documental confere os destinos locais dos links novos e a presença
dos avisos; não é uma repetição dos experimentos citados. Métricas antigas
mantêm sua data e escopo, inclusive quando o resultado é negativo.

Consolidação anterior conferida: seis páginas centrais e 21 documentos contextualizados;
128 referências locais verificadas sem destino ausente. Corpos históricos
foram preservados ao inserir os avisos. Não foram repetidos testes de código,
inferência, rádio ou recuperação nesta atualização exclusivamente documental.
