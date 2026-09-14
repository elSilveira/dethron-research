use serde_json::{json, Value};
use tron_window::network::{probe, workload, Worker};

struct FirstChoice;
impl Worker for FirstChoice {
    fn metadata(&self) -> Value {
        json!({"simulated":true})
    }
    fn execute(&mut self, request: Value) -> Result<Value, String> {
        Ok(
            json!({"data":{"outputs":[{"selected":request["candidates"][0]}],"evaluated_tokens":10}}),
        )
    }
}
#[test]
fn compares_serial_pool_and_cooperative_waves_on_same_cases_and_budget() {
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(FirstChoice), Box::new(FirstChoice)];
    let report = probe::compare(&mut workers, 2, 4).unwrap();
    let trials = report["trials"].as_array().unwrap();
    assert_eq!(trials.len(), 8);
    assert_ne!(trials[0]["mode"], trials[4]["mode"]);
    for trial in trials {
        assert_eq!(trial["questions"], 4);
        assert_eq!(trial["run"]["token_budget"], 100000);
        assert_eq!(trial["run"]["failed"], 0);
        assert_eq!(trial["run"]["blocked"], 0);
        let mode = trial["mode"].as_str().unwrap();
        assert_eq!(
            trial["run"]["completed"],
            if mode.ends_with("wave") { 12 } else { 4 }
        );
        if mode.starts_with("serial") {
            assert_eq!(trial["run"]["max_in_flight"], 1);
        }
    }
}
#[test]
fn wave_sources_and_direct_sources_use_identical_facts_and_keep_answers_out_of_join() {
    let direct = workload::questions(0, 4, false);
    let waves = workload::questions(0, 4, true);
    for i in 0..4 {
        assert!(direct[i].prompt.contains(&format!("parcel p{i}")));
        assert!(waves[i * 3].prompt.contains(&format!("parcel p{i}")));
        assert_eq!(direct[i].candidates, waves[i * 3 + 2].candidates);
        assert_eq!(waves[i * 3 + 2].parents.len(), 2);
        assert!(!waves[i * 3 + 2].prompt.contains("is assigned to"));
        assert_eq!(direct[i].context, waves[i * 3 + 2].context);
    }
    assert!(probe::compare(&mut [Box::new(FirstChoice)], 0, 4).is_err());
}
