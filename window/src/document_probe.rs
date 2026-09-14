use serde_json::{json, Value};
use std::{collections::BTreeSet, time::Instant};
use tron_v2::network::{dna::Dna, reconstruction::reconstruct, Worker};

pub fn assess_generation(output: &Value, dna: &Value) -> Value {
    let raw = output["text"].as_str().unwrap_or("");
    let final_text = raw
        .rsplit_once("</think>")
        .map_or(raw, |(_, text)| text)
        .trim();
    let json_text = final_text
        .strip_prefix("```json")
        .and_then(|text| text.strip_suffix("```"))
        .unwrap_or(final_text)
        .trim();
    let parsed: Value = serde_json::from_str(json_text).unwrap_or(Value::Null);
    let answer = parsed["answer"].as_str();
    let citations: BTreeSet<_> = parsed["citations"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(Value::as_str)
        .collect();
    let allowed: BTreeSet<_> = dna["source_ids"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(Value::as_str)
        .collect();
    let complete_route = dna["routes"].as_array().map_or_else(
        || allowed.is_subset(&citations),
        |routes| {
            routes.iter().any(|r| {
                r["issue"].is_null()
                    && r["conclusion"] == dna["conclusion"]
                    && r["source_ids"].as_array().is_some_and(|ids| {
                        ids.iter()
                            .all(|id| id.as_str().is_some_and(|s| citations.contains(s)))
                    })
            })
        },
    );
    let format_ok = answer.is_some()
        && parsed["citations"]
            .as_array()
            .is_some_and(|a| a.iter().all(Value::is_string));
    let grounded = dna["state"] == "accepted"
        && answer == dna["conclusion"].as_str()
        && complete_route
        && citations.is_subset(&allowed);
    let abstained =
        dna["state"] == "abstained" && answer == Some("UNKNOWN") && citations.is_empty();
    json!({"answer":answer,"citations":citations,"format_ok":format_ok,
        "parser":"final_json_after_think_v2","scope":"Only final answer and citations; reasoning prose is not certified",
        "accepted":format_ok && output["finish_reason"]=="eos" && grounded,
        "valid_abstention":format_ok && output["finish_reason"]=="eos" && abstained})
}
pub fn execute(worker: &mut dyn Worker, case: &Value) -> Result<Value, String> {
    let routes: Vec<Dna> = case["routes"]
        .as_array()
        .ok_or("Missing routes")?
        .iter()
        .map(Dna::parse)
        .collect::<Result<_, _>>()?;
    let start = Instant::now();
    let dna = reconstruct(&routes, "document", 1)?;
    let dna_seconds = start.elapsed().as_secs_f64();
    let selected: BTreeSet<String> = routes
        .iter()
        .flat_map(|d| d.recognize("document", 1))
        .map(|s| s.id)
        .collect();
    let excerpt = selected
        .iter()
        .map(|id| format!("[{id}] {}", case["sections"][id].as_str().unwrap_or("")))
        .collect::<Vec<_>>()
        .join("\n\n");
    let mut modes = Vec::new();
    for (name, text) in [
        ("full", case["document"].as_str().ok_or("Missing document")?),
        ("selected", excerpt.as_str()),
    ] {
        let prompt=format!("Read the handbook evidence. Follow the question's relationships. If evidence is missing or contradicts itself, answer UNKNOWN. Return only JSON with keys answer (short name or UNKNOWN) and citations (section IDs supporting the whole reasoning path; empty for UNKNOWN). Do not add explanations.\n\n{text}\n\nQuestion: {}\nJSON answer:",case["question"].as_str().ok_or("Missing question")?);
        let request = json!({"op":"generate","prompts":[prompt],"max_new_tokens":256});
        let start = Instant::now();
        let response = worker.execute(request.clone())?;
        let assessment = assess_generation(&response["data"]["outputs"][0], &dna);
        let answer_correct = assessment["format_ok"] == true
            && assessment["answer"] == case["expected"]
            && response["data"]["outputs"][0]["finish_reason"] == "eos";
        modes.push(json!({"mode":name,"request":request,"response":response,
            "assessment":assessment,"answer_correct":answer_correct,"seconds":start.elapsed().as_secs_f64()}));
    }
    Ok(
        json!({"id":case["id"],"question":case["question"],"expected":case["expected"],
        "document":case["document"],"selected_text":excerpt,"routes":case["routes"],"removed":case["removed"],
        "dna_correct":dna["conclusion"].as_str().unwrap_or("UNKNOWN")==case["expected"].as_str().unwrap_or(""),
        "dna":dna,"dna_seconds":dna_seconds,"modes":modes}),
    )
}
