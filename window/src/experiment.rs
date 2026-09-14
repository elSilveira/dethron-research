use crate::{lineage, stream::Stream};
use serde_json::json;
use std::time::Instant;
use tron_v2::{
    task::factorize,
    trit::{pack, unpack, Trit},
    tron::Tron,
};

pub fn run(cycles: usize, stream: &mut Stream) -> Result<(), String> {
    stream.emit(
        "started",
        json!({"cycles":cycles, "step_delay_ms":stream.delay_ms,
        "task":"bounded_integer_factorization", "compute_type":"classical_binary_hardware"}),
    )?;
    let mut parent = Tron::new(0);
    stream.emit(
        "parent_created",
        json!({"identity":parent.audit.identity(),
        "strategy":parent.strategy(), "version":parent.version()}),
    )?;
    let learned = parent.run(997, 2000)?;
    stream.emit(
        "learned",
        json!({"input":997, "divisions":learned.work.divisions,
        "knowledge_count":parent.knowledge_len()}),
    )?;
    let (mut overhead, mut evolution_ns) = (0_u64, 0_u128);
    let mut history = Vec::new();
    for index in 0..cycles {
        let start = Instant::now();
        let report = parent.evolve();
        let duration = start.elapsed().as_nanos();
        evolution_ns += duration;
        overhead += report.evaluation_divisions;
        stream.emit(
            "evolution",
            json!({"cycle":index + 1, "measurement":report,
            "strategy":parent.strategy(), "version":parent.version(), "duration_ns":duration}),
        )?;
        history.push(report);
    }
    let workload = [1009, 1013, 1019, 1021, 1024, 1089, 1155, 1296];
    let (mut baseline, mut evolved, mut correct) = (0_u64, 0_u64, true);
    let (mut baseline_ns, mut evolved_ns) = (0_u128, 0_u128);
    for (index, number) in workload.iter().enumerate() {
        // Alternate order; clocks exclude event output and visualization delays.
        let strategies = if index % 2 == 0 {
            [Trit::Minus, parent.strategy()]
        } else {
            [parent.strategy(), Trit::Minus]
        };
        let mut results = Vec::new();
        for strategy in strategies {
            let start = Instant::now();
            let work = factorize(*number, strategy, 2000)?;
            results.push((work, start.elapsed().as_nanos()));
        }
        if index % 2 != 0 {
            results.reverse();
        }
        let (before, before_ns) = &results[0];
        let (after, after_ns) = &results[1];
        let equal = before.factors == after.factors;
        baseline += before.divisions;
        evolved += after.divisions;
        baseline_ns += before_ns;
        evolved_ns += after_ns;
        correct &= equal;
        stream.emit(
            "task",
            json!({"input":number, "correct":equal,
            "baseline_divisions":before.divisions, "evolved_divisions":after.divisions,
            "baseline_task_ns":before_ns, "evolved_task_ns":after_ns}),
        )?;
        if !equal {
            return Err("Workload correctness failed".into());
        }
    }
    let lineage = lineage::run(&mut parent, stream)?;
    let values: Vec<_> = (0..100_000)
        .map(|i| [Trit::Minus, Trit::Zero, Trit::Plus][i % 3])
        .collect();
    let packed = pack(&values);
    let encoding = json!({"symbols":values.len(), "trit_bytes":packed.len(),
        "two_bit_bytes":values.len().div_ceil(4), "roundtrip":unpack(&packed, values.len())? == values,
        "scope":"payload only; two-bit size calculated; headers excluded"});
    stream.emit("encoding", encoding.clone())?;
    if lineage["child_recalled"] != true || encoding["roundtrip"] != true {
        return Err("Inheritance or encoding verification failed".into());
    }
    let mut report = json!({"schema":1, "task":"bounded_integer_factorization",
        "compute_type":"classical_binary_hardware", "correct":correct,
        "cycles":history, "workload":workload, "cache_enabled_for_comparison":false,
        "baseline_divisions":baseline, "evolved_divisions":evolved,
        "evaluation_divisions":overhead,
        "net_divisions_saved":baseline as i64 - evolved as i64 - overhead as i64,
        "baseline_task_ns":baseline_ns, "evolved_task_ns":evolved_ns,
        "evolution_ns":evolution_ns, "encoding":encoding, "step_delay_ms":stream.delay_ms,
        "timing_scope":"single smoke run; task kernels and evolution timed separately; excludes display delays and output",
        "limits":"fixed strategies and memoized inheritance; not distributed inference or a speedup benchmark"});
    report
        .as_object_mut()
        .unwrap()
        .extend(lineage.as_object().unwrap().clone());
    stream.emit("completed", report)
}
