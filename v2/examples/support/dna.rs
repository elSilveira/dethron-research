use super::check;
use serde_json::{json, Value};
use tron_v2::network::{dna::Dna, reconstruction::reconstruct};

fn route(prefix: &str, answer: &str, seed: u64) -> Result<Dna, String> {
    let middle = format!("node-{seed}-{prefix}");
    Dna::parse(&json!({"sources":[
        {"id":format!("{prefix}1"),"context":"probe","revision":2,"entity":"item",
         "relation":"via","target":middle,"revoked":false},
        {"id":format!("{prefix}2"),"context":"probe","revision":2,"entity":middle,
         "relation":"answer","target":answer,"revoked":false}],
        "queries":[{"entity":"item","relations":["via","answer"]}]}))
}

pub fn run(seed: u64, checks: &mut Vec<Value>) -> Result<String, String> {
    let answer = format!("value-{seed}");
    let a = route("a", &answer, seed)?;
    let b = route("b", &answer, seed)?;
    let report = reconstruct(&[a.clone(), b.clone()], "probe", 2)?;
    checks.push(check(
        "dna_reconstruction",
        json!(answer),
        report["conclusion"].clone(),
    ));
    checks.push(check(
        "source_work",
        json!(true),
        json!(report["source_checks"].as_u64().unwrap_or(0) > 0),
    ));
    let mut lost = a.clone();
    lost.sources.pop();
    checks.push(check(
        "route_loss",
        json!(answer),
        reconstruct(&[lost.clone(), b], "probe", 2)?["conclusion"].clone(),
    ));
    checks.push(check(
        "all_routes_missing",
        json!("abstained"),
        reconstruct(&[lost], "probe", 2)?["state"].clone(),
    ));
    let changed = format!("updated-{seed}");
    checks.push(check(
        "changed_facts",
        json!(changed),
        reconstruct(&[route("c", &changed, seed)?], "probe", 2)?["conclusion"].clone(),
    ));
    checks.push(check(
        "conflict_veto",
        json!("abstained"),
        reconstruct(&[a.clone(), route("c", &changed, seed)?], "probe", 2)?["state"].clone(),
    ));
    let mut states = Vec::new();
    for kind in ["stale", "revoked", "foreign"] {
        let mut invalid = a.clone();
        match kind {
            "stale" => invalid.sources[1].revision = 1,
            "revoked" => invalid.sources[1].revoked = true,
            _ => invalid.sources[1].context = "foreign".into(),
        }
        states.push(reconstruct(&[invalid], "probe", 2)?["state"].clone());
    }
    checks.push(check(
        "inactive_sources",
        json!(["abstained", "abstained", "abstained"]),
        json!(states),
    ));
    checks.push(check(
        "wrong_answer_rejected",
        json!("rejected"),
        a.assess("probe", 2, "constant-answer", false)["state"].clone(),
    ));
    Ok(answer)
}
