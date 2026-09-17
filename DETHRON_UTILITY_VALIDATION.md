# Validação de utilidade e diferenciação do Dethron

Entrada: [índice consolidado](README.md). Próximas ações: [plano G0–G7](DETHRON_VALIDATION_PLAN.md).

**Atualização G0, 15/09/2026:** a referência Reticulum/LXMF foi executada e atendeu
ao recorte local de mensagens completas após crash. [Resultados e limites](window/G0_REFERENCE.md).
A próxima fatia é integração em G1; diferenciação por fragmentos continua uma
hipótese de G2. A análise de antecedentes abaixo não equivale a validação de mercado.

Data: 15/09/2026. Revisão documental de fontes primárias e das evidências locais
já examinadas. Não é benchmark entre implementações, teste de rádio, validação
com usuários, pesquisa exaustiva de anterioridade ou análise de patentes.

## Parecer

A hipótese final de adotar a internet como via inicial, migrar para caminhos
próprios e sobreviver com 5% foi analisada no [contrato de autonomia](DETHRON_AUTONOMY_CONTRACT.md).
Ela não altera o parecer de utilidade: autonomia física exige contatos e
infraestrutura suficientes, e um percentual de sobreviventes não certifica
conectividade, recuperação ou inviabilidade de desligamento.

A classe de problema tem utilidade prática e implementação no mundo real.
A ideia geral de preservar, encaminhar por contatos e reconstruir dados de
fragmentos possui antecedentes substanciais. A utilidade específica e a vantagem
do Dethron ainda não estão demonstradas. Não justificar uma implementação global
nova apenas pela visão de swarm, DNA ou sucessivas gerações.

Decisão recomendada: manter a visão original e limitar o próximo investimento
a uma comparação com solução existente em cenário definido. Integrar componentes
existentes quando atendam ao requisito; implementar diferenças somente quando
uma lacuna mensurável tiver sido identificada. Nenhuma implementação de rede
foi acrescentada durante esta revisão.

## Antecedentes próximos e natureza da evidência

| Necessidade | Antecedente | O que permite concluir |
| --- | --- | --- |
| Entrega após interrupções | NASA DTN / missão PACE | Há uso operacional dessa classe de comunicação |
| Comunicação por vários meios físicos | Reticulum | Existe stack aberta com interfaces para meios heterogêneos |
| Mensagens persistentes em rede de pares | LXMF sobre Reticulum | Nós de propagação sincronizam mensagens e permitem retirada posterior |
| Mensagens sem internet por Wi-Fi/Bluetooth | Briar | Existe aplicação distribuída com esses meios; não equivale automaticamente ao swarm de fragmentos proposto |
| Recuperação a partir de fragmentos redundantes | RaptorQ e Tahoe-LAFS | Reconstrução com informação suficiente já é mecanismo especificado/implementado |
| Codificação, múltiplos caminhos e DTN | RFCs 9407 e 8975 | A combinação também tem antecedentes de pesquisa; RFC informacional não prova implantação completa |

Fontes:

