use std::collections::BTreeMap;
use tron_v2::{
    crypto,
    network::{
        recipe::{Operation, Recipe, Step},
        recovery_dna::{preserve, Unit},
        regeneration::{regenerate, Node},
    },
};
fn genesis() -> (String, String, Node) {
    let (leaf, bytes) = preserve(
        &Unit {
            payload: b"genesis object".to_vec(),
            children: vec![],
        },
        &[55; 32],
    )
    .unwrap();
    let recipe = Recipe {
        version: 1,
        initial: vec![],
        steps: vec![Step {
            operation: Operation::Append { unit: leaf.clone() },
            expected_hash: crypto::hash(b"genesis object"),
        }],
        expected_hash: crypto::hash(b"genesis object"),
    };
    let (root, data) = preserve(
        &Unit {
            payload: serde_json::to_vec(&recipe).unwrap(),
            children: vec![leaf.clone()],
        },
        &[55; 32],
    )
    .unwrap();
    (
        root.clone(),
        leaf.clone(),
        Node {
            units: BTreeMap::from([(root, data), (leaf, bytes)]),
        },
    )
}
#[test]
fn genesis_expands_and_five_percent_rebuilds_when_information_survives() {
    let (root, _, node) = genesis();
    let initial = regenerate(&root, &[55; 32], &[node], 100).unwrap();
    assert_eq!(initial.nodes.len(), 100);
    let survivors: Vec<_> = [1, 17, 33, 65, 99]
        .iter()
        .map(|i| initial.nodes[*i].clone())
        .collect();
    drop(initial);
    let rebuilt = regenerate(&root, &[55; 32], &survivors, 100).unwrap();
    assert_eq!(rebuilt.nodes.len(), 100);
    assert_eq!(rebuilt.object, b"genesis object");
    assert_eq!(rebuilt.unique_units, 2);
    assert_eq!(
        rebuilt.stored_bytes,
        rebuilt.nodes[0].units.values().map(Vec::len).sum::<usize>() * 100
    );
}
#[test]
fn five_percent_is_not_enough_when_required_content_or_key_is_lost() {
    let (root, leaf, mut node) = genesis();
    node.units.remove(&leaf);
    assert!(regenerate(&root, &[55; 32], &vec![node.clone(); 5], 100).is_err());
    assert!(regenerate(&root, &[54; 32], &[node], 100).is_err());
    assert!(regenerate(&root, &[55; 32], &[], 100).is_err());
}
#[test]
fn node_expansion_is_explicitly_bounded() {
    let (root, _, node) = genesis();
    assert!(regenerate(&root, &[55; 32], std::slice::from_ref(&node), 101).is_err());
    assert!(regenerate(&root, &[55; 32], std::slice::from_ref(&node), 0).is_err());
    assert!(regenerate(&root, &[55; 32], &vec![node; 17], 100).is_err());
}
