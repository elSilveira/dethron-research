# V2 — roteiro de reprodução por estranho

Este roteiro é para quem **não escreveu o código** e vai reproduzir, em outra
máquina, os resultados de G0 a V1 usando apenas o repositório clonado. Se algum
passo exigir ajuda de quem escreveu, ou algum arquivo que não esteja no clone,
isso é uma reprovação do V2 — e é exatamente o que este marco quer descobrir.

Tempo total: cerca de **15 minutos de preparação** e **40 minutos de execução**
sem intervenção. Durante a execução, não use a máquina para nada pesado e não a
deixe suspender.

## Regra única

**Nada da máquina original entra.** Não copie `results/`, ambientes virtuais,
chaves, nem qualquer arquivo por fora. O clone é a única entrada. Se você já tem
uma cópia antiga deste projeto na máquina, use uma pasta nova.

## Pré-requisitos

| Item | Exigência | Como conferir |
| --- | --- | --- |
| Sistema | Windows 10 ou 11 | A evidência do G4 usa `netstat`; outros sistemas não foram exercitados |
| Python | **3.10.x**, no PATH como `python` (foi executado com 3.10.11) | `python --version` |
| Git | qualquer versão recente | `git --version` |
| Rust (`cargo`) | **opcional**: só os 15 testes do *survival* precisam dele | `cargo --version`; sem ele o executor detecta e os exclui sozinho |
| Caminho do clone | **curto (até 100 caracteres) e sem espaços, aspas ou acentos**, por exemplo `C:\dethron` | O Windows limita caminhos a 260 caracteres e os artefatos dos experimentos acrescentam cerca de 150; a ponte do G4 recusa espaços. O executor mede isso e para antes de rodar se o caminho for longo |
| Rede | internet apenas para o `pip install`; os experimentos usam só `127.0.0.1` | O Firewall do Windows pode perguntar sobre `python.exe`: permitir |
| Espaço | ~300 MB (ambiente virtual e artefatos) | — |

Instale Python pelo instalador oficial de python.org marcando "Add to PATH";
o atalho da Microsoft Store não serve para criar o ambiente virtual.

## Qual terminal usar

Os comandos abaixo funcionam **tanto no PowerShell quanto no Prompt de Comando
(cmd)**, porque nenhum deles depende de variável de ambiente: o executor define
o que precisa sozinho. Se você encontrar em outro documento uma linha começando
com `$env:`, ela só funciona no PowerShell — prefira sempre o executor.

## Passo 1 — clonar

No terminal:

```powershell
git clone https://github.com/elSilveira/dethron.git C:\dethron
cd C:\dethron
git log --oneline -1
```

**Esperado:** a última linha mostra o hash e a mensagem do commit mais recente.
Anote esse hash: ele vai no seu relatório.

## Passo 2 — ambiente fixado

```powershell
python --version
python -m venv window\.venv-gateway
window\.venv-gateway\Scripts\python.exe -m pip install -r window\requirements-gateway.txt
window\.venv-gateway\Scripts\python.exe -c "import importlib.metadata as m; print({n: m.version(n) for n in ('rns','lxmf','cryptography')})"
```

**Esperado:**

- `Python 3.10.x`
- `pip` termina sem `ERROR` (avisos sobre versão nova do pip são normais)
- a última linha imprime exatamente
  `{'rns': '1.5.4', 'lxmf': '1.1.1', 'cryptography': '50.0.1'}`

Qualquer outra versão é reprovação do passo: não continue, relate.

## Passo 3 — suíte rápida

```powershell
window\.venv-gateway\Scripts\python.exe window\run_v2_reproduction.py --fast-only
```

**Esperado, com Rust:**

```
fast full                   ran=203 skipped=8 PASS
V2 PASS - summary: C:\dethron\window\results\v2-...\summary.json
```

**Sem Rust**, a primeira linha será `note: cargo not found...` e o esperado passa a
ser seis linhas `fast test_...  PASS`, uma linha
`fast subset total  ran=133 skipped=8 PASS` e `V2 PASS`.

Os 8 pulados são os testes de reprodução real, que só rodam no passo 4. Leva
cerca de 40 segundos com Rust já compilado; a primeira compilação do *survival*
pode levar alguns minutos.

Se **um único** teste falhar, repita o comando uma vez com a máquina ociosa. Se
falhar de novo, é reprovação: relate a saída completa.

