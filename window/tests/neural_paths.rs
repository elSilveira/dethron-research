use tron_window::neural::{
    memory::{Memory, Tier},
    paths::Paths,
};

#[test]
fn learns_relation_recipe_validates_novel_entities_and_reopens_on_context_changes() {
    let mut memory = Memory::default();
    memory
        .put(1, "parcel", "stored_at", "locker", Tier::Long)
        .unwrap();
    memory
        .put(1, "locker", "assigned_to", "A", Tier::Long)
        .unwrap();
    let trace = memory.trace(1, "parcel", None);
    let mut paths = Paths::default();
    assert_eq!(paths.prepare(1, memory.epoch, true), "reference");
    paths.observe("p0", &trace, true);
    assert!(paths
        .observe("p1", &trace, true)
        .contains(&"candidate_created"));
    assert_eq!(paths.prepare(1, memory.epoch, true), "shadow");
    assert!(!paths.observe("p0", &trace, true).contains(&"promoted"));
    for entity in ["p2", "p3", "p4"] {
        paths.observe(entity, &trace, true);
    }
    assert_eq!(paths.prepare(1, memory.epoch, true), "shortcut");
    let old = paths.nodes();
    paths.lose_nodes();
    paths.prepare(1, memory.epoch, true);
    assert_ne!(old, paths.nodes());
    assert_eq!(paths.recipe().unwrap(), ["stored_at", "assigned_to"]);
    assert_eq!(paths.prepare(2, memory.epoch, true), "shadow");
    assert!(paths.observe("p5", &trace, false).contains(&"reopened"));
    assert_eq!(paths.prepare(2, memory.epoch, false), "reference");
}
