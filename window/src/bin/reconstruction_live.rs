use serde_json::{json, Value};
use std::io::Write;
use tron_v2::network::config;
use tron_window::reconstruction_live::{cases, execute_case};

fn emit(kind: &str, data: Value) -> Result<(), String> {
    println!("{}", json!({"kind":kind,"data":data}));
    std::io::stdout().flush().map_err(|e| e.to_string())
}
fn execute() -> Result<(), String> {
    let path = std::env::args()
        .nth(1)
        .ok_or("Expected endpoint config path")?;
    let config: Value = serde_json::from_slice(&std::fs::read(path).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let endpoints = config::endpoints(&config)?;
    if endpoints.len() != 1 {
        return Err("Live probe requires one worker".into());
    }
    emit("loading", json!({"message":"Loading local model"}))?;
    let mut worker = endpoints[0].start()?;
    emit("worker", worker.metadata())?;
    if config["experiment"] == "document" {
        let data = &config["dataset"];
        emit("document", data.clone())?;
        for case in data["cases"].as_array().ok_or("Missing document cases")? {
            emit("case_started", json!({"id":case["id"]}))?;
            emit(
                "case",
                tron_window::document_probe::execute(worker.as_mut(), case)?,
            )?;
        }
        return emit(
            "complete",
            json!({"experiment":"document","real_model":true}),
        );
    }
    let nonce = tron_v2::crypto::hash(&tron_v2::crypto::random::<16>());
    for case in cases(&format!("object-{}", &nonce[..12])) {
        emit("case_started", json!({"id":case.id}))?;
        emit("case", execute_case(worker.as_mut(), case)?)?;
    }
    emit(
        "complete",
        json!({"controlled_facts":true,"real_model":true}),
    )
}
fn main() {
    if let Err(error) = execute() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
