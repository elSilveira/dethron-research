use tron_window::neural::controller::grounded_decision;

#[test]
fn an_unsupported_neural_guess_cannot_be_presented_as_reconstruction() {
    assert_eq!(
        grounded_decision("A", false),
        ("UNKNOWN", "abstained_missing_evidence")
    );
    assert_eq!(grounded_decision("A", true), ("A", "neural_answer"));
}
