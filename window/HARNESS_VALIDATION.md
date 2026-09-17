# Confiança no harness: integridade primeiro, capacidade depois

<!-- dethron-doc-context-20260915 -->
> **Contexto atualizado - 15/09/2026.** Estudo de modelo/avaliação com escopo secundário. Seus resultados não demonstram conectividade mesh, autonomia da internet ou sobrevivência global. Preservar datas e limites dos experimentos abaixo. [Índice atual](../README.md) - [Plano de decisão](../DETHRON_VALIDATION_PLAN.md) - [Evidências](../DETHRON_EVIDENCE_MAP.md).
<!-- /dethron-doc-context-20260915 -->

O harness é útil como diagnóstico de desenvolvimento. Para sustentar alegações
de capacidade, precisa passar por duas verificações separadas: o placar precisa
estar correto, e o experimento precisa representar o uso pretendido.

## Correção implementada

O resumo do documento passa por `document_audit.py` antes de publicar resultados.
Uma referência Python (`document_oracle.py`) percorre os fatos independentemente
do executor Rust, seleciona os trechos esperados e reavalia o JSON bruto final.

A auditoria rejeita:

- Documento/gabarito diferente do conjunto fixado nesta versão.
- Alterações na pergunta, nas rotas, nas remoções ou no texto enviado.
- Prompt ou limite de geração diferente do protocolo fixado.
- Casos ausentes/duplicados, modos ausentes/duplicados e conclusão duplicada.
- Conclusão ou fontes DNA que discordem da referência independente.
- Flags de acerto, aceitação, abstenção ou formato inconsistentes com a saída bruta.
- Contagem de tokens inconsistente, limites inválidos e tempo negativo/não finito.

Nove mutações de evidência que passavam no resumo antigo foram observadas
falhando nos testes antes da correção. Agora são rejeitadas. A suíte Python
passou com 26 testes; não houve alteração do modelo nem do núcleo Rust nesta etapa.

Para reavaliar um relatório arquivado sem repetir inferência:

```powershell
python audit_document.py results/document-visual-final/report.json --output results/minha-auditoria.json
```

O destino precisa ser novo. O relatório original permanece intacto. A auditoria
registra seu próprio código por hash e o hash dos bytes do relatório examinado,
distinguindo a versão do avaliador da versão que produziu a inferência.
Novas execuções do Window usam essa auditoria após reiniciar o servidor Python.

Reauditoria realizada: `results/document-audit-independent.json`.
As 16 gerações preservaram o placar: DNA 8/8; modelo inteiro 4/8; seleção 5/8;
uma resposta sustentada aceita. É conferência da evidência anterior, não uma
nova repetição experimental nem aumento da amostra.

## Limites da auditoria

As duas implementações seguem o mesmo contrato de relações estruturadas; ambas
podem compartilhar uma hipótese errada. Concordância não valida verdade externa.
Esta auditoria verifica consistência dos registros e não autentica uma máquina
remota nem detecta uma falsificação coerente de toda a execução. A identidade
e os fingerprints completos do worker continuam sendo verificados pelo cliente
Rust durante a execução; o arquivo arquivado não se torna uma atestação assinada.
Tempos e tokens são conferidos quanto a consistência, não medidos outra vez.

## Próximas condições para alegar capacidade

| Prioridade | Mudança no experimento | Critério de avaliação |
| --- | --- | --- |
| 1 | Separar documentos de desenvolvimento e avaliação inédita | Fixar gabarito, prompt, parser e critérios antes de abrir a avaliação |
| 2 | Anotar rotas/citações por revisão humana independente | Resolver discordâncias sem consultar a resposta do modelo avaliado |
| 3 | Acrescentar controles de recuperação convencional e abstenção constante | Medir benefício sobre métodos simples com o mesmo conteúdo e orçamento |
| 4 | Alternar ordem dos modos, aquecer worker e repetir | Relatar variabilidade de tempo; não comparar uma única sequência fixa |
| 5 | Ampliar cenários de falha | Negação, versões, conflito, fonte removida, paráfrase, português e caminho longo |
| 6 | Avaliar texto → DNA sem preparação manual | Medir separadamente extração, seleção, conclusão e fidelidade das citações |

O placar deve sempre separar: acerto da conclusão, cobertura nos casos
respondíveis, abstenção nos não respondíveis, falsos aceites, citações completas,
erros de formato e truncamento. Zero falsos aceites com quase nenhuma resposta
aceita não basta. Não tratar perguntas correlacionadas do mesmo documento ou
repetições determinísticas como amostras independentes de capacidade geral.

Só depois dessa validação semântica faz sentido usar o harness para comparar
joules por resposta correta, concorrência entre máquinas e recuperação após
quedas reais. Um resultado negativo deve permanecer publicado com suas fontes,
configuração e saída bruta; ajustes exigem uma nova versão do experimento.
