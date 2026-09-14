use tron_window::neural::memory::{Memory, Tier};

#[test]
fn reconstructs_only_through_reachable_associations_in_the_right_context() {
    let mut memory = Memory::default();
    memory
        .put(1, "parcel-1", "stored_at", "locker-1", Tier::Short)
        .unwrap();
    memory
        .put(1, "locker-1", "assigned_to", "A", Tier::Long)
        .unwrap();
    memory
        .put(2, "locker-1", "assigned_to", "B", Tier::Long)
        .unwrap();
    let trace = memory.trace(1, "parcel-1", None);
    assert_eq!(trace.len(), 2);
    assert_eq!(trace[1].target, "A");
    assert!(memory.trace(2, "parcel-1", None).is_empty());
    let recipe: Vec<_> = trace.iter().map(|f| f.relation.clone()).collect();
    memory.forget(Tier::Short);
    assert!(memory.trace(1, "parcel-1", Some(&recipe)).is_empty());
    assert_eq!(memory.active(1).len(), 1);
}

#[test]
fn revision_supersedes_old_context_and_tiers_expire_at_different_rates() {
    let mut memory = Memory::default();
    memory
        .put(1, "parcel", "stored_at", "locker", Tier::Medium)
        .unwrap();
    memory
        .put(1, "locker", "assigned_to", "A", Tier::Long)
        .unwrap();
    let epoch = memory.epoch;
    memory
        .put(1, "locker", "assigned_to", "B", Tier::Long)
        .unwrap();
    assert!(memory.epoch > epoch);
    assert_eq!(memory.trace(1, "parcel", None)[1].target, "B");
    for _ in 0..65 {
        memory.advance();
    }
    assert!(memory.trace(1, "parcel", None).is_empty());
    assert_eq!(memory.active(1).len(), 1);
}
