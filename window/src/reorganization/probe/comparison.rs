use super::super::{graph::Primitive::*, Engine, Policy, Request};
use serde_json::{json, Value};
use std::time::Instant;

fn run(seed: u64, policy: Policy) -> Result<Value, String> {
    let shift = (seed % 9) as i64 - 4;
    let multiplier = (seed % 3) as i64 + 2;
    let bias = -((seed % 5) as i64);
    let start = Instant::now();
    let mut engine = Engine::new(policy, 1_000_000);
    engine.register(
        "calibration",
        &[
            Add(shift),
            Multiply(multiplier),
            Add(bias),
            Absolute,
            Add(7),
        ],
    )?;
    let initial_ns = start.elapsed().as_nanos();
    let initial_work_units = 1_000_000 - engine.budget.remaining();
    let mut phases = Vec::new();
    let (mut total_correct, mut total_failures, mut total_ns) = (0, 0, 0_u128);
    for (phase, (label, context)) in [
        ("new_inputs", 1),
        ("context_shift", 2),
        ("return_to_context", 1),
        ("procedure_revision", 1),
    ]
    .into_iter()
    .enumerate()
    {
        let mut elapsed = if phase == 0 { initial_ns } else { 0 };
        let before = engine.budget.remaining();
        if phase == 3 {
            let start = Instant::now();
            engine.revise(
                "calibration",
                &[
                    Add(shift + 1),
                    Multiply(multiplier),
                    Add(bias),
                    Absolute,
                    Add(7),
                ],
            )?;
            elapsed += start.elapsed().as_nanos();
        }
        let (mut correct, mut failures, mut shadows, mut nodes) = (0, 0, 0, 0);
        let mut inputs = Vec::new();
        for index in 0..64 {
            let input =
                phase as i64 * 10_000 + ((seed as i64 * 257 + index * 31) % 10_000) - 20_000;
            inputs.push(input);
            let expected = ((input + shift + i64::from(phase == 3)) * multiplier + bias).abs() + 7;
            let start = Instant::now();
            let result = engine.submit(Request {
                capability: "calibration",
                context,
                input,
                ingress: 900,
                sink: 901,
            });
            match result {
                Ok(delivery) => {
                    let accepted = delivery.value == expected;
                    engine.feedback("calibration", &delivery, accepted)?;
                    correct += usize::from(accepted);
                    shadows += usize::from(!delivery.shadow_nodes.is_empty());
                    nodes += delivery.primary_nodes.len() + delivery.shadow_nodes.len();
                }
                Err(_) => failures += 1,
            }
            elapsed += start.elapsed().as_nanos();
        }
        phases.push(
            json!({"name":label,"context":context,"inputs":inputs,"correct":correct,
            "failures":failures,"total_ns":elapsed,"shadow_tasks":shadows,"node_executions":nodes,
            "work_units":before-engine.budget.remaining()}),
        );
        total_correct += correct;
        total_failures += failures;
        total_ns += elapsed;
    }
    let state = engine.inspect();
    Ok(
        json!({"seed":seed,"policy":format!("{policy:?}"),"budget_limit":1_000_000,
        "attempted":256,"correct":total_correct,"failures":total_failures,"total_ns":total_ns,
        "initial_ns":initial_ns,"initial_work_units":initial_work_units,
        "work_units":1_000_000-engine.budget.remaining(),
        "phases":phases,"diagnostic_state_bytes":serde_json::to_vec(&state).unwrap().len(),
        "work_breakdown":state["work"]}),
    )
}

pub fn benchmark(seeds: u64) -> Result<Value, String> {
    if !(1..=100).contains(&seeds) {
        return Err("Seeds must be 1..100".into());
    }
    let mut runs = Vec::new();
    let policies = [Policy::Fixed, Policy::Compiled, Policy::Adaptive];
    for seed in 1..=seeds {
        for offset in 0..3 {
            runs.push(run(seed, policies[(seed as usize + offset) % 3])?);
        }
    }
    Ok(json!({"schema":1,"runs":runs,"cache_enabled":false,
        "timing_scope":"initialization, registration, revision, all submits and feedback; excludes JSON output",
        "work_scope":"declared bounded work charges, not instruction counts or energy",
        "memory_scope":"diagnostic serialized state bytes, not peak resident memory",
        "limits":"synthetic arithmetic only; declarative capability routing; algebraic composition is hand-specified; no proof of general learning",
        "control":"Compiled uses the same composer on declared procedures, without waiting for experience",
        "validation_policy":{"formation_distinct_inputs":2,"confirmation_distinct_new_inputs":3,"periodic_shadow_every":16}}))
}
