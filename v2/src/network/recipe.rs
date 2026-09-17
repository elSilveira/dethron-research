//! Versioned byte-object reconstruction with verified intermediate states.
use super::recovery_dna::Unit;
use serde::{Deserialize, Serialize};

#[derive(Clone, Serialize, Deserialize)]
pub enum Operation {
    Append { unit: String },
    Xor { mask: u8 },
    Rotate { by: usize },
    Replace { offset: usize, bytes: Vec<u8> },
}
#[derive(Clone, Serialize, Deserialize)]
pub struct Step {
    pub operation: Operation,
    pub expected_hash: String,
}
#[derive(Clone, Serialize, Deserialize)]
pub struct Recipe {
    pub version: u32,
    pub initial: Vec<u8>,
    pub steps: Vec<Step>,
    pub expected_hash: String,
}
#[derive(Serialize)]
pub struct Replay {
    pub object: Vec<u8>,
    pub state_hashes: Vec<String>,
    pub recovered_units: usize,
}
/// Input must already be authenticated by recovery; use `replay` for untrusted storage.
pub fn replay_units(units: &[Unit]) -> Result<Replay, String> {
    use crate::crypto;
    use std::collections::BTreeMap;
    let root = units.first().ok_or("Missing recipe root")?;
    let recipe: Recipe = serde_json::from_slice(&root.payload).map_err(|e| e.to_string())?;
    if recipe.version != 1
        || recipe.steps.len() > 128
        || recipe.initial.len() > 65536
        || units.len() > 512
    {
        return Err("Unsupported recipe version or limits".into());
    }
    let mut available = BTreeMap::new();
    for unit in units.iter().skip(1) {
        let bytes = serde_json::to_vec(unit).map_err(|e| e.to_string())?;
        available.insert(crypto::hash(&bytes), unit);
    }
    let mut object = recipe.initial;
    let mut hashes = vec![];
    for (index, step) in recipe.steps.iter().enumerate() {
        match &step.operation {
            Operation::Append { unit } => {
                let payload = &available
                    .get(unit)
                    .ok_or("Recipe connector unavailable")?
                    .payload;
                if object.len() + payload.len() > 65536 {
                    return Err("Object byte budget exceeded".into());
                }
                object.extend(payload);
            }
            Operation::Xor { mask } => object.iter_mut().for_each(|b| *b ^= mask),
            Operation::Rotate { by } => {
                let len = object.len();
                if len > 0 {
                    object.rotate_left(by % len);
                }
            }
            Operation::Replace { offset, bytes } => {
                let end = offset.checked_add(bytes.len()).ok_or("Patch overflow")?;
                let target = object.get_mut(*offset..end).ok_or("Patch outside object")?;
                target.copy_from_slice(bytes);
            }
        }
        let hash = crypto::hash(&object);
        if hash != step.expected_hash {
            return Err(format!("State proof mismatch at step {index}"));
        }
        hashes.push(hash);
    }
    if crypto::hash(&object) != recipe.expected_hash {
        return Err("Final object proof mismatch".into());
    }
    Ok(Replay {
        object,
        state_hashes: hashes,
        recovered_units: units.len(),
    })
}
pub fn replay<F>(root: &str, key: &[u8; 32], fetch: F) -> Result<Replay, String>
where
    F: FnMut(&str) -> Vec<Vec<u8>>,
{
    replay_units(&super::recovery_dna::recover(root, key, fetch)?)
}
