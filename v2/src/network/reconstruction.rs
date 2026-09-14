//! Bounded reconstruction from explicitly supplied alternative evidence routes.
use super::dna::Dna;
use serde_json::{json, Value};
use std::collections::{BTreeSet, HashMap};

pub enum Presentation {
    Bare,
    Sentence,
}
impl Presentation {
    /// Formats a reconstruction report; never validates arbitrary model prose.
    pub fn render(&self, report: &Value) -> String {
        match report["conclusion"]
            .as_str()
            .filter(|_| report["state"] == "accepted")
        {
            Some(answer) => match self {
                Self::Bare => answer.into(),
                Self::Sentence => format!("Conclusão: {answer}."),
            },
            None => "UNKNOWN".into(),
        }
    }
}

/// Each route must ask the same single relation-path query. Missing routes may
/// be bypassed; any observed contradiction vetoes acceptance. No saved answer
/// or worker is used. Evidence completeness and truth remain caller assumptions.
pub fn reconstruct(routes: &[Dna], context: &str, revision: u64) -> Result<Value, String> {
    if !(1..=16).contains(&routes.len()) {
        return Err("Use 1..16 DNA routes".into());
    }
    let mut identities = HashMap::new();
    let mut dna_bytes = 0;
    for route in routes {
        Dna::parse(&route.value())?;
        if route.queries.len() != 1 || route.value()["queries"] != routes[0].value()["queries"] {
            return Err("Routes must share one identical query".into());
        }
        dna_bytes += route.value().to_string().len();
        for source in &route.sources {
            if let Some(previous) = identities.insert(source.id.clone(), source.value()) {
                if previous != source.value() {
                    return Err("Conflicting source identity across routes".into());
                }
            }
        }
    }
    let mut conclusions = BTreeSet::new();
    let mut citations = BTreeSet::new();
    let mut reports = Vec::new();
    let mut source_checks = 0u64;
    let mut conflict = false;
    for (index, route) in routes.iter().enumerate() {
        let query = &route.queries[0];
        let mut entity = query.entity.clone();
        let mut used = BTreeSet::new();
        let mut issue = None;
        for relation in &query.relations {
            let mut targets = BTreeSet::new();
            for source in &route.sources {
                source_checks += 1;
                if source.active(context, revision)
                    && source.entity == entity
                    && source.relation == *relation
                {
                    targets.insert(source.target.clone());
                    used.insert(source.id.clone());
                }
            }
            if targets.len() != 1 {
                issue = Some(if targets.is_empty() {
                    "missing_or_inactive"
                } else {
                    "contradictory"
                });
                conflict |= targets.len() > 1;
                break;
            }
            entity = targets.into_iter().next().unwrap();
        }
        if issue.is_none() {
            conclusions.insert(entity.clone());
            citations.extend(used.iter().cloned());
        }
        reports.push(json!({"route":index,"issue":issue,"source_ids":used,
            "conclusion":if issue.is_none() {Some(entity)} else {None}}));
    }
    conflict |= conclusions.len() > 1;
    let accepted = !conflict && conclusions.len() == 1;
    Ok(
        json!({"schema":1,"state":if accepted {"accepted"} else {"abstained"},
        "conclusion":if accepted {conclusions.into_iter().next()} else {None},
        "source_ids":if accepted {citations} else {BTreeSet::new()},"routes":reports,
        "conflict":conflict,"source_checks":source_checks,"dna_bytes":dna_bytes,
        "worker_calls":0,"verifier":"alternative_relation_routes_v1",
        "scope":"Conclusion from supplied surviving facts; no external truth or prose verification"}),
    )
}
