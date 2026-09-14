# Viabilidade: primeiro teste da v2

Data: 2026-09-14. Escopo: auditoria local da v2 e experimento executado,
orientados por `../dethron_genesis_sintese_cientifica.md`.

**Resultado: a seleção atual não acrescentou vantagem sobre a estratégia fixa
Plus. A hipótese de reorganização permanece não testada.**

## O que existe

`../v2/src/evolution.rs` escolhe entre três algoritmos escritos previamente.
Treino e validação são constantes; `evolve()` não recebe experiências novas.
`../v2/src/task.rs` implementa divisão tentativa, parada pela raiz quadrada e
salto dos divisores pares. `../v2/src/tron.rs` mantém um cache de respostas
exatas limitado a 128 entradas. Não há criação de procedimentos, grafo mutável
de especialistas ou atribuição de crédito a caminhos nesse mecanismo.

O dashboard compara com Minus. Isso mede a substituição de um algoritmo fraco
por outro melhor, mas não isola o valor da adaptação frente a uma solução fixa
competente. Plus evita testes desnecessários presentes nas outras estratégias;
esta família não oferece um conflito relevante que exija reorganização.

## Experimento executado

Comando, a partir de `window`:

```powershell
cargo run --release --locked --offline --bin feasibility
cargo test --locked --offline --test feasibility
```

Dez sementes determinísticas, 256 inteiros distintos por semente, entre 2.000
e 19.999. Os lotes podem se sobrepor entre sementes. Nenhuma entrada coincide
com os fixtures de evolução. Todos os braços recebem o mesmo lote, orçamento
de até 1.000.000 divisões por entrada e nenhum cache. Cada lote começa com um
Tron novo e uma chamada a evolve; não há ajuste a partir dos resultados de teste.
Comparamos Minus, Zero, Plus e a estratégia selecionada. As respostas são
verificadas por uma implementação independente de fatoração. A ordem dos braços
é rotacionada. Os dez lotes representam partidas novas, não dez atualizações
de um único agente persistente.

Resultado agregado do primeiro release registrado:

| Medida | Valor |
| --- | ---: |
| Respostas corretas | 2.560 por braço |
| Divisões Minus | 5.048.475 |
| Divisões Zero | 96.429 |
| Divisões Plus fixo | 52.929 |
| Divisões da execução selecionada | 52.929 |
| Divisões da seleção | 13.330 |
| Total adaptativo | 66.259 |

A seleção adicionou 25,18% ao número de divisões frente a Plus. Em todos os
lotes a execução selecionada empatou com Plus; portanto, amortizar a seleção
reduz a penalidade relativa, mas não cria vantagem nessa métrica.

O primeiro registro de tempo somou 0,3921 ms para Plus e 3,5591 ms para o braço
adaptativo com inicialização e seleção. Esses tempos curtos são exploratórios,
sem inferência estatística de latência. O braço adaptativo inclui criação de
identidade e auditoria da evolução; os kernels de todos os braços excluem cache
e auditoria por tarefa. Não é uma comparação de runtimes completos com segurança
equivalente. Divisões não medem todas as instruções, energia ou memória.

Evidência bruta: `results/feasibility-20260914.json`. Entradas e medidas por lote
estão preservadas. O teste automatizado verifica o contrato do relatório e o
resultado atual; não substitui uma avaliação de novos mecanismos.

## Decisão

Rejeitar a alegação de que a seleção desta v2 supera a melhor estratégia fixa
por reduzir divisões. Não investir em distribuição para tentar corrigir esse
resultado. Ele não prova que reorganização seja impossível: a v2 ainda não
implementa o mecanismo descrito na síntese. Cache, herança e criptografia podem
ter utilidade própria, mas não respondem à hipótese central.

## Próximo teste necessário, ainda não implementado

Atualização: [REORGANIZATION.md](REORGANIZATION.md) registra uma primeira
implementação de composição de caminhos, validação paralela e memória em três
escalas. O mecanismo passou nas verificações funcionais e perdeu em latência
contra os controles no domínio aritmético. Essa etapa limitada não completa o
protocolo abaixo, especialmente aprendizado semântico, controles treináveis,
memória aproximada e medição de energia.

Hipótese operacional: sob orçamento igual, compor e revisar procedimentos a
partir de experiência melhora tarefas novas frente a alternativas simples.
O critério abaixo é proposto antes desse experimento; não foi aplicado
retroativamente como limiar ao teste acima.

1. Construir tarefas verificáveis de composição de operações numéricas e de
   texto, com subprocedimentos reutilizáveis, novas entradas, novas composições,
   mudança das frequências e retorno às tarefas antigas. Separar esses regimes
   no relatório. Não entregar identificadores de soluções ao roteador.
2. Comparar quatro braços com os mesmos especialistas, exemplos, feedback,
   capacidade de estado e teto de computação: grafo fixo com pesos treináveis;
   roteador convencional treinável sem mudança estrutural; esse roteador com
   cache limitado; versão com criação, fusão, remoção e reabertura de caminhos.
   A versão fixa também aprende: congelar todo aprendizado seria um controle fraco.
3. Separar desenvolvimento, validação e teste. Congelar regras e parâmetros
   antes do teste; usar pelo menos 20 sementes pareadas previamente definidas.
   Feedback online só chega depois da resposta, igualmente para todos os braços.
   Medir curvas de aprendizado, retenção e custo desde a primeira tarefa.
4. Cobrar busca, exploração, respostas erradas, atualização, consolidação,
   reconstrução e validação. Impor os mesmos limites de tempo e memória, contar
   timeouts como falhas e registrar custo por resposta correta. Medir tempo e
   memória reais; só afirmar economia energética com medição de energia.
5. Gate proposto: nos regimes de entradas novas e mudança de distribuição,
   reduzir pelo menos 10% o tempo total por resposta correta contra o melhor
   controle escolhido na validação, com limite inferior do IC pareado de 95%
   acima de zero; qualidade e retenção não podem cair mais de 1 ponto percentual
   (avaliar também a incerteza dessas diferenças). Publicar todos os regimes.
   Ganhar só em repetições idênticas não passa como aprendizado de procedimentos.
6. Remover separadamente consolidação e reabertura para atribuir o ganho.
   Se falhar, classificar como falha desta implementação ou inconclusivo conforme
   a precisão, investigar uma correção delimitada e registrá-la antes de novo
   teste. Não mudar continuamente tarefas e métricas para fabricar aprovação.

Uma implementação pode passar esse teste e ainda perder ao ser distribuída.
Somente depois executar o mesmo trabalho em máquinas reais, com baseline local,
custos de transporte, falhas, disponibilidade e energia medidos. Sucesso local
autoriza essa investigação; não demonstra AGI nem viabilidade em qualquer IoT.
