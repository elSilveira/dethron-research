#[path = "../examples/support/mod.rs"]
mod support;

#[test]
fn summary_keeps_failures_blocks_and_trial_errors_visible() {
    let trials = vec![
        serde_json::json!({"checks":[
        {"name":"recall","status":"FAIL"},{"name":"tiers","status":"BLOCKED"}]}),
        serde_json::json!({"error":"execution failed","checks":[]}),
    ];
    let summary = support::summarize(&trials);
    assert_eq!(summary["attempted"], 2);
    assert_eq!(summary["execution_errors"], 1);
    assert_eq!(summary["checks"]["recall"]["FAIL"], 1);
    assert_eq!(summary["checks"]["tiers"]["BLOCKED"], 1);
}

#[test]
fn repeated_probe_exercises_real_dna_and_memory_and_labels_gaps() {
    let result = support::trial(17).unwrap();
    let checks = result["checks"].as_array().unwrap();
    assert!(checks.len() >= 12);
    for name in [
        "dna_reconstruction",
        "changed_facts",
        "route_loss",
        "conflict_veto",
        "inactive_sources",
        "wrong_answer_rejected",
        "short_recall",
        "interference_recall",
        "snapshot_restore",
        "capacity_correctness",
    ] {
        let check = checks.iter().find(|c| c["name"] == name).unwrap();
        assert_eq!(check["status"], "PASS", "{name}: {check}");
    }
    for name in ["natural_language_paraphrase", "time_based_memory_tiers"] {
        let check = checks.iter().find(|c| c["name"] == name).unwrap();
        assert_eq!(check["status"], "BLOCKED");
    }
}

#[test]
fn repeated_probe_changes_inputs_without_sharing_tron_state() {
    let a = support::trial(17).unwrap();
    let b = support::trial(18).unwrap();
    assert_ne!(a["input"], b["input"]);
    assert_ne!(a["answer"], b["answer"]);
    assert_eq!(a["initial_cached"], false);
    assert_eq!(b["initial_cached"], false);
}
