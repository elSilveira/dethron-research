use super::Worker;
use crate::neural::client::Client;
use serde_json::{json, Value};
use std::{process::Command, time::Duration};

pub struct Endpoint {
    pub name: String,
    python: String,
    model: String,
    device: String,
    remote: Option<(String, String)>,
}
fn field(value: &Value, name: &str) -> Result<String, String> {
    value[name]
        .as_str()
        .filter(|s| !s.is_empty() && s.len() <= 4096 && !s.contains(['\0', '\n', '\r']))
        .map(str::to_string)
        .ok_or_else(|| format!("Invalid endpoint {name}"))
}
fn quote(value: &str) -> String {
    format!("'{}'", value.replace('\'', "'\"'\"'"))
}
impl Endpoint {
    pub fn parse(value: &Value) -> Result<Self, String> {
        let device = field(value, "device")?;
        if !["cpu", "cuda"].contains(&device.as_str()) {
            return Err("Invalid device".into());
        }
        let remote = match value["kind"].as_str() {
            Some("local") => None,
            Some("ssh") => {
                let host = field(value, "host")?;
                if host.starts_with('-')
                    || !host
                        .bytes()
                        .all(|c| c.is_ascii_alphanumeric() || b"@.-_:[]".contains(&c))
                {
                    return Err("Invalid SSH host".into());
                }
                Some((host, field(value, "directory")?))
            }
            _ => return Err("Endpoint kind must be local or ssh".into()),
        };
        Ok(Self {
            name: field(value, "name")?,
            python: field(value, "python")?,
            model: field(value, "model")?,
            device,
            remote,
        })
    }
    pub fn command(&self) -> Command {
        let arguments = [
            "-u",
            "-m",
            "neural_worker",
            "--model",
            &self.model,
            "--device",
            &self.device,
        ];
        if let Some((host, directory)) = &self.remote {
            let mut command = Command::new("ssh");
            let invocation = std::iter::once(self.python.as_str())
                .chain(arguments)
                .map(quote)
                .collect::<Vec<_>>()
                .join(" ");
            command.args([
                "-T",
                "-o",
                "BatchMode=yes",
                "-o",
                "StrictHostKeyChecking=yes",
                "-o",
                "ConnectTimeout=10",
                "-o",
                "ServerAliveInterval=10",
                "-o",
                "ServerAliveCountMax=2",
                host,
            ]);
            command.arg(format!("cd {} && exec {invocation}", quote(directory)));
            command
        } else {
            let mut command = Command::new(&self.python);
            command.args(arguments);
            command
        }
    }
    pub fn start(&self) -> Result<Box<dyn Worker>, String> {
        let mut command = self.command();
        let client = if self.remote.is_some() {
            Client::start_over_ssh(&mut command, Duration::from_secs(180))?
        } else {
            Client::start(&mut command, Duration::from_secs(180))?
        };
        Ok(Box::new(NeuralWorker {
            name: self.name.clone(),
            client,
            host: self
                .remote
                .as_ref()
                .map(|(host, _)| host.clone())
                .unwrap_or_else(|| "localhost".into()),
        }))
    }
}
struct NeuralWorker {
    name: String,
    host: String,
    client: Client,
}
impl Worker for NeuralWorker {
    fn metadata(&self) -> Value {
        json!({"name":self.name,"host":self.host,"handshake":self.client.metadata})
    }
    fn execute(&mut self, request: Value) -> Result<Value, String> {
        self.client.request(request, Duration::from_secs(60))
    }
}
