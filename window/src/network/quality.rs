use super::dna::Dna;
use serde_json::{json, Value};
use std::collections::BTreeMap;

pub fn inherit(dna: Option<&Dna>, parents: &[Value]) -> Result<Option<Dna>, String> {
    let Some(dna) = dna else { return Ok(None) };
    let mut sources = BTreeMap::new();
    for value in std::iter::once(dna.value()).chain(parents.iter().map(|p| p["dna"].clone())) {
        if let Some(items) = value["sources"].as_array() {
            for source in items {
                let id = source["id"]
                    .as_str()
                    .ok_or("Missing source identity")?
                    .to_string();
                if let Some(previous) = sources.insert(id, source.clone()) {
                    if previous != *source {
                        return Err("Source identity was rewritten across waves".into());
                    }
                }
            }
        }
    }
    let mut value = dna.value();
    value["sources"] = json!(sources.into_values().collect::<Vec<_>>());
    Dna::parse(&value).map(Some)
}
pub fn usable(parent: &Value, protected: bool) -> bool {
    parent["status"] == "completed"
        && match parent["assessment"]["state"].as_str() {
            Some("accepted") => true,
            Some("unverified") => !protected,
            _ => false,
        }
}
pub fn assess(packet: &Value, response: &Value, raw: &str, generation: bool) -> Value {
    let finish = &response["data"]["outputs"][0]["finish_reason"];
    let truncated = generation && finish != "eos";
    let mut assessment = if packet["dna"].is_object() {
        match Dna::parse(&packet["dna"]) {
            Ok(dna) => dna.assess(
                packet["context"].as_str().unwrap(),
                packet["revision"].as_u64().unwrap(),
                raw,
                truncated,
            ),
            Err(error) => json!({"state":"rejected","error":error,"accepted_output":null}),
        }
    } else {
        json!({"state":if truncated {"truncated"} else {"unverified"},"accepted_output":null})
    };
    assessment["finish_reason"] = finish.clone();
    assessment
}
pub fn evidence(dna: &Dna, context: &str, revision: u64) -> String {
    let mut lines = Vec::new();
    for source in &dna.sources {
        let sentence = match source.relation.as_str() {
            "stored_at" => format!(
                "Parcel {} is stored in locker {}.",
                source.entity, source.target
            ),
            "assigned_to" => format!("Locker {} is assigned to {}.", source.entity, source.target),
            _ => format!("{} {} {}.", source.entity, source.relation, source.target),
        };
        lines.push(format!(
            "[{}; {}] {sentence}",
            source.id,
            if source.active(context, revision) {
                "CURRENT"
            } else {
                "INACTIVE: do not use"
            }
        ));
    }
    if lines.is_empty() {
        "No eligible evidence.".into()
    } else {
        lines.join("\n")
    }
}
