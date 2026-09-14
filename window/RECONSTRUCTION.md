# Reconstrução funcional por DNA

O v2 fornece `network::reconstruction::reconstruct(routes, context, revision)`.
Cada rota é um DNA com uma consulta idêntica (mesma entidade e sequência de
relações), mas pode usar fontes e entidades intermediárias diferentes.
O chamador declara as rotas alternativas; esta etapa não descobre rotas sozinha.

O algoritmo percorre fatos ativos de cada rota. Uma rota incompleta pode ser
substituída por outra completa. Todas as rotas completas precisam concordar na
conclusão. Uma contradição encontrada durante qualquer percurso impede aceitação.
Sem conclusão sustentada, o resultado é `abstained`, com conclusão nula.
IDs iguais com conteúdos diferentes são rejeitados entre rotas.

O relatório inclui fontes utilizadas, resultados de cada rota, comparação de
fontes (`source_checks`) e tamanho JSON dos DNAs (`dna_bytes`). Esses valores
medem percurso e volume de entrada; não medem tráfego real, energia ou custo total.
Há limite de 16 rotas, cada uma respeitando os limites existentes do DNA.

`Presentation::Bare` e `Presentation::Sentence` renderizam a mesma conclusão
como, por exemplo, `Paris` e `Conclusão: Paris.`. Isso separa a representação
textual da conclusão verificada. São templates determinísticos, não avaliação
semântica de prosa arbitrária produzida por um LLM. O avaliador anterior e o
scheduler continuam com seu contrato existente; esta API é explícita e separada.

## Probe reproduzível

No diretório window:

```powershell
cargo run --example reconstruction_probe
```

O exemplo executa nove cenários sintéticos sem resposta salva e sem worker:

| Cenário | Resultado esperado e observado |
| --- | --- |
| Duas rotas íntegras | Paris |
| Perda da rota A | Paris |
| Perda da rota B | Paris |
| Rota B incompleta, A íntegra | Paris |
| Única rota sem evidência final | Abstenção |
| Evidência final revogada | Abstenção |
| Revisão diferente | Abstenção |
| Contexto diferente | Abstenção |
| Rotas completas discordam | Abstenção |

Resultado: 9/9 cenários passaram; quatro conclusões corretas, cinco abstenções
esperadas e zero erros aceitos. São fixtures pequenas e declaradas: não estimam
a taxa de erro em dados reais. Os testes Rust também cobrem contradição dentro
de uma rota e rejeição de planos vazios, divergentes ou acima do limite.

## O que esta entrega demonstra

Uma conclusão estruturada pode ser recalculada de fatos sobreviventes por outra
rota, sem recuperar seu texto anterior. Não reconstrói fatos indispensáveis
ausentes de todas as rotas, pesos de modelo, nem memória arbitrária.

As fontes e a separação entre rotas são fornecidas pelo chamador. IDs distintos
não provam independência das origens. Omissão de fatos contraditórios pode mudar
o resultado: aceitação significa sustentação nos fatos fornecidos, não verdade
externa. Uma contradição escondida após um trecho ausente não é detectável pelo
percurso. Réplicas continuam tratando integridade e continuidade do estado;
reconstrução funcional deve ocorrer numa nova execução explícita, sem alterar
silenciosamente o plano autenticado nem repetir tarefas indeterminadas.

Próxima validação: fontes reais, falhas combinadas e comparação contra busca
determinística simples; depois medir tráfego e energia em máquinas distintas.
