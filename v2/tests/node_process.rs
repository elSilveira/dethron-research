use serde_json::json;
use std::{
    fs,
    path::Path,
    process::{Child, Command},
    time::{Duration, Instant},
};
use tron_v2::network::{
    node_control::{genesis, repair},
    node_store::Store,
    node_wire::request,
};

struct Server(Child);
impl Drop for Server {
    fn drop(&mut self) {
        let _ = self.0.kill();
        let _ = self.0.wait();
    }
}
fn start(dir: &Path, ready: &Path) -> (Server, serde_json::Value) {
    let child = Command::new(env!("CARGO_BIN_EXE_dna_node"))
        .args(["serve", dir.to_str().unwrap(), ready.to_str().unwrap()])
        .spawn()
        .unwrap();
    let server = Server(child);
    let deadline = Instant::now() + Duration::from_secs(10);
    loop {
        if let Ok(bytes) = fs::read(ready) {
            if let Ok(value) = serde_json::from_slice(&bytes) {
                return (server, value);
            }
        }
        assert!(Instant::now() < deadline, "node did not start");
        std::thread::sleep(Duration::from_millis(20));
    }
}
#[test]
fn fresh_processes_restore_identity_and_repair_only_from_authenticated_live_services() {
    let folder = std::env::temp_dir().join(format!(
        "tron-nodes-{}",
        tron_v2::crypto::hash(&tron_v2::crypto::random::<16>())
    ));
    fs::create_dir(&folder).unwrap();
    let source = folder.join("source");
    let authority = genesis(
        &Store::open(&source).unwrap(),
        b"an independently expected object",
    )
    .unwrap();
    let (first, hello) = start(&source, &folder.join("first.json"));
    let identity = hello["node_id"].clone();
    drop(first);
    let (second, resumed) = start(&source, &folder.join("second.json"));
    assert_eq!(resumed["node_id"], identity);
    assert_ne!(resumed["session"], hello["session"]);
    let (target, replacement) = start(&folder.join("replacement"), &folder.join("target.json"));
    let donor = resumed["address"].as_str().unwrap().to_string();
    let dest = replacement["address"].as_str().unwrap().to_string();
    let report = repair(
        &authority,
        std::slice::from_ref(&donor),
        std::slice::from_ref(&dest),
    )
    .unwrap();
    assert_eq!(report["object"], "an independently expected object");
    assert_eq!(report["verified_steps"], 3);
    assert_eq!(report["verified_targets"], 1);
    let mut wrong = authority.clone();
    wrong.key[0] ^= 1;
    assert!(repair(&wrong, std::slice::from_ref(&donor), &[]).is_err());
    assert!(request(&donor, &json!({"op":"get","id":"../identity"})).is_err());
    drop(second);
    let restored = repair(&authority, std::slice::from_ref(&dest), &[]).unwrap();
    assert_eq!(restored["object_hash"], authority.expected_hash);
    assert!(repair(&authority, &[donor], &[]).is_err());
    drop(target);
}
