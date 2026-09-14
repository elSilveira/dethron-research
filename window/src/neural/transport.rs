use std::{
    io::{BufRead, BufReader, Read, Write},
    process::{Child, Command, Stdio},
    sync::mpsc::{self, Receiver, SyncSender},
    thread::{self, JoinHandle},
    time::Duration,
};

pub struct Transport {
    child: Child,
    input: Option<SyncSender<String>>,
    output: Option<Receiver<Result<String, String>>>,
    threads: Vec<JoinHandle<()>>,
    failed: bool,
}

impl Transport {
    pub fn start(command: &mut Command) -> Result<Self, String> {
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000);
        }
        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()
            .map_err(|e| e.to_string())?;
        let mut stdin = child.stdin.take().ok_or("Worker stdin missing")?;
        let stdout = child.stdout.take().ok_or("Worker stdout missing")?;
        let (tx, rx) = mpsc::sync_channel(2);
        let (input, writes) = mpsc::sync_channel::<String>(1);
        let errors = tx.clone();
        let writer = thread::spawn(move || {
            while let Ok(line) = writes.recv() {
                if let Err(error) = writeln!(stdin, "{line}").and_then(|_| stdin.flush()) {
                    let _ = errors.send(Err(error.to_string()));
                    break;
                }
            }
        });
        let reader = thread::spawn(move || {
            let mut reader = BufReader::new(stdout);
            loop {
                let mut line = String::new();
                let result = match (&mut reader).take(65537).read_line(&mut line) {
                    Ok(0) => Err("Worker closed stdout".into()),
                    Ok(_) if line.len() > 65536 => Err("Worker response exceeds limit".into()),
                    Ok(_) => Ok(line),
                    Err(error) => Err(error.to_string()),
                };
                let failed = result.is_err();
                if tx.send(result).is_err() || failed {
                    break;
                }
            }
        });
        Ok(Self {
            child,
            input: Some(input),
            output: Some(rx),
            threads: vec![reader, writer],
            failed: false,
        })
    }
    pub fn receive(&mut self, timeout: Duration) -> Result<String, String> {
        if self.failed {
            return Err("Worker connection is failed".into());
        }
        let result = self
            .output
            .as_ref()
            .unwrap()
            .recv_timeout(timeout)
            .map_err(|e| format!("Worker response deadline/disconnection: {e}"))
            .and_then(|v| v);
        if result.is_err() {
            self.abort();
        }
        result
    }
    pub fn send(&mut self, line: &str) -> Result<(), String> {
        if self.failed || line.len() > 65535 || line.contains('\n') {
            return Err("Invalid request or failed worker".into());
        }
        self.input
            .as_ref()
            .unwrap()
            .try_send(line.to_string())
            .map_err(|e| e.to_string())
    }
    pub fn pid(&self) -> u32 {
        self.child.id()
    }
    pub fn abort(&mut self) {
        if self.failed {
            return;
        }
        self.failed = true;
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            // A Windows venv launcher may own the actual Python worker as a child.
            let _ = Command::new("taskkill")
                .args(["/PID", &self.child.id().to_string(), "/T", "/F"])
                .creation_flags(0x08000000)
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status();
        }
        let _ = self.child.kill();
    }
}

impl Drop for Transport {
    fn drop(&mut self) {
        self.abort();
        self.input.take();
        self.output.take();
        let _ = self.child.wait();
        for thread in self.threads.drain(..) {
            let _ = thread.join();
        }
    }
}
