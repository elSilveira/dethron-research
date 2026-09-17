use std::collections::BTreeMap;
use tron_v2::{
    crypto,
    network::{
        recipe::{replay, Operation, Recipe, Step},
        recovery_dna::{preserve, Unit},
    },
};

fn fixture() -> (String, BTreeMap<String, Vec<u8>>) {
    let (leaf, bytes) = preserve(
        &Unit {
            payload: b"xyz".to_vec(),
            children: vec![],
        },
        &[55; 32],
    )
    .unwrap();
    let recipe = Recipe {
        version: 1,
        initial: vec![],
        steps: vec![
            Step {
                operation: Operation::Append { unit: leaf.clone() },
                expected_hash: crypto::hash(b"xyz"),
            },
            Step {
                operation: Operation::Rotate { by: 1 },
                expected_hash: crypto::hash(b"yzx"),
            },
            Step {
                operation: Operation::Replace {
                    offset: 1,
                    bytes: b"A".to_vec(),
                },
                expected_hash: crypto::hash(b"yAx"),
            },
            Step {
                operation: Operation::Xor { mask: 1 },
                expected_hash: crypto::hash(b"x@y"),
            },
        ],
        expected_hash: crypto::hash(b"x@y"),
    };
    let (root, root_bytes) = preserve(
        &Unit {
            payload: serde_json::to_vec(&recipe).unwrap(),
            children: vec![leaf.clone()],
        },
        &[55; 32],
    )
    .unwrap();
    (
        root.clone(),
        BTreeMap::from([(root, root_bytes), (leaf, bytes)]),
    )
}
#[test]
fn encrypted_recipe_recreates_object_from_empty_state_and_live_connector() {
    let (root, store) = fixture();
    let result = replay(&root, &[55; 32], |id| vec![store[id].clone()]).unwrap();
    assert_eq!(result.object, b"x@y");
    assert_eq!(result.state_hashes.len(), 4);
    assert_eq!(result.recovered_units, 2);
    assert!(replay(&root, &[54; 32], |id| vec![store[id].clone()]).is_err());
    assert!(replay(&root, &[55; 32], |id| if id == root {
        vec![store[id].clone()]
    } else {
        vec![]
    })
    .is_err());
}
#[test]
fn recipe_rejects_bad_versions_limits_and_incorrect_state_proofs() {
    use tron_v2::network::recipe::replay_units;
    let step = Step {
        operation: Operation::Xor { mask: 1 },
        expected_hash: crypto::hash(&[1]),
    };
    let base = Recipe {
        version: 1,
        initial: vec![0],
        steps: vec![step.clone()],
        expected_hash: crypto::hash(&[1]),
    };
    for kind in 0..6 {
        let mut r = base.clone();
        match kind {
            0 => r.version = 2,
            1 => r.steps[0].expected_hash = crypto::hash(b"wrong"),
            2 => r.expected_hash = crypto::hash(b"wrong"),
            3 => r.steps = vec![step.clone(); 129],
            4 => r.initial = vec![0; 65537],
            _ => {
                r.steps[0].operation = Operation::Replace {
                    offset: 8,
                    bytes: vec![1],
                }
            }
        }
        assert!(
            replay_units(&[Unit {
                payload: serde_json::to_vec(&r).unwrap(),
                children: vec![]
            }])
            .is_err(),
            "kind {kind}"
        );
    }
}
