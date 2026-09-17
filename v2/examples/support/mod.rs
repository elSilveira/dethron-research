use serde_json::{json, Value};
mod dna;
mod retention;

pub fn summarize(trials: &[Value]) -> Value {
    let mut counts =
        std::collections::BTreeMap::<String, std::collections::BTreeMap<String, usize>>::new();
    for trial in trials {
        if let Some(checks) = trial["checks"].as_array() {
            for check in checks {
                *counts
                    .entry(check["name"].as_str().unwrap().into())
                    .or_default()
                    .entry(check["status"].as_str().unwrap().into())
                    .or_default() += 1;
            }
        }
    }
    json!({"attempted":trials.len(),"execution_errors":trials.iter().filter(|t| t.get("error").is_some()).count(),
        "cached_after_capacity_pressure":trials.iter().filter(|t| t["memory"]["cached_after_capacity_pressure"]==true).count(),
        "checks":counts})
}

pub fn check(name: &str, expected: Value, observed: Value) -> Value {
    json!({"name":name,"status":if expected==observed {"PASS"} else {"FAIL"},
        "expected":expected,"observed":observed})
}

pub fn trial(seed: u64) -> Result<Value, String> {
    let mut checks = Vec::new();
    let answer = dna::run(seed, &mut checks)?;
    let memory = retention::run(seed, &mut checks)?;
    for (name, reason) in [
        (
            "natural_language_paraphrase",
            "Presentation renders a conclusion; no arbitrary prose equivalence API",
        ),
        (
            "time_based_memory_tiers",
            "No explicit short/medium/long-term retention policy in Tron knowledge",
        ),
    ] {
        checks.push(json!({"name":name,"status":"BLOCKED","reason":reason}));
    }
    Ok(json!({"seed":seed,"answer":answer,"input":memory["input"],
        "initial_cached":memory["initial_cached"],"memory":memory,"checks":checks}))
}
