use crate::crypto::{hash, random};
use ring::signature::{self, Ed25519KeyPair, KeyPair};
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Clone, Serialize, Deserialize)]
pub struct Event {
    pub sequence: usize,
    pub kind: String,
    pub identity: String,
    pub previous: String,
    pub commitment: String,
    pub related: Option<String>,
    pub signature: Vec<u8>,
}

fn encoded<T: Serialize>(value: &T) -> Vec<u8> {
    serde_json::to_vec(value).expect("Serializable audit data")
}

impl Event {
    fn message(&self) -> Vec<u8> {
        encoded(&(
            1,
            self.sequence,
            &self.kind,
            &self.identity,
            &self.previous,
            &self.commitment,
            &self.related,
        ))
    }
    pub fn hash(&self) -> String {
        hash(&encoded(self))
    }
}

pub struct Audit {
    pub(crate) seed: [u8; 32],
    pub(crate) events: Vec<Event>,
    pub(crate) openings: Vec<Value>,
}
impl Audit {
    pub fn new() -> Self {
        Self {
            seed: random(),
            events: vec![],
            openings: vec![],
        }
    }
    fn signer(&self) -> Ed25519KeyPair {
        Ed25519KeyPair::from_seed_unchecked(&self.seed).unwrap()
    }
    pub fn identity(&self) -> String {
        hash(&self.key())
    }
    pub fn append(&mut self, kind: &str, payload: Value, related: Option<String>) {
        let opening = serde_json::json!({"salt": random::<32>(), "payload":payload});
        let mut event = Event {
            sequence: self.events.len(),
            kind: kind.into(),
            identity: self.identity(),
            previous: self.head(),
            commitment: hash(&encoded(&opening)),
            related,
            signature: vec![],
        };
        event.signature = self.signer().sign(&event.message()).as_ref().to_vec();
        self.events.push(event);
        self.openings.push(opening);
    }
    pub fn key(&self) -> Vec<u8> {
        self.signer().public_key().as_ref().to_vec()
    }
    pub fn head(&self) -> String {
        self.events
            .last()
            .map(Event::hash)
            .unwrap_or_else(|| "0".repeat(64))
    }
    pub fn proof(&self) -> Vec<Event> {
        self.events.clone()
    }
    pub fn opening(&self, index: usize) -> Value {
        self.openings[index].clone()
    }
    pub fn check_opening(&self, index: usize, opening: &Value) -> bool {
        self.events
            .get(index)
            .is_some_and(|event| event.commitment == hash(&encoded(opening)))
    }
}

impl Default for Audit {
    fn default() -> Self {
        Self::new()
    }
}

pub fn verify(proof: &[Event], key: &[u8], head: &str) -> Result<(), String> {
    let identity = hash(key);
    let mut previous = "0".repeat(64);
    for (index, event) in proof.iter().enumerate() {
        if event.sequence != index || event.identity != identity || event.previous != previous {
            return Err("Audit ordering/identity mismatch".into());
        }
        signature::UnparsedPublicKey::new(&signature::ED25519, key)
            .verify(&event.message(), &event.signature)
            .map_err(|_| "Invalid signature")?;
        previous = event.hash();
    }
    if previous != head {
        return Err("Audit checkpoint mismatch".into());
    }
    Ok(())
}
