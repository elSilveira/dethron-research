# G0 — referência real antes de ampliar o Dethron

Data: 15/09/2026. Vinculado ao [plano mestre](../DETHRON_MASTER_PLAN.md).

Continuação, 16/09/2026: [G1 integrado e validado](G1_INTEGRATION.md).
Os próximos passos abaixo registram a decisão tomada ao concluir G0.

## Requisito congelado

Uso de laboratório: uma origem deixa mensagens em gateways enquanto o
destinatário está offline. A origem sai; os gateways sofrem encerramento abrupto,
mantêm seus discos e reiniciam. O destinatário conserva sua identidade, visita
os gateways em momentos distintos e recebe os conteúdos íntegros.

O recorte testa uma necessidade técnica plausível. Não constitui pesquisa de
demanda, benchmark de mercado ou demonstração de novidade comercial.

| Parâmetro | Configuração |
| --- | --- |
| Referência | Reticulum/rns 1.5.4 + LXMF 1.1.1, pacotes reais do PyPI |
| Ambiente | Windows, Python 3.10.11, um computador |
| Papéis | O, A, B, C, D, cada instância em processo e diretório próprios |
| Mensagens | 1.024, 65.536 e 1.048.576 bytes; conteúdo determinístico SHAKE-256 |
| Distribuição | A guarda a pequena, B a média, C a grande; objetos completos |
| Negativo | Mensagem adicional de 1.024 bytes em A, identidade destinatária nunca iniciada |
| Contatos | O conecta a A/B/C; depois D conecta somente a A, depois B, depois C |
| Transporte | TCP em 127.0.0.1; sem AutoInterface, compartilhamento de instância ou transporte de terceiros |
| Descoberta | Anúncios nativos dos propagadores; contatos e chaves públicas provisionados pelo ensaio |
| Persistência | `messagestore` nativo do LXMF; sem substituir seu algoritmo |
| Limites configurados | Propagação e entrega: 2.048 kB; sincronização: 8.192 kB (kB decimal na API); autopeer desativado |
| Proteção | Criptografia e assinatura nativas; custo de propagação nativo mantido |
| Crash | `os._exit(23)`, sem handlers de encerramento; diretório/disco mantidos |
| Prazo | 120 s após confirmar armazenamento e reiniciar os propagadores; inclui contatos/reinícios de D |
| Esperas de preparação | Até 180 s por transferência; até 60 s para indexação persistente |

O prazo de 120 s **não inclui** o envio inicial nem a reinicialização dos
propagadores. Os timestamps permitem medir essas etapas separadamente. Trata-se
do recorte G0 de objetos completos permitido no plano, não do cenário G2 de
fragmentos complementares. Não houve redução de payload para caber no limite
padrão da referência: o limite público foi aumentado antes do envio de 1 MiB.

## Critério de decisão

- **Atende ao recorte:** três conteúdos corretos no destino dentro do prazo,
  assinatura de origem válida, origem encerrada, persistência após crash e
  ausência de falsa entrega no controle negativo.
- **Lacuna reproduzível:** falha de requisito após investigar configuração e
  reproduzir a causa. Uma falha do harness não é vantagem do Dethron.
- **Inconclusivo:** erro de execução, evidência ausente ou configuração não resolvida.

O callback de envio se chama `handoff_only` na evidência: ele não comprova
entrega nem persistência já concluída. O teste aguarda a indexação, reinicia os
propagadores e só considera entrega quando lê o pacote recebido em D.

## Auditoria e controles

`gateway_contract.py` compara o conteúdo completo com o esperado e verifica a
assinatura Ed25519 diretamente com `cryptography`, sem confiar no booleano de
validação do LXMF. O parser MessagePack é o fornecido por RNS. A assinatura é
da origem: **não é um recibo assinado pelo destinatário enviado de volta à origem**.
Aqui, a entrega é observada pelo harness no processo receptor.

`gateway_archive.py` relê os artefatos depois que os processos saem, verifica a
sequência, os três pacotes e a presença da mensagem do destinatário ausente no
armazenamento de A. O contador genérico de mensagens, sozinho, não passa esse
controle. Os testes do auditor rejeitam corrupção, endpoint trocado, conteúdo
inesperado, estado “enviado” usado como recibo, sequência inválida e armazenamento
de outra identidade usado para justificar o negativo.

Os controles de corrupção são testes do **auditor**, não uma campanha de ataques
injetados no transporte nativo. O destinatário ausente não possui processo receptor:
a conclusão é “nenhuma entrega observada em 120 s e mensagem retida”, não
impossibilidade de entrega futura. Não se configurou TTL de 120 s.

## Reprodução

Na raiz, PowerShell:

```powershell
python -m venv window/.venv-gateway
window/.venv-gateway/Scripts/python.exe -m pip install -r window/requirements-gateway.txt
$env:PYTHONPATH='window'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p 'test_gateway_*.py'
$env:RUN_GATEWAY_G0='1'
window/.venv-gateway/Scripts/python.exe -m unittest discover -s window/tests -p test_gateway_reference.py
Remove-Item Env:RUN_GATEWAY_G0
```

Alternativa para ver o progresso diretamente:

```powershell
window/.venv-gateway/Scripts/python.exe window/run_gateway_probe.py
window/.venv-gateway/Scripts/python.exe window/gateway_archive.py window/results/gateway-g0-ID
```

Cada execução cria diretório exclusivo em `window/results/`, com manifesto,
configurações, versões instaladas, hashes dos fontes do ensaio, logs JSONL e
stderr por processo/geração, timeline e relatório. Rodadas inconclusivas ficam
preservadas. Esses diretórios contêm chaves privadas descartáveis do laboratório
e são ignorados pelo Git; não são o pacote público de documentação.

