use super::{
    dispatch::{execute as dispatch, Job},
    journal::Journal,
    outcome::outcome,
    packet, quality, recovery, Limits, Task, Worker,
};
use serde_json::{json, Value};
use std::time::Instant;

pub fn run(
    workers: &mut [Box<dyn Worker>],
    tasks: &[Task],
    limits: Limits,
) -> Result<Value, String> {
    execute(workers, tasks, limits, None)
}

pub fn run_persistent(
    workers: &mut [Box<dyn Worker>],
    tasks: &[Task],
    limits: Limits,
    directory: &std::path::Path,
    key: &[u8; 32],
    backend_revision: &str,
) -> Result<Value, String> {
    packet::validate(tasks, workers.len(), limits)?;
    let mut journal = Journal::open(directory, key, tasks, limits, backend_revision)?;
    let mut report = execute(workers, tasks, limits, Some(&mut journal))?;
    report["checkpoint_head"] = json!(journal.head());
    Ok(report)
}

fn execute(
    workers: &mut [Box<dyn Worker>],
    tasks: &[Task],
    limits: Limits,
    mut journal: Option<&mut Journal>,
) -> Result<Value, String> {
    packet::validate(tasks, workers.len(), limits)?;
    let origin = Instant::now();
    let recovered = recovery::restore(&mut journal, tasks)?;
    let recovered_records = recovered.records.len();
    let mut records = recovered.records;
    let (mut spent, mut tokens, mut max_in_flight) = (recovered.spent, recovered.tokens, 0);
    for wave in recovered.wave..32 {
        if records.len() == tasks.len() {
            break;
        }

        let ready: Vec<_> = tasks
            .iter()
            .enumerate()
            .filter(|(_, t)| {
                !records.contains_key(&t.id) && t.parents.iter().all(|p| records.contains_key(p))
            })
            .collect();
        let mut jobs = Vec::new();
        let mut reserved = spent;
        for (index, task) in ready {
            let mut record = json!({"id":task.id,"wave":wave,"status":"blocked"});
            if task
                .parents
                .iter()
                .any(|p| !quality::usable(&records[p], task.dna.is_some()))
            {
                record["error"] =
                    json!("Dependency failed, blocked, or lacks an acceptable answer");
            } else if task.reservation() > limits.token_budget.saturating_sub(reserved) {
                record["error"] = json!("Token reservation exceeds remaining budget");
            } else {
                match task.packet(&records, limits.packet_bytes) {
                    Ok((packet, request)) => {
                        reserved += task.reservation();
                        jobs.push(Job {
                            index,
                            packet,
                            request,
                        });
                        continue;
                    }
                    Err(error) => {
                        record["status"] = json!("failed");
                        record["error"] = json!(error);
                    }
                }
            }
            records.insert(task.id.clone(), record);
        }
        let mut pending: Vec<String> = jobs.iter().map(|j| tasks[j.index].id.clone()).collect();
        spent = reserved;
        recovery::save(&mut journal, &records, spent, tokens, &pending, wave + 1)?;
        let (completed, peak) = dispatch(workers, &jobs, origin);
        max_in_flight = max_in_flight.max(peak);
        for completion in completed {
            let job = &jobs[completion.job];
            let task = &tasks[job.index];
            let mut record = json!({"id":task.id,"wave":wave,"worker":completion.worker,
                "packet":job.packet,"request":job.request,"started_seconds":completion.start,
                "finished_seconds":completion.end,"service_seconds":completion.end-completion.start});
            let result = completion
                .response
                .as_ref()
                .map_err(Clone::clone)
                .and_then(|r| outcome(r, task));
            match result {
                Ok((output, count)) => {
                    spent = spent - task.reservation() + count;
                    tokens += count;
                    record["status"] = json!("completed");
                    record["output"] = json!(output);
                    record["response"] = completion.response.unwrap();
                    record["assessment"] = quality::assess(
                        &job.packet,
                        &record["response"],
                        &output,
                        task.candidates.is_empty(),
                    );
                    if job.packet.get("evidence_status").is_some() {
                        record["decision"] =
                            quality::decision(&job.packet, &record["assessment"], &output);
                    }
                }
                Err(error) => {
                    record["status"] = json!("failed");
                    record["error"] = json!(error);
                    record["reserved_failure_tokens"] = json!(task.reservation());
                }
            }
            records.insert(task.id.clone(), record);
            pending.retain(|id| id != &task.id);
            recovery::save(&mut journal, &records, spent, tokens, &pending, wave + 1)?;
        }
        if records.len() == tasks.len() {
            break;
        }
    }
    let seconds = origin.elapsed().as_secs_f64();
    let records: Vec<_> = tasks
        .iter()
        .map(|t| records.remove(&t.id).unwrap())
        .collect();
    let count = |status| records.iter().filter(|r| r["status"] == status).count();
    let completed = count("completed");
    Ok(
        json!({"schema":1,"completed":completed,"failed":count("failed"),"blocked":count("blocked"),
        "recovered_records":recovered_records,"wall_seconds":seconds,"tasks_per_second":completed as f64 / seconds,
        "evaluated_tokens":tokens,"charged_tokens":spent,"token_budget":limits.token_budget,
        "accepted":records.iter().filter(|r| r["assessment"]["state"]=="accepted").count(),
        "max_in_flight":max_in_flight,"workers":workers.iter().map(|w| w.metadata()).collect::<Vec<_>>(),
        "records":records}),
    )
}
