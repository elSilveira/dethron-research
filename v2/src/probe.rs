use crate::{
    audit::verify, crypto::random, encoding_probe, task::factorize, trit::Trit, tron::Tron,
};
use serde_json::{json, Value};
use std::time::Instant;

pub fn run(cycles: usize) -> Result<Value, String> {
    if !(1..=100).contains(&cycles) {
        return Err("Cycles must be in [1,100]".into());
    }
    let mut parent = Tron::new(0);
    parent.run(997, 2000)?;
    let mut history = Vec::new();
    let mut overhead = 0;
    let start = Instant::now();
    for _ in 0..cycles {
        let report = parent.evolve();
        overhead += report.evaluation_divisions;
        history.push(report);
    }
    let evolution_ns = start.elapsed().as_nanos();
    // These inputs are outside the evolution train/validation fixture sets.
    let workload = [1009, 1013, 1019, 1021, 1024, 1089, 1155, 1296];
    let (mut baseline, mut evolved, mut correct) = (0, 0, true);
    let mut baseline_ns = 0;
    let mut evolved_ns = 0;
    for n in workload {
        let start = Instant::now();
        let before = factorize(n, Trit::Minus, 2000)?;
        baseline_ns += start.elapsed().as_nanos();
        let start = Instant::now();
        let after = factorize(n, parent.strategy(), 2000)?;
        evolved_ns += start.elapsed().as_nanos();
        baseline += before.divisions;
        evolved += after.divisions;
        correct &= before.factors == after.factors;
    }
    let child = parent.spawn(true)?;
    let mut child = child;
    let key = random();
    let encrypted = child.checkpoint(&key)?;
    let child_key = child.audit.key();
    let child_head = child.audit.head();
    drop(child);
    let mut child = Tron::restore(&encrypted, &key, &child_key, &child_head)?;
    let child_recalled = child.run(997, 2000)?.cached;
    verify(
        &parent.audit.proof(),
        &parent.audit.key(),
        &parent.audit.head(),
    )?;
    verify(
        &child.audit.proof(),
        &child.audit.key(),
        &child.audit.head(),
    )?;
    Ok(
        json!({"schema":1,"compute_type":"classical_binary_hardware",
        "task":"bounded_integer_factorization","correct":correct,"cycles":history,
        "workload":workload,"cache_enabled_for_comparison":false,
        "baseline_divisions":baseline,"evolved_divisions":evolved,
        "evaluation_divisions":overhead,"net_divisions_saved":baseline as i64-evolved as i64-overhead as i64,
        "baseline_task_ns":baseline_ns,"evolved_task_ns":evolved_ns,"evolution_ns":evolution_ns,
        "timing_scope":"single small smoke run; task kernel only; not a production benchmark",
        "child_recalled":child_recalled,"audit_verified":true,
        "encrypted_checkpoint_bytes":encrypted.len(),"encoding":encoding_probe::run(),
        "parent":{"public_key":parent.audit.key(),"head":parent.audit.head(),"events":parent.audit.proof()},
        "child":{"public_key":child.audit.key(),"head":child.audit.head(),"events":child.audit.proof()},
        "limits":"fixed candidate strategies; inherited memoized results; not source synthesis or quantum computation"}),
    )
}
