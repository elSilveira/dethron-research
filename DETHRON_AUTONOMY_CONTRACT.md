# Autonomia da internet e sobrevivência com 5%

> **Nota de 19/09/2026.** Este documento cita trabalho anterior ao Dethron — sondas
> BitNet/Genesis, *crates* Rust, *worker* neural, painel de navegador — que saiu da
> árvore quando o repositório foi preparado para publicação. Os links para esse
> material foram desfeitos, e o texto mantido. O conteúdo continua no histórico do git.

Data: 15/09/2026. Contrato proposto para avaliar a visão final do usuário.
Não é resultado experimental nem garantia da implementação atual.

## Intenção a preservar

A internet serve de via durante a expansão orgânica dos gateways. A ambição é
que a rede Dethron adquira caminhos próprios suficientes para deixar de precisar
dessa via e, mesmo após perder 95% dos nós, preservar sua continuidade.
O desligamento automático da via internet é uma funcionalidade desejada a
avaliar, não uma ação autorizada em equipamentos reais nesta etapa documental.

## Duas hipóteses independentes

**H-A — autonomia:** a rede sustenta o serviço declarado sem depender de enlaces
de internet, servidores centrais ou infraestrutura de descoberta indispensável
que só seja acessível por esses enlaces.

**H-S — sobrevivência:** após perdas definidas, os sobreviventes conservam dados,
identidades e estado suficientes para manter ou recuperar esse serviço.

Passar H-A não implica H-S. Recuperar um objeto em H-S não implica conectividade
entre os sobreviventes nem entrega ao destinatário. O protocolo não substitui
distância física, alcance de rádio, energia, hardware ou transporte disponível.

## O que significa sobreviver

| Nível | Critério | O que não decorre dele |
| --- | --- | --- |
| Processo | Um executável continua ativo | Dados ou identidade preservados |
| Informação | Um objeto é reconstruído exatamente | Destinatário alcançável |
| Serviço | Usuários declarados recebem dentro do prazo | Alcance global ou mesma capacidade anterior |
| Regeneração | Nós novos recuperam estado válido | Capacidade física criada do nada |
| Autonomia | O serviço funciona sem a via internet no cenário | Impossibilidade de interrupção em outros cenários |

Se o destinatário foi destruído, definir previamente se há dispositivo substituto
e mecanismo de recuperação da identidade. Não contar entrega a um processo que
o avaliador criou com uma chave oculta como continuidade autônoma do destinatário.

## "5%" exige denominador e modelo de falha

Declarar se são 5% dos processos, dispositivos, armazenamento, capacidade de
rádio ou regiões. Processos no mesmo computador não são falhas independentes.
Fixar o número de nós antes da injeção: excluir os mortos do denominador não
transforma uma rede quebrada em 100% saudável.

Separar:

1. Sobreviventes escolhidos para preservar cópias e caminhos.
2. Perdas aleatórias, com distribuição e sementes registradas.
3. Falhas correlacionadas: uma região, energia compartilhada ou um gateway comum.
4. Perdas direcionadas aos nós que concentram dados, chaves ou conectividade.
5. Perdas simultâneas e perdas graduais com oportunidade de reparo.

Resultados do primeiro caso não demonstram os demais. Uma pequena rede pode ter
todos os dados e perder sua única ponte. Milhares de nós podem permanecer ativos
em ilhas sem contato futuro. Essa é uma impossibilidade de entrega naquele
cenário, não uma falha corrigível apenas renomeando o roteamento como swarm.

## Custo mínimo de garantir quaisquer 5%: argumento limitado

Exemplo matemático, não medição do repositório: há 100 nós, cada um conserva
`s` bytes da representação, e um objeto arbitrário tem `M` bytes de
informação incompressível. Não há outra fonte de dados fora desses nós.
Se **qualquer conjunto de cinco nós** deve reconstruir exatamente o objeto:

```text
5 × s >= M
100 × s >= 20 × M
```

No modelo de armazenamento uniforme, são necessários pelo menos 20 volumes do
objeto, antes de metadados e outros custos. É um limite de informação desse
contrato forte, não uma recomendação de algoritmo. Compressão de dados com
redundância se mede contra sua informação efetiva; uma receita ou chave pequena
não elimina a necessidade de preservar informação arbitrária.

Esquemas com perdas probabilísticas, sobreviventes restritos ou reparos ao longo
do tempo têm contratos diferentes e podem ter outras relações de custo. Não
usar este exemplo como limite universal de toda política de sobrevivência.
Mesmo redundância suficiente não garante que os fragmentos possam se encontrar.

## O que os testes atuais dizem

Sobrevivência de processos: 20 serviços no mesmo
computador, um sobrevivente com cópia completa, chave e raiz confiável mantidas
pelo controlador. Três provas registradas recompuseram os serviços.
O teste demonstra recuperação local no cenário definido. Não prova um limiar
universal de 5%, economia de armazenamento, perdas geográficas ou continuidade
sem controlador e seus recursos.

O experimento anterior em memória também usa replicação completa.
Seus 20/20 ensaios não devem ser somados às três provas de processos como se fossem
ensaios independentes do mesmo contrato ou de uma rede mundial.

## Desconexão automática da internet

O gatilho deve depender de capacidade observada no escopo atendido: destinos
alcançáveis por caminhos alternativos, prazos, taxa de entrega, capacidade de
filas e recuperação dos serviços de identidade/descoberta. Quantidade de gadgets
ou percentual de adoção não é, sozinha, um gatilho válido.

Avaliar separadamente:

- Preferência por caminhos próprios mantendo a internet como opção.
- Modo de operação que desativa a interface externa explicitamente.
- Comutação automática, com política de reativação ou de permanência isolada
  declarada antes do teste, e sem oscilar a cada contato breve.

A recomendação inicial é validar a autonomia por corte controlado da via externa.
Isso testa a ambição sem presumir que desligar uma rota útil melhora o serviço.
O produto pode oferecer escolha de política aos operadores. Nenhuma política
de corte será habilitada em máquinas reais por estes documentos.

O ensaio offline deve iniciar também a frio: descobrir pares, validar identidades,
recuperar estado e receber mensagens com os serviços externos bloqueados.
Sucesso apenas com caches quentes não estabelece autonomia de inicialização.
Internet ausente não significa IP proibido: Wi-Fi local pode usar IP sem WAN.
Um túnel IP que atravessa provedor externo continua dependente dessa via.

## Formulação que podemos tentar demonstrar

"No cenário S, com a via internet indisponível e perdas F, preservamos os dados
e entregamos X de Y mensagens elegíveis até o prazo T, usando recursos R."

Manter no relatório também mensagens não elegíveis, causas de impossibilidade
e contagem total original. Não excluir destinos inacessíveis para inflar o placar.
Não converter isso em "praticamente impossível desligar": seria preciso um
modelo de ameaça, esforço de interrupção e evidência que hoje não existem.

Referências: [DTN/BPv7](https://www.rfc-editor.org/rfc/rfc9171.html),
[Reticulum e meios físicos](https://markqvist.github.io/Reticulum/manual/networks.html),
[Tahoe-LAFS e codificação](https://github.com/tahoe-lafs/tahoe-lafs/blob/master/docs/architecture.rst).
O argumento numérico acima é uma derivação explícita, não resultado atribuído
a essas fontes. Próximos passos no [plano de validação](DETHRON_VALIDATION_PLAN.md).
