use serde_json::Value;
use std::{
    io::{BufRead, BufReader},
    process::{Command, Stdio},
    sync::mpsc,
    time::Duration,
};

#[test]
fn live_events_describe_real_computation_and_public_evidence() {
    let output = Command::new(env!("CARGO_BIN_EXE_tron-window"))
        .args(["3", "0"])
        .output()
        .unwrap();
    assert!(output.status.success());
    let events: Vec<Value> = String::from_utf8(output.stdout)
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    assert!(!events.is_empty(), "Execution must emit live events");
    assert_eq!(events[0]["kind"], "started");
    for (index, event) in events.iter().enumerate() {
        assert_eq!(event["sequence"], index);
        assert!(event["elapsed_ms"].is_number());
    }
    let cycles: Vec<_> = events.iter().filter(|e| e["kind"] == "evolution").collect();
    assert_eq!(cycles.len(), 3);
    assert_eq!(cycles[0]["data"]["measurement"]["promoted"], true);
    assert_eq!(cycles[1]["data"]["measurement"]["promoted"], false);
    let tasks: Vec<_> = events.iter().filter(|e| e["kind"] == "task").collect();
    assert_eq!(tasks.len(), 8);
    assert!(tasks.iter().all(|e| e["data"]["correct"] == true));
    let last = events.last().unwrap();
    assert_eq!(last["kind"], "completed");
    let report = &last["data"];
    assert_eq!(report["baseline_divisions"], 4103);
    assert_eq!(report["evolved_divisions"], 95);
    assert_eq!(report["net_divisions_saved"], 2199);
    assert_eq!(report["child_recalled"], true);
    assert_eq!(report["audit_verified"], true);
    assert_eq!(report["encoding"]["roundtrip"], true);
    for owner in ["parent", "child"] {
        let audit = &report[owner];
        tron_v2::audit::verify(
            &serde_json::from_value::<Vec<tron_v2::audit::Event>>(audit["events"].clone()).unwrap(),
            &serde_json::from_value::<Vec<u8>>(audit["public_key"].clone()).unwrap(),
            audit["head"].as_str().unwrap(),
        )
        .unwrap();
    }
    let text = serde_json::to_string(&events).unwrap();
    for private in [
        "\"seed\"",
        "\"openings\"",
        "\"salt\"",
        "\"factors\"",
        "\"knowledge\"",
    ] {
        assert!(!text.contains(private), "Private payload leaked: {private}");
    }
}

#[test]
fn progress_is_flushed_before_the_process_finishes() {
    let mut process = Command::new(env!("CARGO_BIN_EXE_tron-window"))
        .args(["3", "500"])
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    let stdout = process.stdout.take().unwrap();
    let (sender, receiver) = mpsc::channel();
    let reader = std::thread::spawn(move || {
        let mut line = String::new();
        BufReader::new(stdout).read_line(&mut line).unwrap();
        sender.send(line).unwrap();
    });
    let first = receiver.recv_timeout(Duration::from_secs(3)).unwrap();
    let still_running = process.try_wait().unwrap().is_none();
    let _ = process.kill();
    process.wait().unwrap();
    reader.join().unwrap();
    assert!(!first.is_empty(), "Progress must arrive before completion");
    assert!(still_running, "First event must precede completion");
}

#[test]
fn invalid_controls_fail_without_claiming_success() {
    for args in [["0", "0"], ["101", "0"], ["1", "2001"], ["x", "0"]] {
        let output = Command::new(env!("CARGO_BIN_EXE_tron-window"))
            .args(args)
            .output()
            .unwrap();
        assert!(
            !output.status.success(),
            "Invalid controls must fail: {args:?}"
        );
        assert!(output.stdout.is_empty());
    }
}
