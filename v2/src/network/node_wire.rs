//! Bounded JSON requests over loopback TCP. No cross-machine authentication.
use super::node_store::Store;
use serde_json::{json, Value};
use std::{
    io::{BufRead, BufReader, Read, Write},
    net::{SocketAddr, TcpListener, TcpStream},
    path::Path,
    time::Duration,
};
const LIMIT: u64 = 2_000_000;
fn receive(stream: &mut TcpStream) -> Result<Value, String> {
    let mut line = String::new();
    BufReader::new(stream.take(LIMIT))
        .read_line(&mut line)
        .map_err(|e| e.to_string())?;
    if !line.ends_with('\n') {
        return Err("Truncated or oversized node message".into());
    }
    serde_json::from_str(&line).map_err(|e| e.to_string())
}
fn send(stream: &mut TcpStream, value: &Value) -> Result<(), String> {
    let mut bytes = serde_json::to_vec(value).map_err(|e| e.to_string())?;
    bytes.push(b'\n');
    if bytes.len() as u64 > LIMIT {
        return Err("Node message too large".into());
    }
    stream.write_all(&bytes).map_err(|e| e.to_string())
}
fn deadlines(stream: &TcpStream) -> Result<(), String> {
    stream
        .set_read_timeout(Some(Duration::from_secs(2)))
        .map_err(|e| e.to_string())?;
    stream
        .set_write_timeout(Some(Duration::from_secs(2)))
        .map_err(|e| e.to_string())
}
pub fn request(address: &str, value: &Value) -> Result<Value, String> {
    let address: SocketAddr = address
        .parse()
        .map_err(|_| "Invalid numeric socket address")?;
    if !address.ip().is_loopback() {
        return Err("Node transport is loopback only".into());
    }
    let mut stream = TcpStream::connect_timeout(&address, Duration::from_millis(500))
        .map_err(|e| e.to_string())?;
    deadlines(&stream)?;
    send(&mut stream, value)?;
    let response = receive(&mut stream)?;
    if response["ok"] != true {
        return Err(response["error"]
            .as_str()
            .unwrap_or("Node request failed")
            .into());
    }
    Ok(response["data"].clone())
}
fn handle(store: &Store, hello: &Value, value: Value) -> Result<Value, String> {
    let id = value["id"].as_str().unwrap_or("");
    match value["op"].as_str() {
        Some("health") => Ok(hello.clone()),
        Some("get") => Ok(json!({"bytes":store.get(id)?})),
        Some("put") => {
            let bytes: Vec<u8> =
                serde_json::from_value(value["bytes"].clone()).map_err(|e| e.to_string())?;
            store.put(id, &bytes)?;
            Ok(json!({"stored_bytes":bytes.len()}))
        }
        _ => Err("Unknown node operation".into()),
    }
}
pub fn serve(directory: &Path, ready: &Path) -> Result<(), String> {
    let store = Store::open(directory)?;
    let listener = TcpListener::bind("127.0.0.1:0").map_err(|e| e.to_string())?;
    let hello = json!({"address":listener.local_addr().map_err(|e| e.to_string())?.to_string(),
        "pid":std::process::id(),"node_id":store.identity,
        "session":crate::crypto::hash(&crate::crypto::random::<16>())});
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(ready)
        .map_err(|e| e.to_string())?;
    file.write_all(hello.to_string().as_bytes())
        .map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())?;
    for connection in listener.incoming() {
        let mut stream = connection.map_err(|e| e.to_string())?;
        if deadlines(&stream).is_err() {
            continue;
        }
        let result = receive(&mut stream).and_then(|value| handle(&store, &hello, value));
        let response = match result {
            Ok(data) => json!({"ok":true,"data":data}),
            Err(error) => json!({"ok":false,"error":error}),
        };
        let _ = send(&mut stream, &response);
    }
    Ok(())
}
