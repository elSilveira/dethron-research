use tron_window::reorganization::graph::Primitive::*;
use tron_window::{
    budget::Activity,
    reorganization::{Engine, Policy, Request},
};

fn request(input: i64) -> Request<'static> {
    Request {
        capability: "calibration",
        context: 1,
        input,
        ingress: 900,
        sink: 901,
    }
}

#[test]
fn five_to_three_requires_parallel_agreement_on_new_inputs() {
    let mut engine = Engine::new(Policy::Adaptive, 10_000);
    engine
        .register(
            "calibration",
            &[Add(2), Multiply(3), Add(-1), Absolute, Add(7)],
        )
        .unwrap();
    let first = engine.submit(request(-5)).unwrap();
    assert_eq!(first.value, 17);
    assert_eq!(first.sink, 901);
    assert_eq!(first.primary_nodes.len(), 5);
    assert!(first.shadow_nodes.is_empty());
    let second = engine.submit(request(-4)).unwrap();
    assert!(second.events.contains(&"candidate_created"));
    for input in [-3, -3, -3, -2] {
        let result = engine.submit(request(input)).unwrap();
        assert_eq!(result.phase, "shadow");
        assert_eq!(result.primary_nodes.len(), 3);
        assert_eq!(result.shadow_nodes.len(), 5);
        assert_eq!(result.workers.len(), 2);
        assert_ne!(result.workers[0], result.workers[1]);
        assert!(result.consensus);
        assert!(!result.events.contains(&"promoted"));
    }
    let promoted = engine.submit(request(-1)).unwrap();
    assert!(promoted.events.contains(&"promoted"));
    assert_eq!(engine.memory_stats().long, 1);
    let next = engine.submit(request(8765)).unwrap();
    assert_eq!(next.phase, "shortcut");
    assert_eq!(next.value, ((8765_i64 + 2) * 3 - 1).abs() + 7);
    assert!(next.shadow_nodes.is_empty());
    assert!(engine.budget.spent(Activity::Validate) >= 5 * 10);
    assert!(engine.budget.spent(Activity::Consolidate) > 0);
}

#[test]
fn strong_control_can_compose_without_adaptive_validation() {
    for (policy, nodes) in [(Policy::Fixed, 5), (Policy::Compiled, 3)] {
        let mut engine = Engine::new(policy, 1000);
        engine
            .register(
                "calibration",
                &[Add(2), Multiply(3), Add(-1), Absolute, Add(7)],
            )
            .unwrap();
        let delivery = engine.submit(request(21)).unwrap();
        assert_eq!(delivery.value, 75);
        assert_eq!(delivery.primary_nodes.len(), nodes);
        assert!(delivery.shadow_nodes.is_empty());
    }
}
