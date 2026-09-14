# Integração neural local: execução e testes

Objetivo autorizado: manter o controlador Rust, usar os pesos locais de um modelo
real em processo residente e testar especialistas, memória e reconstrução durante
a implementação. A integração não reutiliza os fallbacks simulados dos backups.

## Fatias e critérios

1. `neural_worker/{protocol,model,server}.py`: validar requisições e carregar
   exclusivamente o checkpoint local. Testes Python devem falhar antes da
   implementação de limites, identidade e erros. Inferência real é um teste
   separado dos testes de protocolo; dublês nunca contam como qualidade do modelo.
2. `src/neural/{client,transport}.rs`: processo persistente JSONL, handshake com
   identidade, prazos e encerramento. Testes Rust com processos auxiliares devem
   falhar antes de implementar correlação, morte do worker e timeout.
3. `src/neural/{memory,controller}.rs`: trons com capacidade e memória alcançável;
   memória versionada, associações por entidade/contexto, revogação e reconstrução.
   Testar perda de dados, contradições e isolamento de contexto antes da integração.
4. Executar um preflight real e um experimento de perguntas com evidência textual,
   incluindo fatos novos, substituição de fatos e ausência de vestígios. Registrar
   respostas erradas, truncamentos, tokens, tempo e custos de validação. Comparar
   controles competentes com os mesmos pesos, dados e limites.

Cada fonte e teste tem limite de 200 linhas. Não há download de novos pesos;
dependências ficam em `.venv-neural`, cache em `.cache/pip`. O teste deve falhar
se o checkpoint ou runtime não carregar; não há resposta sintética substituta.

Runtime inicial fixado em PyTorch 2.8.0/CUDA 12.8 e Transformers 4.56.2.
Referências consultadas: [instalação do PyTorch](https://pytorch.org/get-started/previous-versions/)
e [Qwen2 no Transformers](https://huggingface.co/docs/transformers/v4.56.2/en/model_doc/qwen2).

## Executar no Windows

Na pasta `window`, com o ambiente local já instalado:

```powershell
python run_neural.py --mode preflight
python run_neural.py --mode probe
```

O caminho padrão aponta para o checkpoint existente no backup; `--model CAMINHO`
permite selecionar outro checkpoint local compatível. O launcher compila o binário
Rust offline e grava status, relatório, logs, resumo e hashes em
`results/neural-<data>-<id>/`. Status `completed` indica execução e preflight
válidos; não significa que todas as respostas do experimento estejam corretas.

Para repetir os testes com pesos reais, usando o mesmo caminho padrão:

```powershell
$env:NEURAL_MODEL_PATH = python -c "from run_neural import DEFAULT_MODEL; print(DEFAULT_MODEL.resolve())"
./.venv-neural/Scripts/python.exe -m unittest discover -s neural_checks -p 'test_*.py' -v
```

Esses testes exigem o binário release gerado pelo launcher. Os testes rápidos
continuam disponíveis com `python -m unittest discover -s tests -p 'test_*.py'`
e `cargo test --locked --offline`.

## Resultado observado em 14 de setembro de 2026

Evidência local: `results/neural-20260914T122543Z-cfeec847/`.
Os hashes das fontes foram conferidos antes da correção de limpeza do teste
Python; o controlador e o worker desse experimento não foram alterados.
O worker carregou os pesos uma vez, em CUDA/bfloat16, na RTX 4060 Ti.

| Política | Acertos finais | Acertos neurais | Tokens avaliados | Tempo das respostas |
| --- | ---: | ---: | ---: | ---: |
| Indexed | 22/22 | 20/22 | 14.000 | 2,607 s |
| Adaptive | 17/22 | 17/22 | 33.580 | 5,264 s |
| Full | 17/22 | 17/22 | 28.405 | 4,444 s |

As duas correções adicionais de Indexed são abstenções `UNKNOWN` impostas pelo
controlador quando falta evidência alcançável. O relatório preserva a previsão
neural original separadamente. O resultado atual favorece o controle indexado;
a adaptação não demonstrou vantagem neste conjunto.

As 22 perguntas cobrem entidades novas, dois contextos, revisão de fatos com
perda de nós e esquecimento de memória curta. O modelo pontua alternativas
fechadas (`A`, `B`, `C`, `D`, `UNKNOWN`) por verossimilhança condicional média.
Isso não mede qualidade de respostas livres. A geração de texto é verificada
separadamente no preflight e nos testes reais.

O tempo da tabela soma as chamadas do controlador e exclui carregamento do
modelo e compilação. Tokens avaliados incluem candidatos e validação paralela;
não representam apenas tokens gerados. Os custos do orçamento combinam tokens
com unidades de atualização e validação, sem equivalência a energia ou FLOPs.
Há uma única sequência fixa de políticas e um conjunto pequeno de perguntas;
os tempos não constituem benchmark estatístico. O feedback usa a resposta
esperada do experimento. Não há treinamento de pesos nem especialistas neurais
independentes: as rotas do controlador compartilham o mesmo modelo residente.

Na execução conjunta dos testes reais, o teste Python agora libera seu modelo e
o cache CUDA antes de iniciar os workers Rust. Antes dessa limpeza, o probe
excedeu o prazo de resposta ao executar após o teste de geração na mesma suíte.
