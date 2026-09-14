# Prova visual com modelo local

Inicie `python app.py` no window e abra `/reconstruction`, também acessível
pelo link na barra lateral do dashboard original. Se usar outra porta, mantenha
o mesmo caminho. Clique em **Executar com modelo real** e selecione CUDA ou CPU.
O teste usa o ambiente `.venv-neural` e os pesos locais já configurados em
`run_neural.DEFAULT_MODEL`; não baixa modelos.

Cada início cria um diretório `results/reconstruction-<data>-<id>/`, compila o
binário Rust `reconstruction_live` e carrega um worker real. Eventos são gravados
e disponibilizados enquanto chegam. Há até 180 segundos para build e 300 para
execução; timeout encerra a árvore de processos pelo runner existente.
Fechar a aba não cancela o teste. Reiniciar o servidor esvazia sua visão atual,
mas os arquivos de resultados continuam no disco.

## O que aparece

- Fontes efetivamente presentes em cada rota e evidências removidas.
- Conclusão recalculada pela API v2, sem leitura de resposta salva.
- Escolha bruta do modelo, incluindo erros e abstenções excessivas.
- Saída protegida: só aceita a escolha do modelo se coincidir com a conclusão
  sustentada; caso contrário, UNKNOWN. Não substitui silenciosamente o modelo
  pelo resultado correto do algoritmo.
- Tempos, comparações de fontes, bytes JSON e tokens realmente avaliados.
- PID, metadados e fingerprints do modelo, requisições e respostas completas
  no relatório, junto aos hashes de fontes, configuração e binário.

Os fatos são controlados e usam um identificador de objeto novo por execução.
Os rótulos Amber/Violet e a estrutura das tarefas são fixos. O modelo ranqueia
três candidatos: Amber, Violet e UNKNOWN. Não é geração livre nem avaliação de
fatos externos. As rotas são removidas do input em memória; o teste não derruba
máquinas nem restaura arquivos de réplica.

## Resultado observado em 14/09/2026

Duas execuções CUDA com DeepSeek-R1-Distill-Qwen-1.5B local, bfloat16:

- `reconstruction-20260914T192723Z-edda0d08` (primeira versão da validação).
- `reconstruction-20260914T192952Z-a20b0b2f` (validação final de consistência).

| Cenário | Esperado | DNA | Modelo bruto | Saída protegida |
| --- | --- | --- | --- | --- |
| Duas rotas | Amber | Amber | UNKNOWN | UNKNOWN |
| Rota A removida | Amber | Amber | UNKNOWN | UNKNOWN |
| Evidência indispensável removida | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Rotas contraditórias | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

DNA: 4/4; modelo: 2/4, com zero respostas úteis nos dois casos suportados.
O guard não aceitou conclusões erradas, mas também não recuperou a cobertura
do modelo. O comportamento de sempre responder UNKNOWN já alcança 2/4 aqui.
Portanto, não há evidência de vantagem do modelo sobre esse baseline nesta prova.
O algoritmo de percurso de fatos é a própria referência determinística.

O resultado demonstra reconstrução estruturada por uma rota sobrevivente e
abstenção diante de perda essencial/conflito, com inferência real registrada
separadamente. Não prova economia de energia, LLM distribuído, independência
das fontes ou assertividade geral. Os tempos pequenos do DNA não são uma
comparação de tarefas equivalentes com inferência de linguagem.

## Validação

Testes Rust e Clippy do window passaram, assim como 22 testes Python e cinco
testes JavaScript. Os novos testes rejeitam evidência parcial e inconsistência
entre resposta bruta, resultado esperado, flags de acerto e saída protegida.

O teste `tests/reconstruction_browser.mjs` executou o modelo pelo botão da tela,
conferiu conclusão, relatório, quatro cenários, ausência de erros JavaScript e
layout móvel sem overflow. Capturas finais em `results/reconstruction-visual-final/`:
`idle.png`, `running.png`, `completed.png`, `mobile.png`, com cópia do relatório.
O smoke test do dashboard original também passou.

Próximo experimento: avaliar apresentação de evidências e cobertura do modelo
com conjunto de desenvolvimento separado de casos reservados para avaliação.
Manter abstenções e falsos aceites separados, comparando com UNKNOWN constante
e busca determinística. Não ajustar o prompt até obter um resultado bonito
nestes mesmos quatro casos e tratar isso como generalização.
