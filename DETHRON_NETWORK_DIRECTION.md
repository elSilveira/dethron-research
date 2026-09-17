# Dethron: direção da rede e critérios de viabilidade

Índice: [documentação consolidada](README.md). Execução: [plano G0–G7](DETHRON_VALIDATION_PLAN.md).
Hipótese final: [autonomia da internet e sobrevivência com 5%](DETHRON_AUTONOMY_CONTRACT.md).

Atualizado em 15/09/2026 após esclarecimento do objetivo pelo usuário.

Antes de implementar os marcos abaixo, aplicar os critérios da
[validação de utilidade e diferenciação](DETHRON_UTILITY_VALIDATION.md): comparar
com referências existentes e demonstrar uma lacuna. A prova própria de entrega
mostra funcionamento, mas sozinha não demonstra vantagem que justifique recriar
uma stack completa.

Correção de enquadramento: essa visão já pertence ao projeto anterior, incluindo
DNA, swarm, reconstrução e comunicação por ondas. Este documento organiza a
validação dessa intenção; não inaugura um objetivo novo. Ver a
[síntese histórica](dethron_genesis_sintese_cientifica.md), especialmente 2.5–2.9.
Os nomes históricos, como "criptografia viva", não certificam propriedades:
cada propriedade precisa de definição operacional, implementação e teste real.

## Objetivo principal

Uma hipótese adicional é remunerar a manutenção por serviço verificável, com
possível token transferível. Ver [incentivos e seus critérios](DETHRON_INCENTIVES.md).
Remuneração pode favorecer participação; disponibilidade, financiamento e
compatibilidade com períodos offline continuam exigindo demonstração.

A ambição inclui a migração de uma rede apoiada na internet para uma rede com
caminhos próprios suficientes, com possível comutação automática de transporte.
Esse processo depende de cobertura e serviço observados; crescer em número de
nós não demonstra que seja seguro desligar a via internet. Preservar o objetivo
sem assumir sobrevivência universal quando restarem 5% dos participantes.

BitNet, com base no protocolo Genesis, deve permitir uma rede Dethron que
preserve e entregue mensagens através de desconexões e sucessivas gerações de
nós, com armazenamento recuperável, diferentes transportes e participação aberta.
O objetivo inclui aproveitar pequenos nós e reduzir recursos consumidos.
Qualidade de respostas de LLM é uma aplicação secundária, não o critério central
de viabilidade da rede. As medições anteriores continuam válidas em seu escopo.

"Imortal" descreve a ambição de continuidade; não é garantia técnica absoluta.
O contrato verificável é recuperação e entrega sob condições declaradas:
informação suficiente sobrevive, chaves e identidade continuam utilizáveis,
há armazenamento, energia e dispositivos compatíveis, e existe uma sequência
temporal de contatos que permite chegar ao destinatário antes da expiração.
Não é necessário que exista um caminho conectado inteiro em um único instante.
Sem contato futuro ou com perda de toda informação indispensável, não há entrega.

## Swarm como encontro de partes complementares

A mensagem pode viajar por vários caminhos, transportes e gerações de nós.
Nenhum caminho individual precisa entregar a mensagem inteira. O destino acumula
partes verificadas até que a informação recebida permita a reconstrução exata.
Nós intermediários também podem acumular e encaminhar partes sem decifrar o
conteúdo; a verificação desse transporte precisa ser projetada separadamente
da chave privada de leitura do destinatário.

"Buscar seu par" significa descobrir informação útil que falta: os nós anunciam
inventários, reconhecem mensagem/versão/esquema de codificação e trocam partes
complementares. Fragmentos não se descobrem sozinhos; o protocolo executado nos
dispositivos implementa essa busca. Réplicas idênticas não acrescentam informação
para decodificação, embora possam melhorar disponibilidade.

Há duas opções a comparar, não uma implementação já escolhida:

- Unidades originais por ID: é necessário obter cada unidade indispensável.
- Símbolos com redundância codificada: combinações suficientes podem substituir
  partes específicas perdidas, conforme as propriedades do código escolhido.