## Limites da evidência

- Um host e loopback: não mede rádio, Wi-Fi/Bluetooth, WAN, banda limitada,
  interferência, mobilidade ou falha física correlacionada.
- O supervisor agenda os contatos; não há demonstração de descoberta autônoma,
  swarm independente dele ou bootstrap sem provisionamento.
- O diretório da origem é renomeado para `O.offline`, sem processo ativo. Isso
  remove o caminho usado pelo ensaio; não é isolamento hostil por permissões.
- O reinício conserva armazenamento e chaves. Não testa perda de disco, energia,
  hardware ou todas as cópias de uma informação.
- O receptor salva bytes entregues pela API; não recebe os originais pelo canal
  de controle. O harness tem gabarito para auditoria e é parte da base de confiança.
- Não há medição elétrica, ocupação física comparativa, garantia de 5%, token,
  remuneração ou comparação de desempenho com o Dethron nesta etapa.
- Uma mensagem por tamanho é evidência funcional de desenvolvimento, insuficiente
  para estimar confiabilidade ou percentis de latência.

## Decisão de arquitetura e próxima fatia

A referência **atendeu ao recorte executado**. Adotar **integração com
Reticulum/LXMF como hipótese de arquitetura para G1**, preservando o núcleo v2
como componente experimental.
Não há justificativa, nesse recorte, para recriar descoberta, criptografia e
propagação de mensagens completas. O valor próprio continua por demonstrar.

Próxima implementação, em ordem:

1. G1: contrato de adaptador para enviar, consultar pendência e receber;
   distinguir entrega observada, handoff e confirmação final. Testar persistência,
   repetição após crash, limites de fila e recibo de destinatário quando exigido.
2. G2: manifestos e partes exatas autenticadas sobre o mesmo transporte. Cada
   caminho deve possuir apenas parte da mensagem; união suficiente completa e
   união insuficiente permanece incompleta. Testar duplicatas e partes corrompidas.
3. Comparar partes exatas e replicação com mesmo orçamento de contatos, bytes e
   armazenamento. Introduzir código de apagamento estabelecido só depois.
4. Se não surgir ganho útil, manter integração/aplicação ou encerrar a hipótese
   de protocolo próprio. Rádio, autonomia, energia e incentivos seguem G3–G9.

Nenhum desses próximos itens está implementado pelo ensaio G0.

## Fontes primárias

- [LXMF e propagação](https://github.com/markqvist/LXMF).
- [Interfaces Reticulum](https://markqvist.github.io/Reticulum/manual/interfaces.html).
- [Pacote RNS 1.5.4](https://pypi.org/project/rns/1.5.4/).
- [Pacote LXMF 1.1.1](https://pypi.org/project/lxmf/1.1.1/).

Os resultados locais estão abaixo; resultados dos autores não são nossos benchmarks.

## Registro das rodadas locais

| Rodada (`gateway-g0-…`) | Resultado | Interpretação |
| --- | --- | --- |
| `1789494902001906700` | Inconclusivo | Sandbox bloqueou `taskkill`; encerramento do primeiro processo excedeu o prazo. Corrigido para crash explícito dentro do processo com `os._exit(23)`. |
| `1789494979856066300` | Inconclusivo | Harness consultou armazenamento logo após handoff, antes de concluir indexação. Corrigido para aguardar o estado persistido antes de provocar crash. |
| `1789495077778687500` | Atende ao recorte; auditoria posterior passou | Três entregas válidas, armazenamento recuperado e negativo retido após 120 s. |
| `1789495309858991400` | Atende ao recorte; teste de integração passou | Repetição com auditoria de arquivos incorporada ao runner; três entregas válidas e negativo retido. |

Na primeira rodada funcional, tempos acumulados desde `distribution_complete`:
1 KiB em **4,407 s**, 64 KiB em **8,844 s** e 1 MiB em **13,391 s**.
São observações de uma rodada, não médias, percentis ou velocidade de uma rede real.

Artefatos da primeira rodada funcional:
[relatório](results/gateway-g0-1789495077778687500/report.json),
[manifesto](results/gateway-g0-1789495077778687500/manifest.json),
[timeline](results/gateway-g0-1789495077778687500/timeline.jsonl).
As duas tentativas inconclusivas permanecem em `results/`, com causa e traceback.

Na repetição final: **4,421 s / 8,828 s / 13,390 s**, respectivamente. O teste
automatizado inteiro levou **167,085 s**, incluindo preparação, envio e a janela
negativa. [Relatório final com auditoria](results/gateway-g0-1789495309858991400/report.json),
[manifesto final](results/gateway-g0-1789495309858991400/manifest.json) e
[timeline final](results/gateway-g0-1789495309858991400/timeline.jsonl).

Verificação da implementação:

- 8 testes rápidos do contrato/auditor passaram no ambiente da referência.
- 1 teste de integração real passou, executando a rodada final acima.
- Suíte existente: **124 passaram, 3 pulados** com
  `$env:PYTHONPATH='window'; python -m pytest window/tests probes/tests -q`.
  Os pulos são os dois módulos que exigem RNS/LXMF fora do Python global e o
  ensaio demorado opt-in; esses componentes foram executados separadamente no venv.
- Novos módulos e testes têm menos de 200 linhas; links locais conferidos.
- Houve falhas observadas antes da implementação dos comportamentos de auditoria
  e antes da criação do ensaio real. Os erros de execução estão preservados;
  não foram contados como sucesso nem como lacuna técnica da referência.
