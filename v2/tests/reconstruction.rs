use serde_json::json;
use tron_v2::network::{
    dna::Dna,
    reconstruction::{reconstruct, Presentation},
};

fn route(prefix: &str, answer: &str) -> Dna {
    Dna::parse(&json!({"sources":[
        {"id":format!("{prefix}1"),"context":"c","revision":1,"entity":"item","relation":"via","target":prefix,"revoked":false},
        {"id":format!("{prefix}2"),"context":"c","revision":1,"entity":prefix,"relation":"answer","target":answer,"revoked":false}],
        "queries":[{"entity":"item","relations":["via","answer"]}]})).unwrap()
}
#[test]
fn reconstructs_without_saved_output_and_survives_either_route_loss() {
    let a = route("a", "Paris");
    let b = route("b", "Paris");
    for routes in [vec![a.clone(), b.clone()], vec![a], vec![b]] {
        let result = reconstruct(&routes, "c", 1).unwrap();
        assert_eq!(result["state"], "accepted");
        assert_eq!(result["conclusion"], "Paris");
        assert!(result["source_ids"].as_array().unwrap().len() >= 2);
        assert!(result["source_checks"].as_u64().unwrap() > 0);
        assert!(result["dna_bytes"].as_u64().unwrap() > 0);
        assert_ne!(
            Presentation::Bare.render(&result),
            Presentation::Sentence.render(&result)
        );
    }
}
#[test]
fn missing_inactive_and_conflicting_evidence_never_becomes_an_answer() {
    let good = route("a", "Paris");
    let mut broken = route("b", "Paris");
    broken.sources.pop();
    assert_eq!(
        reconstruct(&[broken.clone(), good.clone()], "c", 1).unwrap()["conclusion"],
        "Paris"
    );
    assert_eq!(
        reconstruct(&[broken], "c", 1).unwrap()["state"],
        "abstained"
    );
    for (context, revision) in [("foreign", 1), ("c", 2)] {
        assert_eq!(
            reconstruct(std::slice::from_ref(&good), context, revision).unwrap()["state"],
            "abstained"
        );
    }
    let mut revoked = good.clone();
    revoked.sources[1].revoked = true;
    assert_eq!(
        reconstruct(&[revoked], "c", 1).unwrap()["state"],
        "abstained"
    );
    let result = reconstruct(&[good.clone(), route("b", "Tokyo")], "c", 1).unwrap();
    assert_eq!(result["state"], "abstained");
    assert!(result["conclusion"].is_null());
    assert_eq!(Presentation::Sentence.render(&result), "UNKNOWN");
    let mut conflict = good.clone();
    let mut extra = conflict.sources[1].clone();
    extra.id = "conflict".into();
    extra.target = "Tokyo".into();
    conflict.sources.push(extra);
    assert_eq!(
        reconstruct(&[good, conflict], "c", 1).unwrap()["state"],
        "abstained"
    );
}
#[test]
fn rejects_empty_mismatched_or_unbounded_route_plans() {
    assert!(reconstruct(&[], "c", 1).is_err());
    let a = route("a", "Paris");
    let mut b = route("b", "Paris");
    b.queries[0].entity = "different".into();
    assert!(reconstruct(&[a.clone(), b], "c", 1).is_err());
    assert!(reconstruct(&vec![a; 17], "c", 1).is_err());
}
