use serde_json::{json, Value};
use std::sync::{
    atomic::{AtomicUsize, Ordering},
    Arc, Mutex,
};
use std::time::Duration;
use tron_window::network::{run, Limits, Task, Worker};

struct Probe {
    active: Arc<AtomicUsize>,
    peak: Arc<AtomicUsize>,
    prompts: Arc<Mutex<Vec<String>>>,
}
impl Worker for Probe {
    fn metadata(&self) -> Value {
        json!({"simulated":true})
    }
    fn execute(&mut self, request: Value) -> Result<Value, String> {
        let prompt = request["prompts"][0].as_str().unwrap().to_string();
        self.prompts.lock().unwrap().push(prompt.clone());
        let active = self.active.fetch_add(1, Ordering::SeqCst) + 1;
        self.peak.fetch_max(active, Ordering::SeqCst);
        std::thread::sleep(Duration::from_millis(30));
        self.active.fetch_sub(1, Ordering::SeqCst);
        if prompt.contains("FAIL") {
            return Err("fixture failure".into());
        }
        Ok(json!({"data":{"outputs":[{"selected":" A"}],"evaluated_tokens":8}}))
    }
}
type Fixture = (
    Vec<Box<dyn Worker>>,
    Arc<AtomicUsize>,
    Arc<Mutex<Vec<String>>>,
);
fn workers() -> Fixture {
    let active = Arc::new(AtomicUsize::new(0));
    let peak = Arc::new(AtomicUsize::new(0));
    let prompts = Arc::new(Mutex::new(Vec::new()));
    let workers = (0..2)
        .map(|_| {
            Box::new(Probe {
                active: active.clone(),
                peak: peak.clone(),
                prompts: prompts.clone(),
            }) as Box<dyn Worker>
        })
        .collect();
    (workers, peak, prompts)
}
fn task(id: &str, parents: &[&str]) -> Task {
    Task {
        id: id.into(),
        context: "session-1".into(),
        revision: 1,
        parents: parents.iter().map(|s| s.to_string()).collect(),
        prompt: format!("Question {id}"),
        candidates: vec![" A".into(), " B".into()],
        max_new_tokens: 16,
        dna: None,
    }
}

#[test]
fn independent_tasks_overlap_and_each_executes_once() {
    let (mut workers, peak, prompts) = workers();
    let tasks: Vec<_> = (0..6).map(|i| task(&i.to_string(), &[])).collect();
    let report = run(&mut workers, &tasks, Limits::default()).unwrap();
    assert_eq!(peak.load(Ordering::SeqCst), 2);
    assert_eq!(prompts.lock().unwrap().len(), 6);
    assert_eq!(report["completed"], 6);
    assert_eq!(report["evaluated_tokens"], 48);
    assert_eq!(report["max_in_flight"], 2);
}

#[test]
fn waves_forward_parent_results_with_lineage_and_no_unrelated_context() {
    let (mut workers, _, prompts) = workers();
    let tasks = vec![
        task("left", &[]),
        task("right", &[]),
        task("join", &["left", "right"]),
    ];
    let report = run(&mut workers, &tasks, Limits::default()).unwrap();
    let records = report["records"].as_array().unwrap();
    assert_eq!(records[2]["wave"], 1);
    assert_eq!(records[2]["packet"]["parents"][0]["id"], "left");
    assert_eq!(records[2]["packet"]["parents"][0]["output"], "A");
    let last = prompts.lock().unwrap().last().unwrap().clone();
    assert!(last.contains("left") && last.contains("right"));
    assert!(last.contains("A"));
}

#[test]
fn rejects_cycles_missing_parents_duplicate_ids_and_context_revision_crossing() {
    let invalid = vec![
        vec![task("a", &["b"]), task("b", &["a"])],
        vec![task("a", &["missing"])],
        vec![task("a", &[]), task("a", &[])],
        {
            let mut b = task("b", &["a"]);
            b.context = "other".into();
            vec![task("a", &[]), b]
        },
        {
            let mut b = task("b", &["a"]);
            b.revision = 2;
            vec![task("a", &[]), b]
        },
    ];
    for tasks in invalid {
        let (mut workers, _, prompts) = workers();
        assert!(run(&mut workers, &tasks, Limits::default()).is_err());
        assert!(prompts.lock().unwrap().is_empty());
    }
}

#[test]
fn failure_blocks_descendants_but_independent_work_finishes() {
    let (mut workers, _, _) = workers();
    let report = run(
        &mut workers,
        &[task("FAIL", &[]), task("child", &["FAIL"]), task("ok", &[])],
        Limits::default(),
    )
    .unwrap();
    assert_eq!(report["completed"], 1);
    assert_eq!(report["failed"], 1);
    assert_eq!(report["blocked"], 1);
    assert_eq!(report["records"][1]["status"], "blocked");
}

#[test]
fn budget_and_packet_limits_prevent_unbounded_work_without_truncating() {
    let (mut workers, _, prompts) = workers();
    let limits = Limits {
        token_budget: 1,
        ..Limits::default()
    };
    let report = run(&mut workers, &[task("a", &[])], limits).unwrap();
    assert_eq!(report["blocked"], 1);
    assert!(prompts.lock().unwrap().is_empty());
    let limits = Limits {
        packet_bytes: 8,
        ..Limits::default()
    };
    let report = run(&mut workers, &[task("a", &[])], limits).unwrap();
    assert_eq!(report["failed"], 1);
    assert!(prompts.lock().unwrap().is_empty());
}
