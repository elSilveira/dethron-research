use super::accuracy_data::Case;
use serde_json::{json, Value};
use std::collections::BTreeMap;

pub fn summarize(cases: &[Case], run: &Value) -> Value {
    let control_start = std::time::Instant::now();
    let evidence_control_correct = cases
        .iter()
        .filter(|case| {
            let answer = ["A", "B", "C", "D"]
                .into_iter()
                .find(|candidate| {
                    case.corpus
                        .assess(&case.task.context, case.task.revision, candidate, false)["state"]
                        == "accepted"
                })
                .unwrap_or("UNKNOWN");
            answer == case.expected
        })
        .count();
    let evidence_control_seconds = control_start.elapsed().as_secs_f64();
    let records = run["records"].as_array().unwrap();
    let (mut raw_correct, mut accepted, mut accepted_correct, mut abstentions) = (0, 0, 0, 0);
    let mut supported_raw_correct = 0;
    let mut labels = BTreeMap::<String, usize>::new();
    let mut details = Vec::new();
    let mut by_kind = BTreeMap::<String, Value>::new();
    for case in cases {
        *labels.entry(case.expected.clone()).or_default() += 1;
        let record = records.iter().find(|r| r["id"] == case.task.id).unwrap();
        let correct = record["status"] == "completed" && record["output"] == case.expected;
        let accepted_answer = record["assessment"]["state"] == "accepted";
        let correct_acceptance = accepted_answer && correct && case.expected != "UNKNOWN";
        raw_correct += usize::from(correct);
        supported_raw_correct += usize::from(correct && case.expected != "UNKNOWN");
        accepted += usize::from(accepted_answer);
        accepted_correct += usize::from(correct_acceptance);
        abstentions +=
            usize::from(record["assessment"]["state"] == "abstained" && case.expected == "UNKNOWN");
        let kind = by_kind
            .entry(case.kind.clone())
            .or_insert(json!({"count":0,"raw_correct":0,"accepted":0}));
        for (key, increment) in [
            ("count", 1),
            ("raw_correct", usize::from(correct)),
            ("accepted", usize::from(accepted_answer)),
        ] {
            kind[key] = json!(kind[key].as_u64().unwrap() + increment as u64);
        }
        details.push(json!({"id":case.task.id,"kind":case.kind,"expected":case.expected,"raw":record["output"],
            "raw_correct":correct,"assessment":record["assessment"],"corpus_sources":case.corpus.sources.len(),
            "corpus_bytes":case.corpus.value().to_string().len(),"packet_sources":case.task.dna.as_ref().unwrap().sources.len()}));
    }
    let supported = cases.iter().filter(|c| c.expected != "UNKNOWN").count();
    let coverage = accepted_correct as f64 / supported.max(1) as f64;
    let gate = accepted > 0
        && accepted == accepted_correct
        && coverage >= 0.75
        && run["failed"] == 0
        && run["blocked"] == 0;
    json!({"cases":cases.len(),"supported_cases":supported,"raw_correct":raw_correct,
        "evidence_control_correct":evidence_control_correct,"evidence_control_seconds":evidence_control_seconds,
        "supported_raw_correct":supported_raw_correct,"accepted_answers":accepted,"accepted_correct":accepted_correct,
        "accepted_wrong":accepted-accepted_correct,"correct_abstentions":abstentions,
        "accepted_precision":if accepted==0 {Value::Null} else {json!(accepted_correct as f64/accepted as f64)},
        "supported_coverage":coverage,"constant_baseline_correct":labels.values().max().copied().unwrap_or(0),
        "expansion_gate_passed":gate,"by_kind":by_kind,"details":details,
        "verifier_control":"Deterministic relation lookup can solve this structured task; acceptance is not a neural accuracy gain"})
}
