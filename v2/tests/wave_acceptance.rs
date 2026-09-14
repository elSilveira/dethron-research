use serde_json::{json, Value};
use tron_v2::network::{config, run, Limits, Worker};

struct Answer {
    text: &'static str,
    truncated: bool,
}
impl Worker for Answer {
    fn metadata(&self) -> Value {
        json!({"simulated":true})
    }
    fn execute(&mut self, request: Value) -> Result<Value, String> {
        let output = if request["op"] == "generate" {
            json!({"text":self.text,"generated_tokens":1,"token_ids":[1],
                "finish_reason":if self.truncated {"length"} else {"eos"}})
        } else {
            json!({"selected":format!(" {}",self.text)})
        };
        Ok(json!({"data":{"outputs":[output],"evaluated_tokens":8}}))
    }
}
fn task(id: &str, parents: &[&str]) -> Value {
    json!({"id":id,"context":"c","revision":1,"parents":parents,"prompt":"Who owns p?",
        "candidates":[" A"," B"],"dna":{"queries":[{"entity":"p","relations":["owner"]}],
        "sources":[{"id":"s","context":"c","revision":1,"entity":"p","relation":"owner","target":"B","revoked":false}]}})
}
fn execute(tasks: Vec<Value>, text: &'static str, truncated: bool) -> Value {
    let tasks = tasks
        .iter()
        .map(config::task)
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Answer { text, truncated })];
    run(&mut workers, &tasks, Limits::default()).unwrap()
}
#[test]
fn unsupported_output_stays_visible_but_cannot_feed_a_later_wave() {
    let report = execute(vec![task("root", &[]), task("join", &["root"])], "A", false);
    assert_eq!(report["records"][0]["output"], "A");
    assert_eq!(report["records"][0]["assessment"]["state"], "rejected");
    assert_eq!(report["records"][1]["status"], "blocked");
    assert_eq!(report["accepted"], 0);
}
#[test]
fn accepted_packets_carry_sources_and_acceptance_without_overwriting_raw_output() {
    let mut join = task("join", &["root"]);
    join["dna"]["sources"] = json!([]);
    let report = execute(vec![task("root", &[]), join], "B", false);
    assert_eq!(report["accepted"], 2);
    assert_eq!(
        report["records"][1]["packet"]["dna"]["sources"][0]["id"],
        "s"
    );
    assert_eq!(
        report["records"][1]["packet"]["parents"][0]["assessment"]["state"],
        "accepted"
    );
}
#[test]
fn a_parent_source_cannot_be_rewritten_under_the_same_identity() {
    let mut join = task("join", &["root"]);
    join["dna"]["sources"][0]["target"] = json!("A");
    let report = execute(vec![task("root", &[]), join], "B", false);
    assert_eq!(report["records"][1]["status"], "failed");
    assert!(report["records"][1]["error"]
        .as_str()
        .unwrap()
        .contains("identity"));
}
#[test]
fn truncated_generation_is_marked_and_cannot_be_used_as_a_complete_parent() {
    let mut root = task("root", &[]);
    root["candidates"] = json!([]);
    let report = execute(vec![root, task("join", &["root"])], "B", true);
    assert_eq!(report["records"][0]["assessment"]["state"], "truncated");
    assert_eq!(report["records"][1]["status"], "blocked");
}
