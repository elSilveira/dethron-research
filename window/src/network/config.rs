use super::{connector::Endpoint, Task};
use serde_json::Value;
use std::collections::HashSet;

pub fn experiment(value: &Value) -> Result<&str, String> {
    match value.get("experiment") {
        None => Ok("throughput"),
        Some(v) => v
            .as_str()
            .filter(|s| ["throughput", "accuracy"].contains(s))
            .ok_or("Unknown experiment".into()),
    }
}
pub fn tasks(value: &Value) -> Result<Option<Vec<Task>>, String> {
    if value.get("tasks").is_none() {
        return Ok(None);
    }
    value["tasks"]
        .as_array()
        .ok_or("Tasks must be an array")?
        .iter()
        .map(task)
        .collect::<Result<Vec<_>, _>>()
        .map(Some)
}

fn string(value: &Value, key: &str) -> Result<String, String> {
    value[key]
        .as_str()
        .map(str::to_string)
        .ok_or_else(|| format!("Missing string {key}"))
}
fn strings(value: &Value, key: &str) -> Result<Vec<String>, String> {
    if value[key].is_null() {
        return Ok(Vec::new());
    }
    value[key]
        .as_array()
        .ok_or_else(|| format!("Invalid array {key}"))?
        .iter()
        .map(|s| {
            s.as_str()
                .map(str::to_string)
                .ok_or_else(|| format!("Invalid string in {key}"))
        })
        .collect()
}
pub fn task(value: &Value) -> Result<Task, String> {
    Ok(Task {
        id: string(value, "id")?,
        context: string(value, "context")?,
        revision: value["revision"].as_u64().ok_or("Missing revision")?,
        parents: strings(value, "parents")?,
        prompt: string(value, "prompt")?,
        candidates: strings(value, "candidates")?,
        dna: if value["dna"].is_null() {
            None
        } else {
            Some(super::dna::Dna::parse(&value["dna"])?)
        },
        max_new_tokens: if value["max_new_tokens"].is_null() {
            64
        } else {
            value["max_new_tokens"]
                .as_u64()
                .and_then(|n| usize::try_from(n).ok())
                .ok_or("Invalid generation limit")?
        },
    })
}
pub fn endpoints(value: &Value) -> Result<Vec<Endpoint>, String> {
    let workers = value["workers"].as_array().ok_or("Missing workers")?;
    if !(1..=16).contains(&workers.len()) {
        return Err("Use 1..16 workers".into());
    }
    let endpoints: Vec<_> = workers
        .iter()
        .map(Endpoint::parse)
        .collect::<Result<_, _>>()?;
    let mut names = HashSet::new();
    if endpoints.iter().any(|e| !names.insert(e.name.clone())) {
        return Err("Duplicate worker name".into());
    }
    Ok(endpoints)
}
