use std::process::Command;

#[test]
fn executable_produces_machine_readable_evidence_and_rejects_bad_cycles() {
    let output = Command::new(env!("CARGO_BIN_EXE_tron-v2"))
        .args(["probe", "2"])
        .output()
        .unwrap();
    assert!(output.status.success());
    let report: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["correct"], true);
    assert_eq!(report["child_recalled"], true);
    let bad = Command::new(env!("CARGO_BIN_EXE_tron-v2"))
        .args(["probe", "0"])
        .output()
        .unwrap();
    assert!(!bad.status.success());
}

#[test]
fn help_is_available_without_running_an_experiment() {
    let output = Command::new(env!("CARGO_BIN_EXE_tron-v2"))
        .arg("--help")
        .output()
        .unwrap();
    assert!(output.status.success());
    assert!(String::from_utf8(output.stdout).unwrap().contains("probe"));
}

#[test]
fn report_export_refuses_to_overwrite_existing_evidence() {
    let path = std::env::temp_dir().join(format!(
        "tron-v2-{}-{}.json",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    let run = || {
        Command::new(env!("CARGO_BIN_EXE_tron-v2"))
            .args(["probe", "1"])
            .arg(&path)
            .output()
            .unwrap()
    };
    assert!(run().status.success());
    let original = std::fs::read(&path).unwrap();
    assert!(!run().status.success());
    assert_eq!(std::fs::read(&path).unwrap(), original);
    std::fs::remove_file(path).unwrap();
}
