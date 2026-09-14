use serde_json::json;
use std::process::Command;
use tron_window::network::config;

#[test]
fn accuracy_mode_is_explicit_and_malformed_task_lists_are_not_silently_ignored() {
    assert_eq!(config::experiment(&json!({})).unwrap(), "throughput");
    assert_eq!(
        config::experiment(&json!({"experiment":"accuracy"})).unwrap(),
        "accuracy"
    );
    assert!(config::experiment(&json!({"experiment":"typo"})).is_err());
    assert!(config::tasks(&json!({"tasks":"not an array"})).is_err());
}

#[test]
fn parses_explicit_task_packets_and_rejects_invalid_config_before_loading() {
    let task = json!({"id":"join","context":"c","revision":1,"parents":["left"],
        "prompt":"Summarize the supplied results.","max_new_tokens":32});
    let parsed = config::task(&task).unwrap();
    assert_eq!(parsed.parents, vec!["left"]);
    assert!(parsed.candidates.is_empty());
    assert_eq!(parsed.max_new_tokens, 32);
    let mut invalid = task;
    invalid["parents"] = json!([42]);
    assert!(config::task(&invalid).is_err());
    assert!(config::endpoints(&json!({"workers":[]})).is_err());
}

#[test]
fn cli_requires_explicit_config_and_never_claims_success_on_error() {
    let output = Command::new(env!("CARGO_BIN_EXE_network"))
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(output.stdout.is_empty());
    assert!(String::from_utf8_lossy(&output.stderr).contains("Usage:"));
}
