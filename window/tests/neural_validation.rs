use serde_json::json;
use tron_window::neural::validation;

#[test]
fn accepts_worker_child_of_windows_venv_launcher_with_verified_fingerprints() {
    let file = json!({"sha256":"a".repeat(64),"bytes":1});
    let message = json!({"schema":1,"kind":"ready","pid":43,"parent_pid":42,
        "data":{"simulated":false,"load_count":1,"checkpoint":{"model_type":"qwen2",
        "files":{"config.json":file,"tokenizer.json":file,"tokenizer_config.json":file,"model.safetensors":file}}}});
    assert!(validation::ready(&message, 42).is_ok());
    assert!(validation::ready(&message, 99).is_err());
}

#[test]
fn refuses_simulated_or_unidentified_handshakes() {
    for message in [
        json!({}),
        json!({"schema":1,"kind":"ready","pid":42,
        "data":{"load_count":1,"simulated":true}}),
    ] {
        assert!(validation::ready(&message, 42).is_err());
    }
}

#[test]
fn rejects_wrong_correlations_and_invented_rank_results() {
    let request = json!({"id":"task-1","op":"rank","prompts":["Answer:"],"candidates":["A","B"]});
    let good = json!({"schema":1,"kind":"result","pid":42,"id":"task-1","sequence":1,
        "data":{"outputs":[{"selected":"A","scores":[-0.1,-2.0]}],"evaluated_tokens":6,"seconds":0.2}});
    assert!(validation::response(&good, &request, 1, 42).is_ok());
    for field in ["id", "pid", "sequence", "kind"] {
        let mut bad = good.clone();
        bad[field] = json!("wrong");
        assert!(validation::response(&bad, &request, 1, 42).is_err());
    }
    let mut bad = good.clone();
    bad["data"]["outputs"][0]["selected"] = json!("invented");
    assert!(validation::response(&bad, &request, 1, 42).is_err());
    bad = good.clone();
    bad["data"]["evaluated_tokens"] = json!(0);
    assert!(validation::response(&bad, &request, 1, 42).is_err());
}
