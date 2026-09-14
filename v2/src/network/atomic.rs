//! One source relation per content-addressed evidence unit; no model replicas.
use super::{
    dna::{Dna, Query, Source},
    reconstruction::reconstruct,
};
use crate::crypto;
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

pub struct AtomicDna {
    atoms: BTreeMap<String, Source>,
    recipes: Vec<(Vec<String>, Vec<Query>)>,
}
impl AtomicDna {
    pub fn compile(routes: &[Dna]) -> Result<Self, String> {
        // Reuse the existing query and source-identity contract.
        reconstruct(routes, "", 0)?;
        let mut atoms = BTreeMap::new();
        let mut recipes = Vec::new();
        for route in routes {
            let mut references = Vec::new();
            for source in &route.sources {
                let identity = crypto::hash(source.value().to_string().as_bytes());
                atoms.insert(identity.clone(), source.clone());
                references.push(identity);
            }
            recipes.push((references, route.queries.clone()));
        }
        if atoms.len() > 512 {
            return Err("Atomic DNA exceeds 512 unique facts".into());
        }
        Ok(Self { atoms, recipes })
    }
    pub fn lose_source(&mut self, id: &str) -> bool {
        let before = self.atoms.len();
        self.atoms.retain(|_, source| source.id != id);
        self.atoms.len() != before
    }
    fn routes(&self) -> Vec<Dna> {
        self.recipes
            .iter()
            .map(|(refs, queries)| Dna {
                sources: refs
                    .iter()
                    .filter_map(|id| self.atoms.get(id).cloned())
                    .collect(),
                queries: queries.clone(),
            })
            .collect()
    }
    pub fn reconstruct(&self, context: &str, revision: u64) -> Result<Value, String> {
        reconstruct(&self.routes(), context, revision)
    }
    pub fn evidence_text(&self, context: &str, revision: u64) -> String {
        let mut sources = BTreeMap::new();
        for route in self.routes() {
            for source in route.recognize(context, revision) {
                sources.insert(source.id.clone(), source);
            }
        }
        sources
            .values()
            .map(|s| format!("[{}] {} --{}--> {}.", s.id, s.entity, s.relation, s.target))
            .collect::<Vec<_>>()
            .join("\n")
    }
    pub fn inventory(&self) -> Value {
        let required: BTreeSet<_> = self.recipes.iter().flat_map(|(refs, _)| refs).collect();
        json!({"schema":1,"unit":"one annotated source relation; not a neural model",
            "atoms":self.atoms.iter().map(|(id,s)|json!({"hash":id,"fact":s.value()})).collect::<Vec<_>>(),
            "recipes":self.recipes.iter().map(|(refs,queries)|json!({"references":refs,
                "queries":queries.iter().map(|q|json!({"entity":q.entity,"relations":q.relations})).collect::<Vec<_>>()})).collect::<Vec<_>>(),
            "missing_atoms":required.iter().filter(|id|!self.atoms.contains_key(**id)).count()})
    }
}
