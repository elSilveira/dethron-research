use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
};
use tron_v2::network::{config, run_persistent, Limits, Worker};

struct Counter(Arc<AtomicUsize>);
impl Worker for Counter {
    fn metadata(&self) -> Value {
        json!({"backend":"fixture-v1"})
    }
    fn execute(&mut self, _: Value) -> Result<Value, String> {
        self.0.fetch_add(1, Ordering::SeqCst);
        Ok(json!({"data":{"outputs":[{"selected":" B"}],"evaluated_tokens":8}}))
    }
}
fn folder() -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "tron-persist-{}",
        tron_v2::crypto::hash(&tron_v2::crypto::random::<32>())
    ));
    std::fs::create_dir(&path).unwrap();
    path
}
fn tasks() -> Vec<tron_v2::network::Task> {
    [json!({"id":"a","context":"c","revision":1,"prompt":"Answer","candidates":[" A"," B"]}),
     json!({"id":"b","context":"c","revision":1,"parents":["a"],"prompt":"Answer","candidates":[" A"," B"]})]
        .iter().map(config::task).collect::<Result<_,_>>().unwrap()
}
#[test]
fn completed_execution_recovers_without_repeating_inference() {
    let path = folder();
    let calls = Arc::new(AtomicUsize::new(0));
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Counter(calls.clone()))];
    let first = run_persistent(
        &mut workers,
        &tasks(),
        Limits::default(),
        &path,
        &[7; 32],
        "model-v1",
    )
    .unwrap();
    assert_eq!(first["completed"], 2);
    let second = run_persistent(
        &mut workers,
        &tasks(),
        Limits::default(),
        &path,
        &[7; 32],
        "model-v1",
    )
    .unwrap();
    assert_eq!(calls.load(Ordering::SeqCst), 2);
    assert_eq!(second["completed"], 2);
    assert_eq!(second["charged_tokens"], 16);
    assert_eq!(second["recovered_records"], 2);
    std::fs::remove_dir_all(path).unwrap();
}
#[test]
fn wrong_key_changed_plan_backend_and_corrupted_latest_checkpoint_fail_closed() {
    let path = folder();
    let calls = Arc::new(AtomicUsize::new(0));
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Counter(calls.clone()))];
    run_persistent(
        &mut workers,
        &tasks(),
        Limits::default(),
        &path,
        &[7; 32],
        "model-v1",
    )
    .unwrap();
    assert!(run_persistent(
        &mut workers,
        &tasks(),
        Limits::default(),
        &path,
        &[8; 32],
        "model-v1"
    )
    .is_err());
    assert!(run_persistent(
        &mut workers,
        &tasks(),
        Limits::default(),
        &path,
        &[7; 32],
        "model-v2"
    )
    .is_err());
    let mut changed = tasks();
    changed[0].prompt = "different".into();
    assert!(run_persistent(
        &mut workers,
        &changed,
        Limits::default(),
        &path,
        &[7; 32],
        "model-v1"
    )
    .is_err());
    let latest = std::fs::read_dir(&path)
        .unwrap()
        .map(|e| e.unwrap().path())
        .max()
        .unwrap();
    std::fs::write(latest, b"broken").unwrap();
    assert!(run_persistent(
        &mut workers,
        &tasks(),
        Limits::default(),
        &path,
        &[7; 32],
        "model-v1"
    )
    .is_err());
    assert_eq!(calls.load(Ordering::SeqCst), 2);
    std::fs::remove_dir_all(path).unwrap();
}

struct CrashOnSecond(usize);
fn crash_tasks() -> Vec<tron_v2::network::Task> {
    let mut plan = tasks();
    plan.push(
        config::task(&json!({"id":"c","context":"c","revision":1,
        "parents":["b"],"prompt":"Answer","candidates":[" A"," B"]}))
        .unwrap(),
    );
    plan
}
impl Worker for CrashOnSecond {
    fn metadata(&self) -> Value {
        json!({"backend":"fixture-v1"})
    }
    fn execute(&mut self, _: Value) -> Result<Value, String> {
        self.0 += 1;
        if self.0 == 2 {
            std::process::exit(73);
        }
        Ok(json!({"data":{"outputs":[{"selected":" B"}],"evaluated_tokens":8}}))
    }
}
#[test]
fn crash_child() {
    let Ok(path) = std::env::var("TRON_CRASH_PROBE") else {
        return;
    };
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(CrashOnSecond(0))];
    run_persistent(
        &mut workers,
        &crash_tasks(),
        Limits::default(),
        &PathBuf::from(path),
        &[7; 32],
        "model-v1",
    )
    .unwrap();
    panic!("Crash injection did not fire");
}
#[test]
fn process_death_preserves_completed_work_and_marks_inflight_work_uncertain() {
    let path = folder();
    let output = std::process::Command::new(std::env::current_exe().unwrap())
        .args(["--exact", "crash_child", "--nocapture"])
        .env("TRON_CRASH_PROBE", &path)
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(73));
    let calls = Arc::new(AtomicUsize::new(0));
    let mut workers: Vec<Box<dyn Worker>> = vec![Box::new(Counter(calls.clone()))];
    let recovered = run_persistent(
        &mut workers,
        &crash_tasks(),
        Limits::default(),
        &path,
        &[7; 32],
        "model-v1",
    )
    .unwrap();
    assert_eq!(recovered["completed"], 1);
    assert_eq!(recovered["failed"], 1);
    assert_eq!(recovered["blocked"], 1);
    assert_eq!(recovered["records"][0]["output"], "B");
    assert_eq!(recovered["records"][1]["recovery"], "indeterminate");
    assert_eq!(recovered["charged_tokens"], 8 + tasks()[1].reservation());
    assert_eq!(calls.load(Ordering::SeqCst), 0);
    std::fs::remove_dir_all(path).unwrap();
}
