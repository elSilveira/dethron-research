use serde_json::json;
use std::{process::Command, time::Duration};
use tron_window::neural::{client::Client, experiment};

fn execute() -> Result<(), String> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.len() != 3 || !["preflight", "probe"].contains(&args[2].as_str()) {
        return Err("Usage: neural <python> <local-model-directory> preflight|probe".into());
    }
    let mut command = Command::new(&args[0]);
    command.args(["-u", "-m", "neural_worker", "--model", &args[1]]);
    let mut client = Client::start(&mut command, Duration::from_secs(120))?;
    eprintln!("Real model ready, pid={}", client.metadata["pid"]);
    let generation =
        json!({"op":"generate","prompts":["The capital of France is"],"max_new_tokens":8});
    let first = client.request(generation.clone(), Duration::from_secs(60))?;
    let second = client.request(generation, Duration::from_secs(60))?;
    let rank = client.request(
        json!({"op":"rank","prompts":["The capital of France is"],
        "candidates":[" Paris"," Tokyo"]}),
        Duration::from_secs(60),
    )?;
    if first["data"]["outputs"][0]["token_ids"] != second["data"]["outputs"][0]["token_ids"]
        || rank["data"]["outputs"][0]["selected"] != " Paris"
    {
        return Err("Real-model preflight failed".into());
    }
    let runs = if args[2] == "probe" {
        experiment::run(&mut client)?
    } else {
        Vec::new()
    };
    let report = json!({"schema":1,"preflight_passed":true,"worker":client.metadata,
        "preflight":[first,second,rank],"runs":runs,
        "scope":"Frozen local weights, constrained neural answers, learned memory relation recipes",
        "limits":"single resident GPU worker; branches queued on shared model; synthetic tasks; not training model weights or a general learning benchmark"});
    println!(
        "{}",
        serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
    );
    Ok(())
}

fn main() {
    if let Err(error) = execute() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
