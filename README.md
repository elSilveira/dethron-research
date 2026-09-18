# BitNet / Genesis / Dethron — documentação de decisão

**Comece pelo [plano mestre de arquitetura, hipóteses e testes](DETHRON_MASTER_PLAN.md).**
Ele reúne a ordem atual G0–G9, contratos dos módulos, primeira campanha e critérios
para implementar, integrar uma solução existente ou abandonar uma hipótese.

Consolidação: 15/09/2026. Este índice orienta o trabalho atual. Documentos
históricos preservam a intenção e as alegações da época; seus exemplos e
placares não substituem evidência de execução real no escopo declarado.

## Objetivo original

Gadgets participantes hospedam pequenos nós e gateways. Mensagens e seus
fragmentos atravessam caminhos e contatos diferentes, sobrevivem à substituição
de nós e são reconstruídos no destino. A internet é uma via inicial e opcional;
a ambição é operar também sem ela, quando houver infraestrutura alternativa.
Armazenamento eficiente e computação compartilhada são objetivos adicionais.

## Leitura principal

| Documento | Função |
| --- | --- |
| [Direção da rede](DETHRON_NETWORK_DIRECTION.md) | Visão, swarm, gateways, código examinado e contratos |
| [Autonomia e sobrevivência com 5%](DETHRON_AUTONOMY_CONTRACT.md) | Hipótese final, condições físicas, redundância e limites |
| [Utilidade e diferenciação](DETHRON_UTILITY_VALIDATION.md) | Antecedentes, uso candidato e comparação com soluções existentes |
| [Plano de decisão e experimentos](DETHRON_VALIDATION_PLAN.md) | Ordem de trabalho, controles, evidências e critérios de abandono |
| [Mapa de evidências e documentação](DETHRON_EVIDENCE_MAP.md) | O que foi medido, o que é histórico e onde está cada registro |
| [Incentivos e remuneração](DETHRON_INCENTIVES.md) | Serviço verificável, financiamento, tokens e pagamentos durante partições |

## Decisão atual

- Há fundamento e aplicações reais para redes tolerantes a interrupções.
- Existem antecedentes próximos: Reticulum/LXMF, DTN, RaptorQ e armazenamento codificado.
- O projeto tem recuperação local real; swarm por rádio, independência da internet,
  autonomia sem controlador, economia de 5% e adoção global não foram demonstrados.
- Não existe justificativa para prometer sobrevivência universal com 5% ou
  impossibilidade de desligamento. Tamanho da rede não implica essas propriedades.
- G0 executado: Reticulum/LXMF atendeu ao recorte local de mensagens completas
  persistentes após crash. G1 integrou caixa persistente e recibo autenticado,
  com resultado satisfatório no laboratório. G2 encerrou com a comparação pareada
  de objeto completo, partes exatas e paridade XOR: sem perda a redundância só
  custa; com uma rota perdida, só ela entrega. G3 atravessou duas gerações
  completas de transportadores e quatro supervisores, com falha explícita quando
  a credencial declarada foi retirada. G4 entregou o objeto com zero endpoints IP
  nos processos envolvidos; removida a ponte, nada é entregue e o objeto fica
  pendente. Independência física e rádio continuam sem evidência.
- Reenquadramento de 17/09/2026: as propriedades de rede demonstradas são do
  Reticulum/LXMF; o entregável passa a ser o harness de evidência reproduzível e
  a entrega verificável — prova quando há entrega, pendência visível quando não
  há. Rede própria, tokens e processamento ficam após aceitação externa.
- Antes de cada avanço, registrar satisfação dos critérios, utilidade do próximo
  investimento e razões para continuar, integrar, reduzir ou parar.

## Código e experimentos existentes

- [v2](v2/README.md): núcleo Rust atual de execução, evidências e recuperação.
- [Window](window/README.md): provas locais, integração com modelo e dashboard.
- [Sobrevivência de processos](window/PROCESS_SURVIVAL.md): 20 serviços locais,
  reposição de 19 a partir de um sobrevivente com cópia completa.
- [Comparação de respostas](window/RESPONSE_COMPARISON.md): aplicação secundária,
  32 gerações reais; não demonstra comunicação mesh.
- [Avaliadores](probes/README.md): testes dos critérios de avaliação.
- [G0 — referência executada](window/G0_REFERENCE.md): Reticulum/LXMF real,
  entrega offline após crash; decisão de integrar como base de G1.
- [G1 — integração validada](window/G1_INTEGRATION.md): persistência transacional,
  recibo do destinatário, duplicatas e controles negativos.
- [G2 — partes complementares](window/G2_PARTS.md): reconstrução exata,
  controle de parte ausente e comparação pareada de três políticas.
- [G3 — gerações](window/G3_GENERATIONS.md): troca de todos os transportadores e
  supervisores, bloqueio das gerações aposentadas e recusa sem credencial.
- [G4 — independência lógica](window/G4_INDEPENDENCE.md): entrega sem a pilha IP
  por ponte de arquivos, com corte total e corte reversível como controles.
- [V1 — custódia](window/V1_CUSTODY.md): recibo de custódia assinado pelos relés,
  prova de entrada, pendência localizável e relé que atestou e descartou nomeado.
- [V1 — recibo de volta](window/V1_RECEIPT_RETURN.md): a prova de saída chega à
  origem por qualquer relé, sem origem e destino online ao mesmo tempo; pendência
  de prova visível quando o relé visitado não a tem.
- [V2 — reprodução por estranho](window/V2_REPRODUCTION.md): roteiro, pré-requisitos,
  executor único e resultados esperados para reproduzir G0–V1 a partir do clone.
- [V3a — bancada multi-máquina](window/V3A_BENCH.md): cronograma pré-declarado,
  encontro por instante sem canal vivo, janela surda e verificada, entrega entre
  máquinas fisicamente distintas.

Comandos de reprodução já disponíveis, na raiz:

```powershell
python window/run_survival.py --runs 3
python window/run_comparison.py
$env:PYTHONPATH='window'
python -m pytest window/tests probes/tests -q
```

Os launchers exigem os ambientes descritos em suas documentações. Esses comandos
não executam os novos experimentos do plano nem provam comunicação sem internet.
Na consolidação documental não foram repetidas inferências ou provas de rede.

## Como usar o histórico

[Auditoria anterior](PROJECT_FEASIBILITY_REPORT.md),
[síntese conceitual](dethron_genesis_sintese_cientifica.md) e planos de arquitetura
continuam acessíveis pelo mapa de evidências. Não reescrever relatórios antigos
para fazê-los parecer provas atuais. Toda promoção de uma hipótese exige uma
nova execução, configuração identificável e registros brutos preservados.
