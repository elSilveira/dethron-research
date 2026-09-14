use tron_window::reorganization::graph::{Graph, Primitive::*, Recipe};

#[test]
fn composes_executed_procedure_instead_of_remembering_one_answer() {
    let original = Recipe::new(&[Add(2), Multiply(3), Add(-1), Absolute, Add(7)]).unwrap();
    let shorter = original.compose().expect("new procedure");
    assert_eq!(original.steps().len(), 5);
    assert_eq!(shorter.steps().len(), 3);
    for input in -1000..=1000 {
        let expected = ((input + 2_i64) * 3 - 1).abs() + 7;
        assert_eq!(original.execute(input).unwrap(), expected);
        assert_eq!(shorter.execute(input).unwrap(), expected);
    }
    assert!(shorter.work() < original.work());
    let mut ids = 0;
    let first = Graph::rebuild(shorter.clone(), &mut ids);
    let rebuilt = Graph::rebuild(shorter, &mut ids);
    assert!(first.ids.iter().all(|id| !rebuilt.ids.contains(id)));
    assert_eq!(first.recipe.execute(9123), rebuilt.recipe.execute(9123));
}

#[test]
fn respects_nonlinear_boundaries_and_bounded_arithmetic() {
    let recipe = Recipe::new(&[Multiply(-2), Absolute, Add(1)]).unwrap();
    assert!(recipe.compose().is_none());
    assert!(recipe.execute(1_000_001).is_err());
    assert!(Recipe::new(&[Multiply(i64::MAX)]).is_err());
    assert!(Recipe::new(&[]).is_err());
    assert!(Recipe::new(&[Add(1); 9]).is_err());
    let worst = Recipe::new(&[Multiply(16); 8]).unwrap();
    assert_eq!(worst.execute(1_000_000).unwrap(), 4_294_967_296_000_000);
}
