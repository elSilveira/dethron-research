//! Verified, bounded recovery of connected content units.
use crate::crypto;
use serde::{Deserialize, Serialize};
use std::collections::{HashSet, VecDeque};

const AAD: &[u8] = b"tron-v2-connected-recovery-v1";
fn valid_id(id: &str) -> bool {
    id.len() == 64
        && id
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn validate(unit: &Unit) -> Result<(), String> {
    if unit.payload.len() > 65536
        || unit.children.len() > 64
        || unit.children.iter().any(|id| !valid_id(id))
    {
        return Err("Invalid recovery unit or limits".into());
    }
    Ok(())
}

#[derive(Clone, Serialize, Deserialize)]
pub struct Unit {
    pub payload: Vec<u8>,
    pub children: Vec<String>,
}
pub fn preserve(unit: &Unit, key: &[u8; 32]) -> Result<(String, Vec<u8>), String> {
    validate(unit)?;
    let plain = serde_json::to_vec(unit).map_err(|e| e.to_string())?;
    Ok((crypto::hash(&plain), crypto::seal(key, AAD, &plain)?))
}
/// The owner supplies a trusted root and key. Fetch must be local/bounded or
/// enforce its own deadline. Up to 16 replicas per unit; no executable recipes.
/// Returns root-first verified content only if every linked unit is available.
pub fn recover<F>(root: &str, key: &[u8; 32], mut fetch: F) -> Result<Vec<Unit>, String>
where
    F: FnMut(&str) -> Vec<Vec<u8>>,
{
    if !valid_id(root) {
        return Err("Invalid trusted root".into());
    }
    let mut pending = VecDeque::from([root.to_string()]);
    let mut visited = HashSet::from([root.to_string()]);
    let mut result = Vec::new();
    let mut total = 0;
    while let Some(id) = pending.pop_front() {
        let replicas = fetch(&id);
        if replicas.len() > 16 {
            return Err("Replica limit exceeded".into());
        }
        let mut verified = None;
        for bytes in replicas {
            if bytes.len() > 300_000 {
                continue;
            }
            let Ok(plain) = crypto::open(key, AAD, &bytes) else {
                continue;
            };
            if crypto::hash(&plain) != id {
                continue;
            }
            let Ok(unit) = serde_json::from_slice::<Unit>(&plain) else {
                continue;
            };
            if validate(&unit).is_err() {
                continue;
            }
            verified = Some(unit);
            break;
        }
        let unit = verified.ok_or_else(|| format!("Missing or invalid recovery unit: {id}"))?;
        total += unit.payload.len();
        if total > 16 * 1024 * 1024 {
            return Err("Recovery byte budget exceeded".into());
        }
        for child in &unit.children {
            if visited.insert(child.clone()) {
                if visited.len() > 512 {
                    return Err("Recovery node budget exceeded".into());
                }
                pending.push_back(child.clone());
            }
        }
        result.push(unit);
    }
    Ok(result)
}
