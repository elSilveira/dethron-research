use serde_json::{json, Value};
use std::collections::HashSet;
use tron_window::network::{accuracy, accuracy_data, accuracy_metrics, run, Limits, Worker};

struct Constant;
impl Worker for Constant {
    fn metadata(&self) -> Value {
        json!({"simulated":true})
    }
    fn execute(&mut self, _: Value) -> Result<Value, String> {
        Ok(json!({"data":{"outputs":[{"selected":" UNKNOWN"}],"evaluated_tokens":10}}))
    }
}

#[test]
fn comparison_keeps_raw_and_accepted_results_separate_and_tests_a_protected_wave() {
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Constant)];
    let report = accuracy::compare(&mut workers).unwrap();
    assert_eq!(report["trials"].as_array().unwrap().len(), 7);
    assert_eq!(report["expansion_ready"], false);
    assert_eq!(report["guarded_wave"]["records"][1]["status"], "blocked");
    let heldout = report["trials"]
        .as_array()
        .unwrap()
        .iter()
        .find(|t| t["split"] == "heldout" && t["policy"] == "recognized")
        .unwrap();
    assert_eq!(heldout["summary"]["raw_correct"], 20);
    assert_eq!(heldout["summary"]["evidence_control_correct"], 40);
}
#[test]
fn fixed_evaluation_is_disjoint_from_calibration_and_balances_supported_answers() {
    let calibration = accuracy_data::cases("calibration", "raw").unwrap();
    let heldout = accuracy_data::cases("heldout", "raw").unwrap();
    assert_eq!(heldout.len(), 40);
    let names: HashSet<_> = calibration.iter().map(|c| &c.task.context).collect();
    assert!(heldout.iter().all(|c| !names.contains(&c.task.context)));
    for label in ["A", "B", "C", "D"] {
        assert_eq!(heldout.iter().filter(|c| c.expected == label).count(), 5);
    }
    for kind in ["missing", "conflict", "stale", "revoked", "foreign"] {
        assert_eq!(heldout.iter().filter(|c| c.kind == kind).count(), 4);
    }
    assert!(accuracy_data::cases("heldout", "unknown").is_err());
}
#[test]
fn recognizing_dna_reduces_large_corpus_without_picking_a_conflicting_answer() {
    let expanded = accuracy_data::cases("expansion", "recognized").unwrap();
    for case in expanded {
        assert!(case.corpus.value().to_string().len() > 8192);
        assert_eq!(case.task.dna.as_ref().unwrap().sources.len(), 2);
        assert!(case.task.packet(&Default::default(), 8192).is_ok());
    }
    let cases = accuracy_data::cases("heldout", "recognized").unwrap();
    for case in cases.iter().filter(|c| c.kind == "conflict") {
        assert_eq!(case.task.dna.as_ref().unwrap().sources.len(), 3);
        assert_eq!(
            case.task
                .dna
                .as_ref()
                .unwrap()
                .assess(&case.task.context, 2, "A", false)["state"],
            "rejected"
        );
    }
}
#[test]
fn abstaining_everywhere_cannot_pass_the_expansion_gate_or_inflate_accuracy() {
    let cases = accuracy_data::cases("heldout", "recognized").unwrap();
    let tasks: Vec<_> = cases.iter().map(|c| c.task.clone()).collect();
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Constant)];
    let report = run(&mut workers, &tasks, Limits::default()).unwrap();
    let summary = accuracy_metrics::summarize(&cases, &report);
    assert_eq!(summary["raw_correct"], 20);
    assert_eq!(summary["constant_baseline_correct"], 20);
    assert_eq!(summary["accepted_answers"], 0);
    assert!(summary["accepted_precision"].is_null());
    assert_eq!(summary["supported_coverage"], 0.0);
    assert_eq!(summary["expansion_gate_passed"], false);
}
