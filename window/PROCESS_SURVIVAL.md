# Sobrevivência com processos reais

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Prova de recuperação no escopo declarado abaixo. Sobrevivencia local com réplicas não implica autonomia da internet nem garantia de que quaisquer 5% dos nós preservem conectividade e dados. [Índice atual](../README.md) - [Plano de decisão](../DETHRON_VALIDATION_PLAN.md) - [Evidências](../DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

Abra **http://127.0.0.1:8765/survival** após iniciar `python window/app.py`.
O link também aparece na barra lateral do Window. O botão compila o serviço v2
offline e executa de 1 a 10 provas completas; o padrão é 3. Pela linha de comando:

```powershell
python window/run_survival.py --runs 3
```

## O que mudou

O experimento anterior representava nós por mapas em memória. Agora cada nó é
um processo `dna_node`, com diretório, identidade persistente, sessão e socket
TCP próprios. O armazenamento e a reconstrução pertencem ao v2; o Window
controla o experimento, injeta falhas e apresenta a evidência.

## Resultado medido em 15/09/2026

O botão da tela executou **3/3 provas aprovadas**, com gênesis diferentes e
sobreviventes nos slots 3, 10 e 17. Foram 33 eventos auditados, 11 por execução.
O objeto tinha 137 bytes. Cada prova recompôs 19 serviços a partir de 1 e
verificou os 20 individualmente após reinício completo.

| Execução | Detecção e reposição | Tempo até o último evento |
| --- | ---: | ---: |
| 1 | 7,187 s | 10,750 s |
| 2 | 7,156 s | 10,547 s |
| 3 | 7,235 s | 10,672 s |

Na primeira execução, a recuperação v2 e verificação dos 19 destinos levou
0,1132 s e escreveu 46.284 bytes cifrados. O ciclo de 7,187 s também inclui
consultas sequenciais com timeout aos serviços mortos e criação dos processos.
Não é uma estimativa de latência entre máquinas nem comparação com inferência.

[Relatório bruto e manifesto](results/survival-20260915T125653Z-71e25ad2/report.json).
[Tela desktop](results/survival-visual-20260915/completed.png) e
[tela móvel](results/survival-visual-20260915/mobile.png).
As imagens finais incluem a seleção antes/depois, adicionada após essa execução;
os hashes no manifesto identificam o código usado para produzir o relatório.

Passaram as suítes Rust do v2 e Window, Clippy do v2, formatação e testes Python.
O teste de navegador iniciou as três execuções pelo botão, conferiu 33 eventos,
relatório, troca de execução, recarga e layout móvel sem overflow ou exceções JS.
Outro teste verificou os estados antes/depois e a remoção de resultados antigos
quando uma nova execução ainda não tem evidências. A auditoria rejeita objeto
alterado, sequência incompleta e evidência duplicada de destino.

```mermaid
flowchart LR
  G[Gênesis: receita e dados cifrados] --> N[20 serviços locais]
  N --> F[Encerrar 19 processos]
  F --> S[1 sobrevivente com cópia completa]
  S --> C[Supervisor consulta serviços]
  A[Controlador: chave e raiz confiável] --> R[Recuperação v2 em processo novo]
  C --> R
  R --> V[19 substitutos: gravar, reler e verificar]
  V --> I[Retirar o sobrevivente original]
  I --> P[Recompor e reiniciar todos os 20]
```

## Validação ponto a ponto

1. **Gênesis:** cria um texto com identificador aleatório e salva uma receita
   cifrada que usa append, XOR e XOR inverso. O hash do objeto é registrado antes
   da recuperação. A receita é determinística e não representa aprendizado.
2. **Expansão:** inicia 20 serviços simultâneos, com PIDs distintos. Distribui as
   unidades por TCP e reconstrói o objeto após reler cada destino.
3. **Reinício individual:** encerra o futuro sobrevivente e inicia outro processo
   no mesmo diretório. Confere identidade preservada e sessão alterada.
4. **Perda de 95%:** encerra 19 processos e renomeia seus diretórios para caminhos
   indisponíveis ao fluxo ativo. Nenhuma recuperação consulta esses diretórios.
5. **Reposição:** o supervisor consulta os endpoints, sem receber a lista de
   falhas injetadas. Cria serviços vazios e pede ao v2 que os recupere somente
   pelo serviço sobrevivente. Cada substituto precisa passar por leitura final.
6. **Perda do último original:** encerra o sobrevivente e verifica os 19 novos.
7. **Segundo ciclo:** detecta a nova falha e volta a 20 serviços.
8. **Reinício total:** encerra todos, reabre seus diretórios e verifica cada um
   individualmente, sem recorrer a outro nó para completar dados faltantes.
9. **Chave errada:** o processo de recuperação deve falhar sem produzir objeto.
10. **Informação perdida:** retira a unidade de entrada de todos os 20 serviços;
    uma recuperação com até 16 doadores deve falhar, apesar de ter chave e raiz.
11. **Auditoria:** o Python recalcula SHA-256 do objeto retornado e confere a
    sequência, mortes, sessões, contagens, destinos distintos e erros esperados.

Cada chamada de recuperação é um processo novo. Recebe apenas caminho da
autoridade, endpoints doadores e endpoints destinos; não recebe o texto esperado
nem consulta relatórios anteriores. Os serviços não recebem a chave de decifração.

## Como ler a tela e os arquivos

A tela permite selecionar execução e etapa, inspecionar PIDs e identidades,
ler o objeto reconstruído, comparar hashes e baixar JSON público. Os cartões
representam observações registradas. Ao terminar, os processos são encerrados.
Etapas negativas bem-sucedidas mostram o erro esperado, não um objeto inventado.

Em `window/results/survival-<data>-<id>/` ficam:

- `events.jsonl`, `report.json`, `status.json`: eventos, auditoria e estado;
- `manifest.json`: hashes do código e binário, plataforma e escopo;
- `trial-N/`: diretórios dos nós, handshakes, configurações e saídas dos processos;
- `authority.private.json`: chave local, raiz e hash esperado dentro de cada trial.

Arquivos de autoridade são privados, dependem das permissões locais do diretório
e não entram no relatório HTTP. Não há cofre de chaves, consenso nem recuperação
automática de uma chave perdida. Os testes negativos finais deixam nós sem uma
unidade; arquivos `.lost` e diretórios `.unavailable` permanecem para auditoria.
O probe não entrega uma rede de produção em execução ao terminar.

Fechar a aba não cancela o probe. O botão de parada solicita cancelamento, encerra
os processos próprios e preserva eventos parciais. Reiniciar o Window recarrega
o último relatório e o audita; uma execução incompleta não vira aprovação.
Build tem limite de 180 segundos, chamadas de recuperação de 30 segundos e o
experimento completo de 600 segundos. A parada é cooperativa entre operações.

## O que este marco prova — e o que permanece aberto

Há recuperação real após morte de processos e reinício de armazenamento local.
Os ciclos de supervisão executam reposição automaticamente a partir das consultas,
mas são acionados pelo harness e limitados ao experimento. Não existe ainda um
serviço de supervisão permanente, autônomo ou tolerante à própria perda.

**5% funciona porque usamos replicação completa.** Um nó intacto conserva todos
os dados. Não é um limiar descoberto nem garantia para dados particionados. O
custo inclui todas as cópias, metadados, cifragem e leitura de confirmação.

Tudo roda na mesma máquina, sobre loopback. Não mede falhas de máquinas, partições
de rede, perda de energia, throughput distribuído, prosa livre ou inferência
neural. O protocolo local não oferece autenticação de clientes para exposição
remota. Operações de arquivo são sincronizadas e substituídas por rename; não
alegamos durabilidade diante de qualquer falha de energia ou transação atômica
de reparo em múltiplos nós. Um reparo interrompido pode deixar destinos parciais,
que não devem ser considerados completos antes de nova verificação.

Os próximos marcos são supervisão persistente com recuperação do controlador,
transporte autenticado entre máquinas e uma política de redundância que preserve
decodabilidade sem copiar tudo em todo nó. Cada marco precisa de sua própria
injeção de falhas e validação independente.