A primeira linha impressa, `environment: {...}`, deve terminar com `"problems": []`.
Se aparecer `PROBLEM: repository path too long`, o clone está num caminho longo
demais: mova-o para algo como `C:\dethron` e recomece do passo 2. Esse caso foi
observado na máquina de origem: um clone em caminho de 135 caracteres passou a
suíte rápida e reprovou **os oito** experimentos reais com `inconclusive`, porque
o Reticulum não conseguia gravar em `rns\storage`.

## Passo 4 — os oito caminhos de reprodução real

```powershell
window\.venv-gateway\Scripts\python.exe window\run_v2_reproduction.py
```

O comando repete a suíte rápida e depois
executa, um por vez, os oito experimentos reais. Cada um sobe processos
Reticulum/LXMF de verdade em `127.0.0.1`, grava um diretório em
`window\results\` e produz um veredito. **Esperado**, na ordem:

| Linha impressa começa com | Veredito esperado | Tempo de referência |
| --- | --- | --- |
| `test_gateway_reference.py` | `meets_scoped_requirement` | 208 s |
| `test_g1_reference.py` | `meets_g1_lab_contract` | 31 s |
| `test_g2_reference.py` | `meets_g2_scoped_contract` | 185 s |
| `test_g2_comparison_reference.py` | `g2_scoped_pass` | 754 s |
| `test_g3_reference.py` | `g3_scoped_pass` | 295 s |
| `test_g4_reference.py` | `g4_scoped_pass` | 167 s |
| `test_v1_reference.py` | `v1_custody_scoped_pass` | 213 s |
| `test_v1_return_reference.py` | `v1_return_scoped_pass` | 332 s |

Cada linha deve terminar com `PASS` e a última linha deve ser
`V2 PASS - summary: ...`. **Nenhuma janela de console deve abrir** durante a
execução; os processos dos experimentos rodam ocultos. Se janelas piscarem,
anote quando e relate — isso aconteceu na máquina de origem antes de uma correção
e é um dado útil. Os tempos de referência foram medidos na máquina de
origem. Numa segunda máquina já validada, os mesmos caminhos levaram de 1,0 a
2,3 vezes esses valores — o G3, por exemplo, 663 s contra 295 s. **Até o triplo**
não indica problema. Um caminho que passe do
triplo do tempo de referência ou trave por mais de 15 minutos sem imprimir nada
deve ser interrompido com `Ctrl+C` e relatado.

## O que deve ser idêntico e o que pode diferir

**Idêntico ao esperado, senão é reprovação:**

- as oito strings de veredito e o `V2 PASS` final;
- as contagens da suíte rápida: 203 e 8, ou 133 e 8 sem Rust;
- dentro de cada `report.json`, os resultados de cenário: quais completaram,
  as listas de pendência, a rota da prova, a presença da recusa, zero endpoints
  IP nos cenários isolados do G4 e pelo menos um na linha de base `ip`.

**Pode e vai diferir, sem problema:**

- todos os tempos em segundos;
- hashes, identidades, `transient_id`, PIDs, portas e nomes de diretório em
  `results/`;
- número exato de bytes transportados e o número de endpoints na linha de base
  `ip` do G4 (aqui foram três; qualquer valor maior que zero serve).

Os documentos em `window/*.md` apontam para diretórios `results/…` da máquina
original; esses links **não existem no seu clone** até você rodar o passo 4, e
mesmo então terão outros nomes. Isso é esperado e está declarado neles.

## Resultado: aprovado em 18/09/2026

A execução completa numa segunda máquina, numa única passada, **passou**:
veredito `v2_pass` em 58,0 minutos, com os oito caminhos produzindo o veredito
declarado e a suíte em 113 e 8 — o `cargo` estava ausente e o executor o detectou
sozinho, como deve.

| Caminho | Veredito | Tempo | Referência |
| --- | --- | --- | --- |
| `test_gateway_reference.py` | `meets_scoped_requirement` | 214,8 s | 208 s |
| `test_g1_reference.py` | `meets_g1_lab_contract` | 30,1 s | 31 s |
| `test_g2_reference.py` | `meets_g2_scoped_contract` | 181,0 s | 185 s |
| `test_g2_comparison_reference.py` | `g2_scoped_pass` | 744,6 s | 754 s |
| `test_g3_reference.py` | `g3_scoped_pass` | 704,1 s | 295 s |
| `test_g4_reference.py` | `g4_scoped_pass` | 366,6 s | 167 s |
| `test_v1_reference.py` | `v1_custody_scoped_pass` | 501,9 s | 213 s |
| `test_v1_return_reference.py` | `v1_return_scoped_pass` | 658,6 s | 332 s |

O código executado foi o commit `1e2d190`, deduzido das contagens da suíte e das
expectativas registradas no resumo; o executor **não gravava** qual commit rodava,
o que é uma falha do instrumento e não do resultado. Desde então ele grava, e o
resumo falha de forma visível se o `git` não responder.

### O que este resultado é, e o que não é

É reprodução em máquina independente, por quem não escreveu o código, seguindo
apenas o documento. Não é reprodução por um estranho no sentido estrito: quem
executou é o autor do projeto, teve contato com quem escreveu o código e, na
primeira tentativa, precisou de explicação fora do roteiro — o que por este
próprio critério foi uma reprovação, registrada abaixo. Esta passada testou o
roteiro já corrigido e não exigiu ajuda.

## Primeira execução real, 17/09/2026

A primeira execução deste roteiro numa segunda máquina **reprovou**, e vale
registrar o que ela encontrou, porque é para isso que o marco existe:

| O que falhou | Causa | Onde ficou a correção |
| --- | --- | --- |
| Dois testes da suíte | `cargo` ausente, e o executor exigia `--no-survival` manual | O executor detecta `cargo` sozinho |
| G3, `inconclusive` | Defeito do LXMF 1.1.1: um carimbo válido descartado por `ZeroDivisionError` numa linha de log, matando em silêncio a chave de peering | [G3](G3_GENERATIONS.md) e `dethron_gateway/lxmf_stamp.py` |
| Repetir o G3 pelo roteiro | A instrução usava `$env:` do PowerShell; no cmd a variável não é definida e o teste **se pula reportando `OK`** | `--only <marco>`, sem variável de ambiente |

Os outros sete caminhos reproduziram com veredito idêntico na primeira tentativa.
Depois das correções, o G3 também passou na segunda máquina, em 663 s. Falta a
execução completa numa única passada para fechar o marco.

## Repetir um marco isolado

Se só um dos oito falhou e você quer repetir apenas ele, sem esperar os 40 minutos:

```
window\.venv-gateway\Scripts\python.exe window\run_v2_reproduction.py --only g3
```

Os nomes aceitos são `gateway`, `g1`, `g2`, `g2_comparison`, `g3`, `g4`, `v1` e
`v1_return`. A saída é uma linha `PASS` ou `FAIL` e o veredito obtido.

## Se algo falhar

Rode, na mesma pasta:

```powershell
window\.venv-gateway\Scripts\python.exe window\v2_diagnose.py
```

Ele grava um arquivo de texto com o ambiente, o nome e o traceback de cada teste
que falhou, e o erro registrado no experimento que não passou. O caminho aparece
na última linha. Envie esse arquivo: ele costuma bastar para o diagnóstico.

## O que enviar de volta

1. O arquivo `window\results\v2-...\summary.json` (o caminho aparece na última
   linha impressa). Ele contém ambiente, contagens, vereditos e tempos.
2. A saída completa do console dos passos 2, 3 e 4, copiada como texto.
3. O hash do passo 1, `python --version`, a versão do Windows e o processador.
4. Se algo falhou: o que você fez, o que apareceu, e se precisou perguntar algo a
   alguém — **isso é um dado**, não um constrangimento.

Não envie os diretórios `results\gateway-*`: contêm chaves descartáveis de
laboratório e não são necessários; o `summary.json` basta.

## Como o resultado será julgado

| Situação | Julgamento |
| --- | --- |
| Tudo idêntico ao esperado, sem ajuda externa | **V2 aprovado** |
| Precisou de um arquivo, comando ou explicação que não está neste roteiro | V2 reprovado por documentação; o roteiro é corrigido e o teste repete |
| Um veredito diferente do esperado | V2 reprovado; investiga-se se é ambiente ou defeito real — os dois são resultados válidos |
| Falha só na primeira tentativa da suíte rápida e sucesso na repetição | Aprovado com nota: intermitência registrada para investigação |

Nenhum destes resultados é ruim para o projeto. O V2 existe para descobrir a
distância entre "funciona na máquina de quem escreveu" e "funciona a partir do
que está publicado", e qualquer distância encontrada é o que ele mede.
