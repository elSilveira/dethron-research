use crate::{
    audit::Audit,
    task::{factorize, Work},
    trit::Trit,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::BTreeMap;

pub struct Receipt {
    pub work: Work,
    pub cached: bool,
}
#[derive(Debug, Serialize)]
pub struct Evolution {
    pub promoted: bool,
    pub evaluation_divisions: u64,
    pub before_divisions: u64,
    pub after_divisions: u64,
}
#[derive(Clone, Serialize, Deserialize)]
pub(crate) struct Knowledge {
    pub factors: Vec<u64>,
    pub source: String,
    pub learned_version: u64,
}
#[derive(Clone, Serialize, Deserialize)]
pub(crate) struct State {
    pub strategy: Trit,
    pub version: u64,
    pub generation: u64,
    pub parent: Option<String>,
    pub active: bool,
    pub auto_every: u64,
    pub completed: u64,
    pub knowledge: BTreeMap<u64, Knowledge>,
}
pub struct Tron {
    pub audit: Audit,
    pub(crate) state: State,
}
impl Tron {
    pub fn new(auto_every: u64) -> Self {
        let mut tron = Self {
            audit: Audit::new(),
            state: State {
                strategy: Trit::Minus,
                version: 0,
                generation: 0,
                parent: None,
                active: true,
                auto_every,
                completed: 0,
                knowledge: BTreeMap::new(),
            },
        };
        tron.audit.append("birth", json!(&tron.state), None);
        tron
    }
    pub(crate) fn ready(&self) -> Result<(), String> {
        if !self.state.active {
            return Err("TRON is stopped".into());
        }
        if self.audit.events.len() >= 10_000 {
            return Err("Audit capacity reached".into());
        }
        Ok(())
    }
    pub fn run(&mut self, number: u64, budget: u64) -> Result<Receipt, String> {
        self.ready()?;
        if !(1..=1_000_000).contains(&number) || !(1..=1_000_000).contains(&budget) {
            return Err("Input/budget outside [1, 1000000]".into());
        }
        if let Some(known) = self.state.knowledge.get(&number) {
            let work = Work {
                factors: known.factors.clone(),
                divisions: 0,
            };
            self.audit.append(
                "recall",
                json!({"input":number,"source":known.source}),
                None,
            );
            return Ok(Receipt { work, cached: true });
        }
        let work = match factorize(number, self.state.strategy, budget) {
            Ok(work) => work,
            Err(error) => {
                self.audit
                    .append("failed", json!({"input":number,"error":error}), None);
                return Err(error);
            }
        };
        if self.state.knowledge.len() == 128 {
            self.state.knowledge.pop_first();
        }
        self.state.knowledge.insert(
            number,
            Knowledge {
                factors: work.factors.clone(),
                source: self.audit.identity(),
                learned_version: self.state.version,
            },
        );
        self.state.completed += 1;
        self.audit.append(
            "learn",
            json!({"input":number,"factors":work.factors,
            "divisions":work.divisions,"version":self.state.version}),
            None,
        );
        if self.state.auto_every > 0 && self.state.completed % self.state.auto_every == 0 {
            self.evolve();
        }
        Ok(Receipt {
            work,
            cached: false,
        })
    }
    pub fn strategy(&self) -> Trit {
        self.state.strategy
    }
    pub fn version(&self) -> u64 {
        self.state.version
    }
    pub fn generation(&self) -> u64 {
        self.state.generation
    }
    pub fn knowledge_len(&self) -> usize {
        self.state.knowledge.len()
    }
    pub fn stop(&mut self) {
        self.state.active = false;
        self.audit.append("stop", json!({}), None);
    }
    pub fn resume(&mut self) {
        self.state.active = true;
        self.audit.append("resume", json!({}), None);
    }
    pub fn spawn(&mut self, inherit: bool) -> Result<Self, String> {
        self.ready()?;
        let mut child = Self {
            audit: Audit::new(),
            state: self.state.clone(),
        };
        if !inherit {
            child.state.knowledge.clear();
        }
        child.state.generation += 1;
        child.state.completed = 0;
        self.audit.append(
            "spawn",
            json!({"inherit":inherit, "version":self.state.version}),
            Some(child.audit.identity()),
        );
        child.state.parent = Some(self.audit.head());
        child
            .audit
            .append("birth", json!(&child.state), child.state.parent.clone());
        Ok(child)
    }
}
