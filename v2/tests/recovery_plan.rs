use serde_json::json;
use tron_v2::network::recovery_plan::{preserve_plan, recover_plan};
#[test]
fn task_dna_roundtrip_retains_versions_revocations_and_queries() {
    let plan = json!({"workers":[],"tasks":[{"id":"task","dna":{"sources":[
        {"id":"s","context":"c","revision":2,"entity":"parcel","relation":"stored_at","target":"locker","revoked":true,"provenance":{"document":"original-note"}}],
        "queries":[{"entity":"parcel","relations":["stored_at"]}]}}]});
    let saved = preserve_plan(&plan, &[7; 32]);
    assert!(saved.is_ok());
    let (root, store) = saved.unwrap();
    assert_eq!(store.len(), 3);
    assert_eq!(
        recover_plan(&root, &[7; 32], |id| vec![store[id].clone()]).unwrap(),
        plan
    );
    assert!(recover_plan(&root, &[7; 32], |id| if id == root {
        vec![store[id].clone()]
    } else {
        vec![]
    })
    .is_err());
}
