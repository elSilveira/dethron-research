use serde_json::{json, Value};
use tron_v2::network::{config, run, Limits, Worker};

struct Broken;
impl Worker for Broken {
    fn metadata(&self) -> Value {
        json!({"simulated":true})
    }
    fn execute(&mut self, _: Value) -> Result<Value, String> {
        Ok(json!({"data":{"outputs":[{"text":"B","generated_tokens":0,
            "token_ids":[],"finish_reason":"eos"}],"evaluated_tokens":8}}))
    }
}

#[test]
fn core_rejects_empty_generation_even_if_worker_claims_completion() {
    let task = config::task(&json!({"id":"root","context":"c","revision":1,
        "prompt":"Answer","max_new_tokens":8}))
    .unwrap();
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Broken)];
    let report = run(&mut workers, &[task], Limits::default()).unwrap();
    assert_eq!(report["failed"], 1);
    assert_eq!(report["completed"], 0);
}

#[test]
fn core_dna_checks_are_available_without_the_window_runtime() {
    let dna = tron_v2::network::dna::Dna::parse(&json!({"sources":[],
        "queries":[{"entity":"missing","relations":["owner"]}]}))
    .unwrap();
    assert_eq!(dna.assess("c", 1, "A", false)["state"], "rejected");
    assert_eq!(dna.assess("c", 1, "UNKNOWN", false)["state"], "abstained");
}
