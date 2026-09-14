use serde_json::Value;
use std::process::Command;

#[test]
fn demo_exposes_real_routes_memories_reconstruction_and_external_checks() {
    let output = Command::new(env!("CARGO_BIN_EXE_reorganization"))
        .arg("demo")
        .output()
        .unwrap();
    assert!(output.status.success());
    let report: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["mechanism_checks_passed"], true);
    let events = report["events"].as_array().unwrap();
    assert!(events
        .iter()
        .any(|e| e["phase"] == "shadow" && e["primary_nodes"].as_array().unwrap().len() == 3));
    assert!(events.iter().any(|e| e["events"]
        .as_array()
        .unwrap()
        .iter()
        .any(|x| x == "reconstructed_from_long_memory")));
    assert!(events.iter().any(|e| e["events"]
        .as_array()
        .unwrap()
        .iter()
        .any(|x| x == "reopened")));
    assert!(events.iter().all(|e| e["externally_correct"] == true));
    assert!(report["final_state"]["dna"].is_array());
}

#[test]
fn benchmark_keeps_strong_control_and_all_regimes_under_equal_limits() {
    let output = Command::new(env!("CARGO_BIN_EXE_reorganization"))
        .args(["bench", "2"])
        .output()
        .unwrap();
    assert!(output.status.success());
    let report: Value = serde_json::from_slice(&output.stdout).unwrap();
    let runs = report["runs"].as_array().unwrap();
    assert_eq!(runs.len(), 6);
    for run in runs {
        assert_eq!(run["budget_limit"], 1_000_000);
        assert_eq!(run["attempted"], 256);
        assert_eq!(run["correct"], 256);
        assert_eq!(run["phases"].as_array().unwrap().len(), 4);
        assert_eq!(run["failures"], 0);
        let phase_work: u64 = run["phases"]
            .as_array()
            .unwrap()
            .iter()
            .map(|phase| phase["work_units"].as_u64().unwrap())
            .sum();
        assert_eq!(
            run["work_units"].as_u64().unwrap(),
            phase_work + run["initial_work_units"].as_u64().unwrap()
        );
    }
}

#[test]
fn invalid_cli_never_emits_a_success_report() {
    let output = Command::new(env!("CARGO_BIN_EXE_reorganization"))
        .args(["bench", "0"])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(output.stdout.is_empty());
}
