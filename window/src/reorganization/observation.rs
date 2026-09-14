use super::{
    engine::Engine,
    graph::{Recipe, Step},
    model::Delivery,
};
use crate::budget::Activity;
use serde_json::{json, Value};

fn procedure(recipe: &Recipe) -> Vec<Value> {
    recipe
        .steps()
        .iter()
        .map(|step| match step {
            Step::Primitive(p) => json!({"primitive":format!("{p:?}")}),
            Step::Affine { scale, bias } => json!({"composed_affine":{"scale":scale,"bias":bias}}),
        })
        .collect()
}

impl Engine {
    /// Diagnostic state, not an authenticated persistence format or resident-memory measure.
    pub fn inspect(&self) -> Value {
        let dna: Vec<_> = self.regions.iter().map(|(name, r)| json!({
            "capability":name, "version":r.version, "reference_nodes":r.reference.ids,
            "reference_recipe":procedure(&r.reference.recipe),
            "shortcut":r.shortcut.as_ref().map(|g| json!({"nodes":g.ids,"recipe":procedure(&g.recipe)}))
        })).collect();
        let short: Vec<_> = self
            .memory
            .short
            .iter()
            .map(|m| {
                json!({
                    "capability":m.capability,"version":m.version,"context":m.context,
                    "input":m.input,"tick":m.tick,"executed_recipe":procedure(&m.recipe)
                })
            })
            .collect();
        let medium: Vec<_> = self
            .memory
            .medium
            .iter()
            .map(|(name, m)| {
                json!({
                    "capability":name,"version":m.version,"context":m.context,
                    "formation_inputs":m.formation_inputs,"validation_inputs":m.inputs,
                    "recipe":procedure(&m.recipe),"tick":m.tick
                })
            })
            .collect();
        let long: Vec<_> = self
            .memory
            .long
            .iter()
            .map(|(name, m)| {
                json!({
                    "capability":name,"version":m.version,"recipe":procedure(&m.recipe),
                    "relevance":m.relevance,"last_used_tick":m.tick
                })
            })
            .collect();
        let work: Vec<_> = [
            Activity::Execute,
            Activity::Explore,
            Activity::Update,
            Activity::Consolidate,
            Activity::Reconstruct,
            Activity::Validate,
        ]
        .iter()
        .map(|a| json!({"activity":format!("{a:?}"),"units":self.budget.spent(*a)}))
        .collect();
        json!({"dna":dna,"short":short,"medium":medium,"long":long,"work":work,
            "remaining_budget":self.budget.remaining(),"tick":self.tick,
            "limits":{"regions":8,"short":16,"medium":8,"long":4},
            "answer_cache":false})
    }
}

impl Delivery {
    pub fn inspect(&self) -> Value {
        json!({"value":self.value,"sink":self.sink,"version":self.version,
            "phase":self.phase,"primary_nodes":self.primary_nodes,"shadow_nodes":self.shadow_nodes,
            "workers":self.workers,"events":self.events,"internal_agreement":self.consensus,
            "reference_fallback":self.phase == "shadow" && !self.consensus})
    }
}
