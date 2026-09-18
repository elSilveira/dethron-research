# Preparar duas máquinas para a bancada V3

Do zero até uma rodada completa. Uma das máquinas será **alpha** (relé e origem), a
outra **beta** (destinatário). Tanto faz qual é qual, desde que você não troque no meio.

Tempo: cerca de 20 minutos de preparação por máquina, uma vez só, e 10 minutos por
rodada depois disso.

## O que cada máquina precisa

| Item | Exigência | Como conferir |
| --- | --- | --- |
| Sistema | Windows 10 ou 11 | — |
| Python | **3.10.x**, no PATH como `python` | `python --version` |
| Git | qualquer versão recente | `git --version` |
| Caminho | **curto e sem espaços**: use `C:\dethron` | — |
| Rede | as duas na mesma rede local, enxergando uma à outra | passo 6 |
| Espaço | ~300 MB | — |
| Rust | **não é necessário** para a bancada V3 | — |

Instale o Python pelo instalador de [python.org](https://www.python.org/downloads/release/python-31011/)
marcando **"Add python.exe to PATH"**. O atalho da Microsoft Store não serve: ele não
cria ambientes virtuais corretamente.

---

# Parte 1 — preparação, nas DUAS máquinas

## 1. Clonar

```
git clone https://github.com/elSilveira/dethron.git C:\dethron
cd C:\dethron
```

## 2. Criar o ambiente

```
python --version
python -m venv window\.venv-gateway
window\.venv-gateway\Scripts\python.exe -m pip install -r window\requirements-gateway.txt
```

**Esperado:** `Python 3.10.x` e o `pip` terminando sem `ERROR`.

## 3. Conferir

```
window\.venv-gateway\Scripts\python.exe window\run_v2_reproduction.py --fast-only
```

**Esperado:** `fast subset total  ran=137 skipped=8 PASS` e `V2 PASS`.

Se você tiver Rust instalado, serão `207 e 8` em vez de `137 e 8`; os dois estão certos.

Se aparecer `PROBLEM: repository path too long`, o clone está num caminho comprido
demais — mova para `C:\dethron`.

---

# Parte 2 — descobrir os endereços

## 4. Na máquina ALPHA

```
ipconfig
```

Anote o **Endereço IPv4** da rede local, algo como `192.168.x.x`. Ele será o
**IP-ALPHA** em todos os passos seguintes.

## 5. Liberar a porta na ALPHA

PowerShell **como administrador**:

```powershell
New-NetFirewallRule -DisplayName "Dethron V3" -Direction Inbound -Protocol TCP -LocalPort 45810-45812 -Action Allow -Profile Any
```

## 6. Confirmar que a BETA alcança a ALPHA

Na **alpha**, deixe um ouvinte temporário:

```
window\.venv-gateway\Scripts\python.exe -c "import socket;s=socket.socket();s.bind(('0.0.0.0',45810));s.listen(1);print('ouvindo 60s');s.settimeout(60);print('CONECTOU:',s.accept()[1])"
```

Na **beta**, enquanto isso:

```powershell
Test-NetConnection IP-ALPHA -Port 45810
```

**Esperado:** `TcpTestSucceeded : True` na beta, e `CONECTOU:` na alpha.

Se der `False`, nada mais adiante vai funcionar. Causas comuns: a regra do passo 5 não
foi criada, a rede está como **Pública** com entrada bloqueada
(`Get-NetConnectionProfile`), ou o roteador isola os clientes entre si — nesse último
caso, use cabo.

> Testar essa porta **sem** o ouvinte rodando dá `False` mesmo com tudo correto, porque
> nada escuta nela fora do experimento. O ouvinte é o que torna o teste válido.

---

# Parte 3 — uma rodada

Cada rodada usa uma **pasta nova**. Não reaproveite: a bancada é de uso único, e
tentar reusá-la é recusado com uma mensagem explicando por quê.

## 7. Na ALPHA, preparar

Trocando `IP-ALPHA` pelo endereço do passo 4:

```
window\.venv-gateway\Scripts\python.exe window\run_v3_bench.py C:\dethron\bench1 IP-ALPHA 600
```

Ele imprime a **hora em que a janela abre** — 600 segundos de folga — e cria
`C:\dethron\bench1\control`.

## 8. Copiar para a BETA

Copie a pasta `C:\dethron\bench1\control` inteira para a beta, no mesmo caminho:
`C:\dethron\bench1\control`.

Pen drive, pasta compartilhada, e-mail: tanto faz. **Não precisa de rede compartilhada** —
as máquinas não trocam comandos durante o experimento, só combinam o instante de início.

## 9. Iniciar as duas, antes da hora impressa

Na **alpha**:
```
window\.venv-gateway\Scripts\python.exe window\run_v3_agent.py C:\dethron\bench1 alpha
```

Na **beta**:
```
window\.venv-gateway\Scripts\python.exe window\run_v3_agent.py C:\dethron\bench1 beta
```

As duas ficam esperando e imprimem quanto falta. Na hora marcada elas abrem juntas e
executam sozinhas por 4 minutos. **Não mexa em nada**, principalmente na pasta
`control`, que fica lacrada.

**Esperado no fim, nas duas:** `"verdict": "v3_agent_complete"`.

Se a alpha morrer no passo 0, pare tudo: a pasta já foi usada. Use `bench2`.

## 10. Juntar e gerar o veredito

Copie `C:\dethron\bench1\beta` da beta para a **alpha**, ficando ao lado da pasta
`alpha`. Então, na alpha:

```
window\.venv-gateway\Scripts\python.exe window\run_v3_report.py C:\dethron\bench1
```

**Esperado:** `"verdict": "v3a_scoped_pass"`.

O relatório fica em `C:\dethron\bench1\report.json`.

---

## Como ler o relatório

| Campo | O que significa |
| --- | --- |
| `machines[].control_unchanged` | A pasta de controle ficou lacrada: ninguém dirigiu a máquina durante a janela |
| `machines[].max_drift` | Quanto cada passo atrasou em relação ao horário declarado |
| `rendezvous.skew_seconds` | Quanto as duas janelas abriram fora de sincronia, sem canal vivo entre elas |
| `delivery.completed` | O destinatário reconstruiu os bytes exatos e emitiu recibo |
| `distinct_machines.evidenced` | As máquinas provaram ser distintas, por nome e pelo dono do endereço do relé |

Qualquer um deles falhando reprova a rodada, e o relatório diz qual e por quê.

## Quando algo falha

O `report.json` traz `verdict: inconclusive` e o erro. Os erros mais comuns:

| Erro | Causa |
| --- | --- |
| `missing authenticated parts: []` | O objeto não chegou. Veja o `evidence.jsonl` da beta: se o `fetch` ficou com `sync=240`, ela não alcançou o relé — volte ao passo 6 |
| `node already launched` | Pasta de bancada reutilizada. Use uma nova |
| `the recipient reached the relay over loopback` | Você usou `127.0.0.1` em vez do IP real |
| `the relay address ... belongs to ...` | O `IP-ALPHA` não é da máquina que rodou a alpha |
