# G3 — gerações de nós e de supervisores

16/09/2026. Fatia funcional de laboratório sobre Reticulum 1.5.4/LXMF 1.1.1.
O [G2 encerrado](G2_PARTS.md) autorizou esta fatia: testar H06, a travessia da
mensagem por gerações completas de nós, incluindo a troca do supervisor.

## Contrato

O objeto tem 24.576 bytes determinísticos, dividido em três partes exatas de
8.192 bytes pelo esquema `exact` já usado em G2. A origem `O` distribui uma parte
para cada transportador `A`, `B` e `C` e sai; o destinatário é `D`.

A execução tem quatro fases, cada uma em **um processo de supervisor diferente**:

| Fase | O que faz | Sobrevive ao fim da fase |
| --- | --- | --- |
| `seed` | Provisiona a credencial declarada, distribui as partes, aposenta a origem | A0, B0, C0 |
| `generation-1` | Levanta A1/B1/C1 vazios, transfere pela rede, aposenta A0/B0/C0 | A1, B1, C1 |
| `generation-2` | Levanta A2/B2/C2 vazios, transfere pela rede, aposenta A1/B1/C1 | A2, B2, C2 |
| `deliver` | Busca nos três contatos e reconstrói, ou recusa sem a credencial | nada |

Os transportadores são processos destacados que **continuam vivos quando o
supervisor termina**; o canal de comandos é um par de arquivos por nó, então
qualquer geração de supervisor pode assumir os nós ainda ativos. Um nó novo
ignora comandos das encarnações anteriores.

O supervisor seguinte só pode retomar a partir de três fontes declaradas:

1. `checkpoint-N.json`, validado por `g3_contract.py`, que aceita **apenas
   metadados públicos** — versão, geração, cenário, identidades públicas de
   origem/destino, manifesto do objeto, validade e, por transportador, destino,
   chave pública, nó de propagação e inventário cifrado. Qualquer campo extra,
   chave privada ou carga útil reprova o arquivo.
2. Os arquivos de controle dos nós **ainda vivos**, que contêm pid e porta.
3. A credencial persistente declarada do destinatário.

Cada geração aposentada é renomeada para `retired/` e todo supervisor instala um
hook de auditoria que transforma leitura sob `retired/` em `PermissionError`.
Um supervisor que ainda alcançasse uma geração aposentada falha ao iniciar, e
cada fase registra `guard: true` ao terminar. Para a fase `seed` isso só vale
depois que ela própria aposenta a origem; as garantias interessantes são as das
fases seguintes, que não conseguem ler o que aposentaram. Um sucessor sem
`checkpoint-0.json` recusa em vez de improvisar.

## Resultado

A [rodada final](results/gateway-g3-1789613422588119200/report.json), com
[fontes congelados](results/gateway-g3-1789613422588119200/sources.json),
passou nos dois cenários e no controle negativo: veredito `g3_scoped_pass`.

| Cenário | Tempo | Supervisores distintos | Transferências nativas | Aposentados | Resultado |
| --- | --- | --- | --- | --- | --- |
| `complete` | 229,9 s | 4 | 6 | O, A0–C0, A1–C1 | 24.576 bytes exatos, recibo verificado |
| `missing` | 198,9 s | 4 | 6 | O, A0–C0, A1–C1 | Recusa explícita, sem saída e sem recibo |

No cenário `complete`, as três gerações usaram **nove identidades distintas** de
transportador e o inventário cifrado permaneceu **idêntico nos três checkpoints**:
os mesmos bytes armazenados atravessaram duas trocas completas de frota. O
destinatário reuniu as três partes autenticadas em três contatos e produziu
`sha256 ada077a478903115055d93de132441ac15051b603ec36ca9a66cb74b2572dc17`.

No cenário `missing`, a credencial declarada do destinatário foi apagada antes da
entrega. O nó recusou iniciar com `declared credential is absent`; não houve
`output.bin` nem recibo. O serviço parou de forma explícita em vez de degradar
em silêncio ou recorrer a outra fonte.

O controle negativo de continuidade roda um supervisor de segunda geração em um
diretório sem checkpoint: ele falha apontando `checkpoint-0.json` ausente.

## Evidência e auditoria

Cada rodada preserva fontes congelados, versões, checkpoints, `timeline.jsonl`
de todas as fases, logs por fase, pacotes autenticados e relatório em
`results/gateway-g3-ID`. O auditor em `g3_audit.py` recomputa as alegações a
partir desses registros, sem confiar no relatório do experimento:

