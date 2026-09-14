use super::Task;
use serde_json::Value;
pub(super) fn outcome(response: &Value, task: &Task) -> Result<(String, u64), String> {
    let data = &response["data"];
    let tokens = data["evaluated_tokens"]
        .as_u64()
        .ok_or("Missing evaluated tokens")?;
    if tokens == 0 || tokens > task.reservation() {
        return Err("Invalid token accounting".into());
    }
    let outputs = data["outputs"].as_array().ok_or("Missing outputs")?;
    if outputs.len() != 1 {
        return Err("Expected exactly one output".into());
    }
    let output = &outputs[0];
    let text = if task.candidates.is_empty() {
        let ids = output["token_ids"]
            .as_array()
            .ok_or("Missing generated token IDs")?;
        if ids.is_empty()
            || ids.len() > task.max_new_tokens
            || ids.iter().any(|id| id.as_u64().is_none())
            || output["generated_tokens"].as_u64() != Some(ids.len() as u64)
            || !matches!(output["finish_reason"].as_str(), Some("eos" | "length"))
        {
            return Err("Invalid generation evidence".into());
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
