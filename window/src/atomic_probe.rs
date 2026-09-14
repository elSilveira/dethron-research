use crate::document_probe::assess_generation;
use serde_json::{json, Value};
use std::{collections::BTreeSet, time::Instant};
use tron_v2::network::{atomic::AtomicDna, dna::Dna, Worker};

pub fn execute(worker: &mut dyn Worker, case: &Value, atomic_first: bool) -> Result<Value, String> {
    let routes: Vec<Dna> = case["routes"]
        .as_array()
        .ok_or("Missing routes")?
        .iter()
        .map(Dna::parse)
        .collect::<Result<_, _>>()?;
    let start = Instant::now();
    let network = AtomicDna::compile(&routes)?;
    let dna = network.reconstruct("document", 1)?;
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
    let atomic_text = network.evidence_text("document", 1);
    let inventory = network.inventory();
    let mut conditions = vec![
        ("selected", excerpt.as_str()),
        ("atomic", atomic_text.as_str()),
    ];
    if atomic_first {
        conditions.reverse();
    }
    let mut modes = Vec::new();
    for (name, text) in conditions {
        let prompt=format!("Read the handbook evidence. Follow the question's relationships. If evidence is missing or contradicts itself, answer UNKNOWN. Return only JSON with keys answer (short name or UNKNOWN) and citations (section IDs supporting the whole reasoning path; empty for UNKNOWN). Do not add explanations.\n\n{text}\n\nQuestion: {}\nJSON answer:",case["question"].as_str().ok_or("Missing question")?);
        let request = json!({"op":"generate","prompts":[prompt],"max_new_tokens":256});
        let start = Instant::now();
        let response = worker.execute(request.clone())?;
        let assessment = assess_generation(&response["data"]["outputs"][0], &dna);
        let correct = assessment["format_ok"] == true
            && assessment["answer"] == case["expected"]
            && response["data"]["outputs"][0]["finish_reason"] == "eos";
        modes.push(
            json!({"mode":name,"request":request,"response":response,"assessment":assessment,
            "answer_correct":correct,"seconds":start.elapsed().as_secs_f64()}),
        );
    }
    Ok(
        json!({"id":case["id"],"question":case["question"],"expected":case["expected"],
        "document":case["document"],"selected_text":excerpt,"atomic_text":atomic_text,"inventory":inventory,
        "bundle_bytes":inventory.to_string().len(),"paragraph_bytes":excerpt.len(),"atomic_text_bytes":atomic_text.len(),
        "routes":case["routes"],"removed":case["removed"],"dna":dna,"dna_seconds":dna_seconds,
        "dna_correct":dna["conclusion"].as_str().unwrap_or("UNKNOWN")==case["expected"].as_str().unwrap_or(""),"modes":modes}),
    )
}