- cada fase foi registrada por um único pid e os quatro pids são distintos;
- cada transportador usou uma identidade diferente em cada geração e todos os
  originais, inclusive a origem, aparecem como aposentados;
- as seis transferências nativas carregaram exatamente uma mensagem cada;
- os três checkpoints trocam de frota e mantêm o mesmo inventário;
- os pacotes guardados pelo destinatário autenticam contra a chave da origem,
  estão entre as entradas declaradas, reconstroem o digest exato e o recibo local
  corresponde ao envelope esperado.

Esses eventos são evidência do harness, não atestação independente do hardware
nem de um supervisor hostil.

## Rodadas e verificações

Uma rodada anterior passou nos dois cenários antes de a execução pela via de
reprodução declarada reprovar na auditoria: uma transferência foi registrada com
`stored = 0` e inventário de um arquivo. Não foi perda de dados. O nó grava a
mensagem no armazenamento antes de o roteador terminar de indexá-la, então as
duas visões do mesmo estado divergem por instantes. O laço de transferência
aceitava só o inventário e podia aposentar a geração anterior nessa janela.

A correção espera as duas visões concordarem antes de declarar a transferência
concluída; a auditoria continua exigindo exatamente uma mensagem por
transferência, agora sem depender do instante da amostra. Essa rodada reprovada
continua em `results/gateway-g3-1789612781500495200`. A mesma passagem também
reduziu o custo do canal: a prova de vida de um nó abria um subprocesso a cada
50 ms de espera e passou a rodar a cada dois segundos.

- Testes G3 rápidos no ambiente fixado: **9 passaram, 1 opt-in pulado**.
- `unittest discover -s window/tests` no ambiente fixado: **115 passaram,
  5 opt-in pulados**.
- `python -m pytest window/tests probes/tests -q` no Python global:
  **154 passaram, 12 pulados**; módulos que dependem de RNS/LXMF são executados
  separadamente no ambiente fixado. G0–G2 reais não foram repetidos nesta entrega.
- Cada fonte de G3 tem menos de 200 linhas e os links documentais locais foram
  conferidos. A suíte global mantém o aviso preexistente de configuração do
  escopo de fixtures `pytest_asyncio`.

## Limites

Tudo ocorreu em um host, sobre TCP de loopback. "Trocar todos os nós" significa
trocar processos, identidades e diretórios na mesma máquina; não houve troca de
hardware, de operador nem de domínio de falha. O supervisor é substituído entre
fases, mas as fases são lançadas por um processo de prova; autonomia sem qualquer
supervisor não foi demonstrada.

O bloqueio das gerações aposentadas é um hook de auditoria do Python dentro do
processo sucessor. Ele prova que o sucessor não lê os diretórios aposentados; não
é isolamento de sistema operacional contra um supervisor hostil, que poderia
simplesmente não instalar o hook. Portas e pids vêm dos arquivos de controle dos
nós vivos: metadados de transporte, sem conteúdo nem chaves.

A credencial do destinatário é uma dependência persistente declarada. G3 mostra
que o serviço para explicitamente sem ela, não que exista recuperação sem chave.
Foram um objeto de 24 KiB e uma rodada por cenário, com duas trocas de frota;
não é estimativa estatística, não há rotatividade contínua e esta fatia não mede
tráfego, armazenamento ou energia. Rádio, independência da internet, demanda
comercial e tokens continuam não validados.

## Reprodução

Usar o ambiente fixado em [G0](G0_REFERENCE.md#reprodução), a partir da raiz:

```powershell
$env:PYTHONPATH='window'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p 'test_g3_*.py'
$env:RUN_GATEWAY_G3='1'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p test_g3_reference.py
Remove-Item Env:RUN_GATEWAY_G3
```

A campanha real leva cerca de sete minutos e grava cada cenário separadamente.
Artefatos locais incluem chaves de laboratório e são ignorados pelo Git.

## Decisão e próximo passo

H06 está verificado no escopo declarado: a mensagem atravessou duas gerações
completas de transportadores e quatro supervisores, sem consultar origem,
snapshot ou chave não declarada, e a retirada do recurso declarado indispensável
produziu falha explícita. Nada aqui sustenta autonomia sem supervisor, rádio ou
economia.

Próxima fatia: **G4 — independência lógica**, com corte da via externa, início a
frio e ponte alternativa, mantendo a regra de revisão antes de avançar.
