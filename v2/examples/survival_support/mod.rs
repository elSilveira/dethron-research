use std::collections::BTreeMap;
use tron_v2::{
    crypto,
    network::{
        recipe::{Operation, Recipe, Step},
        recovery_dna::{preserve, Unit},
        regeneration::Node,
    },
};

pub fn genesis(seed: u8, key: &[u8; 32]) -> Result<(String, String, Node, Vec<u8>), String> {
    let mut object: Vec<u8> = (0..64).map(|n| n ^ seed).collect();
    let (leaf, bytes) = preserve(
        &Unit {
            payload: object.clone(),
            children: vec![],
        },
        key,
    )?;
    let mut steps = vec![Step {
        operation: Operation::Append { unit: leaf.clone() },
        expected_hash: crypto::hash(&object),
    }];
    for _ in 0..12 {
        object.iter_mut().for_each(|n| *n ^= 55);
        steps.push(Step {
            operation: Operation::Xor { mask: 55 },
            expected_hash: crypto::hash(&object),
        });
    }
    for _ in 0..12 {
        object.rotate_left(1);
        steps.push(Step {
            operation: Operation::Rotate { by: 1 },
            expected_hash: crypto::hash(&object),
        });
    }
    for offset in 0..5 {
        object[offset] = seed + offset as u8;
        steps.push(Step {
            operation: Operation::Replace {
                offset,
                bytes: vec![object[offset]],
            },
            expected_hash: crypto::hash(&object),
        });
    }
    for _ in 0..3 {
        object.iter_mut().for_each(|n| *n ^= 3);
        steps.push(Step {
            operation: Operation::Xor { mask: 3 },
            expected_hash: crypto::hash(&object),
        });
    }
    let recipe = Recipe {
        version: 1,
        initial: vec![],
        steps,
        expected_hash: crypto::hash(&object),
    };
    let (root, data) = preserve(
        &Unit {
            payload: serde_json::to_vec(&recipe).map_err(|e| e.to_string())?,
            children: vec![leaf.clone()],
        },
        key,
    )?;
    let store = BTreeMap::from([(root.clone(), data), (leaf.clone(), bytes)]);
    Ok((root, leaf, Node { units: store }, object))
}
