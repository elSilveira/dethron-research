pub mod config;
pub mod connector;
mod dispatch;
pub mod dna;
pub mod packet;
mod quality;
mod recognition;
mod scheduler;
pub use packet::{Limits, Task};
pub use scheduler::{run, run_persistent};
mod journal;
mod recovery;
use serde_json::Value;
pub trait Worker: Send {
    fn metadata(&self) -> Value;
    fn execute(&mut self, request: Value) -> Result<Value, String>;
}

pub mod atomic;
pub mod node_control;
pub mod node_store;
pub mod node_wire;
mod outcome;
pub mod recipe;
pub mod reconstruction;
pub mod recovery_dna;
pub mod recovery_plan;
pub mod regeneration;
pub mod replica;
