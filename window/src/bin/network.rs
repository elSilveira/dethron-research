use serde_json::{json, Value};
use std::time::Instant;
use tron_window::network::{accuracy, config, packet, probe, run, workload, Limits, Worker};

fn execute() -> Result<(), String> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() != 1 {
        return Err("Usage: network <config.json>".into());
    }
    let bytes = std::fs::read(&args[0]).map_err(|e| e.to_string())?;
    if bytes.len() > 1_048_576 {
        return Err("Config exceeds 1 MiB".into());
    }
    let config: Value = serde_json::from_slice(&bytes).map_err(|e| e.to_string())?;
    let endpoints = config::endpoints(&config)?;
    let experiment = config::experiment(&config)?;
    let tasks = config::tasks(&config)?;
    let persistence = tron_window::persistence::settings(&config, tasks.is_some())?;
    if experiment == "accuracy" && tasks.is_some() {
        return Err("Accuracy uses its fixed dataset; omit tasks".into());
    }
    let limits = Limits {
        token_budget: config["token_budget"].as_u64().unwrap_or(100_000),
        ..Limits::default()
    };
    let repeats = config["repeats"].as_u64().unwrap_or(3) as usize;
    let cases = config["cases"].as_u64().unwrap_or(4) as usize;
    if let Some(tasks) = &tasks {
        packet::validate(tasks, endpoints.len(), limits)?;
    } else if !(1..=8).contains(&repeats) || !(2..=16).contains(&cases) {
        return Err("Use 1..8 repeats and 2..16 cases".into());
    }
    let start = Instant::now();
    let mut workers = Vec::<Box<dyn Worker>>::new();
    let mut warmups = Vec::new();
    for endpoint in endpoints {
        eprintln!("Loading worker {}", endpoint.name);
        let mut worker = endpoint.start()?;
        let reply = worker.execute(json!({"op":"rank","prompts":["The capital of France is"],"candidates":[" Paris"," Tokyo"]}))?;
        if reply["data"]["outputs"][0]["selected"] != " Paris" {
            return Err("Worker preflight failed".into());
        }
        warmups.push(reply);
        workers.push(worker);
    }
    let startup_seconds = start.elapsed().as_secs_f64();
    let identities: Vec<_> = workers.iter().map(|w| w.metadata()).collect();
    if tasks.is_none()
        && identities.iter().any(|w| {
            w["handshake"]["data"]["checkpoint"]["files"]
                != identities[0]["handshake"]["data"]["checkpoint"]["files"]
        })
    {
        return Err("Comparison requires identical model and tokenizer fingerprints".into());
    }
    let mut report = json!({"schema":1,"preflight_passed":true,"workers":identities,
        "startup_and_warmup_seconds":startup_seconds,"warmups":warmups});
    let mut failed = false;
    if experiment == "accuracy" {
        let result = accuracy::compare(&mut workers)?;
        failed = result["execution_passed"] != true;
        report["accuracy"] = result;
    } else if let Some(tasks) = tasks {
        let result = if let Some(settings) = &persistence {
            tron_window::persistence::run(&mut workers, &tasks, limits, settings)?
        } else {
            run(&mut workers, &tasks, limits)?
        };
        failed = result["failed"] != 0 || result["blocked"] != 0;
        report["task_run"] = result;
    } else {
        report["comparison"] = probe::compare(&mut workers, repeats, cases)?;
        for trial in report["comparison"]["trials"].as_array().unwrap() {
            failed |= trial["run"]["failed"] != 0 || trial["run"]["blocked"] != 0;
        }
        if config["generation_demo"] == true {
            let demo = run(&mut workers, &workload::generation(), limits)?;
            failed |= demo["failed"] != 0 || demo["blocked"] != 0;
            report["generation_demo"] = demo;
        }
    }
    report["execution_passed"] = json!(!failed);
    println!(
        "{}",
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
    );
    if failed {
        Err("Network recorded failed or blocked tasks; inspect report".into())
    } else {
        Ok(())
    }
}
fn main() {
    if let Err(error) = execute() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
