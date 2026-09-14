use super::dna::{Dna, Source};
use serde_json::{json, Value};
use std::collections::BTreeSet;

impl Dna {
    pub fn recognize(&self, context: &str, revision: u64) -> Vec<Source> {
        let mut selected = BTreeSet::new();
        for query in &self.queries {
            let mut frontier = BTreeSet::from([query.entity.clone()]);
            for relation in &query.relations {
                let mut next = BTreeSet::new();
                for source in &self.sources {
                    if source.active(context, revision)
                        && frontier.contains(&source.entity)
                        && source.relation == *relation
                    {
                        selected.insert(source.id.clone());
                        next.insert(source.target.clone());
                    }
                }
                frontier = next;
            }
        }
        self.sources
            .iter()
            .filter(|s| selected.contains(&s.id))
            .cloned()
            .collect()
    }
    pub fn assess(&self, context: &str, revision: u64, raw: &str, truncated: bool) -> Value {
        let mut citations = BTreeSet::new();
        let mut answers = Vec::new();
        let mut issues = Vec::new();
        for query in &self.queries {
            let mut entity = query.entity.clone();
            for relation in &query.relations {
                let matches: Vec<_> = self
                    .sources
                    .iter()
                    .filter(|s| {
                        s.active(context, revision) && s.entity == entity && s.relation == *relation
                    })
                    .collect();
                let targets: BTreeSet<_> = matches.iter().map(|s| s.target.clone()).collect();
                if targets.len() != 1 {
                    issues.push(if targets.is_empty() {
                        "missing_or_inactive"
                    } else {
                        "contradictory"
                    });
                    break;
                }
                citations.extend(matches.iter().map(|s| s.id.clone()));
                entity = targets.into_iter().next().unwrap();
            }
            answers.push(entity);
        }
        let raw = raw.trim();
        let state = if truncated {
            "truncated"
        } else if issues.is_empty() && raw == answers.join(", ") {
            "accepted"
        } else if !issues.is_empty() && raw == "UNKNOWN" {
            "abstained"
        } else {
            "rejected"
        };
        json!({"state":state,"accepted_output":if state=="accepted" {Some(raw)} else {None},
            "source_ids":citations,"issues":issues,"verifier":"bounded_relation_paths_v1",
            "scope":"Entailment from caller-supplied structured facts; not verification of external truth",
            "excluded_source_ids":self.sources.iter().filter(|s| !s.active(context,revision)).map(|s| &s.id).collect::<Vec<_>>()})
    }
}
