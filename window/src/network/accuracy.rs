use super::{accuracy_data, accuracy_metrics, run, Limits, Worker};
use serde_json::{json, Value};
use std::time::Instant;

pub fn compare(workers: &mut [Box<dyn Worker>]) -> Result<Value, String> {
    let mut trials = Vec::new();
    for split in ["calibration", "heldout", "expansion"] {
        for policy in ["raw", "examples", "recognized"] {
            if split == "expansion" && policy != "recognized" {
                continue;
            }
            eprintln!("Accuracy trial: {split}, {policy}");
            let start = Instant::now();
            let cases = accuracy_data::cases(split, policy)?;
            let tasks: Vec<_> = cases.iter().map(|c| c.task.clone()).collect();
            let preparation_seconds = start.elapsed().as_secs_f64();
            let result = run(workers, &tasks, Limits::default())?;
            let summary = accuracy_metrics::summarize(&cases, &result);
            trials.push(json!({"split":split,"policy":policy,"summary":summary,"run":result,
                "preparation_seconds":preparation_seconds,"end_to_end_seconds":start.elapsed().as_secs_f64(),
                "corpora":cases.iter().map(|c| c.corpus.value()).collect::<Vec<_>>()}));
        }
    }
    let first = accuracy_data::cases("heldout", "recognized")?
        .remove(0)
        .task;
    let mut child = first.clone();
    child.id = "verified-consumer".into();
    child.parents = vec![first.id.clone()];
    child.dna.as_mut().unwrap().sources.clear();
    let wave = run(workers, &[first, child], Limits::default())?;
    let heldout = trials
        .iter()
        .find(|t| t["split"] == "heldout" && t["policy"] == "recognized")
        .unwrap();
    let expansion = trials.last().unwrap();
    let ready = heldout["summary"]["expansion_gate_passed"] == true
        && expansion["summary"]["expansion_gate_passed"] == true
        && wave["accepted"] == 2;
    let execution_passed = trials
        .iter()
        .all(|t| t["run"]["failed"] == 0 && t["run"]["blocked"] == 0)
        && wave["failed"] == 0;
    Ok(
        json!({"schema":1,"trials":trials,"guarded_wave":wave,"expansion_ready":ready,
        "execution_passed":execution_passed,
        "gate":"No accepted wrong answers, at least 75% supported-case coverage on heldout and expansion sets, and two accepted connected-wave answers",
        "scope":"Frozen synthetic relation tasks and prompts. Examples and evaluation entities are disjoint. No weight learning. Recognition is deterministic bounded retrieval; verification assumes supplied sources are authoritative."}),
    )
}
