# Reorganização de caminhos: implementação e evidência

**O mecanismo executável passou nas verificações funcionais. Não apresentou
vantagem de latência sobre os controles neste experimento.**

Implementação guiada pela descrição do autor em 2026-09-14: DNA encaminha
para uma região; um caminho conhecido resolve; uma receita mais curta é
proposta; os dois caminhos executam em paralelo durante validação; depois os
trons do caminho anterior ficam livres. Memória curta registra experiências,
média retém propostas e evidências, longa retém receitas reconstruíveis.

Escolhas iniciais explícitas: tarefas inteiras com resultado exato; especialistas
aritméticos pequenos; regiões com capacidades declaradas; composição algébrica
de operações executadas. Isso testa reorganização executável em domínio limitado,
não a aprendizagem de qualquer habilidade nem uma descrição biológica do cérebro.

## Fatias executáveis e testes

1. `src/reorganization/graph.rs`, `tests/graph.rs`: executar caminhos e produzir
   uma receita nova por composição de três operações contíguas. Rodar
   `cargo test --locked --offline --test graph`; antes da implementação, os
   testes devem falhar por ausência de resultado e de composição.
2. `src/reorganization/{memory,engine,execution}.rs`, `tests/reorganization.rs`:
   manter os dois caminhos, validar em paralelo, promover somente com evidência
   em entradas distintas, liberar a rota antiga e cobrar ambos os caminhos.
   Rodar `cargo test --locked --offline --test reorganization`; esperar falhas
   nos estados e entregas antes de implementar cada transição.
3. Memória e recuperação: reconstruir grafo com identidades novas sem cache de
   respostas; invalidar receitas por mudança de versão ou contradição externa;
   limitar estado e manter custos já gastos em falhas. Testes direcionados antes
   de cada comportamento.
4. `src/bin/reorganization.rs` e módulos do experimento: executar evidência
   reproduzível contra caminho fixo e um controle simples que compõe operações
   diretamente. Contabilizar exploração, validação e reconstrução. Concordância
   interna e acerto externo são métricas distintas. Medir tempo real sem tratar
   contagem abstrata de trabalho como energia.

Cada fonte e teste deve ficar abaixo de 200 linhas. O dashboard existente
continua sendo o experimento de fatoração; este mecanismo terá um executável
próprio para que seus resultados não sejam confundidos com os da v2 anterior.

## O que foi implementado

O esclarecimento do autor foi incorporado: reconstrução depende de DNA e de
memórias alcançáveis, com contexto recente e relevância geral em escalas distintas.

| Elemento | Comportamento executado |
| --- | --- |
| DNA | Registro de capacidade, versão da região e receitas de encaminhamento. A capacidade inicial é declarada; não há classificador de linguagem aprendendo regiões. |
| Proposta de caminho | Após duas entradas distintas, compõe três operações afins contíguas da rota observada. Os coeficientes do novo tron são derivados dessas operações; a resposta não é armazenada. |
| Validação | Caminho novo e referência executam em duas threads locais, sincronizadas por barreira. Três entradas distintas, excluindo as usadas na formação da proposta, são necessárias para promoção no contexto atual. |
| Liberação | Após promoção, só a rota curta executa normalmente. A referência fica dormente, disponível para revalidação; sua receita continua ocupando estado. Não são cinco processos físicos liberados. |
| Curta | Até 16 vestígios de execução, com entrada, contexto, versão e procedimento; expiram após 32 solicitações globais. |
| Média | Até uma proposta/evidência por região, no máximo oito. Retém receita, contexto e entradas de confirmação; expira após 128 solicitações sem confirmação. |
| Longa | Até quatro receitas validadas, sem respostas guardadas. Reutilização aumenta relevância; falta de espaço remove a menos relevante, com recência como desempate. |
| Reconstrução | Perder os nós executáveis permite reconstruir identidades novas a partir de uma receita compatível de longa ou média duração. Confiança contextual continua sendo verificada. |
| Falta de vestígios | Se todas as memórias foram removidas, executa o procedimento-base do DNA e reaprende. Não declara ter recuperado a memória perdida. |
| Reabertura | Contexto novo exige confirmação; a cada 16 solicitações da região há revalidação. Divergência remove o atalho e usa o resultado da referência. Mudança explícita de versão invalida memórias dependentes. |
| Validação externa | Feedback negativo remove confiança mesmo após consenso interno. Isso não inventa uma função correta se o procedimento-base também estiver errado. |

Os limiares 2/3/16/32/128 e capacidades são escolhas experimentais iniciais,
não constantes biológicas nem valores otimizados para demonstrar vantagem.
"Consenso" aqui é concordância entre os resultados de dois caminhos, não uma
votação de cinco agentes independentes. Ambos partem da mesma especificação.

Um exemplo aprendido:

```text
Antes: entrada → +2 → ×3 → −1 → absoluto → +7 → destinatário
Depois: entrada → (3x + 5) → absoluto → +7 → destinatário
```

