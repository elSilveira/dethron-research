# TRON Window

A local browser dashboard for the real Rust TRON prototype. All application
files live here. The small Rust adapter depends on `../v2`; it calls the existing
library and streams public events as each operation executes. The `v2` source
does not need to be changed.

## Start

From the repository root:

```powershell
python window/app.py
```

On macOS/Linux, use `python3 window/app.py` if `python` is unavailable.
The launcher builds the adapter, starts a server, and opens
<http://127.0.0.1:8765>. From inside `window`, use `python app.py`.

Requirements: Python 3.10+, Rust/Cargo 1.89+ with the platform's native build
tools, and a modern browser. No pip packages, Node, React, CDN, or account is
required to run the app. Keep `window` and `v2` beside each other.

The launcher builds offline using cached Cargo dependencies. On a new machine,
download them once from inside `window`:

```powershell
cargo build --release --locked
python app.py
```

Options:

```powershell
python app.py --port 8766
python app.py --no-browser
python app.py --skip-build
```

`--skip-build` uses the existing release adapter; rebuild after Rust changes.
The server listens only on this computer. Press Ctrl+C in its terminal to stop
the server and any active worker. Closing the browser tab leaves the server
running; reopening the page reconnects to its current run.

## Try these experiments

1. Keep **3 cycles / 350 ms**, then click **Start experiment**. Watch the parent
   learn, evolve, compare eight inputs, and spawn a child. The child is encrypted,
   restored in the same worker process, and checked for inherited recall.
2. Expect a promotion on cycle 1 and plateaus afterward. For the fixed workload,
   expect 4,103 baseline divisions, 95 evolved divisions, and 1,809 candidate
   evaluation divisions: 2,199 net divisions saved with three cycles.
3. Select an event in **Inside the run** to inspect its data. Filter by evolution,
   workload, or lineage/audit. Timestamps include pacing; task/evolution timings
   exclude pacing and event output.
4. Try **20 cycles**. Repeated evaluation adds cost after the strategy plateaus;
   net work saved becomes negative. More cycles do not guarantee more benefit.
5. Start **100 cycles / 750 ms**, then click **Stop run**. The status becomes
   stopped, partial events remain visible, and no completed report is offered.
6. Try **No delay**. Operations execute as quickly as possible, so several events
   may arrive in one screen update. There is no simulated playback or fabricated
   activity. The browser checks for new events every 200 ms.

Live measurements start empty. A report becomes downloadable only after the
worker exits successfully and correctness, inherited recall, audit verification,
and encoding roundtrip checks pass. Errors, malformed events, missing results,
worker termination, and the five-minute execution deadline fail the run.

## Evidence and scope

Each start creates a distinct `window/results/<run-id>/` folder containing:

- `events.jsonl`: flushed public events, including partial runs.
- `stderr.log`: worker diagnostics.
- `status.json`: controls, final status, error, and finish timestamp.
- `report.json`: verified result, created only after successful execution.

Use **Events** or **Report** to download the current run from the browser.
Older runs remain on disk; restarting the server starts with an empty dashboard.
Results and build output are ignored by version control.

This visualizes integer factorization, selection among three fixed strategies,
memoized inheritance, signed audit commitments, and ternary packing on classical
hardware. Parent and child are Rust objects in one worker process, not separate
machines. Public identity and lineage are visible; signing keys, encryption keys,
factor payloads, and private audit openings are not sent to the dashboard.

The encoding view compares actual packed ternary bytes with the calculated size
of two-bit packing. Both exclude headers. The timing view is a small smoke
experiment, not a general performance benchmark. Include evolution cost when
interpreting task time; division savings alone do not prove a latency benefit.

## Feasibility probe

The new path-reorganization mechanism and its measured limits are documented in
[REORGANIZATION.md](REORGANIZATION.md). Run `python run_reorganization.py` to build
and save its reconstruction demo and a comparison over 20 paired seeds. This is
a separate executable; the browser dashboard still shows the original v2 probe.

The held-out comparison against all three fixed strategies is documented in
[FEASIBILITY.md](FEASIBILITY.md). Run `cargo run --release --locked --offline
--bin feasibility`. The current selector matches fixed Plus execution and adds
selection cost; this does not test structural path reorganization.

## Local neural integration

For evidence recognition and answer acceptance, run
`python run_network.py --experiment accuracy --workers 1 --device cuda`.
See [ACCURACY.md](ACCURACY.md) for the measured accuracy, packet contract, and
the current expansion gate.

The Rust controller can also run a resident local DeepSeek model, with versioned
memory, context isolation, and evidence-based reconstruction. Run
`python run_neural.py --mode preflight` for a real-model smoke check or
`python run_neural.py` for the three-policy experiment. This requires the separate
`.venv-neural` environment and the existing local checkpoint.
See [NEURAL_INTEGRATION.md](NEURAL_INTEGRATION.md) for commands, measured results,
and limitations. This experiment is available through the CLI; the browser still
shows the original factorization experiment.

## Verification

For concurrent workers and cooperative context waves, run
`python run_network.py --workers 2 --device cpu --generation-demo`.
See [NETWORK.md](NETWORK.md) for the serial/pool/wave comparison, custom task
graphs, and SSH endpoints for multiple machines.

From `window`:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
cargo test --locked --offline
cargo clippy --locked --offline --all-targets -- -D warnings
cargo fmt -- --check
```

Optional JavaScript state tests require Node 18+:

```powershell
node tests/model.test.mjs
```

Verified on Windows: 11 Python tests, 3 Rust adapter tests, 5 JavaScript tests,
and the existing 18 `v2` tests. Source/test files are below 200 lines.
Actual Chrome testing covers live updates before completion, measurements,
filters, event inspection, JSON download, stop/restart controls, and mobile
layout. macOS/Linux execution has not been tested on this machine.

`tests/browser_smoke.mjs` is an optional developer check requiring Node 22+ and
an isolated Chrome instance launched with `--headless=new`,
`--remote-debugging-port=0`, and a dedicated `--user-data-dir`. Run it against
a dedicated dashboard server, since it starts and stops real experiments:

```powershell
node tests/browser_smoke.mjs results/browser-qa http://127.0.0.1:8765
```

Screenshots from the local verification are in `results/browser-check/`.
