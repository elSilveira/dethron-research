use tron_v2::{audit::verify, trit::Trit, tron::Tron};

#[test]
fn lifecycle_memory_and_failed_work_have_real_semantics() {
    let mut tron = Tron::new(0);
    assert!(tron.run(997, 2).is_err());
    assert_eq!(tron.knowledge_len(), 0);
    assert!(!tron.run(84, 2000).unwrap().cached);
    let cached = tron.run(84, 2000).unwrap();
    assert!(cached.cached);
    assert_eq!(cached.work.divisions, 0);
    assert_eq!(cached.work.factors, vec![2, 2, 3, 7]);
    tron.stop();
    assert!(tron.run(49, 2000).is_err());
    tron.resume();
    assert_eq!(tron.run(49, 2000).unwrap().work.factors, vec![7, 7]);
    verify(&tron.audit.proof(), &tron.audit.key(), &tron.audit.head()).unwrap();
}

#[test]
fn automatic_development_promotes_measured_improvement_and_stops_at_plateau() {
    let mut tron = Tron::new(2);
    assert_eq!(tron.strategy(), Trit::Minus);
    tron.run(84, 2000).unwrap();
    tron.run(49, 2000).unwrap();
    assert_eq!(tron.strategy(), Trit::Plus);
    assert_eq!(tron.version(), 1);
    assert_eq!(tron.run(997, 2000).unwrap().work.factors, vec![997]);
    let result = tron.evolve();
    assert!(!result.promoted);
    assert!(result.evaluation_divisions > 0);
    assert_eq!(tron.version(), 1);
}

#[test]
fn authorized_children_inherit_knowledge_and_have_distinct_identity_and_lineage() {
    let mut parent = Tron::new(0);
    parent.run(997, 2000).unwrap();
    parent.evolve();
    let mut child = parent.spawn(true).unwrap();
    assert_ne!(parent.audit.key(), child.audit.key());
    assert_eq!(child.generation(), 1);
    assert_eq!(child.strategy(), parent.strategy());
    assert!(child.run(997, 2000).unwrap().cached);
    let endorsement = parent.audit.proof().last().unwrap().clone();
    assert_eq!(endorsement.kind, "spawn");
    assert_eq!(
        endorsement.related.as_ref().unwrap(),
        &child.audit.identity()
    );
    assert_eq!(
        child.audit.proof()[0].related.as_ref().unwrap(),
        &endorsement.hash()
    );
    let empty = parent.spawn(false).unwrap();
    assert_eq!(empty.knowledge_len(), 0);
    parent.stop();
    assert!(parent.spawn(true).is_err());
}
