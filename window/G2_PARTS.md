# G2 — composição de partes em contatos incompletos

16/09/2026. Fatia funcional de laboratório sobre Reticulum 1.5.4/LXMF 1.1.1.
O G1 justificou este experimento pequeno; não aprovou uma rede própria.
Duas partes: a fatia inicial de partes exatas e a comparação ampliada pareada
que encerra G2.

## Contrato e comparação

O perfil fixado em `g2_scenario.py` usa 98.304 bytes determinísticos, três
propagadores A/B/C e um destinatário D. Cada propagador recebe um objeto completo
ou uma parte exata de 32.768 bytes. A origem sai e seu diretório é renomeado;
os propagadores sofrem crash e reiniciam com armazenamento persistente.
D visita C, A e B, com reinício entre contatos e uma busca nativa de 64 kB por
contato. O prazo da campanha de contatos é 120 segundos, sem incluir distribuição.

As três variantes usam o mesmo calendário e limite nativo:

- `whole`: três réplicas completas; não cabem no limite por transferência.
- `split`: partes 2, 0 e 1; a união permite reconstrução exata no terceiro contato.
- `missing`: partes 2, 0 e 0; duplicar uma parte não substitui a parte 1 ausente.

Depois da medição restrita, `whole` recebe uma busca de 256 kB como controle
positivo. Esse controle não entra no contador de tráfego da fase restrita.
O limite é de transferência LXMF, não uma simulação de perda de rádio nem um
orçamento idêntico de tráfego total. A colocação das partes é provisionada.

## Evidência e auditoria

Cada tentativa preserva perfil, versões, hashes dos fontes, manifesto, eventos,
pacotes autenticados, bancos e relatório em `results/gateway-g2-ID`.
O auditor verifica a assinatura da origem, submissões declaradas, partes únicas,
reconstrução byte a byte e assinatura do recibo local do destinatário. Também
confere estados de conclusão e contagens por contato, incluindo o controle
negativo. Esses eventos são evidência do harness, não atestação independente
do hardware ou de um supervisor hostil.

O recibo é produzido localmente; não retorna à origem offline. A composição
desse retorno permanece pendente. Metadados e codificação base64 estão incluídos
nos bytes LXMF submetidos; arquivos dos propagadores e contadores de interface
são medidos separadamente. Os contadores são amostras antes do encerramento,
não captura exaustiva de pacotes. Banco do destinatário, RAM, CPU e energia não
são contabilizados como custo total. Não inferir economia geral desses números.

## Reprodução

