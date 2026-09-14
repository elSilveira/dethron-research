use super::Worker;
use serde_json::Value;
use std::{
    sync::atomic::{AtomicUsize, Ordering},
    time::Instant,
};

pub struct Job {
    pub index: usize,
    pub packet: Value,
    pub request: Value,
}
pub struct Completion {
    pub job: usize,
    pub worker: usize,
    pub start: f64,
    pub end: f64,
    pub response: Result<Value, String>,
}

pub fn execute(
    workers: &mut [Box<dyn Worker>],
    jobs: &[Job],
    origin: Instant,
) -> (Vec<Completion>, usize) {
    let next = AtomicUsize::new(0);
    let active = AtomicUsize::new(0);
    let peak = AtomicUsize::new(0);
    let results = std::thread::scope(|scope| {
        let handles: Vec<_> = workers
            .iter_mut()
            .enumerate()
            .map(|(worker, client)| {
                let (next, active, peak) = (&next, &active, &peak);
                scope.spawn(move || {
                    let mut results = Vec::new();
                    loop {
                        let job = next.fetch_add(1, Ordering::SeqCst);
                        if job >= jobs.len() {
                            break;
                        }
                        peak.fetch_max(active.fetch_add(1, Ordering::SeqCst) + 1, Ordering::SeqCst);
                        let start = origin.elapsed().as_secs_f64();
                        let response = client.execute(jobs[job].request.clone());
                        let end = origin.elapsed().as_secs_f64();
                        active.fetch_sub(1, Ordering::SeqCst);
                        results.push(Completion {
                            job,
                            worker,
                            start,
                            end,
                            response,
                        });
                    }
                    results
                })
            })
            .collect();
        handles
            .into_iter()
            .flat_map(|h| h.join().expect("Worker thread panicked"))
            .collect()
    });
    (results, peak.load(Ordering::SeqCst))
}
