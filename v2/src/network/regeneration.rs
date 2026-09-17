//! Bounded local node regeneration from verified survivors; no remote processes.
use std::collections::BTreeMap;
#[derive(Clone)]
pub struct Node {
    pub units: BTreeMap<String, Vec<u8>>,
}
pub struct Regeneration {
    pub nodes: Vec<Node>,
    pub object: Vec<u8>,
    pub unique_units: usize,
    pub stored_bytes: usize,
}
pub fn regenerate(
    root: &str,
    key: &[u8; 32],
    survivors: &[Node],
    target: usize,
) -> Result<Regeneration, String> {
    use super::{
        recipe::replay_units,
        recovery_dna::{preserve, recover},
    };
    if !(1..=100).contains(&target) || !(1..=16).contains(&survivors.len()) {
        return Err("Use 1..16 survivors and 1..100 target nodes".into());
    }
    let units = recover(root, key, |id| {
        survivors
            .iter()
            .filter_map(|n| n.units.get(id).cloned())
            .collect()
    })?;
    let result = replay_units(&units)?;
    let mut store = BTreeMap::new();
    for unit in &units {
        let (id, bytes) = preserve(unit, key)?;
        store.insert(id, bytes);
    }
    let stored_bytes = store.values().map(Vec::len).sum::<usize>() * target;
    Ok(Regeneration {
        nodes: vec![Node { units: store }; target],
        object: result.object,
        unique_units: units.len(),
        stored_bytes,
    })
}
