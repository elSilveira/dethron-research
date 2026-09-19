# G4 — independência lógica da via externa

17/09/2026. Fatia funcional de laboratório sobre Reticulum 1.5.4/LXMF 1.1.1.
O [G3 executado](G3_GENERATIONS.md) autorizou esta fatia: cortar a via externa,
iniciar a frio sem ela e entregar por uma ponte alternativa.

## O problema que este experimento precisava resolver

Em G0–G3 a via de laboratório era TCP de loopback. Cortar uma interface TCP e
usar outra interface TCP não provaria nada: seria o mesmo caminho com outro nome.
Por isso, aqui a "via externa" é **a própria pilha IP**, e a ponte alternativa
não pode tocá-la em nenhum ponto.

A ponte usa o `PipeInterface` nativo do Reticulum: o nó troca quadros HDLC pelo
stdin/stdout de um processo filho, e os dois filhos trocam bytes por arquivos
append-only em um diretório. Nenhum socket participa do caminho.

    nó O ──ponte──> arquivos ──ponte──> relé A
    relé A ──ponte──> arquivos ──ponte──> nó D

Remover o meio é renomear o diretório do canal: o software continua idêntico e
os bytes entregues durante o corte simplesmente não chegam.

## Contrato

O objeto tem 16.384 bytes determinísticos, enviado como uma parte exata pelo
mesmo caminho autenticado do G1–G3. A origem `O` submete ao nó de propagação do
relé `A` e sai; o destinatário `D` busca depois, com a credencial persistente
declarada. Quatro cenários, com resultado exigido antes da execução:

| Cenário | Configuração | Resultado exigido |
| --- | --- | --- |
| `ip` | só TCP; linha de base e controle positivo da evidência | entrega |
| `bridged` | **nenhuma interface IP desde o boot**, só a ponte | entrega os bytes exatos |
| `dark` | meio removido durante toda a janela de entrega | **não** entrega; objeto fica pendente |
| `cut` | meio removido na primeira tentativa, restaurado na segunda | entrega após a restauração |

`bridged` é o início a frio que o plano exige: o nó nunca teve caminho IP, não é
um corte aplicado depois de funcionar.

## Resultado

A [rodada final](evidence/gateway-g4-1789615587351184200/report.json), com
[fontes congelados](evidence/gateway-g4-1789615587351184200/sources.json), passou
nos quatro cenários em 166,2 s: veredito `g4_scoped_pass`.

| Cenário | Tempo | Entregou | Endpoints IP observados | Bytes pela ponte | Perdidos no corte |
| --- | --- | --- | --- | --- | --- |
| `ip` | 17,5 s | Sim | **3 em 2 processos** | — | — |
| `bridged` | 19,0 s | Sim | **0 em 6 processos** | 32.701 | 0 |
| `dark` | 63,6 s | **Não** | 0 em 6 processos | 0 | 53 |
| `cut` | 66,2 s | Sim | 0 em 6 processos | 32.694 | 53 |

No cenário `dark`, a busca nativa terminou em estado de falha, `D` não produziu
saída nem recibo e o relé **continuou guardando o objeto**: pendência preservada,
sem sucesso falso. No `cut`, a primeira tentativa falhou com 53 bytes perdidos no
meio removido e a segunda, após restaurar o diretório, entregou os bytes exatos.

## Por que a ausência de caminho oculto é verificável

Um "zero" só vale se a ferramenta que o produziu souber enxergar um caminho real.
Por isso o cenário `ip` é controle positivo obrigatório: nele o `netstat` do
sistema **precisa** reportar endpoints, e reportou três. Nos cenários isolados a
mesma ferramenta, aplicada aos mesmos tipos de processo, reportou zero.

A verificação cobre quatro camadas independentes:

1. **Configuração.** O auditor relê do registro a configuração de cada nó e exige
   que os três sejam isolados nos cenários sem IP: só `PipeInterface` e
   `share_instance = No`. Sem essa segunda condição o próprio Reticulum abriria
   a porta da instância compartilhada em 127.0.0.1.
2. **Sistema operacional.** Endpoints TCP/UDP dos **nós e também das pontes**,
   pelos PIDs: seis processos inspecionados por cenário isolado, zero endpoints.
   As pontes entram na conta porque um caminho oculto poderia estar nelas.
