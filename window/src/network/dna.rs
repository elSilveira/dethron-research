use serde_json::{json, Value};
use std::collections::HashSet;

#[derive(Clone)]
pub struct Source {
    pub id: String,
    pub context: String,
    pub revision: u64,
    pub entity: String,
    pub relation: String,
    pub target: String,
    pub revoked: bool,
}
#[derive(Clone)]
pub struct Query {
    pub entity: String,
    pub relations: Vec<String>,
}
#[derive(Clone)]
pub struct Dna {
    pub sources: Vec<Source>,
    pub queries: Vec<Query>,
}
fn text(value: &Value, field: &str) -> Result<String, String> {
    value[field]
        .as_str()
        .filter(|s| !s.is_empty() && s.len() <= 128 && !s.chars().any(char::is_control))
        .map(str::to_string)
        .ok_or_else(|| format!("Invalid DNA {field}"))
}
impl Source {
    pub fn value(&self) -> Value {
        json!({"id":self.id,"context":self.context,"revision":self.revision,"entity":self.entity,
            "relation":self.relation,"target":self.target,"revoked":self.revoked})
    }
    pub fn active(&self, context: &str, revision: u64) -> bool {
        self.context == context && self.revision == revision && !self.revoked
    }
}
impl Dna {
    pub fn parse(value: &Value) -> Result<Self, String> {
        let sources = value["sources"].as_array().ok_or("Missing DNA sources")?;
        let queries = value["queries"].as_array().ok_or("Missing DNA queries")?;
        if sources.len() > 512 || !(1..=4).contains(&queries.len()) {
            return Err("DNA size limits exceeded".into());
        }
        let mut ids = HashSet::new();
        let sources = sources
            .iter()
            .map(|s| {
                let id = text(s, "id")?;
                if !ids.insert(id.clone()) {
                    return Err("Duplicate source identity".into());
                }
                Ok(Source {
                    id,
                    context: text(s, "context")?,
                    entity: text(s, "entity")?,
                    relation: text(s, "relation")?,
                    target: text(s, "target")?,
                    revision: s["revision"]
                        .as_u64()
                        .filter(|n| *n > 0)
                        .ok_or("Invalid source revision")?,
                    revoked: s["revoked"].as_bool().ok_or("Missing revoked flag")?,
                })
            })
            .collect::<Result<Vec<_>, String>>()?;
        let queries = queries
            .iter()
            .map(|q| {
                let relations = q["relations"].as_array().ok_or("Missing relations")?;
                if !(1..=4).contains(&relations.len()) {
                    return Err("Use 1..4 relations".into());
                }
                Ok(Query {
                    entity: text(q, "entity")?,
                    relations: relations
                        .iter()
                        .map(|r| text(&json!({"relation":r}), "relation"))
                        .collect::<Result<_, _>>()?,
                })
            })
            .collect::<Result<Vec<_>, String>>()?;
        Ok(Self { sources, queries })
    }
    pub fn value(&self) -> Value {
        json!({"sources":self.sources.iter().map(Source::value).collect::<Vec<_>>(),
            "queries":self.queries.iter().map(|q| json!({"entity":q.entity,"relations":q.relations})).collect::<Vec<_>>()})
    }
}
