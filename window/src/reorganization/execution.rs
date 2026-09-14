use super::{
    graph::Graph,
    model::{Delivery, Request},
};
use crate::budget::{Activity, Budget};
use std::{sync::Barrier, thread};

pub(super) fn run(
    primary: &Graph,
    shadow: Option<&Graph>,
    request: Request<'_>,
    version: u64,
    phase: &'static str,
    budget: &mut Budget,
) -> Result<Delivery, String> {
    let work = primary.recipe.work();
    let validation = shadow.map_or(0, |g| g.recipe.work());
    if budget.remaining() < work + validation {
        return Err("Work budget exhausted".into());
    }
    budget
        .charge(Activity::Execute, work)
        .map_err(|_| "Work budget exhausted")?;
    budget
        .charge(Activity::Validate, validation)
        .map_err(|_| "Work budget exhausted")?;
    let mut workers = Vec::new();
    let (value, consensus) = if let Some(reference) = shadow {
        let barrier = Barrier::new(2);
        let (a, b) = thread::scope(|scope| {
            let left = scope.spawn(|| {
                barrier.wait();
                (
                    primary.recipe.execute(request.input),
                    format!("{:?}", thread::current().id()),
                )
            });
            let right = scope.spawn(|| {
                barrier.wait();
                (
                    reference.recipe.execute(request.input),
                    format!("{:?}", thread::current().id()),
                )
            });
            (left.join(), right.join())
        });
        let (a, left_id) = a.map_err(|_| "Primary worker panicked")?;
        let (b, right_id) = b.map_err(|_| "Validation worker panicked")?;
        workers.extend([left_id, right_id]);
        let (a, b) = (a?, b?);
        (if a == b { a } else { b }, a == b)
    } else {
        workers.push(format!("{:?}", thread::current().id()));
        (primary.recipe.execute(request.input)?, false)
    };
    Ok(Delivery {
        value,
        sink: request.sink,
        version,
        phase,
        primary_nodes: primary.ids.clone(),
        shadow_nodes: shadow.map_or_else(Vec::new, |g| g.ids.clone()),
        workers,
        events: Vec::new(),
        consensus,
    })
}
