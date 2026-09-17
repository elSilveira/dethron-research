# Utilidade, diferenciação e comparação de respostas

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Estudo de modelo/avaliação com escopo secundário. Seus resultados não demonstram conectividade mesh, autonomia da internet ou sobrevivência global. Preservar datas e limites dos experimentos abaixo. [Índice atual](../README.md) - [Plano de decisão](../DETHRON_VALIDATION_PLAN.md) - [Evidências](../DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

**Enquadramento atualizado:** o objetivo central esclarecido pelo usuário é a
rede de mensagens resiliente entre gerações. Este estudo é uma aplicação
secundária. Veja [direção da rede Dethron](../DETHRON_NETWORK_DIRECTION.md).

Data: 15/09/2026. Estado: etapa 1 executada e auditada; sem alegação de novidade científica.

## Decisão de direção

Há uma aplicação plausível: consultar documentos locais com fontes verificáveis
e recuperar essas fontes após falhas. Uma integração simples e econômica pode
ser útil mesmo quando seus mecanismos individuais já são conhecidos.
O valor específico do projeto ainda precisa ser medido frente a alternativas.

Não foi demonstrado um novo princípio de inteligência, compressão de conhecimento
sem perdas, inferência distribuída de um LLM, nem uma vantagem exclusiva do DNA.
Esta revisão não é pesquisa exaustiva de anterioridade ou análise de patentes.

| Componente | Alternativas existentes | Diferencial a testar |
| --- | --- | --- |
| Relações e seleção de evidências | GraphRAG, bancos de grafos e recuperação de trechos | Citações completas e cobertura com menos custo |
| Hashes, cópias e recuperação | Armazenamento endereçado por conteúdo e replicação | Recuperação integrada à tarefa, com custo e limites explícitos |
| Orquestração de perguntas e modelos | Pipelines de RAG, como Haystack | Operação local simples e rastreável |
| Bloqueio de resposta sem suporte | Avaliadores e validação de saídas | Menos erros aceitos sem abstenção excessiva, em avaliação independente |

Referências primárias consultadas:

- [GraphRAG: modos e comparação com busca básica](https://microsoft.github.io/graphrag/query/overview/).
- [Haystack: recuperadores para RAG](https://docs.haystack.deepset.ai/docs/retrievers).
- [IPFS: endereçamento por conteúdo](https://ipfs.tech/).
- [Anthropic: preservar contexto de trechos](https://www.anthropic.com/engineering/contextual-retrieval).

Essas referências estabelecem alternativas e mecanismos conhecidos. Não provam
superioridade de qualquer solução no nosso cenário, que exige comparação direta.

## Evidência anterior que orienta o trabalho

- Recuperação local: 3/3 provas reconstruíram 19 processos a partir de um nó
  com cópia completa. Todos na mesma máquina; controlador e chaves disponíveis.
- Documento: texto inteiro 4/8, seleção por DNA 5/8; uma resposta sustentada
  aceita com citações completas no modo selecionado.
- Átomos apresentados com setas: 2/8, contra 5/8 dos parágrafos selecionados.
  Menos tokens vieram acompanhados de menor qualidade.

Fontes: [sobrevivência](PROCESS_SURVIVAL.md), [documento](DOCUMENT_PROBE.md),
[átomos](ATOMIC_DNA.md). Os relatórios anteriores permanecem preservados.

## Etapa 1: diagnóstico controlado implementado

Executar a partir da raiz:

```powershell
python window/run_comparison.py
```

Usa `.venv-neural`, checkpoint local identificado por hashes e CUDA por padrão.
`--device cpu` é uma escolha explícita; não existe fallback silencioso ou download.
O processo tem prazo de 600 segundos e preserva saídas parciais em caso de falha.

Oito casos existentes, quatro modos, 32 gerações:

1. `full`: documento inteiro disponível em cada cenário.
2. `lexical`: até quatro seções por similaridade cosseno TF-IDF, usando somente
   pergunta e texto disponível. Sem rotas, gabarito, embeddings ou expansão de consulta.
3. `selected`: parágrafos alcançados pelos caminhos DNA fornecidos.
4. `sentences`: os mesmos fatos selecionados expressos em frases com IDs de fonte.

Prompt, parser, modelo e máximo de 256 tokens de saída são iguais entre modos.
Os prompts históricos de `full` e `selected` são preservados. Não há tentativa
de correção, resposta inserida pelo gabarito ou promoção automática de modo.
Cada prompt permanece limitado a 1024 tokens, sem truncamento de entrada.

A ordem dos modos gira a cada caso; cada modo ocupa cada posição duas vezes.
Um aquecimento é registrado separadamente. Isso não substitui repetições da
mesma tarefa em ordens diferentes para avaliar variabilidade de tempo.

### Controles e limitações

- Todos os casos são desenvolvimento; não são avaliação inédita.
- O DNA recebe fatos e caminhos manualmente anotados. A busca lexical recebe
  texto e pergunta; a comparação de inferência não equaliza custo de preparação.
- TF-IDF é um controle simples e limitado, não representa o melhor RAG disponível.
  Não usa lematização, sinônimos, busca semântica ou expansão por múltiplas etapas.
- O modo em frases resume relações anotadas; não é extração automática de prosa.
- Este launcher usa diretamente o runtime Python existente. Não testa novamente
  o executor Rust, transporte v2 ou sobrevivência durante inferência.
- A auditoria reutiliza a referência Python de relações e regenera os pedidos.
  Não é implementação independente de recuperação nem prova contra falsificação
  coerente de todos os registros. Custos registrados não são medidos novamente.
- `supported_accepted` significa aprovação pelo avaliador com acesso à referência.
  Não representa decisão de um guard implantado. Por isso não se publica uma
  taxa artificial de zero falsos aceites derivada desse mesmo gabarito.

### Medidas e artefatos

Separar acerto final, acerto nos cinco casos sustentados, aprovação com citações
completas e presentes no contexto, abstenção válida nos três casos sem resposta,
formato inválido, truncamento e erro de execução. Erros permanecem no denominador.

Registrar tokens e tempo observados, custo de aquecimento e carga do modelo,
tempo de preparação automática e tokens por resposta útil verificada. O custo
manual de anotar fatos fica explicitamente desconhecido; não alegar custo total
menor nem economia energética. Com erro de execução, total de tokens é desconhecido.

`results/comparison-<data>-<id>/` contém plano e dataset, identidade do modelo,
aquecimento, respostas brutas JSONL, relatório, status e logs. O relatório inclui
hashes de código e artefatos. Arquivos de evidência são criados sem sobrescrever.

## Resultado real desta etapa

Execução: [comparison-20260915T132942Z-19a1b580/report.json](results/comparison-20260915T132942Z-19a1b580/report.json).
DeepSeek-R1-Distill-Qwen-1.5B local, CUDA, bfloat16, geração greedy.
As 32 chamadas terminaram sem erro de execução; saídas truncadas contam como
falhas de conclusão. Os arquivos de evidência incluem pesos e tokenizer por hash.

| Medida | Texto inteiro | Busca lexical | DNA: parágrafos | DNA: frases |
| --- | ---: | ---: | ---: | ---: |
| Resposta final correta | 4/8 | 3/8 | 5/8 | 2/8 |
| Acertos nos cinco casos sustentados | 3/5 | 3/5 | 4/5 | 2/5 |
| Sustentadas com citações completas aceitas | 0/5 | 0/5 | 1/5 | 1/5 |
| Abstenção válida | 1/3 | 0/3 | 1/3 | 0/3 |
| Falhas de formato | 1 | 2 | 3 | 3 |
| Gerações truncadas | 1 | 1 | 1 | 2 |
| Tokens de entrada + saída | 5.520 | 2.962 | 2.744 | 1.554 |
| Segundos somados de inferência | 37,80 | 36,29 | 53,66 | 42,91 |

Veredito: frases curtas não resolveram a queda observada com átomos. Preservar
parágrafos como referência de desenvolvimento; não promover o modo em frases.
O placar de texto inteiro e parágrafos reproduziu os acertos históricos.
Esta repetição não aumenta o número de documentos independentes avaliados.

O DNA anotado superou este controle lexical em acerto final, mas a diferença
vem de oito casos conhecidos e preparação privilegiada. Não demonstra vantagem
sobre RAG convencional bem configurado nem viabilidade de extração automática.
Apenas uma resposta sustentada foi aprovada nos dois modos DNA. Não há base
para chamar o sistema de confiável para uso geral ou para publicar economia total.

Próxima etapa concreta: investigar separadamente aderência ao formato final,
limite de geração e citações, mantendo o protocolo atual como baseline arquivado.
Qualquer novo prompt, template ou limite deve receber nova versão e ser aplicado
a todos os modos. Não ajustar o parser para aceitar respostas incorretas.

## Próximos passos e critérios para continuar

| Etapa | Trabalho | Condição para concluir |
| --- | --- | --- |
| 1 — concluída | Rodar e auditar os quatro modos de desenvolvimento | 32 gerações e relatório bruto publicados localmente |
| 2 | Diagnosticar formato, citações e truncamento separadamente | Uma alteração por vez, protocolo versionado, mesmo orçamento por modo |
| 3 | Comparação mais forte e preparação | Busca híbrida/semântica e custo de extração; orçamento de ajuste equivalente |
| 4 | Avaliação inédita | Documentos e perguntas separados, gabaritos revisados sem ver respostas do modelo |
| 5 | Falhas durante tarefa documental | Mesmo conjunto antes/depois, processo e depois máquina, sem evidência indevida |
| 6 | Piloto de uso | Utilidade observada para um usuário real e custo de operação aceitável |

Proposta para etapa 4: pelo menos dez documentos novos em português e inglês,
perguntas diretas, paráfrases, cadeias de relações, ausência, conflito e versões.
Fixar conjunto, rótulos, regras, prompts, parser, recuperação e orçamento antes
de executar os candidatos. Fazer revisão independente dos rótulos; renomear
Atlas/Mira ou repetir uma geração determinística não cria independência.
Relatar diferenças pareadas e incerteza considerando agrupamento por documento.
Esta proposta ainda não foi executada e não define suficiência estatística universal.

Continuar a camada DNA se melhorar cobertura com suporte completo sem aumentar
erros aceitos, ou preservar qualidade reduzindo custo total, em dados inéditos.
Repetir tempos com ordens balanceadas antes de alegar ganho de desempenho.
Se a vantagem desaparecer diante de busca simples ou do custo de preparação,
simplificar essa camada. A recuperação de armazenamento pode ter valor separado.

## Implementação e validação

- `comparison_inputs.py`: controle lexical, frases e plano; testes de seleção,
  fontes removidas, conflitos, ausência de vazamento do gabarito e ordem.
- `comparison_audit.py`: reavaliação de registros completos, citações, custos,
  denominadores e rejeição de alterações.
- `run_comparison.py`: inferência, evidências e preservação de falhas.
- Testes novos em `tests/test_comparison_{inputs,audit,run}.py`.

Cada etapa teve falha comportamental observada antes da implementação:
4 testes de entradas, 4 de auditoria e 2 de execução. Comandos direcionados:

```powershell
$env:PYTHONPATH='window'
python -m pytest window/tests/test_comparison_inputs.py window/tests/test_comparison_audit.py window/tests/test_comparison_run.py -q
python -m pytest window/tests probes/tests -q
```

Não foi necessário alterar o núcleo Rust nem a interface visual.
Passaram 11 testes novos e 124 testes na suíte Python Window + probes.
Os seis arquivos novos de código/teste têm no máximo 95 linhas cada.
Não houve execução nova das suítes Rust ou do navegador, pois essas camadas
não foram alteradas; a integração exercitada foi o modelo Python local.
