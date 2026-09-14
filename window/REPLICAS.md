# Recuperação por réplica no v2

A API `tron_v2::network::replica::ReplicaPlan::restore` cria uma cópia
autenticada em um diretório novo. Serve tanto para preparar uma réplica quanto
para restaurar após perda do journal original.

```rust,ignore
let plan = ReplicaPlan { tasks: &tasks, limits, key: &key, backend: &revision };
// O head vem do relatório de execução e é guardado fora das réplicas.
plan.restore(&[journal.clone()], &backup, &trusted_head)?;
// Depois de uma perda, com todos os coordenadores parados:
let chosen = plan.restore(&[backup, second_backup], &new_journal, &trusted_head)?;
// run_persistent(..., &new_journal, ...) retoma o estado verificado.
```

O destino não pode existir; seu diretório pai precisa existir. O chamador deve
ter controle exclusivo do destino e parar os escritores durante a cópia.
Cada candidato precisa passar pela autenticação da cadeia inteira, vínculo ao
plano/backend/chave e comparação com o head confiável. Uma réplica antiga não
serve como substituta silenciosa da versão solicitada. Os bytes copiados são
verificados novamente em diretório temporário antes da publicação por rename.
Se nenhuma cópia servir, retorna erro sem publicar um journal recuperado.

O teste `v2/tests/replica.rs` remove o original, rejeita sufixo perdido,
corrupção, origem ausente, chave incorreta e head vazio. Depois restaura pela
cópia íntegra, preservando registros, avaliação DNA aceita e custo acumulado,
sem chamar o worker novamente. Também rejeita sobrescrita do destino.
É um teste com worker sintético, não uma medição de qualidade de LLM.

## DNA e assertividade

O DNA fornecido no plano continua sendo necessário: fontes, relações, consultas
e versões orientam a reconstrução. Esta API exige conservar o plano e a chave
fora do journal; o backup não é um pacote autossuficiente de modelo e DNA.
O checkpoint preserva a avaliação histórica, não revalida fatos do mundo atual.
Se as evidências mudarem, é necessário construir um novo plano/execução.

Preservação íntegra do estado e assertividade de uma nova resposta são critérios
distintos. Uma futura regeneração pode produzir outra formulação correta.
O avaliador atual verifica respostas estruturadas derivadas das relações DNA;
não certifica equivalência semântica geral de textos. Esta entrega não adiciona
regeneração de respostas perdidas nem prova melhoria de assertividade.

## Limites

- Replicação explícita por API; sem configuração nova no CLI ou cópia automática.
- Diretórios locais acessíveis; nenhuma sincronização entre máquinas foi testada.
- Head confiável, plano e chave precisam sobreviver separadamente. Se o head
  externo também retroceder, a proteção contra rollback perde sua referência.
- Sem consenso, eleição de líder, failover concorrente ou garantia de perda zero.
- Mantém a política de execução indeterminada após queda, sem repetição automática.
- Arquivos sincronizados; durabilidade do rename sob corte de energia não testada.
- Não prova imortalidade, economia energética, transporte por rádio ou compressão.

Validação desta entrega: 40 testes Rust no v2 e 63 no window passaram;
Clippy do v2 passou. Python e inferência com pesos reais não foram reexecutados.
