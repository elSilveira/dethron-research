use serde_json::{json, Value};
use std::io::Write;
use tron_v2::network::config;
fn emit(kind: &str, data: Value) -> Result<(), String> {
    println!("{}", json!({"kind":kind,"data":data}));
    std::io::stdout().flush().map_err(|e| e.to_string())
}
fn execute() -> Result<(), String> {
    let path = std::env::args().nth(1).ok_or("Expected config")?;
    let config: Value = serde_json::from_slice(&std::fs::read(path).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let endpoints = config::endpoints(&config)?;
    if endpoints.len() != 1 {
        return Err("One real worker required".into());
    }
    let mut worker = endpoints[0].start()?;
    emit("worker", worker.metadata())?;
    // Warm-up excluded from scored cases, but preserved and charged separately.
    let warmup = worker.execute(
        json!({"op":"generate","prompts":["Return the word ready."],"max_new_tokens":16}),
    )?;
    emit("warmup", warmup)?;
    emit("document", config["dataset"].clone())?;
    for (index, case) in config["dataset"]["cases"]
        .as_array()
        .ok_or("Missing cases")?
        .iter()
        .enumerate()
    {
        emit("case_started", json!({"id":case["id"]}))?;
        emit(
            "case",
            tron_window::atomic_probe::execute(worker.as_mut(), case, index % 2 == 1)?,
        )?;
    }
    emit("complete", json!({"experiment":"atomic_evidence_v1"}))
}
fn main() {
    if let Err(error) = execute() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
