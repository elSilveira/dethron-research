# Incentivos para manter a rede Dethron

Data: 15/09/2026. Hipótese acrescentada pelo usuário à visão original.
Documento de avaliação; nenhum token, pagamento, contrato ou mercado foi criado.

## Intenção

Remunerar operadores de gadgets, gateways e servidores por processamento,
armazenamento e conectividade úteis. Um token eventualmente negociável poderia
ser uma forma de pagamento. O objetivo imediato é viabilizar a operação e
reduzir abandono voluntário de recursos; renda distribuída em escala mundial
permanece uma aspiração, sem promessa de rendimento ou adoção.

Pagamento pode incentivar disponibilidade, mas não evita falhas físicas,
perda de energia, interrupção de enlaces ou saída de participantes. Recuperação
continua necessária. A hipótese econômica não valida automaticamente a hipótese
técnica de sobrevivência com 5% dos nós.

## Antecedentes e histórico

- [Golem](https://docs.golem.network/docs/golem/overview): provedores oferecem
  recursos computacionais a solicitantes em troca de GLM. Há custos de pagamento
  e transação, descritos em [pagamentos](https://docs.golem.network/docs/golem/payments).
- [Filecoin](https://docs.filecoin.io/basics/the-blockchain/proofs): utiliza provas
  de replicação e armazenamento ao longo do tempo. Essas provas específicas não
  são provas genéricas de processamento ou encaminhamento de mensagens.
- [Economia histórica BitNet](backup/BITNET_WEB3_ECONOMY/README.md): já descrevia
  token, recompensas e ponte com blockchains. Afirmações de valorização automática,
  eficiência e liquidez nesse documento não são evidência econômica validada.

A leitura do README histórico não é auditoria completa de sua implementação.
Nesta etapa não foram executados contratos, bridges ou testes econômicos antigos.
Remunerar infraestrutura com tokens já tem antecedentes; novidade e viabilidade
da política Dethron exigem validação própria.

## Serviço útil primeiro, unidade de pagamento separada

| Serviço contratado | Evidência a projetar | Incentivo que deve ser evitado |
| --- | --- | --- |
| Processamento | Resultado verificável da tarefa dentro do prazo | Pagar só por CPU ocupada, duração ou resultado autodeclarado |
| Armazenamento | Dados contratados recuperáveis no período, com verificações apropriadas | Remunerar bytes inventados ou cópias desnecessárias |
| Transporte | Encaminhamento/entrega contratado, com recibos e orçamento | Pagar tráfego fabricado, loops ou a mesma obrigação repetida |
| Disponibilidade/reserva | Capacidade contratada e demonstrável quando solicitada | Pagar identidade online como se fosse serviço ou dispositivo independente |

Uma assinatura prova a autoria de um recibo, não necessariamente trabalho útil.
Emissor, provedor e destinatário podem combinar recibos de trabalho fictício.
Múltiplas identidades também não provam múltiplos gadgets independentes.
Verificação, disputa e detecção de abuso têm custo e limites a medir.
Redundância necessária pode ser remunerada, desde que seja explicitamente
contratada e contabilizada; não confundir réplica útil com duplicação de cobrança.

## De onde vem o valor

Escolher uma origem real de financiamento: usuários do serviço, organizações,
assinaturas, contratos ou subsídios explícitos. Emitir tokens não demonstra
receita recorrente, liquidez nem alguém disposto a comprá-los.

Medir separadamente:

```text
resultado do operador = receita realizável pelo serviço
                        - energia - conectividade - desgaste
                        - operação - custos de cobrança/verificação
```

Manter também a conta da rede: pagamentos dos usuários e subsídios, repasses,
despesas de verificação/coordenação e eventuais obrigações futuras. Uma cotação
hipotética do token não é receita realizada. Receber token, conseguir vendê-lo
e ter resultado líquido positivo são eventos diferentes.

Financiamento inicial pode subsidiar cobertura antes de existir demanda local,
mas precisa de orçamento e duração definidos. Medir o que acontece com a oferta
de nós quando esse subsídio termina, sem presumir valorização futura.

Não exigir que todo gadget seja rentável. Alguns recursos podem custar mais para
comunicar, verificar e remunerar do que o trabalho que conseguem fornecer.
Avaliar também concentração: grandes operadores podem ter vantagens de custo,
reduzindo a diversidade de provedores que se pretendia incentivar.

## Compatibilidade com desconexão e partições

Uma rede de transporte pode guardar mensagens durante uma partição. Um sistema
de pagamento não pode presumir que registros isolados de gasto são globalmente
consistentes. Assinar uma promessa offline não impede o mesmo saldo de ser
prometido a vários operadores.

Opções a avaliar incluem créditos pré-alocados com exposição limitada, recibos
provisórios e liquidação posterior. Documentar quem assume risco, quando uma
cobrança é final e como conflitos são resolvidos. Não prometer pagamento final
irrestrito em todas as ilhas e ausência de gasto duplo sem um mecanismo demonstrado.

Se a liquidação depender de uma blockchain acessível apenas pela internet,
registrar essa dependência. A entrega pode continuar offline, enquanto a
liquidação espera. Criar uma blockchain própria acrescenta consenso e segurança;
sobrevivência do armazenamento com 5% não prova segurança ou progresso desse consenso.

## Experimento econômico proposto

1. Escolher um serviço e um solicitante disposto a utilizá-lo; começar com custo
   medido e recibos de uso. Créditos de teste não são negociáveis nem renda real.
2. Comparar participação voluntária e serviço remunerado sob orçamento explícito,
   sem misturar subsídio com demanda orgânica. Piloto financeiro exige definição
   posterior de participantes, orçamento e autorização específica.
3. Simular tentativas de cobrança duplicada, identidades múltiplas, conluio,
   resultados incorretos, perda de dados e recibos conflitantes após partições.
4. Medir utilidade entregue, custo de verificação, resultado líquido do operador,
   custo ao usuário, disponibilidade e concentração. Não pagar pela simulação.
5. Comparar cobrança convencional, créditos de serviço e token transferível.
   Escolher token somente se resolver uma necessidade que compense seus custos.

Continuar se a remuneração sustentar serviço útil, verificável e competitivo.
Simplificar ou abandonar o token se depender de valorização especulativa,
recompensar trabalho fictício ou acrescentar dependência que viole o contrato
de autonomia. A rede pode continuar sem uma moeda própria.

Estado: hipótese documentada; nenhum teste econômico novo executado.
Retomada: [plano de validação](DETHRON_VALIDATION_PLAN.md),
[autonomia](DETHRON_AUTONOMY_CONTRACT.md) e [utilidade](DETHRON_UTILITY_VALIDATION.md).
