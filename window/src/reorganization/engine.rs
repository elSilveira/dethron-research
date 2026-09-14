use super::{
    execution,
    graph::{Graph, Primitive, Recipe},
    memory::{Memory, MemoryStats},
    model::{Delivery, Policy, Region, Request},
};
use crate::budget::{Activity, Budget};
use std::collections::BTreeMap;

pub struct Engine {
    pub budget: Budget,
    pub(super) policy: Policy,
    pub(super) regions: BTreeMap<String, Region>,
    pub(super) memory: Memory,
    pub(super) next_id: u64,
    pub(super) tick: u64,
}

impl Engine {
    pub fn new(policy: Policy, limit: u64) -> Self {
        Self {
            budget: Budget::new(limit),
            policy,
            regions: BTreeMap::new(),
            memory: Memory::default(),
            next_id: 0,
            tick: 0,
        }
    }
    pub(super) fn charge(&mut self, activity: Activity, units: u64) -> Result<(), String> {
        self.budget
            .charge(activity, units)
            .map_err(|_| "Work budget exhausted".into())
    }
    pub fn register(&mut self, capability: &str, steps: &[Primitive]) -> Result<(), String> {
        if capability.is_empty()
            || capability.len() > 64
            || self.regions.len() >= 8
            || self.regions.contains_key(capability)
        {
            return Err("Invalid, duplicate or excessive region".into());
        }
        let recipe = Recipe::new(steps)?;
        self.charge(Activity::Update, steps.len() as u64)?;
        let reference = Graph::rebuild(recipe.clone(), &mut self.next_id);
        let shortcut = if self.policy == Policy::Compiled {
            self.charge(Activity::Consolidate, (steps.len() * 6) as u64)?;
            recipe
                .compose()
                .map(|r| Graph::rebuild(r, &mut self.next_id))
        } else {
            None
        };
        self.regions.insert(
            capability.to_string(),
            Region {
                version: 1,
                reference,
                shortcut,
                calls: 0,
            },
        );
        Ok(())
    }
    pub fn memory_stats(&self) -> MemoryStats {
        self.memory.stats()
    }

    pub fn submit(&mut self, request: Request<'_>) -> Result<Delivery, String> {
        if !(-1_000_000..=1_000_000).contains(&request.input) {
            return Err("Input outside -1000000..1000000".into());
        }
        if !self.regions.contains_key(request.capability) {
            return Err("No reachable region with the requested capability".into());
        }
        self.charge(Activity::Update, 1)?;
        self.tick += 1;
        self.memory.expire(self.tick);
        let mut events = Vec::new();
        self.restore_path(request.capability, &mut events)?;
        let region = self.regions.get_mut(request.capability).unwrap();
        region.calls += 1;
        let shadow = self.policy == Policy::Adaptive
            && region.shortcut.is_some()
            && (!self
                .memory
                .valid(request.capability, request.context, region.version)
                || region.calls % 16 == 0);
        let primary = region.shortcut.as_ref().unwrap_or(&region.reference);
        let phase = if shadow {
            "shadow"
        } else if region.shortcut.is_some() {
            "shortcut"
        } else {
            "reference"
        };
        let mut delivery = execution::run(
            primary,
            shadow.then_some(&region.reference),
            request,
            region.version,
            phase,
            &mut self.budget,
        )?;
        delivery.events.append(&mut events);
        if self.policy == Policy::Adaptive {
            self.learn(request, &mut delivery)?;
        }
        Ok(delivery)
    }

    fn restore_path(
        &mut self,
        capability: &str,
        events: &mut Vec<&'static str>,
    ) -> Result<(), String> {
        let region = &self.regions[capability];
        if self.policy != Policy::Adaptive || region.shortcut.is_some() {
            return Ok(());
        }
        let recipe = self
            .memory
            .long
            .get(capability)
            .filter(|m| m.version == region.version)
            .map(|m| (m.recipe.clone(), "reconstructed_from_long_memory"))
            .or_else(|| {
                self.memory
                    .medium
                    .get(capability)
                    .filter(|m| m.version == region.version)
                    .map(|m| (m.recipe.clone(), "reconstructed_from_medium_memory"))
            });
        if let Some((recipe, source)) = recipe {
            self.charge(Activity::Reconstruct, recipe.steps().len() as u64)?;
            let graph = Graph::rebuild(recipe, &mut self.next_id);
            self.regions.get_mut(capability).unwrap().shortcut = Some(graph);
            events.push(source);
        }
        Ok(())
    }
}