Usar o ambiente fixado em [G0](G0_REFERENCE.md#reprodução), a partir da raiz:

```powershell
$env:PYTHONPATH='window'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p 'test_g2_*.py'
$env:RUN_GATEWAY_G2='1'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p test_g2_reference.py
Remove-Item Env:RUN_GATEWAY_G2
$env:RUN_GATEWAY_G2_COMPARE='1'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p test_g2_comparison_reference.py
Remove-Item Env:RUN_GATEWAY_G2_COMPARE
```

A campanha ampliada leva cerca de dez minutos e grava cada caso separadamente.

Para acompanhar eventos, executar `window/run_g2_probe.py` com o mesmo Python.
Artefatos locais incluem chaves de laboratório e são ignorados pelo Git.

## Rodadas e verificações

A [rodada inicial](evidence/gateway-g2-1789584864583714400/report.json) passou
nos três casos e foi reauditada após o endurecimento do auditor. Dois testes
novos falharam antes da correção: conclusão antecipada declarada na timeline
e contagem incorreta de partes únicas. Ambos passaram após a correção.

A [rodada final](evidence/gateway-g2-1789606473945592000/report.json), com
[fontes congelados](evidence/gateway-g2-1789606473945592000/sources.json), passou
na integração real em **229,390 s**, incluindo preparação das três variantes.

| Variante | Concluiu sob limite | Contatos (s) | Bytes LXMF submetidos | Bytes nos propagadores | TX amostrado |
| --- | --- | --- | --- | --- | --- |
| Objeto completo | Não; controle de 256 kB concluiu | 11,360 | 394.437 | 394.800 | 407.931 |
| Três partes | Sim, SHA-256 e recibo verificados | 11,546 | 177.723 | 178.080 | 370.252 |
| Parte ausente | Não; duas partes únicas | 11,563 | 177.723 | 178.080 | 370.658 |

O TX inclui preparação/distribuição e contatos, até a amostra anterior ao
controle relaxado. Os tempos da tabela cobrem apenas contatos. São duas rodadas
de desenvolvimento com ordem fixa, não estimativa estatística de confiabilidade.

- Testes G2 rápidos no ambiente fixado: **11 passaram, 1 opt-in pulado**.
- `unittest discover -s window/tests` no ambiente fixado: **94 passaram,
  3 opt-in pulados** (97 descobertos).
- `python -m pytest window/tests probes/tests -q` no Python global:
  **142 passaram, 9 pulados**; módulos dependentes de RNS/LXMF são executados
  separadamente no ambiente fixado. G0/G1 reais não foram repetidos nesta entrega.
- Fontes/testes alterados têm menos de 200 linhas; links documentais locais
  foram conferidos. A suíte global emite aviso preexistente de configuração
  do escopo de fixtures `pytest_asyncio`.

Essas contagens são as da entrega do G2 e mantêm sua data e escopo. Os totais
atuais das suítes estão em [G3](G3_GENERATIONS.md#rodadas-e-verificações).

## Comparação ampliada

A [campanha pareada](evidence/g2-comparison-1789608585567685600/report.json) fixada
em `g2_compare_contract.py` executou **12 casos reais** em 590,984 s: duas
repetições, dois cenários e três políticas, com ordem de políticas invertida na
segunda repetição e rota de contatos rotacionada. O objeto tem 49.152 bytes.
`whole` envia o objeto completo, `split` envia três partes exatas e `xor2` envia
duas partes de dados mais uma paridade XOR, recuperável com quaisquer duas.

- Cenário `all`: três contatos (CAB e BAC), busca nativa de 256 kB por contato.
- Cenário `loss`: uma rota perdida, dois contatos (CA e BC), busca de 64 kB.

Orçamentos declarados antes da execução — 2.000.000 bytes de TX amostrado e
8.000.000 bytes de arquivos — foram respeitados em todos os casos; estourá-los
invalidaria o caso em vez de contar como sucesso. Médias das duas repetições:

| Cenário | Política | Concluiu | Bytes LXMF | TX amostrado | Arquivos (pico) | Contatos (s) |
| --- | --- | --- | --- | --- | --- | --- |
| Três contatos | Objeto completo | Sim (2/2) | 197.829 | 411.817 | 255.660 | 10,79 |
| Três contatos | Partes exatas | Sim (2/2) | 90.351 | 194.079 | 365.384 | 10,75 |
| Três contatos | Paridade XOR | Sim (2/2) | 134.019 | 282.271 | 474.583 | 10,76 |
| Rota perdida | Objeto completo | **Não** (0/2) | 197.829 | 207.997 | 205.503 | 7,14 |
| Rota perdida | Partes exatas | **Não** (0/2) | 90.351 | 161.493 | 212.934 | 7,16 |
| Rota perdida | Paridade XOR | **Sim** (2/2) | 134.019 | 235.173 | 404.567 | 7,17 |

O TX amostrado soma distribuição e contatos. A codificação custa 2,7 ms, 1,8 ms
e 4,0 ms por objeto, desprezível diante do transporte. As duas repetições
concordam caso a caso em conclusão e em tráfego dentro de 0,4 %.

## O que a comparação ampliada mostra

Esta é a fatia que testa H05, codificação redundante, e o resultado é um
compromisso, não uma vantagem geral:

- **Sem perda, redundância só custa.** Partes exatas concluem com o menor
  tráfego total; a paridade XOR gasta **+45 % de TX** e **+30 % de arquivos** para
  entregar o mesmo objeto. O objeto completo gasta mais que o dobro do tráfego
  das partes exatas e não cabe no limite de 64 kB por busca.
- **Com uma rota perdida, só a redundância entrega.** Com dois contatos, a
  paridade XOR reconstrói os bytes exatos; partes exatas e objeto completo
  permanecem corretamente incompletos. Nenhuma política produziu conclusão falsa.
- **Armazenamento anda no sentido oposto do tráfego.** O objeto completo tem o
  menor pico de arquivos e o maior tráfego; a paridade XOR, o inverso. Não existe
  política dominante sob este contrato.

A conclusão sustentada é estreita: sob este limite nativo de transferência, a
escolha entre partes exatas e código redundante é um compromisso mensurável entre
tráfego, armazenamento e tolerância a uma rota perdida. Não é novidade frente a
sistemas que já fragmentam e codificam mensagens, nem evidência de economia geral.

## Limites da campanha ampliada

Duas repetições pareadas não são estimativa estatística de confiabilidade. Tudo
ocorreu em um host, sobre TCP de loopback, com colocação de partes provisionada
e perda induzida pela omissão de um contato, não por rádio ou congestionamento.
Os contadores de interface são amostras antes do encerramento, não captura
exaustiva de pacotes. Banco do destinatário, RAM, CPU e energia continuam fora do
custo total. Um único esquema redundante foi medido — paridade XOR sobre três
partes — e não um código estabelecido como Reed-Solomon ou fontain codes.
O reparo após perda não foi medido: nenhuma política tentou recuperar a rota
perdida. O recibo continua produzido localmente e não retorna à origem offline.

## Decisão e próximo passo

G2 está encerrado no escopo declarado. H04 foi verificado na primeira fatia e
H05 recebe um resultado condicional: redundância melhora a entrega sob perda de
rota e piora o custo sem perda. A hipótese de vantagem geral de custo está
**refutada** neste contrato e deve deixar de ser afirmada.

Próxima fatia: **G3 — gerações**, substituição de todos os nós originais e do
supervisor, mantendo o serviço sem consultar fonte oculta, com falha explícita
ao retirar um recurso declarado indispensável. Rádio, demanda comercial,
autonomia sem supervisor e tokens continuam não validados.