[RaptorQ, RFC 6330](https://www.rfc-editor.org/rfc/rfc6330.html) fornece um exemplo
conhecido da segunda opção: recuperação a partir de quase qualquer conjunto
suficientemente grande de símbolos. Isso não garante decodificação com qualquer
quantidade nem constitui implementação de RaptorQ no repositório.

O `v2/src/network/recovery_dna.rs` já percorre referências e aceita uma réplica
verificada para cada unidade exigida. O callback pode buscar unidades em fontes
diferentes. Ainda não implementa codificação redundante, descoberta oportunista
de complementos ou recepção persistente ao longo de contatos; a falta de uma
unidade faz a chamada atual falhar. `node_wire.rs` continua restrito a loopback.

### Experimento prioritário refinado

Distribuir partes de uma mensagem por pelo menos três caminhos incompletos.
Interromper contatos e substituir processos transportadores. Remover a origem
do fluxo de recuperação. O destino deve reunir partes em momentos diferentes,
preservar o progresso após reinício, rejeitar corrupção e mistura de versões,
ignorar duplicatas na contagem de informação e só entregar após validação exata.
Uma execução abaixo do limiar deve permanecer incompleta ou expirar sem inventar
conteúdo. Nenhum caminho individual deve ter sido suficiente na prova positiva.

Esse experimento complementa os marcos 1–3 abaixo. Continua planejado; não foi
executado nesta atualização documental. A meta é validar a intenção original
com evidências reais, aproveitando os componentes atuais que já a sustentam.

## Fundamento técnico e o que já existe

### Gateway e adoção orgânica: intenção histórica e implementação examinada

O usuário esclareceu que gadgets participantes devem atuar como gates; a
internet é uma das vias para ligar segmentos, enquanto contatos locais e outras
redes oferecem caminhos adicionais. Isso já aparece nos materiais anteriores:

- `bkp-dethron/future-plans/01-genesis-gateway-service.md`: entrada na rede,
  descoberta de serviços e ponte entre internet tradicional e BitNet.
- `backup/bitnet_extension/bitnet-p2p-gateway.js`: intenção explícita de transformar
  a extensão num gateway de expansão. DHT e conexão/envio aos pares têm trechos
  simulados ou somente logs; criar e fechar um RTCPeerConnection não comprova
  conexão e entrega a outro dispositivo.
- `Genesis-Protocol/src/network.rs`: papéis Gateway e Relay declarados;
  `discover_organisms` cria nós simulados em endereços loopback.
- `bkp-dethron/Dethron/services/genesis_gateway_service.py`: fallback mock e
  autenticação baseada em formato de string, sem prova de assinatura criptográfica.
- `backup/BitNet-lib/bitnet_lib/core/tron_streaming/living_tron_internet_gateway.py`:
  contém código de servidor HTTP/SSE, distinto de comprovar roteamento mesh.

Constatações de leitura estática em 15/09/2026; não foram executados esses gateways
históricos nesta revisão e não se afirma que todos os arquivos equivalentes
tenham sido auditados. Preservar a intenção e aproveitar componentes reais,
substituindo testes que confirmam somente simulações.

Hipótese de crescimento: mais participantes compatíveis e disponíveis podem
criar mais caminhos úteis. Quantidade mundial de gadgets não mede conectividade
local, diversidade de falhas ou capacidade de encaminhamento. Dois gateways
atrás do mesmo enlace externo continuam dependentes dele para aquele destino.
Mais nós também geram tráfego de descoberta; seu custo entra na comparação.

Teste proposto: dois segmentos comunicam por internet; cortar essa via e
verificar entrega através de gateways por outra ligação fisicamente distinta.
Depois cortar também a alternativa: a mensagem deve ficar pendente, preservada,
até novo contato ou expiração. Variar número e localização dos gateways,
medindo taxa de entrega, atraso, tráfego e energia. Ainda não executado.

Reticulum documenta redes sobre internet e outros meios, participação aberta e
papéis de transporte. É comparação próxima também para essa hipótese de adoção:
[construção de redes](https://markqvist.github.io/Reticulum/manual/networks.html).

- DTN e Bundle Protocol: guardar, transportar e encaminhar dados mesmo quando
  origem e destino não estão simultaneamente conectados.
- Mesh: múltiplos saltos e rotas; Wi-Fi, Bluetooth e outros rádios exigem
  adaptadores, hardware e permissões compatíveis. Um protocolo lógico comum
  não torna diferentes rádios diretamente interoperáveis.
- Endereçamento por conteúdo, verificação de integridade, deduplicação,
  compressão sem perdas e códigos de apagamento são mecanismos conhecidos.
- Computação distribuída beneficia tarefas divisíveis quando o trabalho útil
  supera os custos de transferência, coordenação, verificação e repetição.

Fontes primárias:

- [Bundle Protocol v7, RFC 9171](https://www.rfc-editor.org/rfc/rfc9171.html).
- [Bluetooth Mesh: encaminhamento](https://www.bluetooth.com/mesh-directed-forwarding/).
- [Tahoe-LAFS: arquitetura de armazenamento](https://github.com/tahoe-lafs/tahoe-lafs/blob/master/docs/architecture.rst).
- [SNIA: medição da eficiência energética](https://www.snia.org/energy).

Esses antecedentes não eliminam a utilidade do projeto. A contribuição a testar
é uma integração aberta, interoperável e mensuravelmente eficiente. Não foi
demonstrada novidade científica ou superioridade sobre implementações existentes.
A expressão do usuário "marca aberta" ainda não especifica licença, governança
ou formato de descoberta/identificação; não foi convertida em requisito presumido.

## Estado real e limites

O v2 já possui unidades verificadas, receitas, persistência e recuperação.
O Window demonstrou reposição de processos locais usando um sobrevivente
com cópia completa. Isso não demonstra entrega oportunista, rádio, continuidade
sem controlador, sobrevivência a perda de máquinas ou economia de armazenamento.
Referência: [PROCESS_SURVIVAL.md](window/PROCESS_SURVIVAL.md).

Uma receita só reconstrói aquilo que seus dados e entradas permitem reconstruir.
Hashes verificam bytes; não recuperam bytes perdidos sozinhos. Resumir texto em
fatos pode descartar informação e não libera armazenamento com preservação exata
do original. Atomizar cria oportunidades de compartilhamento, mas também índices,
hashes, autenticação e fragmentação. Granularidade ideal exige medição.

Há tensão entre redundância, reparo, latência e economia. Exemplo ilustrativo:
codificar dez partes de dados em quatorze partes do mesmo tamanho exige cerca de
1,4 vez o volume original, excluindo metadados, e pode tolerar quatro perdas com
um código adequado. Não equivale a tolerar a perda arbitrária de 95% dos dados.
Reparos ao longo do tempo podem atravessar muitas gerações se ocorrerem antes
que os fragmentos restantes caiam abaixo do limiar de recuperação.

## Arquitetura de referência proposta, ainda não implementada

1. Envelope de mensagem: ID estável, destinatário, payload cifrado, autenticação,
   limites, expiração e confirmação de recebimento pelo destinatário.
2. Caixa persistente: gravação verificável, recuperação após reinício,
   deduplicação e política limitada de retenção/encaminhamento.
3. Contatos: transporte por interfaces separadas e encaminhamento oportunista.
4. Recuperação: redundância e reparo de mensagens, índices, identidade e estado
   necessário à continuidade, com recuperação do supervisor e suas dependências.
5. Medição: entrega, integridade, atraso, bytes físicos, tráfego e joules.
6. Computação: extensão posterior para tarefas independentes, após validar a rede.

Não exigir LLM em cada nó nem usar o modelo como mecanismo de integridade.
Considerar integração com Bundle Protocol antes de criar outro protocolo completo.
Nós participam de forma autorizada; reconstrução pressupõe capacidade disponível,
não instalação autônoma em qualquer dispositivo encontrado.

## Próximos experimentos, em ordem

Esta lista organiza capacidades. A ordem operacional é o [plano G0–G7](DETHRON_VALIDATION_PLAN.md),
que exige referência executável e lacuna antes de ampliar implementação própria.

| Marco | Experimento | Evidência necessária |
| --- | --- | --- |
| 1 — mensagem persistente | A entrega para B; A desaparece; B reinicia; depois encontra C | C recebe bytes exatos e confirma; não existe conexão A–C simultânea |
| 2 — gerações | Substituir todos os processos originais em ciclos, incluindo supervisor | Mensagem pendente sobrevive; não há cópia original oculta nem chave perdida |
| 3 — partições | Falta de contato, perda parcial, duplicatas, corrupção, filas cheias e expiração | Entrega quando as condições permitem; falha explícita quando não permitem |
| 4 — hardware | Pelo menos dois transportes reais entre dispositivos distintos | Registro de contatos, entrega, limites e consumo; simulação não conta como rádio |
| 5 — armazenamento | Comparar replicação, deduplicação/compressão e redundância codificada | Mesma informação original, contrato de recuperação e contabilização física |
| 6 — energia | Ensaios pareados completos, com e sem falhas, medição elétrica | Economia líquida, incerteza e mesma qualidade de serviço |
| 7 — processamento | Tarefa particionável com verificação e repetição após falha | Ganho líquido frente à execução local convencional |

Nenhum desses marcos novos foi executado nesta atualização de direção.
Para o marco 1, uma prova local inicial pode usar transporte TCP com contatos
explicitamente controlados; deve ser rotulada como tal, sem alegar mesh de rádio.

## Meta de 5%: duas hipóteses separadas

1. Armazenamento: ao menos 5% menos bytes físicos totais, incluindo réplicas,
   fragmentos, índices, manifestos e autenticação, para os mesmos dados recuperáveis.
2. Energia: ao menos 5% menos joules totais na carga de trabalho declarada,
   incluindo CPU, rádio, discos, ociosidade atribuível, manutenção e reparos.

Comparar com uma alternativa convencional competente, sob o mesmo hardware,
volume, distribuição de falhas, durabilidade, taxa de entrega e prazo tolerado.
Registrar medição bruta e repetições; a incerteza deve permitir distinguir o
ganho de 5% de ruído. Não inferir energia por tokens, bytes ou tempo isoladamente.

Redistribuir dados não reduz automaticamente seu volume global. Deduplicar pode
reduzir cópias evitáveis; redundância necessária à sobrevivência não é desperdício
por definição. Liberar espaço lógico também não implica economia elétrica imediata.
Uma economia demonstrada num cenário local não pode ser extrapolada para 5% mundial
sem evidência de adoção, workloads, hardware e custos de operação representativos.

## Decisão

Priorizar rede de mensagens persistentes e continuidade entre gerações. Manter
os estudos de LLM documentados, sem usá-los como medida de sucesso dessa visão.
Buscar primeiro utilidade e melhoria mensurável em um cenário delimitado;
expansão global e economia energética são etapas posteriores de validação.