1. [NASA: DTN e uso operacional no PACE](https://www.nasa.gov/communicating-with-missions/delay-disruption-tolerant-networking/).
2. [Reticulum: construção de redes heterogêneas](https://markqvist.github.io/Reticulum/manual/networks.html).
3. [LXMF: nós de propagação e roteador](https://github.com/markqvist/LXMF#propagation-nodes).
4. [Briar: funcionamento](https://briarproject.org/how-it-works/).
5. [RaptorQ, RFC 6330](https://www.rfc-editor.org/rfc/rfc6330.html).
6. [Tahoe-LAFS: armazenamento distribuído](https://tahoe-lafs.org/~trac/lafs.pdf).
7. [Tetrys, RFC 9407, seção 6.1](https://www.rfc-editor.org/rfc/rfc9407.html#section-6.1).
8. [Network Coding e DTN, RFC 8975, seção 4.4](https://www.rfc-editor.org/rfc/rfc8975.html#section-4.4).

As funcionalidades acima são descritas pelos projetos/autores; não foram
reproduzidas nesta sessão. Não afirmar que Reticulum/LXMF ou outra ferramenta
implementa exatamente toda a política de fragmentos e regeneração imaginada.
Também não deduzir exclusividade da integração a partir de uma busca limitada.

## Aplicação candidata, a validar com usuários

Troca de mensagens e documentos não urgentes entre equipes em campo que têm
contatos breves e conectividade irregular. O benefício pretendido é completar
transferências após interrupções, preservar progresso e sobreviver à troca de
dispositivos, com limites conhecidos de prazo, energia e armazenamento.

Exemplo de hipótese de uso: um relatório precisa chegar até o fim do dia;
partes ficam em transportadores distintos e o destino reúne o que recebeu.
Isso precisa resolver uma falha ou custo real que um usuário já enfrenta.
Ainda não foram entrevistados usuários nem medidos contatos/dispositivos reais.
Não apresentar esse exemplo como demanda comercial comprovada.

O primeiro produto não deve prometer substituir conexão interativa de baixa
latência ou suportar qualquer carga sobre qualquer rádio. Pequenos nós também
não implicam economia computacional sem contabilizar coordenação e comunicação.

## Possíveis diferenças: hipóteses, não propriedades demonstradas

- Menos tráfego de reparo para completar o mesmo objeto após perdas.
- Mais objetos completos entregues dentro do mesmo prazo e orçamento energético.
- Menos bytes persistidos para o mesmo contrato de recuperação.
- Menor RAM ou operação mais simples em dispositivos participantes disponíveis.

Só chamar qualquer item de diferencial após comparação. A capacidade de mostrar
entrega em três caminhos incompletos prova funcionamento, não superioridade:
soluções convencionais de recuperação também podem satisfazer esse teste.

## Portões de decisão antes de ampliar o projeto

1. **Requisito:** declarar destinatários, tamanhos, contatos, prazo tolerado,
   perdas previstas, hardware e recursos. Validar se uma equipe real necessita
   desse serviço e consegue manter os nós participantes.
2. **Referência executável:** testar uma solução existente adequada. Reticulum
   com LXMF é candidato próximo para mensagens heterogêneas; DTN com Bundle
   Protocol é candidato para entrega tolerante a interrupções. Armazenamento
   codificado precisa de comparação própria. Não escolher a referência mais fraca.
3. **Lacuna:** documentar qual requisito a referência não atende ou atende com
   custo excessivo. Se ela atender, priorizar integração ou contribuição ao projeto.
4. **Diferença isolada:** introduzir somente o mecanismo Dethron que tenta resolver
   essa lacuna. Congelar protocolo experimental e comparar com e sem a mudança.
5. **Medição pareada:** mesmas mensagens, hardware, cronograma de contatos,
   perdas, criptografia e garantias. Contar entrega correta no prazo, duplicatas,
   corrupção rejeitada, bytes físicos, tráfego completo, RAM e energia medida.
6. **Decisão:** continuar se houver benefício reproduzível e operacionalmente útil.
   Para a meta de 5%, medir armazenamento e joules separadamente; declarar
   incerteza e evitar trocar menor consumo por pior serviço sem explicitar isso.

Sem ganho técnico, pode existir valor de produto por facilidade e suporte,
mas isso também exige validação com usuários. Se não houver ganho nem necessidade
de integração, a escolha racional é utilizar a solução existente e parar a
reimplementação equivalente. O trabalho realizado continua útil como aprendizado
e como infraestrutura de testes.

## Situação ao encerrar esta revisão

- Utilidade da classe de problema: sustentada por uso operacional e software existente.
- Novidade do conceito geral: não demonstrada; antecedentes próximos identificados.
- Viabilidade da implementação Dethron completa: não demonstrada.
- Vantagem energética, de armazenamento ou comercial: não demonstrada.
- Próximo trabalho recomendado: requisitos e referência executável, antes de
  ampliar o swarm próprio. Este documento não declara essas etapas concluídas.

Ver também [visão e contratos da rede](DETHRON_NETWORK_DIRECTION.md).
