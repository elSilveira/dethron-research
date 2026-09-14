use super::super::{graph::Primitive::*, Engine, MemoryTier, Policy, Request};
use serde_json::{json, Value};

fn task(
    engine: &mut Engine,
    events: &mut Vec<Value>,
    input: i64,
    context: u64,
    revised: bool,
    stage: &str,
) -> Result<(), String> {
    let result = engine.submit(Request {
        capability: "calibration",
        context,
        input,
        ingress: 900,
        sink: 901,
    })?;
    let expected = if revised {
        ((input + 3) * 2 + 1).abs() + 4
    } else {
        ((input + 2) * 3 - 1).abs() + 7
    };
    if result.value != expected {
        return Err("Independent result check failed".into());
    }
    let mut event = result.inspect();
    event["input"] = json!(input);
    event["context"] = json!(context);
    event["stage"] = json!(stage);
    event["externally_correct"] = json!(result.value == expected);
    let stats = engine.memory_stats();
    event["memory_counts"] = json!({"short":stats.short,"medium":stats.medium,"long":stats.long});
    events.push(event);
    Ok(())
}

pub fn demonstrate() -> Result<Value, String> {
    let mut engine = Engine::new(Policy::Adaptive, 100_000);
    engine.register(
        "calibration",
        &[Add(2), Multiply(3), Add(-1), Absolute, Add(7)],
    )?;
    let mut events = Vec::new();
    for input in 0..6 {
        task(&mut engine, &mut events, input, 1, false, "learning")?;
    }
    engine.lose_path("calibration")?;
    engine.forget(MemoryTier::Short)?;
    task(&mut engine, &mut events, 921, 1, false, "lost_nodes")?;
    for input in 100..104 {
        task(&mut engine, &mut events, input, 2, false, "new_context")?;
    }
    let learned_state = engine.inspect();
    engine.revise(
        "calibration",
        &[Add(3), Multiply(2), Add(1), Absolute, Add(4)],
    )?;
    for input in 0..2 {
        task(
            &mut engine,
            &mut events,
            input,
            2,
            true,
            "procedure_revision",
        )?;
    }
    engine.inject_shortcut_fault("calibration")?;
    task(
        &mut engine,
        &mut events,
        2,
        2,
        true,
        "injected_shortcut_fault",
    )?;
    for input in 3..8 {
        task(&mut engine, &mut events, input, 2, true, "relearning")?;
    }
    let promoted = events.iter().any(|e| {
        e["events"]
            .as_array()
            .unwrap()
            .iter()
            .any(|v| v == "promoted")
    });
    let reopened = events.iter().any(|e| {
        e["events"]
            .as_array()
            .unwrap()
            .iter()
            .any(|v| v == "reopened")
    });
    if !promoted || !reopened {
        return Err("Missing expected mechanism transition".into());
    }
    Ok(
        json!({"schema":1,"mechanism_checks_passed":true,"events":events,
        "learned_state":learned_state,"final_state":engine.inspect(),
        "scope":"bounded integer procedure composition; logical trons, two local shadow threads",
        "limits":"internal agreement is not independent truth; exact reconstruction, no language memory or distributed execution"}),
    )
}
