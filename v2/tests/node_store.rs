use tron_v2::network::node_store::Store;

#[test]
fn persistent_store_retains_identity_and_ciphertext_and_rejects_unsafe_names() {
    let dir = std::env::temp_dir().join(format!(
        "tron-store-{}",
        tron_v2::crypto::hash(&tron_v2::crypto::random::<16>())
    ));
    let store = Store::open(&dir).unwrap();
    let identity = store.identity.clone();
    let id = "a".repeat(64);
    store.put(&id, &[1, 2, 3]).unwrap();
    drop(store);
    let restored = Store::open(&dir).unwrap();
    assert_eq!(restored.identity, identity);
    assert_eq!(restored.get(&id).unwrap(), vec![1, 2, 3]);
    assert!(restored.get("../identity").is_err());
    assert!(restored.put(&id, &vec![0; 300_001]).is_err());
    restored.put(&id, &[4, 5]).unwrap();
    assert_eq!(Store::open(&dir).unwrap().get(&id).unwrap(), vec![4, 5]);
}
