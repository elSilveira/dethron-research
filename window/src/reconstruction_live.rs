use serde_json::{json, Value};
use std::time::Instant;
use tron_v2::network::{dna::Dna, reconstruction::reconstruct, Worker};

pub struct Case {
    pub id: &'static str,
    pub routes: Vec<Dna>,
    pub expected: &'static str,
}
fn route(entity: &str, branch: &str, answer: &str) -> Dna {
    Dna::parse(&json!({"sources":[
        {"id":format!("{branch}-start"),"context":"live","revision":1,"entity":entity,
         "relation":"via","target":branch,"revoked":false},
        {"id":format!("{branch}-end"),"context":"live","revision":1,"entity":branch,
         "relation":"label","target":answer,"revoked":false}],
        "queries":[{"entity":entity,"relations":["via","label"]}]}))
    .unwrap()
}
pub fn cases(entity: &str) -> Vec<Case> {
    let a = route(entity, "route-a", "Amber");
    let b = route(entity, "route-b", "Amber");
    let mut broken = b.clone();
    broken.sources.pop();
    vec![
        Case {
            id: "intact",
            routes: vec![a.clone(), b.clone()],
            expected: "Amber",
        },
        Case {
            id: "lost_a",
            routes: vec![b],
            expected: "Amber",
        },
        Case {
            id: "lost_essential",
            routes: vec![broken],
            expected: "UNKNOWN",
        },
        Case {
            id: "conflict",
            routes: vec![a, route(entity, "route-b", "Violet")],
            expected: "UNKNOWN",
        },
    ]
}
pub fn execute_case(worker: &mut dyn Worker, case: Case) -> Result<Value, String> {
    let start = Instant::now();
    let dna = reconstruct(&case.routes, "live", 1)?;
    let dna_seconds = start.elapsed().as_secs_f64();
    let routes: Vec<_> = case.routes.iter().map(Dna::value).collect();
    let prompt = format!("Use ONLY the supplied facts. Follow via then label from the query entity in each route. If a complete route exists and complete routes agree, return its label. If no complete route exists or routes disagree, return UNKNOWN. Do not guess.\nRoutes: {}\nAnswer:",json!(routes));
    let request =
        json!({"op":"rank","prompts":[prompt],"candidates":[" Amber"," Violet"," UNKNOWN"]});
    let start = Instant::now();
    let response = worker.execute(request.clone())?;
    let model_seconds = start.elapsed().as_secs_f64();
    let raw = response["data"]["outputs"][0]["selected"]
        .as_str()
        .ok_or("Missing model selection")?
        .trim();
    if !["Amber", "Violet", "UNKNOWN"].contains(&raw)
        || response["data"]["evaluated_tokens"].as_u64().unwrap_or(0) == 0
    {
        return Err("Malformed model evidence".into());
    }
    let conclusion = dna["conclusion"].as_str().unwrap_or("UNKNOWN");
    let guarded = if dna["state"] == "accepted" && raw == conclusion {
        raw
    } else {
        "UNKNOWN"
    };
    Ok(
        json!({"id":case.id,"routes":routes,"dna":dna,"raw_model":raw,
        "guarded_output":guarded,"expected":case.expected,"model_correct":raw==case.expected,
        "dna_correct":conclusion==case.expected,"dna_seconds":dna_seconds,
        "model_seconds":model_seconds,"request":request,"response":response,
        "saved_answer_used":false,"model_mode":"candidate ranking, not free text generation"}),
    )
}
