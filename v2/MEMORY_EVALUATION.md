# Repeated DNA and memory evaluation

Target: v2 Rust APIs only. Archived Python memory code is not used. The root
Python arithmetic/semantic scorer tests are separate experiments, not v2 results.

Run from `v2` using a new output directory whose parent already exists:

```powershell
cargo run --release --locked --offline --example memory_batches -- results/new-memory-run
```

The runner saves all per-trial checks and observations as JSONL, plus a JSON
summary. The three batches contain 10, 100 and 1,000 trials with disjoint input
ranges (seed labels 1–10, 11–110 and 111–1110). These are deterministic varied
fixtures, not random population samples. Every trial creates a fresh Tron and
new fact targets; no training or shared evolving memory occurs between trials.

## What is exercised

- DNA reconstruction follows two supplied fact edges and records source work.
  There is no saved final-output cache passed to reconstruction. The terminal
  fact contains the target; this is bounded graph traversal, not arithmetic or
  language-model reasoning.
- Alternate-route loss still allows a conclusion. Complete loss, conflicting
  evidence, stale revisions, revocation and foreign contexts cause abstention.
  Changed source targets change conclusions; a constant wrong answer is rejected.
- Independent product and primality checks verify fresh factorization results.
  Immediate recall and recall after 20 distinct intervening computations must
  remain correct and cached.
- An encrypted snapshot is restored after dropping the original object, then
  cached recall is checked. This repeated probe uses same-process restoration;
  the existing `restart` integration suite separately tests a fresh process.
- Snapshot byte tampering must be rejected.
- After 129 larger-number computations, the original input is queried again.
  Correctness and the 128-entry bound are checked. Cache retention is separately
  measured rather than redefining a cache miss as an incorrect mathematical result.

Fourteen implemented checks are evaluated per trial. Two additional requirements
are recorded as BLOCKED by API inspection, not executed as if implemented:
arbitrary natural-language paraphrase equivalence and explicit time-based
short/medium/long-term memory policies. Presentation formatting is not a semantic
judge. Intervening computations and snapshot restoration do not establish weeks
or months of retention.

## Interpretation

The current `Tron` uses a bounded map of memoized factors. It removes the lowest
numeric key at capacity, even if that key was accessed recently. The source-DNA
reconstruction API and this factorization cache are separate mechanisms; this
probe does not establish a unified persistent semantic DNA memory.

Larger batches test recurrence across more fixtures. They do not improve the
implementation, measure learning, or estimate time to readiness. No conventional
memory baseline or model quality benchmark is included. Related deterministic
checks must not be treated as independent population accuracy measurements.
Timing includes audit signing, verification, instrumentation and report writes;
it is not model latency. Exceptions remain visible as trial execution errors;
per-check totals must be read together with attempted trials and error counts.

Next improvements to evaluate: define memory-tier contracts, choose a retention
policy that protects valuable recent knowledge, persist source-DNA state through
the intended runtime, and test held-out semantic transformations. Compare each
change against the current implementation on the same workload, including its
resource cost. Do not silently relax the existing correctness checks.
