#[test]
fn journal_numbers_survive_json_roundtrip_exactly() {
    let original = serde_json::json!({"service_seconds":0.000010999999999999725_f64});
    let recovered: serde_json::Value = serde_json::from_str(&original.to_string()).unwrap();
    assert_eq!(original, recovered);
}
