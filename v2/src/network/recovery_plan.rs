//! Connect encrypted recovery units to versioned task DNA.
use super::{
    dna::Dna,
    recovery_dna::{preserve, recover, Unit},
};
use serde_json::{json, Value};
use std::collections::BTreeMap;
type Store = BTreeMap<String, Vec<u8>>;
pub fn preserve_plan(plan: &Value, key: &[u8; 32]) -> Result<(String, Store), String> {
    let mut manifest = plan.clone();
    let tasks = manifest["tasks"].as_array_mut().ok_or("Missing tasks")?;
    if tasks.is_empty() || tasks.len() > 128 {
        return Err("Task limit".into());
    }
    let mut store = Store::new();
    let mut branches = vec![];
    for (index, task) in tasks.iter_mut().enumerate() {
        if task["dna"].is_null() {
            continue;
        }
        Dna::parse(&task["dna"])?;
        let mut links = vec![];
        for (position, source) in task["dna"]["sources"]
            .as_array()
            .unwrap()
            .iter()
            .enumerate()
        {
            let payload =
                serde_json::to_vec(&json!({"task":index,"position":position,"source":source}))
                    .map_err(|e| e.to_string())?;
            let (id, bytes) = preserve(
                &Unit {
                    payload,
                    children: vec![],
                },
                key,
            )?;
            store.insert(id.clone(), bytes);
            links.push(id);
        }
        // Branch units keep fanout bounded while allowing many source facts.
        for chunk in links.chunks(64) {
            let (id, bytes) = preserve(
                &Unit {
                    payload: vec![],
                    children: chunk.to_vec(),
                },
                key,
            )?;
            store.insert(id.clone(), bytes);
            branches.push(id);
        }
        task["dna"]["sources"] = json!([]);
    }
    while branches.len() > 64 {
        let mut next = vec![];
        for chunk in branches.chunks(64) {
            let (id, bytes) = preserve(
                &Unit {
                    payload: vec![],
                    children: chunk.to_vec(),
                },
                key,
            )?;
            store.insert(id.clone(), bytes);
            next.push(id);
        }
        branches = next;
    }
    let payload = serde_json::to_vec(&manifest).map_err(|e| e.to_string())?;
    let (root, bytes) = preserve(
        &Unit {
            payload,
            children: branches,
        },
        key,
    )?;
    store.insert(root.clone(), bytes);
    if store.len() > 512 {
        return Err("Plan exceeds recovery node budget".into());
    }
    Ok((root, store))
}
pub fn recover_plan<F>(root: &str, key: &[u8; 32], fetch: F) -> Result<Value, String>
where
    F: FnMut(&str) -> Vec<Vec<u8>>,
{
    let units = recover(root, key, fetch)?;
    let mut plan: Value = serde_json::from_slice(&units[0].payload).map_err(|e| e.to_string())?;
    let tasks = plan["tasks"].as_array_mut().ok_or("Missing tasks")?;
    let mut sources = BTreeMap::new();
    for unit in units.iter().skip(1).filter(|u| !u.payload.is_empty()) {
        let leaf: Value = serde_json::from_slice(&unit.payload).map_err(|e| e.to_string())?;
        let task = leaf["task"].as_u64().ok_or("Missing task index")? as usize;
        let position = leaf["position"].as_u64().ok_or("Missing source position")? as usize;
        if task >= tasks.len()
            || sources
                .insert((task, position), leaf["source"].clone())
                .is_some()
        {
            return Err("Invalid or duplicate source position".into());
        }
    }
    for ((task, position), source) in sources {
        let entries = tasks[task]["dna"]["sources"]
            .as_array_mut()
            .ok_or("Missing source array")?;
        if entries.len() != position {
            return Err("Noncontiguous source positions".into());
        }
        entries.push(source);
    }
    for task in tasks {
        if !task["dna"].is_null() {
            Dna::parse(&task["dna"])?;
        }
    }
    Ok(plan)
}
