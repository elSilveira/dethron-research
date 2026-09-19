# Marcos e harness

Cada marco tem um documento com contrato, resultado, **controles que precisam
falhar**, limites e reprodução. A [evidência citada](evidence/README.md) está
publicada: dá para recalcular em vez de acreditar.

| Marco | O que estabelece |
| --- | --- |
| [G0](G0_REFERENCE.md) | Integração real com Reticulum/LXMF; mensagens sobrevivem ao crash dos propagadores |
| [G1](G1_INTEGRATION.md) | Caixa postal persistente, recibos, protocolo fechado |
| [G2](G2_PARTS.md) | Partes complementares e reconstrução. **Encerrado sem vantagem geral** — o registro diz isso |
| [G3](G3_GENERATIONS.md) | Gerações de nós e supervisores; nós sobrevivem a quem os criou |
| [G4](G4_INDEPENDENCE.md) | Entrega com a pilha IP cortada, com o controle que reprova quando o corte não aconteceu |
| [V1](V1_CUSTODY.md) | Custódia assinada: prova de entrada e pendência localizável. E o [recibo de volta](V1_RECEIPT_RETURN.md) a uma origem que nunca esteve online com o destino |
| [V2](V2_REPRODUCTION.md) | Roteiro de reprodução em máquina independente, com executor único |
| [V3a](V3A_BENCH.md) | Bancada em duas máquinas, janelas isoladas, encontro por instante declarado |
| [V3c](V3C_BENCH.md) | **Um objeto atravessou por um meio que não carrega IP**, com o destinatário provado sem nenhuma interface IP |

Para montar duas máquinas do zero: [preparação passo a passo](V3_SETUP.md).

## Estrutura

| Caminho | O que é |
| --- | --- |
| `dethron_gateway/` | A biblioteca: protocolo, wire, custódia, partes, reconstrução, caixa postal |
| `g1_*`–`g4_*`, `v1_*` | Laboratórios e auditores de cada marco |
| `v2_*` | Executor de reprodução e diagnóstico |
| `v3_*` | Bancada multi-máquina: cronograma, agente, executor, auditor, sonda serial |
| `run_*.py` | Os pontos de entrada. Nada mais é feito para ser chamado à mão |
| `tests/` | 166 testes; 8 são reproduções reais, que só rodam sob demanda |
| `evidence/` | Os artefatos que os documentos citam |
| `upstream/` | Um defeito encontrado no LXMF, com reprodução e correção |

## Rodar

```powershell
python -m venv window/.venv-gateway
window/.venv-gateway/Scripts/python.exe -m pip install -r window/requirements-gateway.txt
```

A suíte, a partir da raiz:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_v2_reproduction.py --fast-only
```

Esperado: `ran=166 skipped=8 PASS`. Os 8 pulados são as reproduções reais, que
levam cerca de uma hora e rodam com `run_v2_reproduction.py` sem `--fast-only`.

Cada fonte tem menos de 200 linhas, por convenção do projeto.
