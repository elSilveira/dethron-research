use super::{journal::Journal, Task};
use serde_json::{json, Value};
use std::collections::HashMap;

#[derive(Default)]
pub struct Recovery {
    pub records: HashMap<String, Value>,
    pub spent: u64,
    pub tokens: u64,
    pub wave: usize,
}
pub fn restore(journal: &mut Option<&mut Journal>, tasks: &[Task]) -> Result<Recovery, String> {
    let Some(journal) = journal else {
        return Ok(Recovery::default());
    };
    if journal.state.is_null() {
        return Ok(Recovery::default());
    }
    let state = &journal.state;
    let mut recovery = Recovery {
        records: serde_json::from_value(state["records"].clone()).map_err(|e| e.to_string())?,
        spent: state["spent"].as_u64().ok_or("Missing persisted budget")?,
        tokens: state["tokens"]
            .as_u64()
            .ok_or("Missing persisted token count")?,
        wave: state["next_wave"]
            .as_u64()
            .ok_or("Missing persisted wave")? as usize,
    };
    for id in state["pending"].as_array().ok_or("Missing pending set")? {
        let id = id.as_str().ok_or("Invalid pending ID")?;
        let task = tasks
            .iter()
            .find(|t| t.id == id)
            .ok_or("Unknown pending task")?;
        recovery.records.insert(
            id.into(),
            json!({"id":id,"status":"failed","wave":recovery.wave.saturating_sub(1),
            "error":"Execution interrupted: completion unknown; automatic retry forbidden",
            "recovery":"indeterminate","reserved_failure_tokens":task.reservation()}),
        );
    }
    journal.save(
        &recovery.records,
        recovery.spent,
        recovery.tokens,
        &[],
        recovery.wave,
    )?;
    Ok(recovery)
}
pub fn save(
    journal: &mut Option<&mut Journal>,
    records: &HashMap<String, Value>,
    spent: u64,
    tokens: u64,
    pending: &[String],
    wave: usize,
) -> Result<(), String> {
    if let Some(journal) = journal {
        journal.save(records, spent, tokens, pending, wave)?;
    }
    Ok(())
}
