# Preparing two machines for the V3 bench

From nothing to a complete round. One machine will be **alpha** (relay and origin), the
other **beta** (recipient). It does not matter which is which, as long as you do not
swap them half way.

Time: about 20 minutes of preparation per machine, once, and 10 minutes per round after
that.

## What each machine needs

| Item | Requirement | How to check |
| --- | --- | --- |
| System | Windows 10 or 11 | — |
| Python | **3.10.x**, on PATH as `python` | `python --version` |
| Git | any recent version | `git --version` |
| Path | **short and without spaces**: use `C:\dethron` | — |
| Network | both on the same local network, able to see each other | step 6 |
| Disk | ~300 MB | — |

Install Python from the [python.org](https://www.python.org/downloads/release/python-31011/)
installer, ticking **"Add python.exe to PATH"**. The Microsoft Store shortcut will not
do: it does not create virtual environments correctly.

---

# Part 1 — preparation, on BOTH machines

## 1. Clone

```
git clone https://github.com/elSilveira/dethron.git C:\dethron
cd C:\dethron
```

## 2. Create the environment

```
python --version
python -m venv window\.venv-gateway
window\.venv-gateway\Scripts\python.exe -m pip install -r window\requirements-gateway.txt
```

**Expected:** `Python 3.10.x`, and `pip` finishing without `ERROR`.

## 3. Check

```
window\.venv-gateway\Scripts\python.exe window\run_v2_reproduction.py --fast-only
```

**Expected:** `fast full  ran=166 skipped=8 PASS` and `V2 PASS`.

If you get `PROBLEM: repository path too long`, the clone sits on too long a path —
move it to `C:\dethron`.

---

# Part 2 — finding the addresses

## 4. On the ALPHA machine

```
ipconfig
```

Write down the local network's **IPv4 Address**, something like `192.168.x.x`. It is
**ALPHA-IP** in every step that follows.

## 5. Open the port on ALPHA

PowerShell **as administrator**:

```powershell
New-NetFirewallRule -DisplayName "Dethron V3" -Direction Inbound -Protocol TCP -LocalPort 45810-45812 -Action Allow -Profile Any
```

## 6. Confirm that BETA reaches ALPHA

On **alpha**, leave a temporary listener running:

```
window\.venv-gateway\Scripts\python.exe -c "import socket;s=socket.socket();s.bind(('0.0.0.0',45810));s.listen(1);print('listening 60s');s.settimeout(60);print('CONNECTED:',s.accept()[1])"
```

On **beta**, while that runs:

```powershell
Test-NetConnection ALPHA-IP -Port 45810
```

**Expected:** `TcpTestSucceeded : True` on beta, and `CONNECTED:` on alpha.

If it says `False`, nothing further will work. Common causes: the rule from step 5 was
not created, the network is **Public** with inbound blocked
(`Get-NetConnectionProfile`), or the router isolates clients from each other — in that
last case, use a cable.

> Testing that port **without** the listener running gives `False` even when everything
> is correct, because nothing listens on it outside the experiment. The listener is what
> makes the test valid.

---

# Part 3 — one round

Every round uses a **new folder**. Do not reuse one: a bench is single use, and trying
to reuse it is refused with a message explaining why.

## 7. On ALPHA, prepare

Replacing `ALPHA-IP` with the address from step 4:

```
window\.venv-gateway\Scripts\python.exe window\run_v3_bench.py C:\dethron\bench1 ALPHA-IP 600
```

It prints **the time the window opens** — 600 seconds of lead — and creates
`C:\dethron\bench1\control`.

## 8. Copy to BETA

Copy the whole `C:\dethron\bench1\control` folder to beta, to the same path:
`C:\dethron\bench1\control`.

USB stick, shared folder, e-mail: it does not matter. **No shared network is needed** —
the machines exchange no commands during the experiment, they only agree on the
starting instant.

## 9. Start both, before the printed time

On **alpha**:
```
window\.venv-gateway\Scripts\python.exe window\run_v3_agent.py C:\dethron\bench1 alpha
```

On **beta**:
```
window\.venv-gateway\Scripts\python.exe window\run_v3_agent.py C:\dethron\bench1 beta
```

Both wait and print how long is left. At the appointed time they open together and run
on their own for 4 minutes. **Touch nothing**, above all not the `control` folder, which
is sealed.

**Expected at the end, on both:** `"verdict": "v3_agent_complete"`.

If alpha dies at step 0, stop everything: the folder has been used already. Use
`bench2`.

## 10. Bring together and produce the verdict

Copy `C:\dethron\bench1\beta` from beta to **alpha**, next to the `alpha` folder. Then,
on alpha:

```
window\.venv-gateway\Scripts\python.exe window\run_v3_report.py C:\dethron\bench1
```

**Expected:** `"verdict": "v3a_scoped_pass"`.

The report lands in `C:\dethron\bench1\report.json`.

---

## Reading the report

| Field | What it means |
| --- | --- |
| `machines[].control_unchanged` | The control folder stayed sealed: nobody steered the machine during the window |
| `machines[].max_drift` | How late each step ran against its declared time |
| `rendezvous.skew_seconds` | How far apart the two windows opened, with no live channel between them |
| `delivery.completed` | The recipient reconstructed the exact bytes and issued a receipt |
| `distinct_machines.evidenced` | The machines proved distinct, by name and by who owns the relay address |

Any one of them failing fails the round, and the report says which and why.

## When something fails

`report.json` carries `verdict: inconclusive` and the error. The most common ones:

| Error | Cause |
| --- | --- |
| `missing authenticated parts: []` | The object never arrived. Look at beta's `evidence.jsonl`: if `fetch` was left with `sync=240`, it did not reach the relay — go back to step 6 |
| `node already launched` | Bench folder reused. Use a new one |
| `the recipient reached the relay over loopback` | You used `127.0.0.1` instead of the real address |
| `the relay address ... belongs to ...` | `ALPHA-IP` does not belong to the machine that ran alpha |
