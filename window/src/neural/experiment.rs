use super::{
    client::Client,
    controller::{Controller, Policy},
    memory::{Memory, Tier},
};
use serde_json::{json, Value};

fn memories() -> Result<Memory, String> {
    let mut memory = Memory::default();
    for context in 1..=2 {
        for index in 0..8 {
            memory.put(
                context,
                &format!("p{index}"),
                "stored_at",
                &format!("l{index}"),
                Tier::Long,
            )?;
            let owner = ["A", "B", "C", "D"][(index + context as usize - 1) % 4];
            memory.put(
                context,
                &format!("l{index}"),
                "assigned_to",
                owner,
                Tier::Long,
            )?;
        }
    }
    memory.put(1, "temporary", "stored_at", "l0", Tier::Short)?;
    Ok(memory)
}

pub fn run(client: &mut Client) -> Result<Vec<Value>, String> {
    let initial = memories()?;
    let mut runs = Vec::new();
    for policy in [Policy::Indexed, Policy::Adaptive, Policy::Full] {
        let mut controller = Controller::new(policy, initial.clone());
        let mut cases = Vec::new();
        for stage in 0..4 {
            if stage == 2 {
                controller
                    .memory
                    .put(1, "l0", "assigned_to", "D", Tier::Long)?;
                controller.paths.lose_nodes();
            }
            if stage == 3 {
                controller.memory.forget(Tier::Short);
            }
            let count = if stage < 2 {
                8
            } else if stage == 2 {
                4
            } else {
                2
            };
            for index in 0..count {
                let context = if stage == 1 { 2 } else { 1 };
                let entity = if stage == 3 {
                    ["temporary", "never-seen"][index].to_string()
                } else if stage == 0 && index == 0 {
                    "temporary".to_string()
                } else {
                    format!("p{index}")
                };
                let expected = if stage == 3 {
                    "UNKNOWN"
                } else if stage == 2 && index == 0 {
                    "D"
                } else {
                    ["A", "B", "C", "D"][(index + context as usize - 1) % 4]
                };
                let mut result = controller.answer(client, context, &entity)?;
                let correct = result["prediction"] == expected;
                controller.feedback(correct)?;
                result["stage"] = json!(
                    [
                        "new_entities",
                        "context_shift",
                        "revision_and_reconstruction",
                        "unreachable_memory"
                    ][stage]
                );
                result["expected"] = json!(expected);
                result["correct"] = json!(correct);
                result["neural_correct"] = json!(result["raw_neural_prediction"] == expected);
                cases.push(result);
            }
        }
        let correct = cases.iter().filter(|c| c["correct"] == true).count();
        let neural_correct = cases.iter().filter(|c| c["neural_correct"] == true).count();
        let tokens: u64 = cases
            .iter()
            .map(|c| c["neural"]["data"]["evaluated_tokens"].as_u64().unwrap())
            .sum();
        let seconds: f64 = cases
            .iter()
            .map(|c| c["wall_seconds"].as_f64().unwrap())
            .sum();
        runs.push(
            json!({"policy":format!("{policy:?}"),"correct":correct,"neural_correct":neural_correct,"attempted":cases.len(),
            "evaluated_tokens":tokens,"wall_seconds":seconds,"budget_limit":1_000_000,
            "spent_units":1_000_000-controller.budget.remaining(),"cases":cases}),
        );
    }
    Ok(runs)
}
