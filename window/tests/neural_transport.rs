use std::{
    process::Command,
    time::{Duration, Instant},
};
use tron_window::neural::transport::Transport;

fn worker() -> Transport {
    let mut command = Command::new("python");
    command.args(["-u", "tests/fixtures/neural_worker.py"]);
    Transport::start(&mut command).unwrap()
}

#[test]
fn keeps_one_process_and_returns_real_pipe_messages() {
    let mut worker = worker();
    let ready: serde_json::Value =
        serde_json::from_str(&worker.receive(Duration::from_secs(3)).unwrap()).unwrap();
    for input in ["one", "two"] {
        worker.send(input).unwrap();
        let reply: serde_json::Value =
            serde_json::from_str(&worker.receive(Duration::from_secs(3)).unwrap()).unwrap();
        assert_eq!(reply["echo"], input);
        assert_eq!(reply["pid"], ready["pid"]);
    }
}

#[test]
fn deadline_crash_and_oversized_output_are_errors() {
    for input in ["hang", "crash", "oversized"] {
        let mut worker = worker();
        worker.receive(Duration::from_secs(3)).unwrap();
        worker.send(input).unwrap();
        let start = Instant::now();
        assert!(worker.receive(Duration::from_millis(200)).is_err());
        assert!(worker.send("after-failure").is_err());
        drop(worker);
        assert!(start.elapsed() < Duration::from_secs(3));
    }
}