O atalho funciona em valores novos porque contém uma operação reutilizável.
A primeira mutação reduz cinco nós a três; não substitui uma resposta por outra
em um cache. A composição preserva as fronteiras não lineares. Este operador
de mutação é escrito por nós: não há síntese irrestrita de código ou aprendizado
de semântica a partir apenas de exemplos. A implementação faz uma composição
por versão de procedimento, não uma busca aberta em grafos arbitrários.

## Executar e inspecionar

De dentro de `window`:

```powershell
python run_reorganization.py
```

O comando compila offline em release, executa demonstração e 20 sementes pareadas,
e cria uma pasta nova em `results/` com `demo.json`, `benchmark.json`,
`summary.json` e `manifest.json`. O manifesto inclui versões, ambiente e SHA-256
das fontes e do binário. As fontes são conferidas antes e depois da execução.

Para ver somente as transições ou mudar a quantidade de sementes:

```powershell
cargo run --release --locked --offline --bin reorganization -- demo
cargo run --release --locked --offline --bin reorganization -- bench 20
```

`demo.json` mostra nós utilizados, threads, contexto, promoção, reconstrução,
reabertura após falha injetada e nova aprendizagem. `learned_state` e `final_state`
expõem DNA e os três níveis de memória. O campo `sink` identifica o consumidor
lógico, distinto do ingresso; a API local é síncrona e retorna um recibo ao
controlador do experimento. Ainda não há entrega por rede ou filas entre agentes.

## Medições preservadas

Execução final: [summary.json](results/reorganization-20260914T114516Z-315b633c/summary.json).
Dados: [benchmark.json](results/reorganization-20260914T114516Z-315b633c/benchmark.json).
Transições: [demo.json](results/reorganization-20260914T114516Z-315b633c/demo.json).
Proveniência: [manifest.json](results/reorganization-20260914T114516Z-315b633c/manifest.json).

| Alternativa | Acertos | Unidades totais de trabalho | Tempo mediano por lote de 256 tarefas |
| --- | ---: | ---: | ---: |
| Caminho fixo | 5.120 / 5.120 | 61.640 | 0,07890 ms |
| Composição convencional direta | 5.120 / 5.120 | 47.480 | 0,07715 ms |
| Reorganização com validação e memória | 5.120 / 5.120 | 59.840 | 4,21400 ms |

Os quatro regimes têm 64 tarefas cada: entradas novas, mudança de contexto,
retorno ao contexto e revisão do procedimento. Todos recebem as mesmas entradas
e alterações por semente, limite de 1.000.000 unidades por execução e os mesmos
limites de representação. A ordem dos braços é rotacionada. O controle convencional
usa o mesmo operador de composição diretamente no procedimento declarado.

O adaptativo reduziu 2,92% das unidades frente ao caminho fixo, mas consumiu
26,03% a mais que a composição convencional e perdeu em tempo real. A unidade
contabiliza despachos e operações dos nós, exploração, composição, reconstrução,
validação e encargos limitados de manutenção; não representa uma instrução de CPU.
O tempo inclui inicialização, revisões, execução e feedback, inclusive criação
das threads de validação. Comparações de bootstrap no resumo são exploratórias;
os tempos dos controles são muito pequenos. Não foi feito um perfil que atribua
precisamente a perda de tempo a cada componente.

## Alcance do resultado

Estão verificadas a mudança estrutural limitada, a reutilização em entradas novas,
a confirmação contextual, a reconstrução dependente de vestígios e a reabertura.
Isso supera a antiga seleção entre três algoritmos prontos, mas não demonstra
vantagem geral do sistema. Neste domínio, um compositor convencional já possui
toda a informação necessária para obter o mesmo atalho sem esperar experiências.

Não foram implementados memória aproximada de linguagem, novas capacidades
semânticas, distribuição entre máquinas, recuperação após reiniciar o processo,
escalonamento de muitos trabalhos simultâneos ou integração desta memória aos
snapshots criptografados da v2. Duração de memória é lógica neste processo.
Energia e pico de memória residente não foram medidos; bytes de diagnóstico JSON
não são consumo de RAM. O protocolo mais amplo de FEASIBILITY.md permanece aberto.

O próximo experimento científico precisará de tarefas em que experiências revelem
estrutura que um compositor estático não conhece, mantendo controles capazes de
aprender e contabilizando seus custos. Não há base neste resultado para declarar
impossibilidade da proposta, AGI ou ganho energético.

## Verificação da entrega

23 testes Rust, 11 Python e cinco JavaScript passaram, junto com Clippy e
formatação. Testes novos foram exercitados com falhas antes das implementações
correspondentes; incluem corrupção de atalho, feedback contraditório, versão
obsoleta, perda de memórias e exclusão dos exemplos de formação da validação.
Fontes e testes novos têm menos de 200 linhas. O dashboard não recebeu alterações
visuais e não foi repetida a verificação manual no navegador nesta entrega.
