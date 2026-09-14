use serde_json::{json, Value};
use std::path::PathBuf;
use tron_v2::network::{run_persistent, Limits, Task, Worker};

pub struct Settings {
    directory: PathBuf,
    key: [u8; 32],
}
impl Drop for Settings {
    fn drop(&mut self) {
        self.key.fill(0);
    }
}
pub fn settings(config: &Value, custom_tasks: bool) -> Result<Option<Settings>, String> {
    let Some(value) = config.get("persistence") else {
        return Ok(None);
    };
    if !custom_tasks {
        return Err("Persistence requires explicit tasks".into());
    }
    let directory = value["directory"]
        .as_str()
        .filter(|s| !s.is_empty())
        .ok_or("Missing checkpoint directory")?;
    let key_file = value["key_file"]
        .as_str()
        .ok_or("Missing external key file")?;
    let bytes = std::fs::read(key_file).map_err(|e| format!("Cannot read key file: {e}"))?;
    let key = bytes
        .try_into()
        .map_err(|_| "Key file must contain exactly 32 binary bytes")?;
    Ok(Some(Settings {
        directory: directory.into(),
        key,
    }))
}
pub fn run(
    workers: &mut [Box<dyn Worker>],
    tasks: &[Task],
    limits: Limits,
    settings: &Settings,
) -> Result<Value, String> {
    let backends: Vec<_>=workers.iter().map(|worker| {
        let metadata=worker.metadata(); let data=&metadata["handshake"]["data"];
        json!({"files":data["checkpoint"]["files"],"torch":data["torch"],"transformers":data["transformers"],
            "device":data["device"],"dtype":data["dtype"]})
    }).collect();
    let revision = tron_v2::crypto::hash(json!(backends).to_string().as_bytes());
    run_persistent(
        workers,
        tasks,
        limits,
        &settings.directory,
        &settings.key,
        &revision,
    )
}
