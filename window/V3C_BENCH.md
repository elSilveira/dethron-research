# V3c — um meio que não carrega IP

18/09/2026. Fatia funcional sobre Reticulum 1.5.4/LXMF 1.1.1, em duas máquinas
Windows fisicamente distintas, ligadas por um enlace Bluetooth SPP. O
[V3a](V3A_BENCH.md) montou a bancada de duas máquinas; esta troca o meio entre elas.

## O que esta fatia resolve

Todo marco anterior atravessou IP. O plano mestre aposta que a sobreposição vive
sem a pilha da internet, e isso nunca tinha sido exercido: uma alegação de
independência feita sobre TCP não vale nada.

A dificuldade não é configurar um enlace serial. É **provar que o objeto não podia
ter ido por outro caminho**. Um destinatário que tenha uma interface IP, mesmo sem
usá-la, destrói a alegação — porque a interface que ele não usou continua sendo um
caminho que ele tinha.

## Contrato

O destinatário recebe uma interface serial e **nada mais**:

| Peça | O que garante |
| --- | --- |
| `config_text(..., serial={'only': True})` | O nó do destinatário nasce com uma interface só. Pedir contatos IP para ele é recusado como contradição |
| `v3_audit.medium()` | Lê o arquivo de configuração que o nó **escreveu em disco**, não o cronograma que o pediu, e exige o conjunto de interfaces igual a `['Serial']` |
| `v3_agent.preflight()` | Recusa, ao carregar, uma porta que esta máquina não tem — antes da espera, não depois |
| `v3_bench.TIMES['serial']` | O relé abre o enlace primeiro; nada é escrito nele antes das duas pontas estarem nele |

O relé é o único nó com transporte ligado, porque é o único que fica entre dois
meios. Um relé que não encaminha entre eles faz do segundo meio enfeite.

## Resultado

Veredito `v3c_scoped_pass`, sobre o commit `2a38607`:

| Medida | alpha (`elSilveira`) | beta (`DESKTOP-CURVS8Q`) |
| --- | --- | --- |
| Passos executados | 8, sem falha | 6, sem falha |
| Atraso na abertura | 0,001 s | 0,014 s |
| Deriva máxima | 0,016 s | 0,016 s |
| Canal de controle | lacrado | lacrado |
| Interfaces do nó | ouvinte loopback + serial | **`['Serial']`** |

**Desvio entre as janelas: 0,012 s.** A origem entregou 29.921 bytes empacotados
ao relé aos 90 s. A primeira busca do destinatário, aos 240 s, pegou a sincronia em
curso; a segunda, aos 320 s, completou. O relé guardava uma mensagem aos 240 s e
nenhuma aos 480 s.

O destinatário reconstruiu os 16.384 bytes exatos
(`sha256 9e390712447e77dedddd75386db336f7a07fb8b1cc210eff3fff9c172b15b4e6`), com o
pacote autenticado contra a chave da origem e o recibo local válido.

## O controle que decide se isto vale algo

Que as duas máquinas são distintas: processadores de fabricantes diferentes
(AMD Ryzen e Intel), nomes diferentes, e **nenhum endereço em comum** — o auditor
recusa a rodada se as duas compartilharem um só.

Que o meio não carrega IP: o auditor abre
`beta/D/rns/config` — o arquivo que o nó escreveu, não o que pedimos — e exige
`['Serial']`. Dez controles cobrem as recusas, incluindo a de um destinatário que
apenas *escuta* em TCP sem nunca usar.

**Isto também aposenta a ressalva de host único** que ficou aberta no V3a: aqui
`distinct_machines.evidenced` é verdadeiro, por nome e por endereços disjuntos.

## Rodadas e verificações

A primeira rodada falhou nas duas máquinas e custou oito minutos de janela para
dizer isso. O nó do destinatário morreu com `OSError 1168` e o relé, logo depois,
travou — e travou de um jeito instrutivo: `RNS/Interfaces/SerialInterface.py:131`
abre a porta com `write_timeout = None`, então `process_outgoing` bloqueia para
sempre escrevendo num enlace sem ninguém do outro lado. Duas falhas, uma causa.

Meu primeiro diagnóstico do 1168 estava errado. `Elemento não encontrado` parece
porta inexistente, e as duas máquinas têm uma COM3. O que existe é a **assimetria**:
uma ponta espera e a outra disca, e a que disca não consegue abrir sua porta
enquanto a que espera não segurar a dela. Os probes manuais nunca esbarraram nisso
porque um humano roda `listen` antes de `send`; a bancada abria as duas no instante
zero, o que sobre IP é inócuo — um soquete ouvinte existe haja ou não quem conecte —
e sobre serial é uma corrida que o destinatário perde.

- Enlace caracterizado antes de construir em cima: 16.384 bytes íntegros a
  **128 KiB/s**, com digest conferido nas duas pontas.
- `v3_serial_probe.py rns` responde se o Reticulum sobe a interface, em 20 s e numa
  máquina só, em vez de vender a resposta por uma janela inteira.
- Suíte completa no ambiente fixado: **222 passaram, 8 opt-in pulados**.

O relatório desta rodada nasceu sem saber que código o produziu: o `git` recusava o
repositório por *dubious ownership* e o campo `commit` guardou a recusa. Corrigido
nos dois executores, e o relatório foi regerado a partir da mesma evidência.

## Limites

**O enlace é Bluetooth, e Bluetooth não é independente do Wi-Fi.** Os dois dividem
a faixa de 2,4 GHz e, com frequência, o mesmo chip combo. Isto prova ausência de
**IP**, não ausência de **rádio** nem de domínio de falha comum. Um par USB-TTL
sobre cobre fecharia essa lacuna; não foi feito.

Dentro da alpha, o relé e a origem continuam conversando por TCP em loopback. O
que atravessa entre as máquinas não tem IP; a fiação interna de uma delas tem.

Uma rodada, um sistema operacional, um objeto de 16 KiB, um enlace. Não é
estimativa estatística, e **não diz nada sobre a H19** — migração de tráfego para
meio próprio sob escala é outra pergunta, que uma rodada com um enlace não toca.

Por causa do `write_timeout = None` do RNS, se o destinatário cair no meio da
janela o relé trava em vez de registrar erro. A bancada contorna pela ordem dos
passos; o defeito é da montante e continua lá.

## Reprodução

Nas duas máquinas, ambiente fixado em [G0](G0_REFERENCE.md#reprodução), e o enlace
provado antes de qualquer bancada:

```powershell
window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py list
window/.venv-gateway/Scripts/python.exe window/v3_serial_probe.py rns COM3
```

Com uma pasta **nova**, na máquina do relé:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_v3_bench.py C:\dethron\v3c2 --serial COM3 COM3 600
```

Copie `C:\dethron\v3c2\control` para a outra máquina, no mesmo caminho, e em cada uma:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_v3_agent.py C:\dethron\v3c2 alpha
window/.venv-gateway/Scripts/python.exe window/run_v3_agent.py C:\dethron\v3c2 beta
```

O destinatário fica parado nos primeiros 30 s por cronograma, não por travamento.
Ao terminar, traga a pasta da outra máquina para junto da primeira:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_v3_report.py C:\dethron\v3c2
```

## Decisão e próximo passo

A trilha V está fechada no que ela podia fechar sozinha. G0–V1 já não carregam a
ressalva de host único, e existe uma rodada em que a entrega verificável atravessou
um meio sem IP.

O que falta para aceitação externa não é mais meio físico: é **uma pessoa de fora
rodar o V2**. Nenhuma quantidade de enlaces compensa nunca ninguém sem contato com
o autor ter reproduzido o trabalho.
