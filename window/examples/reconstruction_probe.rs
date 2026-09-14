use serde_json::{json, Value};
use tron_v2::network::{
    dna::Dna,
    reconstruction::{reconstruct, Presentation},
};

fn route(branch: &str, target: &str) -> Dna {
    Dna::parse(&json!({"sources":[
        {"id":format!("{branch}-start"),"context":"probe","revision":1,"entity":"question","relation":"via","target":branch,"revoked":false},
        {"id":format!("{branch}-end"),"context":"probe","revision":1,"entity":branch,"relation":"answer","target":target,"revoked":false}],
        "queries":[{"entity":"question","relations":["via","answer"]}]})).unwrap()
}
fn main() {
    let a = route("a", "Paris");
    let b = route("b", "Paris");
    let mut missing = b.clone();
    missing.sources.pop();
    let mut revoked = b.clone();
    revoked.sources[1].revoked = true;
    let cases = vec![
        ("intact", vec![a.clone(), b.clone()], "probe", 1, true),
        ("lost_a", vec![b.clone()], "probe", 1, true),
        ("lost_b", vec![a.clone()], "probe", 1, true),
        (
            "broken_b",
            vec![a.clone(), missing.clone()],
            "probe",
            1,
            true,
        ),
        ("lost_essential", vec![missing], "probe", 1, false),
        ("revoked", vec![revoked], "probe", 1, false),
        ("stale", vec![b.clone()], "probe", 2, false),
        ("foreign", vec![b], "other", 1, false),
        ("conflict", vec![a, route("b", "Tokyo")], "probe", 1, false),
    ];
    let mut rows: Vec<Value> = Vec::new();
    let (mut correct, mut false_accepts, mut abstentions) = (0, 0, 0);
    for (name, routes, context, revision, supported) in cases {
        let report = reconstruct(&routes, context, revision).unwrap();
        let accepted = report["state"] == "accepted";
        let valid = if supported {
            accepted && report["conclusion"] == "Paris"
        } else {
            !accepted
        };
        correct += usize::from(valid);
        false_accepts += usize::from(accepted && !valid);
        abstentions += usize::from(!accepted);
        rows.push(json!({"case":name,"expected_supported":supported,"passed":valid,
            "bare":Presentation::Bare.render(&report),"sentence":Presentation::Sentence.render(&report),
            "report":report}));
    }
    println!("{}", serde_json::to_string_pretty(&json!({"fixture":true,"cases":rows,
        "passed":correct,"false_accepts":false_accepts,"abstentions":abstentions,
        "measurement":"dna_bytes is serialized input size, not measured network traffic; source_checks counts traversal comparisons"})).unwrap());
    assert_eq!(correct, 9);
    assert_eq!(false_accepts, 0);
}
