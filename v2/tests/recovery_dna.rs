use std::collections::HashMap;
use tron_v2::network::recovery_dna::{preserve, recover, Unit};

#[test]
fn reconnects_encrypted_units_and_deduplicates_shared_links() {
    let key = [7; 32];
    let leaf = Unit {
        payload: b"original fact".to_vec(),
        children: vec![],
    };
    let (leaf_id, leaf_bytes) = preserve(&leaf, &key).unwrap();
    let branch = Unit {
        payload: b"recipe".to_vec(),
        children: vec![leaf_id.clone()],
    };
    let (branch_id, branch_bytes) = preserve(&branch, &key).unwrap();
    let root = Unit {
        payload: b"manifest".to_vec(),
        children: vec![branch_id.clone(), leaf_id.clone()],
    };
    let (root_id, root_bytes) = preserve(&root, &key).unwrap();
    let storage = HashMap::from([
        (root_id.clone(), root_bytes),
        (branch_id, branch_bytes),
        (leaf_id, leaf_bytes),
    ]);
    let mut calls = 0;
    let result = recover(&root_id, &key, |id| {
        calls += 1;
        vec![vec![0; 32], storage[id].clone()]
    })
    .unwrap();
    assert_eq!(result.len(), 3);
    assert_eq!(calls, 3);
    assert_eq!(result[0].payload, b"manifest");
    assert!(result.iter().any(|u| u.payload == b"original fact"));
}

#[test]
fn missing_tampered_wrong_key_and_wrong_identity_never_complete() {
    let key = [7; 32];
    let (id, bytes) = preserve(
        &Unit {
            payload: vec![42],
            children: vec![],
        },
        &key,
    )
    .unwrap();
    assert!(recover(&id, &key, |_| vec![]).is_err());
    assert!(recover(&id, &[8; 32], |_| vec![bytes.clone()]).is_err());
    assert!(recover(&"a".repeat(64), &key, |_| vec![bytes.clone()]).is_err());
    let mut bad = bytes;
    let last = bad.len() - 1;
    bad[last] ^= 1;
    assert!(recover(&id, &key, |_| vec![bad.clone()]).is_err());
}

#[test]
fn invalid_links_and_excessive_payloads_are_rejected() {
    assert!(preserve(
        &Unit {
            payload: vec![],
            children: vec!["invalid".into()]
        },
        &[7; 32]
    )
    .is_err());
    assert!(preserve(
        &Unit {
            payload: vec![0; 65537],
            children: vec![]
        },
        &[7; 32]
    )
    .is_err());
}
