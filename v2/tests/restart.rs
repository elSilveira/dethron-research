use tron_v2::{crypto::random, tron::Tron};

#[test]
fn restart_preserves_identity_dna_knowledge_and_audit_continuity() {
    let key = random();
    let mut original = Tron::new(0);
    original.run(997, 2000).unwrap();
    original.evolve();
    let state = original.checkpoint(&key).unwrap();
    let identity = original.audit.key();
    let head = original.audit.head();
    drop(original);
    let mut restored = Tron::restore(&state, &key, &identity, &head).unwrap();
    assert_eq!(restored.audit.key(), identity);
    assert_eq!(restored.version(), 1);
    assert!(restored.run(997, 2000).unwrap().cached);
    assert_eq!(restored.spawn(true).unwrap().generation(), 1);
}

#[test]
fn unauthorized_restore_corruption_and_rollback_are_rejected() {
    let key = random();
    let mut tron = Tron::new(0);
    let old = tron.checkpoint(&key).unwrap();
    let old_head = tron.audit.head();
    tron.run(97, 1000).unwrap();
    let new = tron.checkpoint(&key).unwrap();
    let head = tron.audit.head();
    let identity = tron.audit.key();
    assert!(Tron::restore(&old, &key, &identity, &head).is_err());
    assert!(Tron::restore(&new, &key, &identity, &old_head).is_err());
    assert!(Tron::restore(&new, &random(), &identity, &head).is_err());
    assert!(Tron::restore(&new, &key, &Tron::new(0).audit.key(), &head).is_err());
    let mut bad = new;
    let last = bad.len() - 1;
    bad[last] ^= 1;
    assert!(Tron::restore(&bad, &key, &identity, &head).is_err());
}

#[test]
fn snapshot_survives_a_process_boundary() {
    if let Ok(path) = std::env::var("TRON_TEST_SNAPSHOT") {
        let key: [u8; 32] = serde_json::from_str(&std::env::var("TRON_TEST_KEY").unwrap()).unwrap();
        let identity: Vec<u8> =
            serde_json::from_str(&std::env::var("TRON_TEST_ID").unwrap()).unwrap();
        let head = std::env::var("TRON_TEST_HEAD").unwrap();
        let bytes = std::fs::read(path).unwrap();
        let mut restored = Tron::restore(&bytes, &key, &identity, &head).unwrap();
        assert!(restored.run(997, 2000).unwrap().cached);
        assert_eq!(restored.version(), 1);
        return;
    }
    let key = random();
    let mut tron = Tron::new(0);
    tron.run(997, 2000).unwrap();
    tron.evolve();
    let bytes = tron.checkpoint(&key).unwrap();
    let path = std::env::temp_dir().join(format!(
        "tron-state-{}-{}.bin",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    use std::io::Write;
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .unwrap();
    file.write_all(&bytes).unwrap();
    file.sync_all().unwrap();
    drop(file);
    let result = std::process::Command::new(std::env::current_exe().unwrap())
        .args(["--exact", "snapshot_survives_a_process_boundary"])
        .env("TRON_TEST_SNAPSHOT", &path)
        .env("TRON_TEST_KEY", serde_json::to_string(&key).unwrap())
        .env(
            "TRON_TEST_ID",
            serde_json::to_string(&tron.audit.key()).unwrap(),
        )
        .env("TRON_TEST_HEAD", tron.audit.head())
        .output()
        .unwrap();
    std::fs::remove_file(path).unwrap();
    assert!(result.status.success(), "Fresh-process restore failed");
}
