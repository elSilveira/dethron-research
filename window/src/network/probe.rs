use super::{run, workload, Limits, Worker};
use serde_json::{json, Value};

pub fn compare(
    workers: &mut [Box<dyn Worker>],
    repeats: usize,
    cases: usize,
) -> Result<Value, String> {
    if !(1..=8).contains(&repeats) || !(2..=16).contains(&cases) {
        return Err("Use 1..8 repeats and 2..16 cases".into());
    }
    let modes = [
        "serial_direct",
        "pool_direct",
        "serial_wave",
        "parallel_wave",
    ];
    let mut trials = Vec::new();
    for round in 0..repeats {
        for position in 0..4 {
            let mode = modes[(position + round) % 4];
            eprintln!("Trial {}, {mode}, {cases} questions", round + 1);
            let tasks = workload::questions(round, cases, mode.ends_with("wave"));
            let count = if mode.starts_with("serial") {
                1
            } else {
                workers.len()
            };
            let result = run(
                &mut workers[..count],
                &tasks,
                Limits {
                    token_budget: 100_000,
                    ..Limits::default()
                },
            )?;
            let records = result["records"].as_array().unwrap();
            let mut answers = Vec::new();
            let mut latencies = Vec::new();
            for case in 0..cases {
                let id = format!("final-{case}");
                let record = records.iter().find(|r| r["id"] == id).unwrap();
                let expected = workload::expected(round, case);
                answers.push(
                    json!({"id":id,"expected":expected,"actual":record["output"],
                    "correct":record["status"]=="completed" && record["output"]==expected}),
                );
                if let Some(time) = record["finished_seconds"].as_f64() {
                    latencies.push(time);
                }
            }
            latencies.sort_by(f64::total_cmp);
            let correct = answers.iter().filter(|a| a["correct"] == true).count();
            let seconds = result["wall_seconds"].as_f64().unwrap();
            trials.push(json!({"round":round,"mode":mode,"questions":cases,"correct":correct,
                "correct_questions_per_second":correct as f64/seconds,
                "p50_completion_seconds":percentile(&latencies,0.5),
                "p95_completion_seconds":percentile(&latencies,0.95),"answers":answers,"run":result}));
        }
    }
    let summaries: Vec<_> = modes.iter().map(|mode| {
        let matching: Vec<_> = trials.iter().filter(|t| t["mode"]==*mode).collect();
        let correct: u64 = matching.iter().map(|t| t["correct"].as_u64().unwrap()).sum();
        let seconds: f64 = matching.iter().map(|t| t["run"]["wall_seconds"].as_f64().unwrap()).sum();
        let tokens: u64 = matching.iter().map(|t| t["run"]["evaluated_tokens"].as_u64().unwrap()).sum();
        json!({"mode":mode,"correct":correct,"questions":cases*repeats,
            "wall_seconds":seconds,"evaluated_tokens":tokens,"correct_questions_per_second":correct as f64/seconds})
    }).collect();
    Ok(json!({"trials":trials,"summaries":summaries,
        "limits":"Synthetic closed-choice tasks; fixed weights and manually declared branches. Rotating order, no statistical scaling claim. Same per-trial token cap; actual costs include all branches. Serial modes use worker zero while other replicas remain resident."}))
}
fn percentile(values: &[f64], fraction: f64) -> Value {
    if values.is_empty() {
        Value::Null
    } else {
        json!(values[(values.len() as f64 * fraction).ceil() as usize - 1])
    }
}
