use super::memory::Fact;
use std::collections::BTreeSet;

pub struct Paths {
    recipe: Option<Vec<String>>,
    formation_recipe: Vec<String>,
    formation: BTreeSet<String>,
    confirmed: BTreeSet<String>,
    scope: Option<(u64, u64)>,
    nodes: Vec<u64>,
    next_id: u64,
    calls: u64,
    pending: Vec<&'static str>,
}

impl Default for Paths {
    fn default() -> Self {
        Self {
            recipe: None,
            formation_recipe: Vec::new(),
            formation: BTreeSet::new(),
            confirmed: BTreeSet::new(),
            scope: None,
            nodes: Vec::new(),
            next_id: 5,
            calls: 0,
            pending: Vec::new(),
        }
    }
}

impl Paths {
    pub fn prepare(&mut self, context: u64, epoch: u64, reachable: bool) -> &'static str {
        self.calls += 1;
        self.pending.clear();
        if self.scope != Some((context, epoch)) {
            self.confirmed.clear();
            self.formation.clear();
            self.scope = Some((context, epoch));
            if self.recipe.is_some() {
                self.pending.push("context_revalidation");
            }
        }
        if !reachable {
            self.confirmed.clear();
            self.pending.push("missing_reachable_evidence");
            return "reference";
        }
        if self.recipe.is_none() {
            return "reference";
        }
        if self.nodes.is_empty() {
            self.nodes = (self.next_id..self.next_id + 3).collect();
            self.next_id += 3;
            self.pending.push("reconstructed_from_recipe_and_memories");
        }
        if self.confirmed.len() < 3 || self.calls % 16 == 0 {
            "shadow"
        } else {
            "shortcut"
        }
    }
    pub fn observe(&mut self, entity: &str, trace: &[Fact], agrees: bool) -> Vec<&'static str> {
        let mut events = std::mem::take(&mut self.pending);
        if !agrees {
            self.reject();
            events.push("reopened");
            return events;
        }
        if trace.is_empty() {
            return events;
        }
        let recipe: Vec<_> = trace.iter().map(|f| f.relation.clone()).collect();
        if self.recipe.as_ref() != Some(&recipe) {
            if self.formation_recipe != recipe {
                self.formation.clear();
                self.formation_recipe = recipe.clone();
            }
            self.formation.insert(entity.to_string());
            if self.formation.len() >= 2 {
                self.recipe = Some(recipe);
                self.confirmed.clear();
                self.nodes = (self.next_id..self.next_id + 3).collect();
                self.next_id += 3;
                events.push("candidate_created");
            }
        } else if !self.formation.contains(entity) && self.confirmed.len() < 3 {
            self.confirmed.insert(entity.to_string());
            if self.confirmed.len() == 3 {
                events.push("promoted");
            }
        }
        events
    }
    pub fn reject(&mut self) {
        self.recipe = None;
        self.nodes.clear();
        self.confirmed.clear();
        self.formation.clear();
    }
    pub fn lose_nodes(&mut self) {
        self.nodes.clear();
    }
    pub fn nodes(&self) -> Vec<u64> {
        self.nodes.clone()
    }
    pub fn recipe(&self) -> Option<&[String]> {
        self.recipe.as_deref()
    }
}
