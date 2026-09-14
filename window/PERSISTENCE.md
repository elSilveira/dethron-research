# Persistência e reconstrução da execução

O `v2` agora oferece `network::run_persistent`, além da execução em memória.
O journal salva registros, evidências, orçamento, tarefas pendentes e posição nas
ondas. A recuperação exige o mesmo plano, limites, identificação do backend e
chave de 32 bytes. O modelo e seu runtime continuam sendo recursos externos.

## Garantia implementada

Antes de despachar uma onda, o coordenador grava e sincroniza um checkpoint com
as reservas máximas de tokens. Depois grava os resultados devolvidos pela onda.
Cada checkpoint é um arquivo novo, criptografado e autenticado com AES-256-GCM,
com nonce aleatório e encadeamento por SHA-256. O plano está vinculado à autenticação.
Criação exclusiva do arquivo impede sobrescrever uma geração existente.

Ao reabrir uma execução:

- Registros concluídos sobreviventes são reutilizados, sem executar novamente.
- Tarefas reservadas sem conclusão persistida tornam-se falhas indeterminadas.
  Seu custo máximo permanece contabilizado; seus descendentes ficam bloqueados.
- Não há repetição automática. O chamador precisa decidir se cria outra execução
  para tentar novamente; isso pode repetir trabalho que ocorreu antes da queda.
- Chave errada, plano/backend diferente, arquivos fora de sequência ou corrupção
  impedem a recuperação. Não há retorno silencioso a um checkpoint antigo.

A execução paralela atual coleta os resultados ao final da onda. Uma queda antes
da persistência pode deixar indeterminada uma tarefa que já terminou fisicamente.
Essa política prefere declarar incerteza a fabricar certeza ou repetir efeitos.
Não há garantia de exactly-once para efeitos externos.

## Limites importantes

O journal tolera reinício de processo com armazenamento íntegro. Não foi testado
desligamento elétrico, falha de disco, filesystem remoto ou durabilidade do diretório
sob perda de energia. Um arquivo final parcialmente escrito causa falha explícita.

O hash encadeado detecta alterações e lacunas internas, mas não detecta a remoção
de todo o sufixo recente ou a substituição por uma cópia antiga completa. O relatório
expõe `checkpoint_head`; proteção contra rollback exige guardar e verificar uma
referência confiável externa. Isso ainda não está automatizado nesta API.

Use um coordenador por diretório. A criação exclusiva evita publicação concorrente
na mesma geração, mas não há eleição, lease ou suporte a failover ativo simultâneo.
Não iniciar uma recuperação enquanto o coordenador original ainda trabalha.

Há limite de 300 checkpoints e 16 MiB por arquivo. São snapshots completos, não
deltas compactos: o armazenamento cresce com a execução. Não há coleta automática,
replicação entre máquinas ou gestão/backup da chave. Perder a chave ou todas as
cópias utilizáveis impede reconstruir o estado. A chave fica fora do journal.

O backend_revision da API é declarado pelo chamador. O CLI deriva esse vínculo
dos fingerprints dos pesos/tokenizer, versões de Torch/Transformers, dispositivo
e dtype. Não representa atestação de hardware nem assinatura individual de TRON.

## Usar no harness

Em um config com `workers` e `tasks` explícitos, acrescente:

```json
"persistence": {
  "directory": "results/minha-execucao/journal",
  "key_file": "private/minha-chave.bin"
}
```

O arquivo da chave deve conter exatamente 32 bytes binários aleatórios, guardados
separadamente. `private/` está ignorado pelo Git. Execute novamente o mesmo config:

```powershell
python run_network.py --config meu-config.json
```

O CLI ainda carrega o worker e faz preflight ao recuperar uma execução concluída;
somente as inferências das tarefas persistidas são evitadas. Os tempos de cada
registro pertencem à sessão original. O tempo global da recuperação mede a nova
chamada; `tasks_per_second` não deve ser usado como benchmark de inferência quando
`recovered_records` for maior que zero. Tokens/custos persistidos são cumulativos.

## Validação desta etapa

Os testes do core executam uma segunda instância do binário de testes e encerram
o processo com código 73 durante a segunda tarefa, sem destrutores. A reconstrução
preserva a primeira resposta, marca a segunda indeterminada, bloqueia a terceira
dependente e comprova zero chamadas adicionais. O teste usa um worker declarado
como fixture; prova recuperação, não qualidade do modelo.

Outros testes cobrem reabertura concluída, chave errada, mudança de plano/backend,
checkpoint corrompido, orçamento e configuração inválida. A validação com pesos
reais é registrada separadamente abaixo.

Execução real inicial: `results/network-20260914T151454Z-99f72b91/`.
Reabertura em novo processo: `results/network-20260914T151611Z-b3f1c066/`.
O checkpoint local foi `results/persistence-d69477ae/journal/`, com chave externa
em `private/`. A pergunta de controle retornou Paris. Na segunda execução,
`recovered_records` passou de zero para um e o registro completo permaneceu
idêntico, inclusive a identidade do worker original; a nova sessão teve outro PID.
Os manifests das duas execuções coincidem com as fontes finais do núcleo/harness.

Passaram 39 testes Rust do v2, 63 testes Rust do window, 20 testes Python,
Clippy dos dois crates e verificação de formatação. Há cenários repetidos entre
os crates e um teste auxiliar usado como subprocesso de falha. Todos os arquivos
fonte/teste permanecem dentro do limite de 200 linhas.

## Reconstrução, quantização e rádio

Esta etapa fornece continuidade condicionada à sobrevivência do estado e da chave,
não imortalidade. O próximo avanço é reconstruir a partir de réplicas verificadas
quando uma cópia falhar, preservando referências de versão e controle de rollback.

Diminuir pesos por quantização pode reduzir a quantidade de dados de um modelo,
mas não compacta automaticamente o journal, nem mantém necessariamente a mesma
qualidade. Evidências e identidades devem ser preservadas sem perda. Antes de
transmitir por enlaces limitados, precisamos medir snapshots versus deltas,
compressão sem perda, fragmentação e retransmissão.

Rádio pode fornecer comunicação sem internet; continua exigindo transmissores,
receptores, energia e um protocolo. Esta entrega não implementa transporte por
rádio, operação sem enlace, novos formatos quantizados nem economia de energia.
