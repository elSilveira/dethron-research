use serde_json::{json, Value};
use std::{
    io::Write,
    time::{Duration, Instant},
};

pub struct Stream {
    start: Instant,
    sequence: usize,
    pub delay_ms: u64,
}

impl Stream {
    pub fn new(delay_ms: u64) -> Self {
        Self {
            start: Instant::now(),
            sequence: 0,
            delay_ms,
        }
    }

    pub fn emit(&mut self, kind: &str, data: Value) -> Result<(), String> {
        let event = json!({"schema":1, "sequence":self.sequence,
            "elapsed_ms":self.start.elapsed().as_secs_f64() * 1000.0,
            "kind":kind, "data":data});
        let mut stdout = std::io::stdout().lock();
        writeln!(stdout, "{event}").map_err(|e| e.to_string())?;
        stdout.flush().map_err(|e| e.to_string())?;
        self.sequence += 1;
        if kind != "completed" {
            std::thread::sleep(Duration::from_millis(self.delay_ms));
        }
        Ok(())
    }
}
