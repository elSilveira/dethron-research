# Documento maior: o que o teste permite concluir

O Window agora inclui **Documento · geração e citações** em `/reconstruction`.
O texto é um manual controlado em inglês de 493 palavras, dez seções e 572 tokens
antes das instruções. Há oito casos e duas gerações por caso: texto inteiro e
apenas os trechos alcançados pelo DNA. Nenhum prompt é truncado para caber.
O mesmo DeepSeek-R1-Distill-Qwen-1.5B local gera até 256 tokens, sem alternativas.

As perguntas cobrem liderança, localização do responsável (três relações),
localização do backup, separação entre projetos, orçamento ausente, perda da rota
primária, perda da evidência indispensável e contradição entre rotas atuais.
Remoções afetam tanto o documento entregue ao modelo quanto as fontes DNA.

## Critérios e interpretação

1. **Conclusão:** o campo `answer` corresponde ao resultado esperado e a geração
   terminou em EOS. Uma saída truncada não é contada como resposta concluída.
2. **Evidência:** as citações incluem uma rota completa e não incluem fontes
   alheias ao conjunto que sustenta a conclusão. Citar apenas a última relação,
   ou indiscriminadamente todo o documento, não passa.
3. **Abstenção:** UNKNOWN com citações vazias quando a evidência é insuficiente
   ou contraditória. Responder sempre UNKNOWN acertaria três dos oito casos.
4. **Formato:** JSON final com `answer` e `citations`. O parser aceita o bloco
   final cercado por markdown e separa texto anterior a `</think>`. Somente os
   campos finais são avaliados; o raciocínio narrado não é certificado.

A primeira execução (`reconstruction-20260914T195651Z-65e10a5c`) usou um parser
de JSON puro e rejeitou todos os formatos. Seus registros foram preservados.
Eles mostraram respostas finais dentro de markdown após raciocínio intermediário.
Corrigimos o leitor do formato e repetimos as mesmas perguntas, sem ajustar o
prompt, documento, pesos ou limite de geração. Essa correção faz desta rodada
um diagnóstico de desenvolvimento, não avaliação cega em conjunto reservado.

## Resultado final

Execução `reconstruction-20260914T195916Z-bc9ed8eb`, com relatório e manifest em
`results/`. Capturas e cópia do relatório em `results/document-visual-final/`.

| Medida | Texto inteiro | Trechos selecionados pelo DNA |
| --- | --- | --- |
| Resposta final correta | 4/8 | 5/8 |
| Acertos nos cinco casos sustentados | 3/5 | 4/5 |
| Acertos nos três casos de abstenção | 1/3 | 1/3 |
| Respostas sustentadas com citações aceitas | 0/5 | 1/5 |
| Erros aceitos pelo verificador | 0 | 0 |
| Gerações truncadas | 1 | 1 |
| Tokens avaliados (entrada + saída) | 5.520 | 2.744 |
| Tempo somado das chamadas ao modelo | 41,89 s | 62,28 s |

A redução de aproximadamente 50% nos tokens não se traduziu em menor tempo.
São chamadas sequenciais, sem balanceamento de ordem ou repetições suficientes
para um benchmark; carregamento não entra nesses tempos. Não foi medida energia.

O percurso determinístico do DNA acertou 8/8. As anotações estruturadas e os
caminhos foram fornecidos por nós: esse resultado não demonstra extração
automática de conhecimento do texto. Tampouco compara favoravelmente o DNA a
outro algoritmo de busca de grafos; esse tipo de busca é o mecanismo utilizado.

O caso mais relevante é a perda da rota A: com o trecho da rota B, o modelo
produziu **Mira** citando **S3 e S4**, formando uma cadeia completa. Já na perda
essencial, o texto inteiro levou ao nome incorreto **Nora**; a seleção DNA levou
à abstenção. Na pergunta sobre Orion, a seleção corrigiu Mira para Nora, mas
faltou citar uma etapa. A pergunta de três relações não passou em nenhum modo.

Há melhora observada em alguns casos, mas oito perguntas de um único documento
não sustentam generalização. Zero erros aceitos junto de apenas uma resposta
sustentada aceita exige melhorar cobertura, não apenas celebrar a rejeição.

## Veredito sobre o projeto

Há um protótipo funcional de persistência, recuperação por réplica verificada,
percurso de evidências e bloqueio de respostas sem suporte. Esta prova acrescenta
um caso real em que o modelo responde corretamente pela rota sobrevivente.
O sistema ainda não está demonstrado como mecanismo geral e confiável de
reconstrução de conhecimento ou como vantagem exclusiva sobre recuperação
convencional de trechos. O teste avalia este modelo com este prompt e limite;
uma falha aqui não estabelece incapacidade universal do modelo.

## Validações que faltam, em ordem prática

- **Extração de DNA:** partir de documentos sem anotações preparadas, medir
  fatos omitidos, relações erradas, negações, versões e citações de origem.
- **Generalização e cobertura:** separar desenvolvimento e avaliação; usar
  vários documentos novos, português, paráfrases, perguntas compostas e fontes
  conflitantes. Comparar com texto inteiro, busca convencional e UNKNOWN constante.
- **Contexto maior:** ultrapassar documentos de centenas de palavras com
  fragmentação explícita. O worker atual limita cada prompt a 1024 tokens.
- **Recuperação integrada:** perder estado/processos durante uma tarefa textual,
  restaurar réplicas em outra máquina e medir atraso, trabalho repetido e limites
  de versão. Aqui a perda é de trechos em memória, não uma falha de máquina.
- **Escala:** concorrência crescente, hardware heterogêneo, tráfego e falhas de
  conexão. Distribuir tarefas ainda não prova dividir um único LLM grande.
- **Energia:** joules por resposta correta, incluindo modelo, CPU, armazenamento,
  comunicação e réplicas. Tokens e tempo não substituem medição elétrica.
- **Quantização e rádio:** medir qualidade versus tamanho e recuperação de
  fragmentos perdidos antes de alegar transmissão eficiente ou continuidade sem internet.

Testes automatizados cobrem respostas sem suporte, citações incompletas,
truncamento, separação entre raciocínio e JSON final, perda coerente de texto e
fatos e contagem de cobertura sem inflar o resultado com abstenções constantes.
Passaram a suíte Rust do window, Clippy, 25 testes Python e a verificação da
tela em desktop/celular, incluindo download do relatório e ausência de erros JS.
