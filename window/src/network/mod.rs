pub mod accuracy;
pub mod accuracy_data;
pub mod accuracy_metrics;
pub mod config;
pub mod connector;
mod dispatch;
pub mod dna;
pub mod packet;
pub mod probe;
mod quality;
mod recognition;
mod scheduler;
pub mod workload;
pub use packet::{Limits, Task};
pub use scheduler::run;
use serde_json::Value;

pub trait Worker: Send {
    fn metadata(&self) -> Value;
    fn execute(&mut self, request: Value) -> Result<Value, String>;
}
