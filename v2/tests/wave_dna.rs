use serde_json::{json, Value};
use tron_v2::network::dna::Dna;

fn source(id: &str, entity: &str, relation: &str, target: &str) -> Value {
    json!({"id":id,"context":"c","revision":2,"entity":entity,
        "relation":relation,"target":target,"revoked":false})
}
fn evidence() -> Value {
    json!({"sources":[source("s1","parcel","stored_at","locker"),
        source("s2","locker","assigned_to","B")],
        "queries":[{"entity":"parcel","relations":["stored_at","assigned_to"]}]})
}

#[test]
fn accepts_only_an_answer_entailed_by_current_sources_and_preserves_citations() {
    let dna = Dna::parse(&evidence()).unwrap();
    let accepted = dna.assess("c", 2, "B", false);
    assert_eq!(accepted["state"], "accepted");
    assert_eq!(accepted["accepted_output"], "B");
    assert_eq!(accepted["source_ids"], json!(["s1", "s2"]));
    let wrong = dna.assess("c", 2, "A", false);
    assert_eq!(wrong["state"], "rejected");
    assert!(wrong["accepted_output"].is_null());
    assert_eq!(dna.assess("c", 2, "B", true)["state"], "truncated");
}

#[test]
fn missing_conflicting_stale_revoked_and_foreign_sources_cannot_certify_a_guess() {
    for kind in ["missing", "conflict", "stale", "revoked", "foreign"] {
        let mut value = evidence();
        match kind {
            "missing" => {
                value["sources"].as_array_mut().unwrap().pop();
            }
            "conflict" => value["sources"].as_array_mut().unwrap().push(source(
                "s3",
                "locker",
                "assigned_to",
                "A",
            )),
            "stale" => value["sources"][1]["revision"] = json!(1),
            "revoked" => value["sources"][1]["revoked"] = json!(true),
            _ => value["sources"][1]["context"] = json!("other"),
        }
        let dna = Dna::parse(&value).unwrap();
        assert_eq!(
            dna.assess("c", 2, "B", false)["state"],
            "rejected",
            "{kind}"
        );
        assert_eq!(
            dna.assess("c", 2, "UNKNOWN", false)["state"],
            "abstained",
            "{kind}"
        );
        assert!(dna.assess("c", 2, "UNKNOWN", false)["accepted_output"].is_null());
    }
}

#[test]
fn recognition_selects_reachable_sources_and_keeps_conflicts_visible() {
    let mut value = evidence();
    let sources = value["sources"].as_array_mut().unwrap();
    sources.push(source("conflict", "locker", "assigned_to", "C"));
    sources.push(source("noise", "unrelated", "assigned_to", "D"));
    let dna = Dna::parse(&value).unwrap();
    let recognized = dna.recognize("c", 2);
    assert_eq!(recognized.len(), 3);
    assert!(!recognized.iter().any(|s| s.id == "noise"));
    assert!(recognized.iter().any(|s| s.id == "conflict"));
}

#[test]
fn malformed_or_duplicate_source_identity_is_rejected() {
    let mut value = evidence();
    let duplicate = value["sources"][0].clone();
    value["sources"].as_array_mut().unwrap().push(duplicate);
    assert!(Dna::parse(&value).is_err());
    assert!(Dna::parse(&json!({"sources":[],"queries":[]})).is_err());
    value = evidence();
    value["sources"][0]["revoked"] = json!("false");
    assert!(Dna::parse(&value).is_err());
}
