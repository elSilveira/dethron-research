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

/// Explicit solver assistance, not a model prediction. No terminal answer is sent.
pub fn evidence_status(dna: &Dna, context: &str, revision: u64) -> (Value, String) {
    let assessment = dna.assess(context, revision, "UNKNOWN", false);
    let sufficient = assessment["issues"].as_array().is_some_and(Vec::is_empty);
    let instruction = if sufficient {
        "Evidence status: SUFFICIENT. Follow the CURRENT source links and answer in query order."
    } else {
        "Evidence status: INSUFFICIENT. A required link is missing, inactive, or contradictory. Return UNKNOWN. Do not guess or infer a negative fact from absence."
    };
    (
        json!({"sufficient":sufficient,"issues":assessment["issues"],
        "origin":"deterministic DNA path validation; not model reasoning"}),
        instruction.into(),
    )
}

pub fn decision(packet: &Value, assessment: &Value, raw: &str) -> Value {
    if packet.get("evidence_status").is_none() {
        return Value::Null;
    }
    // Derive from the actual verifier result, not a caller's claimed status.
    let insufficient = assessment["issues"]
        .as_array()
        .is_some_and(|v| !v.is_empty());
    if insufficient && assessment["state"] != "truncated" {
        json!({"state":"abstained","output":"UNKNOWN","origin":"dna_sufficiency_gate",
            "raw_model_state":assessment["state"],"issues":assessment["issues"]})
    } else if assessment["state"] == "accepted" {
        json!({"state":"accepted","output":raw,"origin":"verified_model_answer"})
    } else {
        json!({"state":"rejected","output":null,"origin":"verification_gate"})
    }
}