3. **Meio.** Cada ponte mantém um livro-razão do que carregou. Nos cenários com
   entrega, mais bytes do que o objeto atravessaram os arquivos; no `dark`, zero
   bytes atravessaram e 53 se perderam contra o meio ausente.
4. **Conteúdo.** Os pacotes guardados por `D` autenticam contra a chave da origem,
   correspondem à submissão declarada, reconstroem o digest exato e o recibo local
   bate com o envelope esperado, pela mesma auditoria de G1–G3.

Os testes do auditor incluem os casos em que ele **deve reprovar**: nó que ainda
alcança IP, endpoint presente em cenário isolado, linha de base IP sem nenhum
endpoint, amostra que não inspecionou processo algum, corte sem perda e objeto que
não atravessou o meio.

## Limites

Isto demonstra independência da **pilha IP**, não independência física. Mesmo
host, mesmo sistema operacional, mesmo sistema de arquivos e mesmo domínio de
falha. O canal de arquivos não tem perda, latência, alcance nem contenção de um
meio real; a única perda medida foi a que o corte provocou. Rádio e dois meios
físicos distintos continuam sendo G6, e nada aqui sustenta alegação de operação
sem internet em campo.

A evidência de sockets é uma amostra tirada durante a janela de entrega, não
captura contínua de pacotes. O `netstat` mostra endpoints do sistema operacional;
não prova ausência de canais laterais que não usem sockets, e o próprio
experimento usa um desses canais, de propósito. O corte é a remoção de um
diretório, não interferência física. Foram uma rodada por cenário e um objeto de
16 KiB, sem estimativa estatística.

## Reprodução

Usar o ambiente fixado em [G0](G0_REFERENCE.md#reprodução), a partir da raiz:

```powershell
$env:PYTHONPATH='window'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p 'test_g4_*.py'
$env:RUN_GATEWAY_G4='1'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p test_g4_reference.py
Remove-Item Env:RUN_GATEWAY_G4
```

A campanha real leva cerca de três minutos e grava cada cenário separadamente.
Artefatos locais incluem chaves de laboratório e são ignorados pelo Git.

## Rodadas e verificações

Três defeitos reais apareceram antes do resultado e estão corrigidos com teste:

- O comando da ponte era citado com aspas. O `configobj` remove as aspas externas
  e o `shlex` juntava tudo num argumento só, então o nó nem subia. O contrato
  passou a construir e validar o comando, recusando caminho com espaço ou aspas.
- Construir a configuração do destinatário **recriava o diretório do canal**, o
  que desfazia o corte e fazia o cenário `dark` entregar. Criar o meio virou ato
  explícito, e restaurar um meio que reapareceu sozinho agora é erro.
- Um nó encerrado de imediato não recolhe a ponte que o Reticulum criou, e as
  pontes ficavam órfãs. O laboratório e o probe passaram a recolhê-las.

A execução pela via de reprodução declarada repetiu o resultado em 167,0 s, com
os mesmos vereditos por cenário e a mesma contagem de endpoints:
[segunda rodada](evidence/gateway-g4-1789615826730038800/report.json).

- Testes G4 rápidos no ambiente fixado: **24 passaram, 1 opt-in pulado**.
- `unittest discover -s window/tests` no ambiente fixado: **139 passaram,
  6 opt-in pulados**.
- `python -m pytest window/tests probes/tests -q` no Python global:
  **167 passaram, 14 pulados**; módulos que dependem de RNS/LXMF são executados
  separadamente no ambiente fixado. G0–G3 reais não foram repetidos nesta entrega.
- Cada fonte de G4 tem menos de 200 linhas e os links documentais locais foram
  conferidos. A suíte global mantém o aviso preexistente de configuração do escopo
  de fixtures `pytest_asyncio`.

## Decisão e próximo passo

A entrega no escopo declarado não depende da pilha IP, e retirar todas as pontes
impede a entrega preservando a pendência, como o plano exigia. Isso não autoriza
alegar autonomia física nem operação por rádio.

Próxima fatia: **G5 — sobrevivência**, com campanha de 5% sob distribuições de
perda escolhidas, aleatórias, correlacionadas e direcionadas, com placar separado
por modelo de falha.
