use super::{Limits, Task};
use crate::crypto;
use serde_json::{json, Value};
use std::{
    collections::HashMap,
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
};

pub struct Journal {
    directory: PathBuf,
    key: [u8; 32],
    plan: String,
    sequence: u64,
    head: String,
    pub state: Value,
}
impl Drop for Journal {
    fn drop(&mut self) {
        self.key.fill(0);
    }
}
impl Journal {
    pub fn open(
        path: &Path,
        key: &[u8; 32],
        tasks: &[Task],
        limits: Limits,
        backend: &str,
    ) -> Result<Self, String> {
        if backend.is_empty() || backend.len() > 256 {
            return Err("Backend revision is required".into());
        }
        let plan = json!({"schema":1,"backend":backend,"budget":limits.token_budget,"packet_bytes":limits.packet_bytes,
            "tasks":tasks.iter().map(|t| json!({"id":t.id,"context":t.context,"revision":t.revision,
                "parents":t.parents,"prompt":t.prompt,"candidates":t.candidates,"max_new_tokens":t.max_new_tokens,
                "dna":t.dna.as_ref().map(|d| d.value())})).collect::<Vec<_>>()});
        let plan = crypto::hash(plan.to_string().as_bytes());
        fs::create_dir_all(path).map_err(|e| e.to_string())?;
        let mut files: Vec<_> = fs::read_dir(path)
            .map_err(|e| e.to_string())?
            .map(|e| e.map(|e| e.path()).map_err(|e| e.to_string()))
            .collect::<Result<_, _>>()?;
        files.sort();
        if files.len() > 300 {
            return Err("Journal capacity exceeded".into());
        }
        let mut journal = Self {
            directory: path.into(),
            key: *key,
            plan,
            sequence: 0,
            head: String::new(),
            state: Value::Null,
        };
        for file in files {
            let expected = format!("{:06}.checkpoint", journal.sequence);
            if file.file_name().and_then(|n| n.to_str()) != Some(expected.as_str()) {
                return Err("Journal has missing, unexpected or out-of-order files".into());
            }
            if fs::metadata(&file).map_err(|e| e.to_string())?.len() > 16_777_216 {
                return Err("Checkpoint too large".into());
            }
            let bytes = fs::read(&file).map_err(|e| e.to_string())?;
            let plain = crypto::open(key, journal.plan.as_bytes(), &bytes)?;
            let state: Value = serde_json::from_slice(&plain).map_err(|e| e.to_string())?;
            if state["sequence"] != journal.sequence || state["previous"] != journal.head {
                return Err("Broken journal chain".into());
            }
            journal.head = crypto::hash(&bytes);
            journal.sequence += 1;
            journal.state = state;
        }
        Ok(journal)
    }
    pub fn save(
        &mut self,
        records: &HashMap<String, Value>,
        spent: u64,
        tokens: u64,
        pending: &[String],
        next_wave: usize,
    ) -> Result<(), String> {
        if self.sequence >= 300 {
            return Err("Journal capacity exceeded".into());
        }
        let state = json!({"schema":1,"sequence":self.sequence,"previous":self.head,
            "records":records,"spent":spent,"tokens":tokens,"pending":pending,"next_wave":next_wave});
        let plain = state.to_string();
        if plain.len() > 16_777_000 {
            return Err("Checkpoint too large".into());
        }
        let bytes = crypto::seal(&self.key, self.plan.as_bytes(), plain.as_bytes())?;
        let path = self
            .directory
            .join(format!("{:06}.checkpoint", self.sequence));
        // Exclusive creation arbitrates competing coordinators before any dispatch.
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .map_err(|e| e.to_string())?;
        file.write_all(&bytes)
            .and_then(|_| file.sync_all())
            .map_err(|e| e.to_string())?;
        self.head = crypto::hash(&bytes);
        self.sequence += 1;
        self.state = state;
        Ok(())
    }
    pub fn head(&self) -> &str {
        &self.head
    }
}
