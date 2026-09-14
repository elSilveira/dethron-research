use serde_json::{json, Value};
use tron_v2::network::Worker;
use tron_window::reconstruction_live::{cases, execute_case};
struct Guess;
impl Worker for Guess {
    fn metadata(&self) -> Value {
        json!({"fixture":true})
    }
    fn execute(&mut self, request: Value) -> Result<Value, String> {
        assert!(!request["prompts"][0].as_str().unwrap().contains("expected"));
        Ok(json!({"data":{"outputs":[{"selected":" Amber"}],"evaluated_tokens":10}}))
    }
}
#[test]
fn real_probe_keeps_model_errors_visible_and_does_not_accept_unsupported_guesses() {
    let rows: Vec<_> = cases("fresh-id")
        .into_iter()
        .map(|c| execute_case(&mut Guess, c).unwrap())
        .collect();
    assert_eq!(rows.len(), 4);
    assert_eq!(rows[0]["dna"]["conclusion"], "Amber");
    assert_eq!(rows[1]["dna"]["conclusion"], "Amber");
    assert_eq!(rows[2]["model_correct"], false);
    assert_eq!(rows[2]["guarded_output"], "UNKNOWN");
    assert_eq!(rows[3]["guarded_output"], "UNKNOWN");
    assert!(rows.iter().all(|r| r["dna_correct"] == true));
}
