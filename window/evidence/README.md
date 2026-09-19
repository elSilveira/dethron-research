# Evidência publicada

Os artefatos que os documentos de marco citam. `window/results/` continua sendo o
diretório de trabalho descartável que as sondas escrevem; isto aqui é o subconjunto
que sustenta as afirmações, para que se possa **recalcular em vez de acreditar**.

| Pasta | Marco |
| --- | --- |
| `gateway-g0-*` | [G0](../G0_REFERENCE.md) — integração de referência |
| `gateway-g1-*` | [G1](../G1_INTEGRATION.md) — protocolo e caixa postal |
| `gateway-g2-*`, `g2-comparison-*` | [G2](../G2_PARTS.md) — partes e reconstrução |
| `gateway-g3-*` | [G3](../G3_GENERATIONS.md) — gerações de nó |
| `gateway-g4-*` | [G4](../G4_INDEPENDENCE.md) — independência da pilha IP |
| `gateway-v1-*` | [V1](../V1_CUSTODY.md) — custódia e [recibo](../V1_RECEIPT_RETURN.md) |
| `v3a-network-20260918/` | [V3a](../V3A_BENCH.md) — bancada em duas máquinas por rede |
| `v3c-serial-20260918/` | [V3c](../V3C_BENCH.md) — bancada por enlace sem IP |

## Duas ressalvas de proveniência

Os relatórios do V3a e do V3c trazem um campo `commit`. No do **V3a** ele nomeia o
código que **auditou** a rodada, não o que a executou: aquele relatório nasceu com o
campo quebrado — o `git` recusava o repositório por *dubious ownership* — e foi
regerado depois, a partir da mesma evidência intacta. O do V3c nomeia o código que
de fato rodou a bancada.

O `report.json` do G3 contém um caminho absoluto com o nome de usuário do Windows
de quem executou. Ele faz parte da mensagem de um **controle negativo** — uma
credencial declarada e ausente — e foi mantido como saiu. Editar um artefato para
deixá-lo apresentável custaria mais do que o nome vale.
