use std::process::Command;

#[test]
fn probe_compares_against_strong_fixed_control_and_charges_selection() {
    let output = Command::new(env!("CARGO_BIN_EXE_feasibility"))
        .output()
        .expect("probe starts");
    assert!(output.status.success());
    let report: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["correct"], true);
    assert_eq!(report["runs"].as_array().unwrap().len(), 10);
    for run in report["runs"].as_array().unwrap() {
        let fixed = run["fixed_divisions"][2].as_u64().unwrap();
        let adaptive = run["adaptive_divisions"].as_u64().unwrap();
        let overhead = run["selection_divisions"].as_u64().unwrap();
        assert!(overhead > 0);
        assert_eq!(adaptive, fixed);
        assert_eq!(run["total_adaptive_divisions"], adaptive + overhead);
        assert_eq!(run["held_out_count"], 256);
    }
}
