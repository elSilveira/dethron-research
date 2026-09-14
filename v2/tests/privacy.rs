use serde_json::json;
use tron_v2::{
    audit::{verify, Audit},
    crypto::{open, seal},
};

#[test]
fn audit_hides_content_but_verifies_origin_order_and_openings() {
    let mut audit = Audit::new();
    audit.append(
        "birth",
        json!({"secret":"private-customer-knowledge"}),
        None,
    );
    audit.append("learn", json!({"answer":123456}), None);
    let proof = audit.proof();
    verify(&proof, &audit.key(), &audit.head()).unwrap();
    let public = serde_json::to_string(&proof).unwrap();
    assert!(!public.contains("private-customer-knowledge"));
    assert!(!public.contains("123456"));
    assert!(audit.check_opening(1, &audit.opening(1)));
    let mut bad = proof.clone();
    bad[0].kind = "forged".into();
    assert!(verify(&bad, &audit.key(), &audit.head()).is_err());
    assert!(verify(&proof[..1], &audit.key(), &audit.head()).is_err());
    assert!(verify(&proof, &Audit::new().key(), &audit.head()).is_err());
    let mut reverse = proof.clone();
    reverse.reverse();
    assert!(verify(&reverse, &audit.key(), &audit.head()).is_err());
    assert!(!audit.check_opening(1, &json!({"payload":123})));
}

#[test]
fn repeated_secrets_get_distinct_commitments() {
    let mut audit = Audit::new();
    audit.append("learn", json!({"value":1}), None);
    audit.append("learn", json!({"value":1}), None);
    assert_ne!(audit.opening(0), audit.opening(1));
}

#[test]
fn encryption_detects_tampering_wrong_key_context_and_truncation() {
    let secret = b"private-customer-knowledge";
    let encrypted = seal(&[1; 32], b"owner-A", secret).unwrap();
    assert_eq!(open(&[1; 32], b"owner-A", &encrypted).unwrap(), secret);
    assert!(!encrypted.windows(secret.len()).any(|part| part == secret));
    assert_ne!(encrypted, seal(&[1; 32], b"owner-A", secret).unwrap());
    assert!(open(&[2; 32], b"owner-A", &encrypted).is_err());
    assert!(open(&[1; 32], b"owner-B", &encrypted).is_err());
    let mut tampered = encrypted.clone();
    tampered[15] ^= 1;
    assert!(open(&[1; 32], b"owner-A", &tampered).is_err());
    assert!(open(&[1; 32], b"owner-A", &encrypted[..10]).is_err());
}
