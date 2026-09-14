use super::graph::Recipe;
use std::collections::{BTreeMap, BTreeSet, VecDeque};

pub(super) struct Episode {
    pub capability: String,
    pub version: u64,
    pub context: u64,
    pub input: i64,
    pub recipe: Recipe,
    pub tick: u64,
}

pub(super) struct Evidence {
    pub version: u64,
    pub context: u64,
    pub inputs: BTreeSet<i64>,
    pub formation_inputs: BTreeSet<i64>,
    pub recipe: Recipe,
    pub tick: u64,
}

pub(super) struct Lasting {
    pub version: u64,
    pub recipe: Recipe,
    pub relevance: u64,
    pub tick: u64,
}

#[derive(Default)]
pub(super) struct Memory {
    pub short: VecDeque<Episode>,
    pub medium: BTreeMap<String, Evidence>,
    pub long: BTreeMap<String, Lasting>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct MemoryStats {
    pub short: usize,
    pub medium: usize,
    pub long: usize,
}

impl Memory {
    pub fn stats(&self) -> MemoryStats {
        MemoryStats {
            short: self.short.len(),
            medium: self.medium.len(),
            long: self.long.len(),
        }
    }
    pub fn expire(&mut self, tick: u64) {
        self.short.retain(|m| tick - m.tick <= 32);
        self.medium.retain(|_, m| tick - m.tick <= 128);
    }
    pub fn record(&mut self, episode: Episode) {
        if self.short.len() == 16 {
            self.short.pop_front();
        }
        self.short.push_back(episode);
    }
    pub fn valid(&self, capability: &str, context: u64, version: u64) -> bool {
        self.medium
            .get(capability)
            .is_some_and(|m| m.version == version && m.context == context && m.inputs.len() >= 3)
    }
    pub fn agree(
        &mut self,
        capability: &str,
        context: u64,
        version: u64,
        input: i64,
        tick: u64,
        recipe: Recipe,
    ) -> bool {
        let evidence = self
            .medium
            .entry(capability.to_string())
            .or_insert_with(|| Evidence {
                version,
                context,
                inputs: BTreeSet::new(),
                formation_inputs: BTreeSet::new(),
                recipe: recipe.clone(),
                tick,
            });
        if evidence.version != version || evidence.context != context {
            *evidence = Evidence {
                version,
                context,
                inputs: BTreeSet::new(),
                formation_inputs: BTreeSet::new(),
                recipe,
                tick,
            };
        }
        evidence.tick = tick;
        if evidence.inputs.len() < 3 && !evidence.formation_inputs.contains(&input) {
            evidence.inputs.insert(input);
        }
        evidence.inputs.len() >= 3
    }
    pub fn store(&mut self, capability: &str, recipe: Recipe, version: u64, tick: u64) {
        if !self.long.contains_key(capability) && self.long.len() == 4 {
            let victim = self
                .long
                .iter()
                .min_by_key(|(_, m)| (m.relevance, m.tick))
                .unwrap()
                .0
                .clone();
            self.long.remove(&victim);
        }
        let relevance = self
            .long
            .get(capability)
            .map_or(1, |m| m.relevance.saturating_add(1));
        self.long.insert(
            capability.to_string(),
            Lasting {
                version,
                recipe,
                relevance,
                tick,
            },
        );
    }
    pub fn invalidate(&mut self, capability: &str) {
        self.short.retain(|m| m.capability != capability);
        self.medium.remove(capability);
        self.long.remove(capability);
    }
}
