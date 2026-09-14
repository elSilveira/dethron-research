use serde_json::Value;

// Host authentication belongs to SSH; a remote PID is not a local child PID.
pub fn ready_remote(message: &Value) -> Result<(), String> {
    let pid = message["pid"]
        .as_u64()
        .and_then(|p| u32::try_from(p).ok())
        .filter(|p| *p > 0)
        .ok_or("Invalid remote worker pid")?;
    ready(message, pid)
}

pub fn ready(message: &Value, pid: u32) -> Result<(), String> {
    let data = &message["data"];
    if message["schema"] != 1
        || message["kind"] != "ready"
        || (message["pid"] != pid && message["parent_pid"] != pid)
        || data["simulated"] != false
        || data["load_count"] != 1
        || data["checkpoint"]["model_type"] != "qwen2"
    {
        return Err("Worker did not identify a real resident Qwen2 model".into());
    }
    for name in [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "model.safetensors",
    ] {
        let file = &data["checkpoint"]["files"][name];
        let hash = file["sha256"].as_str().unwrap_or("");
        if hash.len() != 64
            || !hash.bytes().all(|c| c.is_ascii_hexdigit())
            || file["bytes"].as_u64().unwrap_or(0) == 0
        {
            return Err("Missing checkpoint fingerprint".into());
        }
    }
    Ok(())
}

pub fn response(message: &Value, request: &Value, sequence: u64, pid: u32) -> Result<(), String> {
    if message["schema"] != 1
        || message["pid"] != pid
        || message["sequence"] != sequence
        || message["id"] != request["id"]
        || message["kind"] != "result"
    {
        return Err(format!(
            "Invalid or failed worker reply: {}",
            message["error"]
        ));
    }
    let data = &message["data"];
    let outputs = data["outputs"].as_array().ok_or("Missing neural outputs")?;
    if outputs.len()
        != request["prompts"]
            .as_array()
            .ok_or("Missing prompts")?
            .len()
        || data["evaluated_tokens"].as_u64().unwrap_or(0) == 0
        || !data["seconds"]
            .as_f64()
            .is_some_and(|s| s.is_finite() && s >= 0.0)
    {
        return Err("Missing or inconsistent neural measurements".into());
    }
    for output in outputs {
        if request["op"] == "rank" {
            let choices = request["candidates"]
                .as_array()
                .ok_or("Missing candidates")?;
            let scores = output["scores"].as_array().ok_or("Missing scores")?;
            if !choices.contains(&output["selected"])
                || scores.len() != choices.len()
                || scores
                    .iter()
                    .any(|s| !s.as_f64().is_some_and(f64::is_finite))
            {
                return Err("Inconsistent candidate result".into());
            }
        } else {
            let tokens = output["token_ids"]
                .as_array()
                .ok_or("Missing generated tokens")?;
            if output["generated_tokens"].as_u64() != Some(tokens.len() as u64)
                || tokens.is_empty()
                || output["text"].as_str().is_none()
            {
                return Err("Missing generation evidence".into());
            }
        }
    }
    Ok(())
}
