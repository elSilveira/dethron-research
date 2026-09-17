use std::{fs, process::Command};
#[test]
fn genesis_retains_authority_without_printing_key_and_failed_repair_is_nonzero() {
    let folder = std::env::temp_dir().join(format!(
        "tron-node-cli-{}",
        tron_v2::crypto::hash(&tron_v2::crypto::random::<16>())
    ));
    fs::create_dir(&folder).unwrap();
    let authority = folder.join("authority.json");
    let binary = env!("CARGO_BIN_EXE_dna_node");
    let output = Command::new(binary)
        .args([
            "genesis",
            folder.join("genesis").to_str().unwrap(),
            authority.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let public: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    let private: serde_json::Value =
        serde_json::from_slice(&fs::read(&authority).unwrap()).unwrap();
    assert!(public.get("key").is_none());
    assert_eq!(private["key"].as_array().unwrap().len(), 32);
    assert_eq!(public["root"], private["root"]);
    let duplicate = Command::new(binary)
        .args([
            "genesis",
            folder.join("unused").to_str().unwrap(),
            authority.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(!duplicate.status.success());
    let config = folder.join("repair.json");
    fs::write(
        &config,
        serde_json::json!({"authority":authority,"donors":[],"targets":[]}).to_string(),
    )
    .unwrap();
    let failed = Command::new(binary)
        .args(["repair", config.to_str().unwrap()])
        .output()
        .unwrap();
    assert!(!failed.status.success());
    assert!(failed.stdout.is_empty());
}
