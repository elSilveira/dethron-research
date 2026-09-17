use super::check;
use serde_json::{json, Value};
use tron_v2::{crypto::random, tron::Tron};

// Independent result check: product and primality, not the production factorizer.
fn correct(number: u64, factors: &[u64]) -> bool {
    factors.iter().try_fold(1u64, |a, b| a.checked_mul(*b)) == Some(number)
        && factors
            .iter()
            .all(|&p| p >= 2 && (2..p).take_while(|d| d * d <= p).all(|d| p % d != 0))
}

pub fn run(seed: u64, checks: &mut Vec<Value>) -> Result<Value, String> {
    let number = 2 + seed % 9000;
    let mut tron = Tron::new(0);
    let first = tron.run(number, 1_000_000)?;
    checks.push(check(
        "computed_correctly",
        json!(true),
        json!(!first.cached && correct(number, &first.work.factors)),
    ));
    let short = tron.run(number, 1_000_000)?;
    checks.push(check(
        "short_recall",
        json!(true),
        json!(short.cached && correct(number, &short.work.factors)),
    ));
    for offset in 1..=20 {
        tron.run(number + offset, 1_000_000)?;
    }
    let medium = tron.run(number, 1_000_000)?;
    checks.push(check(
        "interference_recall",
        json!(true),
        json!(medium.cached && correct(number, &medium.work.factors)),
    ));
    let key = random();
    let snapshot = tron.checkpoint(&key)?;
    let identity = tron.audit.key();
    let head = tron.audit.head();
    drop(tron);
    let mut restored = Tron::restore(&snapshot, &key, &identity, &head)?;
    let long = restored.run(number, 1_000_000)?;
    checks.push(check(
        "snapshot_restore",
        json!(true),
        json!(long.cached && correct(number, &long.work.factors)),
    ));
    let mut tampered = snapshot.clone();
    let last = tampered.len() - 1;
    tampered[last] ^= 1;
    checks.push(check(
        "snapshot_tamper_rejected",
        json!(true),
        json!(Tron::restore(&tampered, &key, &identity, &head).is_err()),
    ));
    // The current bounded map evicts the lowest numeric key, not the oldest access.
    for offset in 21..=129 {
        restored.run(number + offset, 1_000_000)?;
    }
    let pressured = restored.run(number, 1_000_000)?;
    checks.push(check(
        "capacity_correctness",
        json!(true),
        json!(correct(number, &pressured.work.factors) && restored.knowledge_len() <= 128),
    ));
    Ok(json!({"input":number,"initial_cached":first.cached,
        "cached_after_capacity_pressure":pressured.cached,"knowledge_entries":restored.knowledge_len(),
        "snapshot_bytes":snapshot.len(),"restore_scope":"same-process deserialize after dropping original"}))
}
