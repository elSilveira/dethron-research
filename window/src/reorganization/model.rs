use super::graph::Graph;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Policy {
    Fixed,
    Compiled,
    Adaptive,
}

#[derive(Clone, Copy)]
pub enum MemoryTier {
    Short,
    Medium,
    Long,
}

#[derive(Clone, Copy)]
pub struct Request<'a> {
    pub capability: &'a str,
    pub context: u64,
    pub input: i64,
    pub ingress: u64,
    pub sink: u64,
}

#[derive(Debug)]
pub struct Delivery {
    pub value: i64,
    pub sink: u64,
    pub version: u64,
    pub phase: &'static str,
    pub primary_nodes: Vec<u64>,
    pub shadow_nodes: Vec<u64>,
    pub workers: Vec<String>,
    pub events: Vec<&'static str>,
    pub consensus: bool,
}

pub(super) struct Region {
    pub version: u64,
    pub reference: Graph,
    pub shortcut: Option<Graph>,
    pub calls: u64,
}
