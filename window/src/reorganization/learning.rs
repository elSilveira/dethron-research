use super::{
    engine::Engine,
    graph::Graph,
    memory::{Episode, Evidence},
    model::{Delivery, Request},
};
use crate::budget::Activity;
use std::collections::BTreeSet;

impl Engine {
    pub(super) fn learn(
        &mut self,
        request: Request<'_>,
        delivery: &mut Delivery,
    ) -> Result<(), String> {
        self.charge(Activity::Update, 1)?;
        let name = request.capability;
        if delivery.phase == "shadow" {
            if !delivery.consensus {
                self.memory.invalidate(name);
                self.regions.get_mut(name).unwrap().shortcut = None;
                delivery.events.extend(["contradiction", "reopened"]);
                return Ok(());
            }
            let was_valid = self.memory.valid(name, request.context, delivery.version);
            let recipe = self.regions[name].shortcut.as_ref().unwrap().recipe.clone();
            if self.memory.agree(
                name,
                request.context,
                delivery.version,
                request.input,
                self.tick,
                recipe.clone(),
            ) {
                self.charge(Activity::Consolidate, recipe.steps().len() as u64)?;
                self.memory.store(name, recipe, delivery.version, self.tick);
                if !was_valid {
                    delivery
                        .events
                        .extend(["promoted", "reference_route_released"]);
                }
            }
        }
        let region = &self.regions[name];
        let recipe = if delivery.phase == "shortcut" {
            region.shortcut.as_ref().unwrap().recipe.clone()
        } else {
            region.reference.recipe.clone()
        };
        self.memory.record(Episode {
            capability: name.to_string(),
            version: delivery.version,
            context: request.context,
            input: request.input,
            recipe,
            tick: self.tick,
        });
        if let Some(memory) = self.memory.long.get_mut(name) {
            memory.relevance = memory.relevance.saturating_add(1);
            memory.tick = self.tick;
        }
        if self.regions[name].shortcut.is_some() {
            return Ok(());
        }
        let traces: Vec<_> = self
            .memory
            .short
            .iter()
            .filter(|m| {
                m.capability == name
                    && m.version == delivery.version
                    && m.context == request.context
            })
            .collect();
        let distinct: BTreeSet<_> = traces.iter().map(|m| m.input).collect();
        if distinct.len() < 2 {
            return Ok(());
        }
        let observed = traces.last().unwrap().recipe.clone();
        self.charge(Activity::Explore, observed.steps().len() as u64)?;
        self.charge(Activity::Consolidate, (observed.steps().len() * 6) as u64)?;
        if let Some(recipe) = observed.compose() {
            self.memory.medium.insert(
                name.to_string(),
                Evidence {
                    version: delivery.version,
                    context: request.context,
                    inputs: BTreeSet::new(),
                    formation_inputs: distinct,
                    recipe: recipe.clone(),
                    tick: self.tick,
                },
            );
            self.regions.get_mut(name).unwrap().shortcut =
                Some(Graph::rebuild(recipe, &mut self.next_id));
            delivery.events.push("candidate_created");
        }
        Ok(())
    }
}
