# Unidades menores de DNA: implementação e resultado

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Estudo de modelo/avaliação com escopo secundário. Seus resultados não demonstram conectividade mesh, autonomia da internet ou sobrevivência global. Preservar datas e limites dos experimentos abaixo. [Índice atual](../README.md) - [Plano de decisão](../DETHRON_VALIDATION_PLAN.md) - [Evidências](../DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

O v2 oferece `network::atomic::AtomicDna`. Cada unidade contém uma relação
anotada, sua fonte, contexto, revisão e revogação. Seu hash inclui esses campos.
Receitas referenciam unidades; um fato compartilhado é armazenado uma única vez.
São unidades de evidência em memória, não novos modelos neurais, processos ou
instâncias do TRON histórico com memória e aprendizado próprios.

`compile` organiza rotas existentes; `inventory` expõe fatos e referências;
`lose_source` provoca a perda de uma unidade; `reconstruct` usa o verificador
de rotas do v2. `evidence_text` apresenta apenas relações alcançáveis, mantendo
conflitos visíveis. A transformação não extrai fatos de prosa nem descobre novas
rotas. Não encurta a cadeia lógica; simplifica as unidades e sua representação.

Os testes demonstram duas rotas com cinco fatos únicos, incluindo um fato
compartilhado. Remover um fato de uma rota permite usar a outra; remover o fato
compartilhado indispensável exige abstenção. Também verificam versões, conflitos
e rejeição de conteúdos diferentes com a mesma identidade de fonte.

## Comparação real

Executar no window: `python run_atomic.py`.
Este launcher usa os pesos locais e o ambiente CUDA existentes no Windows.
Há aquecimento registrado separadamente e alternância de ordem entre os dois
modos a cada caso. Oito perguntas do documento já usado no desenvolvimento,
16 gerações, mesmos fatos, prompt e limite de 256 tokens. Apenas a representação
da evidência muda: parágrafos selecionados versus relações atômicas com IDs.

Resultado: `results/atomic-20260914T211804Z-f7970faf/report.json`.

| Medida | Parágrafos selecionados | Relações atômicas |
| --- | --- | --- |
| Respostas corretas | 5/8 | 2/8 |
| Corretas nos cinco casos sustentados | 4/5 | 2/5 |
| Abstenções corretas nos três casos sem resposta | 1/3 | 0/3 |
| Respostas sustentadas com citações aceitas | 1 | 1 |
| Erros aceitos | 0 | 0 |
| Falhas de formato | 3 | 4 |
| Gerações truncadas | 1 | 2 |
| Tokens avaliados | 2.744 | 1.555 |
| Tempo somado das chamadas | 52,30 s | 43,41 s |

O DNA determinístico acertou 8/8. O aquecimento custou 22 tokens adicionais.
A relação atômica permitiu resposta com cadeia completa no caso do local de
armazenamento, mas falhou no caso de recuperação após perda da rota A, que o
modo com parágrafos resolveu. Responder sempre UNKNOWN acertaria 3/8.

## Veredito

O resultado não confirma melhora de assertividade por esta representação.
Houve redução de aproximadamente 43% nos tokens, acompanhada de queda nos
acertos. Menos tokens não prova eficiência por resposta correta nem economia
energética. Uma rodada, com ordem alternada mas sem repetições balanceadas,
não constitui benchmark confiável de latência.

A organização interna em átomos é reutilizável e preserva identidade e perdas.
Sua apresentação direta com setas não será promovida a padrão do documento.
O próximo experimento deve separar granularidade de apresentação: comparar os
mesmos fatos atômicos expressos em frases curtas, antes de adicionar mais nós.
Depois validar em documentos inéditos; estes oito casos continuam sendo
desenvolvimento. Unidades pequenas não tornam fontes independentes e fatos
compartilhados continuam sendo pontos cuja perda pode bloquear todas as rotas.

## Integridade e limites

O auditor Python recalcula seleção, conclusão, citações e hashes dos átomos,
confere o dataset fixado, prompts, respostas brutas e custos. Relatório e manifest
preservam evidência completa. Não é atestação contra fabricação coerente de todos
os registros. O inventário completo tem metadados e hashes: seu tamanho não deve
ser confundido com o texto compacto enviado ao modelo, nem com tráfego medido.

As suítes Rust do v2 e window e o Clippy passaram. A suíte Python executou 30
testes, incluindo três repetidos por importação da classe auxiliar de fixtures.
Não houve nova interface visual nesta entrega; o dashboard documental existente
mantém seus modos anteriores. O experimento atômico tem launcher e relatório
próprios, sem alterar silenciosamente a comparação histórica.
