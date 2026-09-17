//! Owner-side verification and repair; storage services never receive the key.
use super::{
    node_store::Store,
    node_wire::request,
    recipe::{replay_units, Operation, Recipe, Step},
    recovery_dna::{preserve, recover, Unit},
};
use crate::crypto;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

#[derive(Clone, Serialize, Deserialize)]
pub struct Authority {
    pub root: String,
    pub key: [u8; 32],
    pub expected_hash: String,
}
pub fn genesis(store: &Store, object: &[u8]) -> Result<Authority, String> {
    let key = crypto::random::<32>();
    let (leaf, bytes) = preserve(
        &Unit {
            payload: object.to_vec(),
            children: vec![],
        },
        &key,
    )?;
    store.put(&leaf, &bytes)?;
    let masked: Vec<_> = object.iter().map(|b| b ^ 55).collect();
    let expected_hash = crypto::hash(object);
    let recipe = Recipe {
        version: 1,
        initial: vec![],
        steps: vec![
            Step {
                operation: Operation::Append { unit: leaf.clone() },
                expected_hash: expected_hash.clone(),
            },
            Step {
                operation: Operation::Xor { mask: 55 },
                expected_hash: crypto::hash(&masked),
            },
            Step {
                operation: Operation::Xor { mask: 55 },
                expected_hash: expected_hash.clone(),
            },
        ],
        expected_hash: expected_hash.clone(),
    };
    let (root, bytes) = preserve(
        &Unit {
            payload: serde_json::to_vec(&recipe).map_err(|e| e.to_string())?,
            children: vec![leaf],
        },
        &key,
    )?;
    store.put(&root, &bytes)?;
    Ok(Authority {
        root,
        key,
        expected_hash,
    })
}
fn fetch(addresses: &[String], id: &str) -> Vec<Vec<u8>> {
    addresses
        .iter()
        .filter_map(|address| {
            let value = request(address, &json!({"op":"get","id":id})).ok()?;
            serde_json::from_value(value["bytes"].clone()).ok()
        })
        .collect()
}
pub fn repair(
    authority: &Authority,
    donors: &[String],
    targets: &[String],
) -> Result<Value, String> {
    if donors.is_empty() || donors.len() > 16 || targets.len() > 100 {
        return Err("Use 1..16 donors and at most 100 targets".into());
    }
    let started = std::time::Instant::now();
    let units = recover(&authority.root, &authority.key, |id| fetch(donors, id))?;
    let result = replay_units(&units)?;
    let hash = crypto::hash(&result.object);
    if hash != authority.expected_hash {
        return Err("Owner object hash mismatch".into());
    }
    let mut stored_bytes = 0;
    for unit in &units {
        let (id, bytes) = preserve(unit, &authority.key)?;
        for address in targets {
            request(address, &json!({"op":"put","id":id,"bytes":bytes}))?;
            stored_bytes += bytes.len();
        }
    }
    let mut verified = Vec::new();
    for address in targets {
        let readback = recover(&authority.root, &authority.key, |id| {
            fetch(std::slice::from_ref(address), id)
        })?;
        if crypto::hash(&replay_units(&readback)?.object) != hash {
            return Err("Target readback mismatch".into());
        }
        verified.push(json!({"address":address,"object_hash":hash,"node":request(address, &json!({"op":"health"}))?}));
    }
    Ok(
        json!({"object":String::from_utf8(result.object.clone()).ok(),"object_hash":hash,
        "object_bytes":result.object.len(),"verified_steps":result.state_hashes.len(),
        "state_hashes":result.state_hashes,"unique_units":units.len(),"verified_targets":verified.len(),
        "targets":verified,"ciphertext_bytes_written":stored_bytes,"seconds":started.elapsed().as_secs_f64()}),
    )
}
