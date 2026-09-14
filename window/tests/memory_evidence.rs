use tron_window::reorganization::graph::Primitive::*;
use tron_window::reorganization::{Engine, MemoryTier, Policy, Request};

fn request(input: i64) -> Request<'static> {
    Request {
        capability: "calibration",
        context: 1,
        input,
        ingress: 900,
        sink: 901,
    }
}
fn engine() -> Engine {
    let mut engine = Engine::new(Policy::Adaptive, 100_000);
    engine
        .register(
            "calibration",
            &[Add(2), Multiply(3), Add(-1), Absolute, Add(7)],
        )
        .unwrap();
    engine
}

#[test]
fn formation_examples_cannot_be_recounted_as_new_validation_evidence() {
    let mut engine = engine();
    for input in [0, 1, 0, 1, 2] {
        let result = engine.submit(request(input)).unwrap();
        assert!(!result.events.contains(&"promoted"));
    }
    assert_eq!(engine.memory_stats().long, 0);
    assert!(!engine
        .submit(request(3))
        .unwrap()
        .events
        .contains(&"promoted"));
    assert!(engine
        .submit(request(4))
        .unwrap()
        .events
        .contains(&"promoted"));
}

#[test]
fn reachable_medium_recipe_can_restore_a_pending_path_without_inventing_trust() {
    let mut engine = engine();
    for input in [0, 1, 2] {
        engine.submit(request(input)).unwrap();
    }
    assert_eq!(engine.memory_stats().long, 0);
    engine.lose_path("calibration").unwrap();
    engine.forget(MemoryTier::Short).unwrap();
    let result = engine.submit(request(3)).unwrap();
    assert!(result.events.contains(&"reconstructed_from_medium_memory"));
    assert_eq!(result.phase, "shadow");
    assert!(!result.events.contains(&"promoted"));
    assert!(engine
        .submit(request(4))
        .unwrap()
        .events
        .contains(&"promoted"));
}

#[test]
fn bounded_memories_keep_frequently_relevant_recipe_over_cold_recipes() {
    let mut engine = engine();
    for input in 0..20 {
        engine.submit(request(input)).unwrap();
    }
    for region in 0..7 {
        let name = format!("other-{region}");
        engine
            .register(&name, &[Add(1), Multiply(2), Add(3)])
            .unwrap();
        for input in 0..5 {
            engine
                .submit(Request {
                    capability: &name,
                    ..request(input)
                })
                .unwrap();
        }
    }
    let stats = engine.memory_stats();
    assert!(stats.short <= 16 && stats.medium <= 8 && stats.long <= 4);
    assert!(engine.register("too-many", &[Add(1)]).is_err());
    engine.lose_path("calibration").unwrap();
    engine.forget(MemoryTier::Short).unwrap();
    engine.forget(MemoryTier::Medium).unwrap();
    assert!(engine
        .submit(request(100))
        .unwrap()
        .events
        .contains(&"reconstructed_from_long_memory"));
}
