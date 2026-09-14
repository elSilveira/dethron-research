use super::{
    dispatch::{execute, Job},
    packet, quality, Limits, Task, Worker,
};
use serde_json::{json, Value};
use std::{collections::HashMap, time::Instant};

fn outcome(response: &Value, task: &Task) -> Result<(String, u64), String> {
    let data = &response["data"];
    let tokens = data["evaluated_tokens"]
        .as_u64()
        .ok_or("Missing evaluated tokens")?;
    if tokens == 0 || tokens > task.reservation() {
        return Err("Invalid token accounting".into());
    }
    let output = &data["outputs"][0];
    let text = if task.candidates.is_empty() {
        if output["generated_tokens"].as_u64().unwrap_or(0) > task.max_new_tokens as u64 {
            return Err("Generation exceeds limit".into());
        }
        output["text"].as_str().ok_or("Missing generated text")?
    } else {
        let text = output["selected"]
            .as_str()
            .ok_or("Missing selected candidate")?;
        if !task.candidates.iter().any(|c| c == text) {
            return Err("Unknown candidate".into());
        }
        text
    };
    if text.len() > 4096 {
        return Err("Output packet exceeds limit".into());
    }
    Ok((text.trim().into(), tokens))
}

pub fn run(
    workers: &mut [Box<dyn Worker>],
    tasks: &[Task],
    limits: Limits,
) -> Result<Value, String> {
    packet::validate(tasks, workers.len(), limits)?;
    let origin = Instant::now();
    let mut records = HashMap::<String, Value>::new();
    let (mut spent, mut tokens, mut max_in_flight) = (0, 0, 0);
    for wave in 0..32 {
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
        let (completed, peak) = execute(workers, &jobs, origin);
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
                    spent += count;
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
                }
                Err(error) => {
                    spent += task.reservation();
                    record["status"] = json!("failed");
                    record["error"] = json!(error);
                    record["reserved_failure_tokens"] = json!(task.reservation());
                }
            }
            records.insert(task.id.clone(), record);
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
        "wall_seconds":seconds,"tasks_per_second":completed as f64 / seconds,
        "evaluated_tokens":tokens,"charged_tokens":spent,"token_budget":limits.token_budget,
        "accepted":records.iter().filter(|r| r["assessment"]["state"]=="accepted").count(),
        "max_in_flight":max_in_flight,"workers":workers.iter().map(|w| w.metadata()).collect::<Vec<_>>(),
        "records":records}),
    )
}
