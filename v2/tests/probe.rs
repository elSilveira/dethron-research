use tron_v2::probe;

#[test]
fn end_to_end_probe_reports_correctness_costs_inheritance_and_privacy() {
    let report = probe::run(3).unwrap();
    assert_eq!(report["correct"], true);
    assert_eq!(report["child_recalled"], true);
    assert_eq!(report["audit_verified"], true);
    assert_eq!(report["cycles"][0]["promoted"], true);
    assert_eq!(report["cycles"][1]["promoted"], false);
    assert!(
        report["baseline_divisions"].as_u64().unwrap()
            > report["evolved_divisions"].as_u64().unwrap()
    );
    assert!(report["evaluation_divisions"].as_u64().unwrap() > 0);
    assert!(
        report["encoding"]["trit_bytes"].as_u64().unwrap()
            < report["encoding"]["two_bit_bytes"].as_u64().unwrap()
    );
    assert_eq!(report["encoding"]["roundtrip"], true);
    assert!(report["encoding"]["trit_encode_ns"].is_u64());
    assert!(report["encoding"]["two_bit_encode_ns"].is_u64());
    assert_eq!(report["compute_type"], "classical_binary_hardware");
}

#[test]
fn autonomous_cycles_are_bounded() {
    assert!(probe::run(0).is_err());
    assert!(probe::run(101).is_err());
}
