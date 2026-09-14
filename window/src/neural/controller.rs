use super::{client::Client, memory::Memory, paths::Paths, prompts::evidence_prompt};
use crate::budget::{Activity, Budget};
use serde_json::{json, Value};
use std::time::{Duration, Instant};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Policy {
    Full,
    Indexed,
    Adaptive,
}

pub fn grounded_decision(raw: &str, reachable: bool) -> (&str, &'static str) {
    if reachable {
        (raw, "neural_answer")
    } else {
        ("UNKNOWN", "abstained_missing_evidence")
    }
}

pub struct Controller {
    pub memory: Memory,
    pub paths: Paths,
    pub budget: Budget,
    pub policy: Policy,
}

impl Controller {
    pub fn new(policy: Policy, memory: Memory) -> Self {
        Self {
            memory,
            paths: Paths::default(),
            budget: Budget::new(1_000_000),
            policy,
        }
    }
    pub fn answer(
        &mut self,
        client: &mut Client,
        context: u64,
        entity: &str,
    ) -> Result<Value, String> {
        let start = Instant::now();
        self.memory.advance();
        let recipe = if self.policy == Policy::Adaptive {
            self.paths.recipe()
        } else {
            None
        };
        let trace = self.memory.trace(context, entity, recipe);
        let full = self.memory.active(context);
        self.budget
            .charge(Activity::Update, (full.len() + trace.len() + 1) as u64)
            .map_err(|_| "Budget exhausted")?;
        let phase = match self.policy {
            Policy::Full => "reference",
            Policy::Indexed => "indexed",
            Policy::Adaptive => self
                .paths
                .prepare(context, self.memory.epoch, !trace.is_empty()),
        };
        let primary = if phase == "reference" { &full } else { &trace };
        let mut prompts = vec![evidence_prompt(entity, primary)];
        if phase == "shadow" {
            prompts.push(evidence_prompt(entity, &full));
        }
        let candidates = [" A", " B", " C", " D", " UNKNOWN"];
        let bound: u64 = prompts
            .iter()
            .map(|p| ((p.len() + 34) * candidates.len()) as u64)
            .sum();
        if self.budget.remaining() < bound {
            return Err("Insufficient budget for bounded inference".into());
        }
        let request = json!({"op":"rank","prompts":prompts,"candidates":candidates});
        let response = match client.request(request, Duration::from_secs(60)) {
            Ok(response) => response,
            Err(error) => {
                self.budget
                    .charge(Activity::Execute, bound)
                    .map_err(|_| "Budget exhausted")?;
                return Err(error);
            }
        };
        let outputs = response["data"]["outputs"]
            .as_array()
            .ok_or("Missing outputs")?;
        for (index, output) in outputs.iter().enumerate() {
            let tokens = output["input_tokens"]
                .as_u64()
                .ok_or("Missing token count")?
                * candidates.len() as u64
                + output["candidate_tokens"]
                    .as_array()
                    .ok_or("Missing candidate lengths")?
                    .iter()
                    .map(|t| t.as_u64().unwrap_or(0))
                    .sum::<u64>();
            self.budget
                .charge(
                    if index == 0 {
                        Activity::Execute
                    } else {
                        Activity::Validate
                    },
                    tokens,
                )
                .map_err(|_| "Budget exhausted")?;
        }
        let first = outputs[0]["selected"]
            .as_str()
            .ok_or("Missing selected answer")?
            .trim();
        let reference = if phase == "shadow" {
            outputs[1]["selected"]
                .as_str()
                .ok_or("Missing reference answer")?
                .trim()
        } else {
            first
        };
        let agree = first == reference;
        let reachable = !trace.is_empty() || !self.memory.trace(context, entity, None).is_empty();
        let (prediction, decision) = grounded_decision(reference, reachable);
        let nodes = if phase == "reference" {
            vec![0, 1, 2, 3, 4]
        } else if self.policy == Policy::Indexed {
            vec![5, 6, 7]
        } else {
            self.paths.nodes()
        };
        let mut events = Vec::new();
        if self.policy == Policy::Adaptive {
            let observed = if phase == "reference" {
                self.memory.trace(context, entity, None)
            } else {
                trace.clone()
            };
            events = self.paths.observe(entity, &observed, agree);
        }
        self.memory.touch(primary);
        let evidence: Vec<_> = primary
            .iter()
            .map(|f| json!({"id":f.id,"version":f.version,"tier":format!("{:?}",f.tier)}))
            .collect();
        Ok(
            json!({"entity":entity,"context":context,"phase":phase,"prediction":prediction,
            "raw_neural_prediction":reference,"decision":decision,"reachable_evidence":reachable,
            "primary_prediction":first,"internal_agreement":if phase == "shadow" { Some(agree) } else { None },
            "primary_nodes":nodes,"shadow_nodes":if phase == "shadow" { vec![0,1,2,3,4] } else { vec![] },
            "recipe":self.paths.recipe(),"events":events,"evidence":evidence,"prompts":prompts,
            "memory_counts":self.memory.counts(),"budget_remaining":self.budget.remaining(),
            "wall_seconds":start.elapsed().as_secs_f64(),"neural":response}),
        )
    }
    pub fn feedback(&mut self, accepted: bool) -> Result<(), String> {
        self.budget
            .charge(Activity::Validate, 1)
            .map_err(|_| "Budget exhausted")?;
        if !accepted && self.policy == Policy::Adaptive {
            self.paths.reject();
        }
        Ok(())
    }
}
