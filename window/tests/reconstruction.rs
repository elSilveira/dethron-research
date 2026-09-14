use tron_window::reorganization::graph::Primitive::*;
use tron_window::{
    budget::Activity,
    reorganization::{Engine, MemoryTier, Policy, Request},
};

fn request(input: i64, context: u64) -> Request<'static> {
    Request {
        capability: "calibration",
        context,
        input,
        ingress: 900,
        sink: 901,
    }
}
fn warmed() -> Engine {
    let mut engine = Engine::new(Policy::Adaptive, 100_000);
    engine
        .register(
            "calibration",
            &[Add(2), Multiply(3), Add(-1), Absolute, Add(7)],
        )
        .unwrap();
    for input in 0..5 {
        engine.submit(request(input, 1)).unwrap();
    }
    engine
}

#[test]
fn reconstructs_new_identities_from_accessible_long_memory_on_a_new_input() {
    let mut engine = warmed();
    let before = engine.submit(request(6, 1)).unwrap();
    engine.forget(MemoryTier::Short).unwrap();
    engine.lose_path("calibration").unwrap();
    let after = engine.submit(request(921, 1)).unwrap();
    assert!(after.events.contains(&"reconstructed_from_long_memory"));
    assert!(before
        .primary_nodes
        .iter()
        .all(|id| !after.primary_nodes.contains(id)));
    assert_eq!(after.value, 2775);
    assert!(engine.budget.spent(Activity::Reconstruct) > 0);
}

#[test]
fn general_recipe_is_not_automatic_trust_in_a_different_context() {
    let mut engine = warmed();
    for input in 100..103 {
        let result = engine.submit(request(input, 2)).unwrap();
        assert_eq!(result.phase, "shadow");
        assert_eq!(result.events.contains(&"promoted"), input == 102);
    }
    assert_eq!(engine.submit(request(103, 2)).unwrap().phase, "shortcut");
    assert_eq!(engine.submit(request(104, 1)).unwrap().phase, "shadow");
    assert_eq!(engine.memory_stats().long, 1);
}

#[test]
fn missing_all_memories_requires_relearning_instead_of_fabricated_reconstruction() {
    let mut engine = warmed();
    engine.lose_path("calibration").unwrap();
    for tier in [MemoryTier::Short, MemoryTier::Medium, MemoryTier::Long] {
        engine.forget(tier).unwrap();
    }
    let result = engine.submit(request(500, 1)).unwrap();
    assert_eq!(result.phase, "reference");
    assert!(!result
        .events
        .iter()
        .any(|event| event.starts_with("reconstructed")));
    assert_eq!(engine.memory_stats().long, 0);
}

#[test]
fn version_change_invalidates_recipes_and_rejects_stale_feedback() {
    let mut engine = warmed();
    let old = engine.submit(request(10, 1)).unwrap();
    engine
        .revise(
            "calibration",
            &[Add(3), Multiply(2), Add(1), Absolute, Add(4)],
        )
        .unwrap();
    assert_eq!(engine.memory_stats().long, 0);
    assert!(engine.feedback("calibration", &old, false).is_err());
    let new = engine.submit(request(10, 1)).unwrap();
    assert_eq!(new.version, old.version + 1);
    assert_eq!(new.phase, "reference");
    assert_eq!(new.value, 31);
}

#[test]
fn shadow_disagreement_reopens_without_delivering_bad_shortcut() {
    let mut engine = Engine::new(Policy::Adaptive, 1000);
    engine
        .register(
            "calibration",
            &[Add(2), Multiply(3), Add(-1), Absolute, Add(7)],
        )
        .unwrap();
    engine.submit(request(0, 1)).unwrap();
    engine.submit(request(1, 1)).unwrap();
    engine.inject_shortcut_fault("calibration").unwrap();
    let result = engine.submit(request(100, 1)).unwrap();
    assert!(!result.consensus);
    assert_eq!(result.value, 312);
    assert!(result.events.contains(&"reopened"));
    assert!(engine.feedback("calibration", &result, true).is_ok());
    assert_eq!(engine.submit(request(101, 1)).unwrap().phase, "reference");
}

#[test]
fn external_rejection_overrides_internal_agreement() {
    let mut engine = warmed();
    let result = engine.submit(request(10, 2)).unwrap();
    assert!(result.consensus);
    engine.feedback("calibration", &result, false).unwrap();
    assert_eq!(engine.memory_stats().long, 0);
    assert_eq!(engine.submit(request(11, 2)).unwrap().phase, "reference");
}
