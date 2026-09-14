#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Tier {
    Short,
    Medium,
    Long,
}

#[derive(Clone, Debug)]
pub struct Fact {
    pub id: String,
    pub context: u64,
    pub entity: String,
    pub relation: String,
    pub target: String,
    pub version: u64,
    pub tier: Tier,
}

#[derive(Clone)]
struct Stored {
    fact: Fact,
    until: Option<u64>,
    accesses: u64,
    last_used: u64,
}

#[derive(Clone, Default)]
pub struct Memory {
    pub epoch: u64,
    tick: u64,
    facts: BTreeMap<String, Stored>,
}

impl Memory {
    pub fn put(
        &mut self,
        context: u64,
        entity: &str,
        relation: &str,
        target: &str,
        tier: Tier,
    ) -> Result<(), String> {
        if [entity, relation, target].iter().any(|s| {
            s.is_empty()
                || s.len() > 64
                || !s
                    .bytes()
                    .all(|c| c.is_ascii_alphanumeric() || c == b'-' || c == b'_')
        }) {
            return Err("Invalid fact identifier".into());
        }
        let id = format!("{context}:{entity}:{relation}");
        let version = self.facts.get(&id).map_or(1, |s| s.fact.version + 1);
        if self.facts.len() == 64 && !self.facts.contains_key(&id) {
            let victim = self
                .facts
                .iter()
                .min_by_key(|(_, s)| {
                    let importance = match s.fact.tier {
                        Tier::Short => 0,
                        Tier::Medium => 10,
                        Tier::Long => 100,
                    };
                    (importance + s.accesses, s.last_used)
                })
                .unwrap()
                .0
                .clone();
            self.facts.remove(&victim);
        }
        let until = match tier {
            Tier::Short => Some(self.tick + 8),
            Tier::Medium => Some(self.tick + 64),
            Tier::Long => None,
        };
        let fact = Fact {
            id: id.clone(),
            context,
            entity: entity.into(),
            relation: relation.into(),
            target: target.into(),
            version,
            tier,
        };
        self.facts.insert(
            id,
            Stored {
                fact,
                until,
                accesses: 0,
                last_used: self.tick,
            },
        );
        self.epoch += 1;
        Ok(())
    }
    /// Find a bounded association chain; a stored recipe restricts relation types, not answers.
    pub fn trace(&self, context: u64, entity: &str, recipe: Option<&[String]>) -> Vec<Fact> {
        let mut queue = VecDeque::from([(entity.to_string(), Vec::<Fact>::new())]);
        while let Some((current, path)) = queue.pop_front() {
            if path.len() == 3 {
                continue;
            }
            for stored in self
                .facts
                .values()
                .filter(|s| s.fact.context == context && s.fact.entity == current)
            {
                let fact = &stored.fact;
                if path.iter().any(|p| p.id == fact.id)
                    || recipe.is_some_and(|r| r.get(path.len()) != Some(&fact.relation))
                {
                    continue;
                }
                let mut next = path.clone();
                next.push(fact.clone());
                if fact.relation == "assigned_to" && recipe.is_none_or(|r| r.len() == next.len()) {
                    return next;
                }
                queue.push_back((fact.target.clone(), next));
            }
        }
        Vec::new()
    }
    pub fn active(&self, context: u64) -> Vec<Fact> {
        self.facts
            .values()
            .filter(|s| s.fact.context == context)
            .map(|s| s.fact.clone())
            .collect()
    }
    pub fn touch(&mut self, facts: &[Fact]) {
        for fact in facts {
            if let Some(stored) = self.facts.get_mut(&fact.id) {
                stored.accesses = stored.accesses.saturating_add(1);
                stored.last_used = self.tick;
            }
        }
    }
    pub fn counts(&self) -> [usize; 3] {
        let mut counts = [0; 3];
        for stored in self.facts.values() {
            counts[stored.fact.tier as usize] += 1;
        }
        counts
    }
    pub fn forget(&mut self, tier: Tier) {
        let before = self.facts.len();
        self.facts.retain(|_, s| s.fact.tier != tier);
        if before != self.facts.len() {
            self.epoch += 1;
        }
    }
    pub fn advance(&mut self) {
        self.tick += 1;
        let before = self.facts.len();
        self.facts
            .retain(|_, s| s.until.is_none_or(|until| self.tick <= until));
        if before != self.facts.len() {
            self.epoch += 1;
        }
    }
}
use std::collections::{BTreeMap, VecDeque};
