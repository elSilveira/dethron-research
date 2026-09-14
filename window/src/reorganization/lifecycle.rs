use super::{
    engine::Engine,
    graph::{Graph, Primitive, Recipe},
    model::{Delivery, MemoryTier, Policy},
};
use crate::budget::Activity;

impl Engine {
    /// Discard live shortcut nodes; reconstructing them requires reachable memories.
    pub fn lose_path(&mut self, capability: &str) -> Result<(), String> {
        if !self.regions.contains_key(capability) {
            return Err("Unknown region".into());
        }
        self.charge(Activity::Update, 1)?;
        self.regions.get_mut(capability).unwrap().shortcut = None;
        Ok(())
    }
    pub fn forget(&mut self, tier: MemoryTier) -> Result<(), String> {
        self.charge(Activity::Update, 1)?;
        match tier {
            MemoryTier::Short => self.memory.short.clear(),
            MemoryTier::Medium => self.memory.medium.clear(),
            MemoryTier::Long => self.memory.long.clear(),
        }
        Ok(())
    }
    /// An explicit environment/procedure revision, not access to a test-set answer.
    pub fn revise(&mut self, capability: &str, steps: &[Primitive]) -> Result<(), String> {
        let recipe = Recipe::new(steps)?;
        let version = self
            .regions
            .get(capability)
            .ok_or("Unknown region")?
            .version
            + 1;
        self.charge(Activity::Update, steps.len() as u64)?;
        let shortcut = if self.policy == Policy::Compiled {
            self.charge(Activity::Consolidate, (steps.len() * 6) as u64)?;
            recipe
                .compose()
                .map(|r| Graph::rebuild(r, &mut self.next_id))
        } else {
            None
        };
        let reference = Graph::rebuild(recipe, &mut self.next_id);
        let region = self.regions.get_mut(capability).unwrap();
        region.version = version;
        region.reference = reference;
        region.shortcut = shortcut;
        region.calls = 0;
        self.memory.invalidate(capability);
        Ok(())
    }
    /// A downstream rejection removes confidence; it cannot invent a corrected procedure.
    pub fn feedback(
        &mut self,
        capability: &str,
        delivery: &Delivery,
        accepted: bool,
    ) -> Result<(), String> {
        let region = self.regions.get(capability).ok_or("Unknown region")?;
        let current = &region.shortcut.as_ref().unwrap_or(&region.reference).ids;
        let fallback = delivery.phase == "shadow"
            && !delivery.consensus
            && delivery.shadow_nodes == region.reference.ids;
        if delivery.version != region.version
            || (!fallback
                && &delivery.primary_nodes != current
                && delivery.primary_nodes != region.reference.ids)
        {
            return Err("Stale or unrelated feedback".into());
        }
        self.charge(Activity::Validate, 1)?;
        if !accepted {
            self.memory.invalidate(capability);
            self.regions.get_mut(capability).unwrap().shortcut = None;
        }
        Ok(())
    }
    /// Deliberate fault injection for validation experiments only.
    pub fn inject_shortcut_fault(&mut self, capability: &str) -> Result<(), String> {
        let region = self.regions.get_mut(capability).ok_or("Unknown region")?;
        let shortcut = region.shortcut.as_mut().ok_or("No shortcut")?;
        shortcut.recipe.inject_fault();
        Ok(())
    }
}
