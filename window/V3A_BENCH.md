# V3a — bancada multi-máquina: a ressalva do host único, aposentada

18/09/2026. Fatia funcional sobre Reticulum 1.5.4/LXMF 1.1.1, em duas máquinas
Windows distintas na mesma rede local. O [V2 aprovado](V2_REPRODUCTION.md) deu o
pré-requisito: uma segunda máquina com o ambiente provado.

## O que esta fatia resolve

Todos os marcos de G0 a V1 carregam a mesma ressalva: *mesmo host, mesmo sistema
operacional, mesmo sistema de arquivos, mesmo domínio de falha*. V3a a retira,
mas só se resolver um problema que o host único escondia.

Num host só, o supervisor dirigia os nós por arquivos que compartilhava com eles.
Entre máquinas isso deixa de ser inocente: **o que carrega comandos durante a
janela também carrega conectividade**, e uma alegação de isolamento feita sobre um
canal de controle vivo não prova nada. É a mesma classe de erro do controle `dark`
do G4, que por um tempo passava por acidente.

## Contrato

Cada máquina recebe, **antes** da janela, um cronograma fixo e com hash, e o
executa do próprio disco. Não recebe mais nada.

| Peça | O que garante |
| --- | --- |
| `v3_schedule.py` | Passos ordenados, dentro da janela, com ação e argumentos fechados. Qualquer edição muda o hash |
| `v3_bench.py` | Identidades cunhadas antes, endereços derivados sem subir nó: nenhum passo descobre nada durante a janela |
| `v3_agent.py` | Espera o instante declarado, conta no próprio relógio monotônico, e lacra o diretório de controle |
| `v3_executor.py` | Traduz um passo em ação real de nó; não tem caminho por onde algo de fora peça o que o cronograma não declarou |

**Sem relógio comum.** Um marcador de partida precisaria de canal vivo para
chegar às duas máquinas — justamente o que a janela isolada não pode ter. O plano
declara o **instante**; cada agente espera por ele no relógio de parede, troca
para o monotônico e grava a hora que de fato observou. O desvio combinado entre
as máquinas fica legível na evidência, não suposto.

**Surdez por construção e por verificação.** O agente nunca lê canal de comando, e
além disso tira uma impressão digital do diretório de controle no instante em que
a janela abre e compara ao fechar. Rodada em que alguém dirigiu uma máquina no
meio **falha**.

## Resultado

Duas máquinas Windows na mesma rede, relé e origem em `alpha`, destinatário em
`beta`, objeto de 16.384 bytes:

| Medida | alpha | beta |
| --- | --- | --- |
| Passos executados | 8, sem falha | 5, sem falha |
| Atraso na abertura | 0,003 s | 0,011 s |
| Deriva máxima | 0,016 s | 0,000 s |
| Canal de controle | lacrado | lacrado |

**Desvio entre as janelas: 0,007 s.** Sete milissegundos entre duas máquinas sem
nenhum canal vivo entre elas, só pelo instante declarado.

O destinatário reconstruiu os 16.384 bytes exatos
(`sha256 9e390712447e77dedddd75386db336f7a07fb8b1cc210eff3fff9c172b15b4e6`),
com o pacote autenticado contra a chave da origem e o recibo local válido — a
mesma auditoria criptográfica dos marcos anteriores.

## O controle que decide se isto vale algo

Dois agentes no mesmo host executam esses mesmos cronogramas com a mesma
obediência. Uma alegação de V3a que não estabeleça **máquinas distintas** não vale
mais que o G1. Por isso o auditor:

- recusa de imediato um endereço de relé em loopback;
- exige que cada máquina tenha reportado sua identidade de host;
- exige que os nomes sejam diferentes;
- exige que o endereço do relé **pertença à máquina do relé e a nenhuma outra**.

Esse auditor ganhou seu lugar reprovando o ensaio de host único do próprio autor,
antes de qualquer rodada real.

## Rodadas e verificações

A primeira tentativa em duas máquinas **não produziu rodada pareada**, e o motivo
era um defeito de desenho: a pasta da bancada não era de uso único. Cada nova
tentativa encontrava os diretórios de nó da anterior, o `Daemon` se recusava a
lançar neles, e a rodada morria no passo 0 com `node already launched` — um erro
sobre um nó que nada dizia do problema real. Na tentativa que a segunda máquina
acompanhou, o relé nunca subiu, e o destinatário passou a janela buscando num
endereço onde não havia ninguém. Preparar ou executar numa pasta já usada passou a
ser recusado, com mensagem que nomeia causa e remédio.

A segunda tentativa falhou por rede, e o diagnóstico mostrou o valor de separar
hipóteses: `Initial connection ... could not be established: timed out` no
destinatário, enquanto o relé guardava a mensagem e esperava. A rede era Pública
no Windows e a porta estava bloqueada. O teste que eu havia proposto para checar
isso estava mal formulado — mandava testar a porta com a bancada parada, quando
nada escutava nela — e produzia `False` mesmo com o firewall correto. Um ouvinte
temporário separou as duas coisas em segundos.

- Testes V3 rápidos no ambiente fixado: **21 passaram**.
- `unittest discover -s window/tests` no ambiente fixado: **207 passaram,
  8 opt-in pulados**.
- Cada fonte do V3a tem menos de 200 linhas.

## Limites

Duas máquinas, um sistema operacional, uma rede sem fio doméstica, um objeto de
16 KiB, uma rodada. Não é estimativa estatística. Ethernet e Wi-Fi não foram
comparados como meios distintos, e nenhum enlace não-IP participou: **isto não é
G6 e não diz nada sobre diversidade física** — essa é a fatia V3b, com enlace
serial, que também passará a servir de base de tempo.

O canal de controle é uma pasta copiada à mão entre as máquinas, declarada e
excluída da janela pelo lacre. As máquinas compartilham a mesma infraestrutura de
rede e a mesma energia, então falhas correlacionadas continuam possíveis. O
auditor prova que ninguém dirigiu as máquinas durante a janela; não prova que um
operador hostil não poderia ter preparado a bancada de má-fé.

## Reprodução

Preparar duas máquinas do zero: [V3_SETUP.md](V3_SETUP.md), com o teste de rede que
separa firewall de bancada e a leitura do relatório.

A partir da raiz, nas duas máquinas, com o ambiente fixado em
[G0](G0_REFERENCE.md#reprodução). Na máquina do relé, descubra o IP local com
`ipconfig` e use uma pasta **nova** a cada rodada:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_v3_bench.py C:\dethron\bench3 <IP-DO-RELE> 600
```

Copie `C:\dethron\bench3\control` para a outra máquina, no mesmo caminho. Então,
em cada uma:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_v3_agent.py C:\dethron\bench3 alpha
window/.venv-gateway/Scripts/python.exe window/run_v3_agent.py C:\dethron\bench3 beta
```

A porta 45810 precisa aceitar entrada na máquina do relé. Ao terminar, traga a
pasta da outra máquina para junto da primeira e gere o veredito:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_v3_report.py C:\dethron\bench3
```

## Decisão e próximo passo

A evidência de G0–V1 sustenta em máquinas fisicamente distintas, com ninguém
dirigindo-as durante a janela. A ressalva do host único sai dos marcos anteriores
no que diz respeito a processo e sistema de arquivos; **não** sai no que diz
respeito a meio físico.

Próxima fatia: **V3b**, com um enlace serial/USB entre as duas máquinas — um meio
não-IP de verdade, que também remove o relógio de parede do encontro, porque o
pulso de partida passa a viajar pelo próprio fio.
