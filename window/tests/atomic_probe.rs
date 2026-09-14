use serde_json::{json, Value};
use tron_v2::network::Worker;
struct Recorder(Vec<Value>);
impl Worker for Recorder {
    fn metadata(&self) -> Value {
        json!({"fixture":true})
    }
    fn execute(&mut self, r: Value) -> Result<Value, String> {
        self.0.push(r);
        Ok(
            json!({"data":{"outputs":[{"text":"{\"answer\":\"UNKNOWN\",\"citations\":[]}","finish_reason":"eos"}],"evaluated_tokens":10}}),
        )
    }
}
#[test]
fn atomic_condition_changes_evidence_not_question_or_expected_answer() {
    let case = json!({"id":"sample","question":"Who leads Atlas?","expected":"Mira","removed":[],
        "document":"[S1] Atlas is led by Mira. Extra unrelated prose.","sections":{"S1":"Atlas is led by Mira. Extra unrelated prose."},
        "routes":[{"sources":[{"id":"S1","context":"document","revision":1,"entity":"Atlas","relation":"lead","target":"Mira","revoked":false}],"queries":[{"entity":"Atlas","relations":["lead"]}]}]});
    let mut worker = Recorder(vec![]);
    let report = tron_window::atomic_probe::execute(&mut worker, &case, false).unwrap();
    assert_eq!(worker.0.len(), 2);
    assert!(report["atomic_text"]
        .as_str()
        .unwrap()
        .contains("[S1] Atlas --lead--> Mira."));
    assert_eq!(report["dna"]["conclusion"], "Mira");
    assert!(worker.0.iter().all(|r| r["max_new_tokens"] == 256));
    assert_eq!(report["modes"][0]["mode"], "selected");
    assert_eq!(report["modes"][1]["mode"], "atomic");
}
