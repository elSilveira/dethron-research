use serde_json::json;
use tron_v2::network::{atomic::AtomicDna, dna::Dna};
fn routes() -> Vec<Dna> {
    ["a","b"].iter().map(|branch|Dna::parse(&json!({"sources":[
        {"id":format!("{branch}1"),"context":"c","revision":1,"entity":"Atlas","relation":"team","target":branch,"revoked":false},
        {"id":format!("{branch}2"),"context":"c","revision":1,"entity":branch,"relation":"lead","target":"Mira","revoked":false},
        {"id":"shared","context":"c","revision":1,"entity":"Mira","relation":"office","target":"Porto","revoked":false}],
        "queries":[{"entity":"Atlas","relations":["team","lead","office"]}]})).unwrap()).collect()
}
#[test]
fn one_fact_per_atom_deduplicates_shared_evidence_and_recovers_after_branch_loss() {
    let mut graph = AtomicDna::compile(&routes()).unwrap();
    assert_eq!(graph.inventory()["atoms"].as_array().unwrap().len(), 5);
    assert_eq!(graph.reconstruct("c", 1).unwrap()["conclusion"], "Porto");
    assert!(graph.lose_source("a2"));
    let restored = graph.reconstruct("c", 1).unwrap();
    assert_eq!(restored["conclusion"], "Porto");
    assert_eq!(restored["source_ids"], json!(["b1", "b2", "shared"]));
    assert!(graph.lose_source("shared"));
    assert_eq!(graph.reconstruct("c", 1).unwrap()["state"], "abstained");
}
#[test]
fn atoms_keep_versions_conflicts_and_source_identity_constraints() {
    let mut plans = routes();
    let original = AtomicDna::compile(&plans).unwrap();
    assert_eq!(original.reconstruct("c", 2).unwrap()["state"], "abstained");
    plans[1].sources[1].target = "Nora".into();
    plans[1].sources[2].id = "other-office".into();
    plans[1].sources[2].entity = "Nora".into();
    plans[1].sources[2].target = "Recife".into();
    let conflicting = AtomicDna::compile(&plans).unwrap();
    assert_eq!(
        conflicting.reconstruct("c", 1).unwrap()["state"],
        "abstained"
    );
    assert!(conflicting.evidence_text("c", 1).contains("Recife"));
    plans[1].sources[2].id = "shared".into();
    assert!(AtomicDna::compile(&plans).is_err());
}
