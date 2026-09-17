use serde_json::json;
use std::collections::HashMap;
use tron_v2::network::config;
use tron_v2::network::{run, Limits, Worker};

struct Guess;
impl Worker for Guess {
    fn metadata(&self) -> serde_json::Value {
        json!({"backend":"explicit-test-fixture"})
    }
    fn execute(&mut self, _: serde_json::Value) -> Result<serde_json::Value, String> {
        Ok(json!({"data":{"outputs":[{"selected":" A"}],"evaluated_tokens":4}}))
    }
}
#[test]
fn system_abstention_preserves_wrong_raw_guess_and_never_repairs_supported_answers() {
    for (sources, state, output) in [
        (json!([]), "abstained", json!("UNKNOWN")),
        (json!([source("b", "B")]), "rejected", json!(null)),
        (json!([source("a", "A")]), "accepted", json!("A")),
    ] {
        let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Guess)];
        let report = run(&mut workers, &[task(sources)], Limits::default()).unwrap();
        let record = &report["records"][0];
        assert_eq!(record["output"], "A");
        assert_eq!(record["decision"]["state"], state);
        assert_eq!(record["decision"]["output"], output);
        if state == "abstained" {
            assert_eq!(record["assessment"]["state"], "rejected");
            assert_eq!(record["decision"]["origin"], "dna_sufficiency_gate");
        }
    }
}

fn task(sources: serde_json::Value) -> tron_v2::network::Task {
    config::task(&json!({"id":"t","context":"c","revision":1,
        "prompt":"{{evidence_status}}\nEvidence:\n{{evidence}}\nQuestion: Who?\nAnswer:",
        "candidates":[" A"," B"," UNKNOWN"],"dna":{"sources":sources,
        "queries":[{"entity":"locker","relations":["assigned_to"]}]}}))
    .unwrap()
}
fn source(id: &str, target: &str) -> serde_json::Value {
    json!({"id":id,"context":"c","revision":1,"entity":"locker",
        "relation":"assigned_to","target":target,"revoked":false})
}
#[test]
fn insufficient_and_conflicting_evidence_get_explicit_abstention_instructions() {
    for sources in [json!([]), json!([source("a", "A"), source("b", "B")])] {
        let (packet, request) = task(sources).packet(&HashMap::new(), 8192).unwrap();
        let prompt = request["prompts"][0].as_str().unwrap();
        assert!(prompt.contains("Evidence status: INSUFFICIENT"));
        assert!(prompt.contains("Return UNKNOWN"));
        assert_eq!(packet["evidence_status"]["sufficient"], false);
    }
}
#[test]
fn supported_hint_does_not_supply_the_answer_or_change_assessment() {
    let task = task(json!([source("a", "B")]));
    let (packet, request) = task.packet(&HashMap::new(), 8192).unwrap();
    assert_eq!(packet["evidence_status"]["sufficient"], true);
    let prompt = request["prompts"][0].as_str().unwrap();
    assert!(prompt.starts_with("Evidence status: SUFFICIENT"));
    assert!(!prompt
        .split("Evidence:\n")
        .next()
        .unwrap()
        .contains("Answer: B"));
    assert_eq!(
        task.dna.unwrap().assess("c", 1, "A", false)["state"],
        "rejected"
    );
}
