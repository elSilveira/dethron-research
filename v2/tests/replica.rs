use serde_json::{json, Value};
use std::{fs, path::PathBuf};
use tron_v2::network::{config, replica::ReplicaPlan, run_persistent, Limits, Worker};

struct Fixture;
impl Worker for Fixture {
    fn metadata(&self) -> Value {
        json!({})
    }
    fn execute(&mut self, _: Value) -> Result<Value, String> {
        Ok(json!({"data":{"outputs":[{"selected":" B"}],"evaluated_tokens":8}}))
    }
}
#[test]
fn replicas_restore_after_loss_and_reject_stale_corrupt_or_wrong_identity() {
    let root = std::env::temp_dir().join(format!(
        "tron-replicas-{}",
        tron_v2::crypto::hash(&tron_v2::crypto::random::<32>())
    ));
    fs::create_dir(&root).unwrap();
    let tasks = vec![config::task(&json!({"id":"a","context":"c","revision":1,
        "prompt":"Answer","candidates":[" A"," B"], "dna":{"sources":[{"id":"fact","context":"c","revision":1,"entity":"item","relation":"owner","target":"B","revoked":false}],"queries":[{"entity":"item","relations":["owner"]}]}}))
    .unwrap()];
    let key = [7; 32];
    let plan = ReplicaPlan {
        tasks: &tasks,
        limits: Limits::default(),
        key: &key,
        backend: "fixture",
    };
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Fixture)];
    let original = root.join("original");
    let first = run_persistent(
        &mut workers,
        &tasks,
        Limits::default(),
        &original,
        &key,
        "fixture",
    )
    .unwrap();
    let head = first["checkpoint_head"].as_str().unwrap();
    let good = root.join("good");
    plan.restore(std::slice::from_ref(&original), &good, head)
        .unwrap();
    let stale = root.join("stale");
    plan.restore(std::slice::from_ref(&original), &stale, head)
        .unwrap();
    let latest = fs::read_dir(&stale)
        .unwrap()
        .map(|e| e.unwrap().path())
        .max()
        .unwrap();
    fs::remove_file(latest).unwrap();
    let corrupt = root.join("corrupt");
    plan.restore(std::slice::from_ref(&original), &corrupt, head)
        .unwrap();
    fs::write(corrupt.join("000000.checkpoint"), b"broken").unwrap();
    fs::remove_dir_all(&original).unwrap();
    assert!(plan
        .restore(
            &[stale.clone(), corrupt.clone(), original.clone()],
            &original,
            head
        )
        .is_err());
    assert!(!original.exists());
    assert!(plan
        .restore(std::slice::from_ref(&good), &original, "")
        .is_err());
    let wrong_key = [8; 32];
    let wrong = ReplicaPlan {
        key: &wrong_key,
        ..plan
    };
    assert!(wrong
        .restore(std::slice::from_ref(&good), &original, head)
        .is_err());
    assert!(!original.exists());
    let chosen: PathBuf = plan
        .restore(&[stale, corrupt, good.clone()], &original, head)
        .unwrap();
    assert_eq!(chosen, good);
    assert!(plan.restore(&[good], &original, head).is_err());
    struct NoInference;
    impl Worker for NoInference {
        fn metadata(&self) -> Value {
            json!({})
        }
        fn execute(&mut self, _: Value) -> Result<Value, String> {
            panic!("must recover")
        }
    }
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(NoInference)];
    let recovered = run_persistent(
        &mut workers,
        &tasks,
        Limits::default(),
        &original,
        &key,
        "fixture",
    )
    .unwrap();
    assert_eq!(recovered["recovered_records"], 1);
    assert_eq!(recovered["records"][0]["assessment"]["state"], "accepted");
    assert_eq!(recovered["records"], first["records"]);
    assert_eq!(recovered["charged_tokens"], first["charged_tokens"]);
    fs::remove_dir_all(root).unwrap();
}
