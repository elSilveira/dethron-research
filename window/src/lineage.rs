use crate::stream::Stream;
use serde_json::{json, Value};
use tron_v2::{audit::verify, crypto::random, tron::Tron};

pub fn public(tron: &Tron) -> Value {
    json!({"identity":tron.audit.identity(), "public_key":tron.audit.key(),
        "head":tron.audit.head(), "events":tron.audit.proof()})
}

pub fn run(parent: &mut Tron, stream: &mut Stream) -> Result<Value, String> {
    let mut child = parent.spawn(true)?;
    stream.emit(
        "child_created",
        json!({"identity":child.audit.identity(),
        "generation":child.generation(), "knowledge_count":child.knowledge_len(),
        "parent":parent.audit.identity()}),
    )?;
    let key = random();
    let encrypted = child.checkpoint(&key)?;
    let trusted_key = child.audit.key();
    let head = child.audit.head();
    stream.emit("checkpoint", json!({"bytes":encrypted.len()}))?;
    drop(child);
    let mut child = Tron::restore(&encrypted, &key, &trusted_key, &head)?;
    let recalled = child.run(997, 2000)?.cached;
    stream.emit(
        "restored",
        json!({"child_recalled":recalled,
        "identity":child.audit.identity(), "scope":"same-process encrypted restore"}),
    )?;
    for tron in [&*parent, &child] {
        verify(&tron.audit.proof(), &tron.audit.key(), &tron.audit.head())?;
    }
    stream.emit(
        "audit_verified",
        json!({"verified":true,
        "parent":public(parent), "child":public(&child)}),
    )?;
    Ok(json!({"child_recalled":recalled, "audit_verified":true,
        "encrypted_checkpoint_bytes":encrypted.len(),
        "parent":public(parent), "child":public(&child)}))
}
