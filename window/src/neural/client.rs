use super::{transport::Transport, validation};
use serde_json::{json, Value};
use std::{process::Command, time::Duration};

pub struct Client {
    transport: Transport,
    pub metadata: Value,
    sequence: u64,
    worker_pid: u32,
}

impl Client {
    pub fn start(command: &mut Command, timeout: Duration) -> Result<Self, String> {
        Self::connect(command, timeout, false)
    }
    pub fn start_over_ssh(command: &mut Command, timeout: Duration) -> Result<Self, String> {
        Self::connect(command, timeout, true)
    }
    fn connect(command: &mut Command, timeout: Duration, remote: bool) -> Result<Self, String> {
        let mut transport = Transport::start(command)?;
        let ready: Value =
            serde_json::from_str(&transport.receive(timeout)?).map_err(|e| e.to_string())?;
        if remote {
            validation::ready_remote(&ready)?;
        } else {
            validation::ready(&ready, transport.pid())?;
        }
        let worker_pid = ready["pid"]
            .as_u64()
            .and_then(|p| u32::try_from(p).ok())
            .ok_or("Invalid worker pid")?;
        Ok(Self {
            transport,
            metadata: ready,
            sequence: 0,
            worker_pid,
        })
    }
    pub fn request(&mut self, mut request: Value, timeout: Duration) -> Result<Value, String> {
        self.sequence += 1;
        request["schema"] = json!(1);
        request["id"] = json!(format!("neural-{}", self.sequence));
        let result = self.exchange(&request, timeout);
        if result.is_err() {
            self.transport.abort();
        }
        result
    }
    fn exchange(&mut self, request: &Value, timeout: Duration) -> Result<Value, String> {
        self.transport.send(&request.to_string())?;
        let response: Value =
            serde_json::from_str(&self.transport.receive(timeout)?).map_err(|e| e.to_string())?;
        validation::response(&response, request, self.sequence, self.worker_pid)?;
        Ok(response)
    }
}
