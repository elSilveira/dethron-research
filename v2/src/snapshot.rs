use crate::{
    audit::{verify, Audit, Event},
    crypto,
    task::factorize,
    trit::Trit,
    tron::{State, Tron},
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

const CONTEXT: &[u8] = b"tron-v2-encrypted-snapshot-v1";
const MAX_SNAPSHOT: usize = 16 * 1024 * 1024;

#[derive(Serialize, Deserialize)]
struct Snapshot {
    schema: u8,
    state: State,
    seed: [u8; 32],
    events: Vec<Event>,
    openings: Vec<Value>,
}

impl Tron {
    pub fn checkpoint(&mut self, key: &[u8; 32]) -> Result<Vec<u8>, String> {
        if self.audit.events.len() >= 10_000 {
            return Err("Audit capacity reached".into());
        }
        self.audit.append("checkpoint", json!(&self.state), None);
        let snapshot = Snapshot {
            schema: 1,
            state: self.state.clone(),
            seed: self.audit.seed,
            events: self.audit.events.clone(),
            openings: self.audit.openings.clone(),
        };
        let bytes = serde_json::to_vec(&snapshot).map_err(|e| e.to_string())?;
        if bytes.len() > MAX_SNAPSHOT - 28 {
            return Err("Snapshot too large".into());
        }
        crypto::seal(key, CONTEXT, &bytes)
    }
    // Trusted key/head must come from the owner, not the incoming snapshot.
    pub fn restore(
        data: &[u8],
        key: &[u8; 32],
        trusted_key: &[u8],
        head: &str,
    ) -> Result<Self, String> {
        if data.len() > MAX_SNAPSHOT {
            return Err("Snapshot too large".into());
        }
        let bytes = crypto::open(key, CONTEXT, data)?;
        let snapshot: Snapshot = serde_json::from_slice(&bytes).map_err(|e| e.to_string())?;
        if snapshot.schema != 1
            || snapshot.events.is_empty()
            || snapshot.events.len() > 10_000
            || snapshot.events.len() != snapshot.openings.len()
            || snapshot.state.knowledge.len() > 128
        {
            return Err("Invalid snapshot schema/limits".into());
        }
        verify(&snapshot.events, trusted_key, head)?;
        let audit = Audit {
            seed: snapshot.seed,
            events: snapshot.events,
            openings: snapshot.openings,
        };
        if audit.key() != trusted_key {
            return Err("Signing identity mismatch".into());
        }
        for (index, opening) in audit.openings.iter().enumerate() {
            if !audit.check_opening(index, opening) {
                return Err("Private commitment mismatch".into());
            }
        }
        if audit.events.last().unwrap().kind != "checkpoint"
            || audit.openings.last().unwrap()["payload"] != json!(&snapshot.state)
        {
            return Err("State does not match signed checkpoint".into());
        }
        for (number, knowledge) in &snapshot.state.knowledge {
            if factorize(*number, Trit::Plus, 2000)?.factors != knowledge.factors {
                return Err("Invalid inherited knowledge".into());
            }
        }
        Ok(Self {
            audit,
            state: snapshot.state,
        })
    }
}
