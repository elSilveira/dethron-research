mod support;
use serde_json::json;
use std::{fs::OpenOptions, io::Write, path::Path, time::Instant};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let destination = std::env::args()
        .nth(1)
        .ok_or("Provide a new results directory")?;
    let destination = Path::new(&destination);
    std::fs::create_dir(destination)?;
    let mut seed = 1u64;
    let mut summaries = Vec::new();
    for count in [10, 100, 1000] {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(destination.join(format!("trials-{count}.jsonl")))?;
        let start_seed = seed;
        let batch_started = Instant::now();
        let mut trials = Vec::new();
        for _ in 0..count {
            let started = Instant::now();
            let mut result = support::trial(seed)
                .unwrap_or_else(|error| json!({"seed":seed,"error":error,"checks":[]}));
            result["elapsed_ns"] = json!(started.elapsed().as_nanos());
            writeln!(file, "{result}")?;
            trials.push(result);
            seed += 1;
        }
        file.sync_all()?;
        let mut summary = support::summarize(&trials);
        summary["start_seed"] = json!(start_seed);
        summary["elapsed_seconds"] = json!(batch_started.elapsed().as_secs_f64());
        println!("{}", serde_json::to_string(&summary)?);
        summaries.push(summary);
    }
    let report = json!({"schema":1,"target":"v2","batches":summaries,
        "scope":"Fresh sequential fixture trials, not training, elapsed-time endurance, or model inference",
        "restore_scope":"same-process restore; separate existing test covers fresh-process restoration",
        "gaps":["natural-language paraphrase understanding","explicit time-based memory tiers"],
        "capacity_probe":"129 larger numeric keys; measures current bounded-map eviction, not arbitrary workloads"});
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(destination.join("summary.json"))?;
    file.write_all(&serde_json::to_vec_pretty(&report)?)?;
    file.sync_all()?;
    Ok(())
}
